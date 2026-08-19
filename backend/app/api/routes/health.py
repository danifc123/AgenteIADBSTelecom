"""Rota de health check — camada api."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])

# region Rotas


@router.get("/health")
async def get_health() -> dict:
    """Verifica se a API está no ar. Retorna `{"status": "ok"}`."""
    return {"status": "ok"}


# endregion
