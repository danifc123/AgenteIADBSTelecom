"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import pytest

from app.core.config import Settings

# region Fixtures


@pytest.fixture
def settings() -> Settings:
    """Settings de teste, com token fictício (nunca aponta para credenciais reais)."""
    return Settings(ixc_token="test-token-123", ixc_base_url="https://demo.ixcsoft.com.br/webservice/v1")


# endregion
