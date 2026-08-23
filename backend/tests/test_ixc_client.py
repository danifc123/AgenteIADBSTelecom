"""Testes do cliente IXC: sucesso, não encontrado, timeout, resposta malformada e formato do header de auth."""

from __future__ import annotations

import base64

import httpx
import pytest
import respx
from httpx import Response

from app.integrations.ixc.client import (
    IXCAuthError,
    IXCClient,
    IXCMalformedResponseError,
    IXCNotFoundError,
    IXCUnavailableError,
)

_BASE_URL = "https://demo.ixcsoft.com.br/webservice/v1"

# region Testes (ordem alfabética)


@respx.mock
async def test_find_cliente_by_telefone_not_found(settings):
    """Consulta sem registros deve levantar `IXCNotFoundError`."""
    respx.post(f"{_BASE_URL}/cliente").mock(
        return_value=Response(200, json={"type": "success", "registros": [], "total": "0"})
    )
    client = IXCClient(settings)
    with pytest.raises(IXCNotFoundError):
        await client.find_cliente_by_telefone("00000000000")
    await client.aclose()


@respx.mock
async def test_find_cliente_by_telefone_success(settings):
    """Consulta com registro encontrado deve retornar o primeiro registro."""
    respx.post(f"{_BASE_URL}/cliente").mock(
        return_value=Response(
            200,
            json={
                "type": "success",
                "registros": [{"id": "1", "razao": "Maria Silva", "telefone_celular": "64998234471"}],
                "total": "1",
            },
        )
    )
    client = IXCClient(settings)
    record = await client.find_cliente_by_telefone("(64) 99823-4471")
    assert record["razao"] == "Maria Silva"
    await client.aclose()


@respx.mock
async def test_malformed_json_response_raises(settings):
    """Corpo que não é JSON válido deve levantar `IXCMalformedResponseError`."""
    respx.post(f"{_BASE_URL}/cliente").mock(return_value=Response(200, text="isto não é JSON"))
    client = IXCClient(settings)
    with pytest.raises(IXCMalformedResponseError):
        await client.find_cliente_by_telefone("64998234471")
    await client.aclose()


@respx.mock
async def test_request_includes_auth_and_listar_headers(settings):
    """O header Authorization deve ser Basic base64(token), e `ixcsoft: listar` deve estar presente."""
    route = respx.post(f"{_BASE_URL}/cliente").mock(
        return_value=Response(200, json={"type": "success", "registros": [], "total": "0"})
    )
    client = IXCClient(settings)
    try:
        await client.find_cliente_by_telefone("64998234471")
    except IXCNotFoundError:
        pass

    sent_request = route.calls[0].request
    expected_auth = "Basic " + base64.b64encode(settings.ixc_token.encode("utf-8")).decode("ascii")
    assert sent_request.headers["authorization"] == expected_auth
    assert sent_request.headers["ixcsoft"] == "listar"
    await client.aclose()


@respx.mock
async def test_unauthorized_status_raises_auth_error(settings):
    """Status 401 deve levantar `IXCAuthError`."""
    respx.post(f"{_BASE_URL}/cliente").mock(return_value=Response(401, json={}))
    client = IXCClient(settings)
    with pytest.raises(IXCAuthError):
        await client.find_cliente_by_telefone("64998234471")
    await client.aclose()


@respx.mock
async def test_unreachable_host_raises_unavailable_error(settings):
    """Timeout de rede deve levantar `IXCUnavailableError`."""
    respx.post(f"{_BASE_URL}/cliente").mock(side_effect=httpx.TimeoutException("timeout"))
    client = IXCClient(settings)
    with pytest.raises(IXCUnavailableError):
        await client.find_cliente_by_telefone("64998234471")
    await client.aclose()


# endregion
