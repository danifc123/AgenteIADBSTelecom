"""Configuração de logging estruturado (structlog), camada core.

Regra de negócio de segurança: nenhum valor de header de autenticação pode
chegar aos logs em texto plano — `_redact_processor` intercepta isso antes
de qualquer log ser emitido.
"""

from __future__ import annotations

import logging
import sys

import structlog

_REDACT_KEYS = {"authorization", "ixc_token", "token"}

# region Processors


def _redact_processor(_logger, _method_name, event_dict: dict) -> dict:
    """Redige valores de chaves sensíveis (token/authorization) do log. Retorna o event_dict modificado."""
    for key in list(event_dict.keys()):
        if key.lower() in _REDACT_KEYS:
            event_dict[key] = "***redacted***"
    return event_dict


# endregion

# region Setup


def configure_logging(level: str = "INFO") -> None:
    """Configura o logging estruturado da aplicação (formato JSON, nível dado). Não retorna valor."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Retorna um logger estruturado nomeado, pronto para uso."""
    return structlog.get_logger(name)


# endregion
