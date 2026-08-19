"""Configuração da aplicação, camada core (transversal)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# region Settings


class Settings(BaseSettings):
    """Configurações da aplicação resolvidas a partir de variáveis de ambiente / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "*"
    log_level: str = "INFO"


# endregion

# region Factory


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única (cacheada) de `Settings` para a aplicação."""
    return Settings()


# endregion
