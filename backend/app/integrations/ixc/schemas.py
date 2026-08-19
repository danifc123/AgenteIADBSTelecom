"""Normalização de registros brutos da IXC para modelos internos — camada integrations.

Regra de negócio: manter essa tradução isolada aqui significa que uma
mudança de nome de campo do lado da IXC só precisa ser corrigida numa
função pequena, sem afetar o resto da aplicação.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.models import Customer

# region Models


class Boleto(BaseModel):
    """Boleto/fatura normalizado a partir de um registro `fn_areceber` da IXC."""

    id: str
    linha_digitavel: str | None = None
    link: str | None = None
    status: str
    valor: str
    vencimento: str


class VisitaTecnica(BaseModel):
    """Confirmação de agendamento de visita técnica (N2), normalizada a partir da resposta da IXC."""

    id: str
    periodo_preferido: str
    status: str


# endregion

# region Mappers (ordem alfabética)


def boleto_from_ixc_record(record: dict) -> Boleto:
    """Converte um registro bruto de `fn_areceber` para `Boleto`. Retorna o modelo normalizado."""
    return Boleto(
        id=str(record.get("id", "")),
        linha_digitavel=record.get("linha_digitavel"),
        link=record.get("link_boleto") or record.get("url_boleto"),
        status=record.get("status", "aberto"),
        valor=record.get("valor", "0"),
        vencimento=record.get("data_vencimento", ""),
    )


def customer_from_ixc_record(record: dict) -> Customer:
    """Converte um registro bruto de `cliente` para `Customer`. Retorna o modelo normalizado."""
    return Customer(
        cpf_cnpj=record.get("cnpj_cpf"),
        id=str(record.get("id", "")),
        name=record.get("razao") or record.get("fantasia") or "Cliente",
        phone=record.get("telefone_celular") or record.get("fone"),
        status=record.get("ativo"),
    )


def visita_tecnica_from_ixc_record(record: dict) -> VisitaTecnica:
    """Converte a resposta de criação de chamado N2 para `VisitaTecnica`. Retorna o modelo normalizado."""
    return VisitaTecnica(
        id=str(record.get("id", "")),
        periodo_preferido=record.get("periodo_preferido", ""),
        status=record.get("status", "aberto"),
    )


# endregion
