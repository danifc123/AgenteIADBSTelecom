"""Cliente HTTP para a API webservice da IXC — camada integrations.

Convenção da API webservice v1 da IXC (verificada contra a documentação
pública de integração da IXC / uso comum da comunidade — os nomes de campo
abaixo, especialmente os das tabelas de chamado/OS, DEVEM ser confirmados
contra a instância demo real durante o desenvolvimento, pois variam um
pouco entre instalações):

- Toda consulta é um POST para https://<host>/webservice/v1/<tabela>
- Autenticação: HTTP Basic onde o par "usuário:senha" é substituído pelo
  próprio token da API, ou seja, `Authorization: Basic base64(<token>)`
  (não é base64("usuario:token") — o token da IXC já contém as duas partes).
- Um header customizado `ixcsoft: listar` é obrigatório para consultas de
  listagem.
- Corpo em JSON: {"qtype": "<tabela>.<coluna>", "query": "<valor>",
  "oper": "=", "page": "1", "rp": "20"}.
- Respostas de sucesso trazem uma lista "registros" e um "total"; respostas
  de erro variam (às vezes HTTP 200 com corpo "type": "error", às vezes
  status != 200) — tratamos as duas formas como falha.

Se os nomes de tabela/campo abaixo divergirem da instalação-alvo, este é o
único arquivo que precisa mudar — quem chama só vê os métodos tipados no
final da classe.
"""

from __future__ import annotations

import base64

import httpx

# Confirmado contra o ambiente demo real: a IXC guarda telefone/CPF/CNPJ
# FORMATADOS (com parênteses/traço/pontos), e a consulta por "=" exige o
# valor exatamente igual ao armazenado — buscar só com dígitos retorna
# zero resultados. Por isso normalizamos para o formato brasileiro padrão
# antes de consultar, em vez de só extrair dígitos.


def _format_telefone(digits: str) -> str:
    """Formata dígitos de telefone no padrão armazenado pela IXC. Retorna a string formatada."""
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return digits


def _format_cpf_cnpj(digits: str) -> str:
    """Formata dígitos de CPF/CNPJ no padrão armazenado pela IXC. Retorna a string formatada."""
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    return digits


# IDs da tabela su_oss_assunto neste ambiente demo (confirmados por leitura
# direta — "Lentidão" e "VISTORIA TECNICA (OS)" respectivamente). Numa
# instalação diferente da IXC, reconferir em Suporte > Assuntos.
_ASSUNTO_LENTIDAO_ID = 6
_ASSUNTO_VISITA_TECNICA_ID = 22

# id do setor "SETOR TECNICO" neste ambiente demo — confirmado comparando
# com um chamado de referência real (id 13623) que aparece corretamente
# no painel. Numa instalação diferente, reconferir em Configurações > Setores.
_SETOR_TECNICO_ID = "7"

from app.core.config import Settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# region Exceptions


class IXCError(Exception):
    """Classe-base para toda falha de integração com a IXC."""


class IXCAuthError(IXCError):
    """A IXC rejeitou as credenciais (token) enviadas."""


class IXCMalformedResponseError(IXCError):
    """A IXC respondeu, mas o payload não veio no formato esperado."""


class IXCNotFoundError(IXCError):
    """A consulta teve sucesso, mas não retornou nenhum registro."""


class IXCUnavailableError(IXCError):
    """A IXC não respondeu — falha de rede, timeout ou erro 5xx."""


class IXCValidationError(IXCError):
    """A IXC recusou a criação do registro por campos obrigatórios ausentes/inválidos."""


# endregion

# region Client


