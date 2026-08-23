"""Testes de integração contra a IXC demo real (não mockada).

Regra de negócio: estes testes só rodam se `RUN_LIVE_IXC_TESTS=1` estiver
setado explicitamente — não devem rodar em CI por padrão (dependem de rede
e de um cliente de teste específico existir no ambiente demo compartilhado).

Para rodar: `RUN_LIVE_IXC_TESTS=1 pytest tests/test_ixc_client_live.py -v`
(com um `.env` válido apontando pro ambiente demo).
"""

from __future__ import annotations

import os

import pytest

from app.core.config import get_settings
from app.integrations.ixc.client import IXCClient

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_IXC_TESTS") != "1",
    reason="Só roda com RUN_LIVE_IXC_TESTS=1 (evita depender de rede/dados reais em CI).",
)

# Cliente de teste conhecido no ambiente demo (não é dado sensível — é um
# registro de exemplo público da própria demo.ixcsoft.com.br).
_KNOWN_PHONE_DIGITS = "54996656569"
_KNOWN_NAME = "Everaldo"

# region Testes (ordem alfabética)


async def test_find_cliente_by_telefone_accepts_digits_only():
    """Buscar só com dígitos (sem o cliente formatar nada) deve encontrar o cliente real."""
    client = IXCClient(get_settings())
    try:
        record = await client.find_cliente_by_telefone(_KNOWN_PHONE_DIGITS)
        assert record["razao"] == _KNOWN_NAME
    finally:
        await client.aclose()


async def test_list_boletos_abertos_only_returns_status_a():
    """Todo boleto retornado deve ter status 'A' (aberto) — nunca um já pago."""
    client = IXCClient(get_settings())
    try:
        cliente = await client.find_cliente_by_telefone(_KNOWN_PHONE_DIGITS)
        boletos = await client.list_boletos_abertos(cliente["id"])
        assert all(b["status"] == "A" for b in boletos)
    finally:
        await client.aclose()


# endregion
