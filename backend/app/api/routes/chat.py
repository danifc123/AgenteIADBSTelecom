"""Rotas de chat — camada api."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_all_tools, get_mcp_gateway_dep, get_ollama_client_dep, get_session_store_dep
from app.core.session_store import SessionStore
from app.services.chat_service import handle_chat_turn
from app.services.ai.mcp_client import McpGateway
from app.services.ai.ollama_client import OllamaClient

router = APIRouter(prefix="/api", tags=["chat"])

# region Schemas


class ChatRequest(BaseModel):
    """Corpo da requisição de uma mensagem de chat."""

    message: str
    session_id: str


class ChatResponse(BaseModel):
    """Resposta de um turno de chat: texto, departamento atual, estágio de suporte e sugestões rápidas."""

    department: str | None = None
    quick_replies: list[str] | None = None
    reply: str
    support_stage: str | None = None


# endregion

# region Rotas


@router.post("/chat", response_model=ChatResponse)
async def post_chat(
    request: ChatRequest,
    ollama_client: OllamaClient = Depends(get_ollama_client_dep),
    mcp_gateway: McpGateway = Depends(get_mcp_gateway_dep),
    session_store: SessionStore = Depends(get_session_store_dep),
    all_tools: list[dict] = Depends(get_all_tools),
) -> ChatResponse:
    """Processa uma mensagem do cliente e retorna a resposta do assistente. Retorna `ChatResponse`."""
    state = await session_store.get(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada. Identifique-se novamente.")

    reply, quick_replies = await handle_chat_turn(state, request.message, ollama_client, mcp_gateway, session_store, all_tools)

    return ChatResponse(
        reply=reply,
        department=state.department,
        support_stage=state.support_stage,
        quick_replies=quick_replies,
    )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, session_store: SessionStore = Depends(get_session_store_dep)) -> dict:
    """Retorna o histórico de mensagens da sessão informada."""
    state = await session_store.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return {"session_id": state.session_id, "history": [m.model_dump(exclude_none=True) for m in state.history]}


# endregion