class IXCClient:
    """Cliente assíncrono para a API webservice v1 da IXC."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        auth_value = base64.b64encode(settings.ixc_token.encode("utf-8")).decode("ascii")
        self._client = httpx.AsyncClient(
            base_url=settings.ixc_base_url.rstrip("/"),
            timeout=settings.ixc_timeout_seconds,
            headers={
                "Authorization": f"Basic {auth_value}",
                "Content-Type": "application/json",
            },
        )

    # --- lifecycle ---

    async def aclose(self) -> None:
        """Fecha a conexão HTTP subjacente. Não retorna valor."""
        await self._client.aclose()

    # --- helpers privados (ordem alfabética) ---

    async def _create(self, table: str, payload: dict) -> dict:
        """Cria um registro na tabela informada (ex: abertura de chamado/OS). Retorna o registro criado pela IXC.

        TODO(verificar contra demo): confirmar se a IXC exige um header
        específico para inclusão (diferente de "ixcsoft: listar") nesta
        instalação — hoje assumimos POST direto sem esse header.
        """
        try:
            response = await self._client.post(f"/{table}", json=payload)
        except httpx.TimeoutException as exc:
            logger.error("ixc_timeout", table=table, operation="create")
            raise IXCUnavailableError(f"IXC não respondeu a tempo ao criar registro em '{table}'") from exc
        except httpx.HTTPError as exc:
            logger.error("ixc_connection_error", table=table, operation="create", error=str(exc))
            raise IXCUnavailableError(f"Falha de conexão com a IXC ao criar registro em '{table}'") from exc

        self._raise_for_error_status(response, table)

        try:
            body = response.json()
        except ValueError as exc:
            logger.error("ixc_malformed_json", table=table, operation="create")
            raise IXCMalformedResponseError("Resposta da IXC não é um JSON válido") from exc

        # A IXC responde HTTP 200 mesmo quando a criação falha por campo
        # obrigatório ausente — o corpo é que indica o erro ("type": "error").
        # Sem este check, uma criação rejeitada era logada e reportada como
        # sucesso silenciosamente (bug real, encontrado testando contra o
        # ambiente demo: faltam id_assunto/filial_id/setor/prioridade/origem
        # no payload de su_oss_chamado — confirmar valores válidos no painel
        # admin antes de usar em produção).
        if isinstance(body, dict) and body.get("type") == "error":
            message = body.get("message", "erro desconhecido")
            logger.error("ixc_create_validation_error", table=table, message=message)
            raise IXCValidationError(f"IXC recusou a criação em '{table}': {message}")

        logger.info("ixc_create_ok", table=table)
        return body

    async def _list(
        self,
        table: str,
        qtype: str,
        query: str,
        oper: str = "=",
        page: str = "1",
        rp: str = "20",
        sortname: str | None = None,
        sortorder: str = "asc",
    ) -> list[dict]:
        """Consulta registros na tabela informada. Retorna a lista de registros encontrados."""
        payload: dict = {"qtype": qtype, "query": query, "oper": oper, "page": page, "rp": rp}
        if sortname:
            payload["sortname"] = sortname
            payload["sortorder"] = sortorder

        try:
            response = await self._client.post(f"/{table}", json=payload, headers={"ixcsoft": "listar"})
        except httpx.TimeoutException as exc:
            logger.error("ixc_timeout", table=table, qtype=qtype)
            raise IXCUnavailableError(f"IXC não respondeu a tempo ao consultar '{table}'") from exc
        except httpx.HTTPError as exc:
            logger.error("ixc_connection_error", table=table, qtype=qtype, error=str(exc))
            raise IXCUnavailableError(f"Falha de conexão com a IXC ao consultar '{table}'") from exc

        self._raise_for_error_status(response, table)

        try:
            body = response.json()
        except ValueError as exc:
            logger.error("ixc_malformed_json", table=table, status=response.status_code)
            raise IXCMalformedResponseError("Resposta da IXC não é um JSON válido") from exc

        if isinstance(body, dict) and body.get("type") == "error":
            message = body.get("message", "erro desconhecido")
            logger.error("ixc_api_error", table=table, message=message)
            raise IXCMalformedResponseError(f"IXC retornou erro: {message}")

        if not isinstance(body, dict) or "total" not in body:
            logger.error("ixc_unexpected_shape", table=table)
            raise IXCMalformedResponseError(f"Resposta inesperada da IXC para '{table}'")

        # Confirmado contra o ambiente demo real: quando a consulta não
        # encontra nenhum registro, a IXC retorna só {"page":..,"total":0},
        # sem a chave "registros" — isso é uma lista vazia válida, não uma
        # resposta malformada.
        registros = body.get("registros") or []
        logger.info("ixc_query_ok", table=table, qtype=qtype, count=len(registros))
        return registros

    @staticmethod
    def _raise_for_error_status(response: httpx.Response, table: str) -> None:
        """Levanta a exceção tipada correspondente ao status HTTP, se for erro. Não retorna valor."""
        if response.status_code in (401, 403):
            logger.error("ixc_auth_error", table=table, status=response.status_code)
            raise IXCAuthError("Credenciais da IXC rejeitadas (verifique IXC_TOKEN)")
        if response.status_code >= 500:
            logger.error("ixc_server_error", table=table, status=response.status_code)
            raise IXCUnavailableError(f"IXC retornou erro {response.status_code}")

    # --- operações tipadas (ordem alfabética) ---

    async def abrir_chamado_suporte(self, cliente_id: str, resumo: str) -> dict:
        """Abre um chamado de suporte N1 (fila remota) para o cliente. Retorna o registro do chamado criado.

        Payload confirmado comparando um insert de teste real com um chamado
        de referência já existente no ambiente demo (id 13623, "Corretiva
        (Sem Acesso)", visível corretamente como "Aberta"/"SETOR TECNICO" no
        painel): `status="A"` (Aberta), `setor="7"` (Setor Técnico) e
        `tipo="C"` (Corretiva) são os valores que a IXC realmente reconhece
        — os que usávamos antes (`status="N"`, `setor="1"`, `tipo="A"`)
        criavam o chamado, mas com esses campos em branco no painel,
        invisíveis nos filtros padrão da fila de Suporte.
        `id_assunto=6` é "Lentidão" no catálogo de assuntos desse ambiente
        demo especificamente — em outra instalação da IXC esse id pode ser
        diferente e precisa ser reconferido em Suporte > Assuntos.
        `origem_endereco="L"` (usar o endereço já cadastrado do cliente) foi
        tentado, mas a IXC exige `id_login` nesse caso — dado que não
        buscamos hoje na identificação. Mantido `"M"` (manual) com o texto
        de aviso até isso ser resolvido (ver limitações conhecidas).
        """
        return await self._create(
            "su_oss_chamado",
            {
                "id_cliente": cliente_id,
                "id_filial": "1",
                "id_assunto": str(_ASSUNTO_LENTIDAO_ID),
                "id_setor": _SETOR_TECNICO_ID,
                "setor": _SETOR_TECNICO_ID,
                "mensagem": resumo,
                "tipo": "C",
                "prioridade": "N",
                "status": "A",
                "liberado": "1",
                "melhor_horario_agenda": "Q",
                "origem_endereco": "M",
                "endereco": "Endereço a confirmar com o cliente",
            },
        )

    async def agendar_visita_tecnica(self, cliente_id: str, periodo_preferido: str, resumo: str) -> dict:
        """Agenda uma visita técnica N2 (defeito físico) para o cliente. Retorna o registro do agendamento criado.

        Mesma base de `abrir_chamado_suporte` — `id_assunto=22` é "VISTORIA
        TECNICA (OS)" nesse ambiente demo, e a prioridade sobe pra "A"
        (Alta) por ser um problema físico que não se resolve remotamente.
        `periodo_preferido` ainda não tem um campo confirmado no
        `su_oss_chamado` para isso — por ora é só anexado ao texto da
        mensagem, não estruturado.
        """
        return await self._create(
            "su_oss_chamado",
            {
                "id_cliente": cliente_id,
                "id_filial": "1",
                "id_assunto": str(_ASSUNTO_VISITA_TECNICA_ID),
                "id_setor": _SETOR_TECNICO_ID,
                "setor": _SETOR_TECNICO_ID,
                "mensagem": f"{resumo} (período preferido: {periodo_preferido})",
                "tipo": "C",
                "prioridade": "A",
                "status": "A",
                "liberado": "1",
                "melhor_horario_agenda": "Q",
                "origem_endereco": "M",
                "endereco": "Endereço a confirmar com o cliente",
            },
        )

    async def find_cliente_by_cpf_cnpj(self, cpf_cnpj: str) -> dict:
        """Busca um cliente pelo CPF/CNPJ. Retorna o primeiro registro encontrado."""
        digits = "".join(ch for ch in cpf_cnpj if ch.isdigit())
        records = await self._list("cliente", "cliente.cnpj_cpf", _format_cpf_cnpj(digits))
        if not records:
            raise IXCNotFoundError("Nenhum cliente encontrado para o documento informado")
        return records[0]

    async def find_cliente_by_telefone(self, telefone: str) -> dict:
        """Busca um cliente pelo telefone celular cadastrado. Retorna o primeiro registro encontrado."""
        digits = "".join(ch for ch in telefone if ch.isdigit())
        records = await self._list("cliente", "cliente.telefone_celular", _format_telefone(digits))
        if not records:
            raise IXCNotFoundError(f"Nenhum cliente encontrado para o telefone {telefone}")
        return records[0]

    async def get_cliente_by_id(self, cliente_id: str) -> dict:
        """Busca um cliente pelo ID interno da IXC. Retorna o registro do cliente."""
        records = await self._list("cliente", "cliente.id", str(cliente_id))
        if not records:
            raise IXCNotFoundError(f"Cliente {cliente_id} não encontrado")
        return records[0]

    async def list_boletos_abertos(self, cliente_id: str) -> list[dict]:
        """Lista os boletos em aberto (contas a receber) do cliente. Retorna a lista de boletos.

        Regra de negócio: a consulta filtra só por `id_cliente` (a API de
        listagem da IXC não confirmadamente suporta duas condições numa só
        chamada) — por isso o filtro de `status == "A"` (aberto, confirmado
        contra o ambiente demo) é aplicado aqui do lado do cliente, para não
        devolver boleto já pago como se estivesse em aberto.
        """
        registros = await self._list(
            "fn_areceber",
            "fn_areceber.id_cliente",
            str(cliente_id),
            sortname="fn_areceber.data_vencimento",
            sortorder="asc",
        )
        return [registro for registro in registros if registro.get("status") == "A"]

    async def list_contratos_ativos(self, cliente_id: str) -> list[dict]:
        """Lista os contratos/planos ativos do cliente. Retorna a lista de contratos."""
        return await self._list("cliente_contrato", "cliente_contrato.id_cliente", str(cliente_id))


# endregion
