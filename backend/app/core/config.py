"""Configuração da aplicação, camada core (transversal).

Regra de negócio: nenhum segredo (token/URL da IXC) pode ter valor padrão
hardcoded aqui — IXC_TOKEN é obrigatório vir do ambiente (.env), nunca do
código-fonte.
"""

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

    # --- IXC ---
    ixc_base_url: str = "https://demo.ixcsoft.com.br/webservice/v1"
    ixc_timeout_seconds: float = 15.0
    ixc_token: str

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_max_tool_rounds: int = 3
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: float = 60.0

    def cors_origin_list(self) -> list[str]:
        """Retorna a lista de origens CORS permitidas, a partir de `cors_origins`."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# endregion

# region Factory


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única (cacheada) de `Settings` para a aplicação."""
    return Settings()


# endregion
