"""Rota de identificação do cliente — camada api.

Regra de negócio: cliente não encontrado não é um erro de sistema — a rota
retorna 200 com `success: false` para o app mobile mostrar uma tela de
"não encontramos seu cadastro" em vez de tratar como bug.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_mcp_gateway_dep, get_session_store_dep
from app.core.session_store import SessionStore
from app.domain.models import Customer
from app.services.identification_service import CustomerNotFoundError, identify_and_greet
from app.services.mcp_client import McpGateway

router = APIRouter(prefix="/api", tags=["identification"])

# region Schemas


class IdentifyRequest(BaseModel):
    """Corpo da requisição de identificação: telefone ou CPF/CNPJ do cliente."""

    contact: str


class IdentifyResponse(BaseModel):
    """Resposta da identificação: sucesso, sessão criada, cliente e saudação — ou falha com mensagem amigável."""

    customer: Customer | None = None
    greeting_message: str | None = None
    message: str | None = None
    session_id: str | None = None
    success: bool


# endregion

# region Rotas


@router.post("/identify", response_model=IdentifyResponse)
async def post_identify(
    request: IdentifyRequest,
    mcp_gateway: McpGateway = Depends(get_mcp_gateway_dep),
    session_store: SessionStore = Depends(get_session_store_dep),
) -> IdentifyResponse:
    """Identifica o cliente pelo contato informado e cria a sessão de atendimento. Retorna `IdentifyResponse`."""
    try:
        state, greeting = await identify_and_greet(request.contact, mcp_gateway, session_store)
    except CustomerNotFoundError as exc:
        return IdentifyResponse(success=False, message=str(exc))

    return IdentifyResponse(
        success=True,
        session_id=state.session_id,
        customer=state.customer,
        greeting_message=greeting,
    )


# endregion
