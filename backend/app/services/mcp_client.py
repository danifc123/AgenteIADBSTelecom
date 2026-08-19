"""Cliente MCP: sobe o servidor MCP como subprocess e fala com ele — camada services.

Regra de negócio: o servidor MCP roda como subprocess via transporte stdio
(não expõe porta de rede), com uma única `ClientSession` de vida longa
reaproveitada durante todo o ciclo de vida da aplicação — não é aberta uma
sessão nova a cada requisição.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# region McpGateway


class McpGateway:
    """Gerencia o subprocess do servidor MCP e expõe `list_tools`/`call_tool` para o restante do backend."""

    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Executa a tool MCP pelo nome, com os argumentos dados. Retorna o resultado já parseado como dicionário."""
        if self._session is None:
            raise RuntimeError("McpGateway não foi iniciado — chame start() antes de call_tool().")

        result = await self._session.call_tool(name, arguments)
        if not result.content:
            return {"success": False, "error_code": "EmptyToolResult", "message": "Tool não retornou conteúdo."}

        first_block = result.content[0]
        text = getattr(first_block, "text", None)
        if text is None:
            return {"success": False, "error_code": "UnsupportedContentType", "message": "Conteúdo da tool não é texto."}

        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            # A tool pode ter retornado texto puro (não-JSON) — devolve como está.
            return {"success": True, "raw_text": text}

    async def list_tools(self) -> list[Tool]:
        """Lista as tools disponíveis no servidor MCP conectado. Retorna a lista de `Tool`."""
        if self._session is None:
            raise RuntimeError("McpGateway não foi iniciado — chame start() antes de list_tools().")
        response = await self._session.list_tools()
        return response.tools

    async def start(self) -> None:
        """Sobe o subprocess do servidor MCP e inicializa a sessão. Não retorna valor.

        Regra de negócio: `StdioServerParameters` NÃO herda o ambiente do
        processo pai por padrão (segurança do próprio SDK do MCP) — por
        isso o `env` precisa ser passado explicitamente, senão o subprocess
        sobe sem IXC_TOKEN/IXC_BASE_URL e falha ao iniciar.
        """
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.integrations.mcp_server.server"],
            env=dict(os.environ),
        )
        read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
        session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._session = session
        logger.info("mcp_gateway_started")

    async def stop(self) -> None:
        """Encerra a sessão MCP e o subprocess. Não retorna valor."""
        await self._exit_stack.aclose()
        self._session = None
        logger.info("mcp_gateway_stopped")


# endregion

# region Factory

_gateway: McpGateway | None = None


def get_mcp_gateway() -> McpGateway:
    """Retorna a instância única de `McpGateway` da aplicação (singleton em processo)."""
    global _gateway
    if _gateway is None:
        _gateway = McpGateway()
    return _gateway


# endregion
