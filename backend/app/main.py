"""Composition root da aplicação — sobe o FastAPI, o gateway MCP e conecta tudo.

Regra de negócio: nenhuma exceção não tratada pode vazar como HTML/stack
trace para o cliente — o handler global sempre responde em JSON estruturado.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, health, identification
from app.core.config import get_settings
from app.core.logging_config import configure_logging, get_logger
from app.services.ai.mcp_client import get_mcp_gateway
from app.services.ai.tool_schema import mcp_tools_to_ollama_format

logger = get_logger(__name__)

# region Lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação: sobe o gateway MCP e carrega as tools no início, encerra no fim."""
    settings = get_settings()
    configure_logging(settings.log_level)

    gateway = get_mcp_gateway()
    await gateway.start()
    mcp_tools = await gateway.list_tools()
    app.state.all_tools = mcp_tools_to_ollama_format(mcp_tools)
    logger.info("app_started", tool_count=len(app.state.all_tools))

    yield

    await gateway.stop()
    logger.info("app_stopped")


# endregion

# region App factory


def create_app() -> FastAPI:
    """Monta a aplicação FastAPI: CORS, rotas e handler global de exceções. Retorna a instância de `FastAPI`."""
    settings = get_settings()
    app = FastAPI(title="DBS TELECOM — Assistente Virtual", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(identification.router)
    app.include_router(chat.router)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        """Handler global: nunca deixa uma exceção não tratada vazar como HTML. Retorna JSON 500 estruturado."""
        logger.error("unhandled_exception", error=str(exc), error_type=type(exc).__name__)
        return JSONResponse(status_code=500, content={"success": False, "message": "Erro interno. Tente novamente em instantes."})

    return app


app = create_app()

# endregion
