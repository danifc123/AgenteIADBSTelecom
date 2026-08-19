"""Composition root da aplicação — sobe a instância do FastAPI.

Regra de negócio: nenhuma exceção não tratada pode vazar como HTML/stack
trace para o cliente — o handler global sempre responde em JSON estruturado.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import health
from app.core.config import get_settings
from app.core.logging_config import configure_logging, get_logger

logger = get_logger(__name__)

# region App factory


def create_app() -> FastAPI:
    """Monta a aplicação FastAPI: rotas e handler global de exceções. Retorna a instância de `FastAPI`."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="DBS TELECOM — Assistente Virtual")
    app.include_router(health.router)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        """Handler global: nunca deixa uma exceção não tratada vazar como HTML. Retorna JSON 500 estruturado."""
        logger.error("unhandled_exception", error=str(exc), error_type=type(exc).__name__)
        return JSONResponse(status_code=500, content={"success": False, "message": "Erro interno. Tente novamente em instantes."})

    return app


app = create_app()

# endregion
