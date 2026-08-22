"""Dependências injetáveis do FastAPI (`Depends`) — camada api.

Regra de negócio: nenhuma lógica de negócio mora aqui — só cabeamento
entre a requisição HTTP e os singletons das outras camadas.
"""

from __future__ import annotations

from fastapi import Request

from app.core.session_store import SessionStore, get_session_store
from app.services.ai.mcp_client import McpGateway, get_mcp_gateway
from app.services.ai.ollama_client import OllamaClient, get_ollama_client

# region Dependências (ordem alfabética)


def get_all_tools(request: Request) -> list[dict]:
    """Lê a lista de tools MCP (já convertidas para o formato Ollama) cacheada em `app.state`. Retorna a lista de tools."""
    return request.app.state.all_tools


def get_mcp_gateway_dep() -> McpGateway:
    """Dependência FastAPI para o `McpGateway`. Retorna a instância singleton."""
    return get_mcp_gateway()


def get_ollama_client_dep() -> OllamaClient:
    """Dependência FastAPI para o `OllamaClient`. Retorna a instância singleton."""
    return get_ollama_client()


def get_session_store_dep() -> SessionStore:
    """Dependência FastAPI para o `SessionStore`. Retorna a instância singleton."""
    return get_session_store()


# endregion
