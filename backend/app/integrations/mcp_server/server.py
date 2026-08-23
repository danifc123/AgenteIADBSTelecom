"""Servidor MCP que expõe as operações da IXC como ferramentas — camada integrations.

Regra de negócio de segurança/confiabilidade: nenhuma exceção da IXC pode
vazar para fora de uma tool — todas são capturadas e convertidas num
payload estruturado de erro (`{"success": False, "error_code": ..., "message": ...}`),
para que o modelo (Ollama) sempre consiga responder de forma conversacional
em vez de travar o atendimento.

As docstrings de cada tool são a engenharia de prompt que orienta o modelo
sobre quando e como chamar cada ferramenta — são propositalmente escritas
de forma prescritiva (quando usar, o que não fazer) para reduzir o risco de
alucinação/uso incorreto pelo modelo local.

Roda como subprocess via stdio, iniciado pelo backend em `main.py`
(`python -m app.integrations.mcp_server.server`).
"""

from __future__ import annotations

from mcp.server import MCPServer

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.integrations.ixc.client import IXCClient, IXCError
from app.integrations.ixc.schemas import (
    boleto_from_ixc_record,
    customer_from_ixc_record,
    visita_tecnica_from_ixc_record,
)
from app.integrations.ixc.static_data import load_plans

logger = get_logger(__name__)

mcp = MCPServer("dbs-telecom-ixc")
_ixc_client = IXCClient(get_settings())

# region Helpers


def _error_payload(exc: IXCError) -> dict:
    """Converte uma exceção da IXC num payload estruturado de erro para o modelo. Retorna o dicionário de erro."""
    return {"success": False, "error_code": type(exc).__name__, "message": str(exc)}


# endregion

# region Tools (ordem alfabética)


@mcp.tool()
async def get_boleto(customer_id: str) -> dict:
    """Consulta o boleto/fatura em aberto mais próximo do vencimento para o cliente já identificado.

    Use esta ferramenta sempre que o cliente pedir boleto, fatura, segunda
    via ou "quanto devo". Não invente valores ou datas — se a consulta
    falhar ou não houver boleto em aberto, informe isso ao cliente
    exatamente como retornado, sem completar com suposições.
    """
    try:
        registros = await _ixc_client.list_boletos_abertos(customer_id)
        if not registros:
            return {"success": True, "boleto": None, "message": "Nenhum boleto em aberto encontrado."}
        boleto = boleto_from_ixc_record(registros[0])
        return {"success": True, "boleto": boleto.model_dump()}
    except IXCError as exc:
        logger.error("mcp_tool_error", tool="get_boleto", error=str(exc))
        return _error_payload(exc)


@mcp.tool()
async def get_customer_plan(customer_id: str) -> dict:
    """Consulta o(s) plano(s)/contrato(s) atualmente ativo(s) do cliente já identificado.

    Use para comparar o plano atual do cliente com uma oferta antes de
    recomendar upgrade, ou quando o cliente perguntar "qual é o meu plano".
    """
    try:
        registros = await _ixc_client.list_contratos_ativos(customer_id)
        return {"success": True, "contratos": registros}
    except IXCError as exc:
        logger.error("mcp_tool_error", tool="get_customer_plan", error=str(exc))
        return _error_payload(exc)


@mcp.tool()
async def identify_customer(contact: str) -> dict:
    """Identifica um cliente na IXC a partir de telefone ou CPF/CNPJ informado por ele.

    Tenta primeiro como telefone; se não encontrar, tenta como CPF/CNPJ.
    Use isso no início do atendimento, antes de qualquer outra ação — nunca
    prossiga com pedidos que dependem do cliente (boleto, plano, chamado)
    sem antes tê-lo identificado com sucesso por esta ferramenta.
    """
    digits = "".join(ch for ch in contact if ch.isdigit())
    try:
        if len(digits) <= 11 and len(digits) >= 10:
            try:
                record = await _ixc_client.find_cliente_by_telefone(digits)
            except IXCError:
                record = await _ixc_client.find_cliente_by_cpf_cnpj(digits)
        else:
            record = await _ixc_client.find_cliente_by_cpf_cnpj(digits)
        customer = customer_from_ixc_record(record)
        return {"success": True, "customer": customer.model_dump()}
    except IXCError as exc:
        logger.error("mcp_tool_error", tool="identify_customer", error=str(exc))
        return _error_payload(exc)


@mcp.tool()
def list_plans() -> dict:
    """Lista o catálogo comercial de planos disponíveis para contratação (planos urbanos e WiFi-6).

    Use esta ferramenta no fluxo Comercial para apresentar opções ao
    cliente. Os valores e condições retornados são a fonte da verdade —
    nunca invente preço, velocidade ou condição de pagamento que não
    esteja no retorno desta ferramenta.
    """
    return {"success": True, **load_plans()}


@mcp.tool()
async def log_support_escalation(customer_id: str, summary: str) -> dict:
    """Abre um chamado de suporte N1 (fila de suporte remoto) para o cliente.

    Use somente depois de concluir o roteiro de diagnóstico básico
    (múltiplos aparelhos, cabos, reiniciar equipamento) sem sucesso, e sem
    nenhum sinal de dano físico no equipamento/cabeamento — para dano
    físico, use `schedule_technical_visit` em vez desta.
    """
    try:
        registro = await _ixc_client.abrir_chamado_suporte(customer_id, summary)
        return {"success": True, "chamado": registro}
    except IXCError as exc:
        logger.error("mcp_tool_error", tool="log_support_escalation", error=str(exc))
        return _error_payload(exc)


@mcp.tool()
async def schedule_technical_visit(customer_id: str, preferred_period: str, summary: str) -> dict:
    """Agenda uma visita técnica N2 para o cliente (defeito físico ou diagnóstico remoto esgotado sem solução).

    Use quando o cliente relatar sinais de dano físico (cabo cortado,
    fibra rompida, equipamento sem nenhuma luz/energia) em qualquer momento
    da conversa, ou quando o roteiro de diagnóstico remoto (N1) não
    resolver o problema. Não tente diagnosticar mais a distância nesses
    casos — o próximo passo correto é o agendamento, não mais perguntas.
    `preferred_period` deve ser "manha", "tarde" ou "qualquer".
    """
    try:
        registro = await _ixc_client.agendar_visita_tecnica(customer_id, preferred_period, summary)
        visita = visita_tecnica_from_ixc_record(registro)
        return {"success": True, "visita": visita.model_dump()}
    except IXCError as exc:
        logger.error("mcp_tool_error", tool="schedule_technical_visit", error=str(exc))
        return _error_payload(exc)


# endregion

if __name__ == "__main__":
    mcp.run()
