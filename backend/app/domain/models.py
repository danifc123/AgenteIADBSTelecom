"""Modelos e enums de domínio — camada domain.

Regra de negócio: esta camada não conhece HTTP, IXC, Ollama ou MCP. Ela só
descreve os conceitos do negócio (cliente, departamento, estágio do
diagnóstico de suporte, estado da conversa) para que `services/` e `api/`
falem a mesma língua.
"""

from __future__ import annotations

import time
import uuid
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

# region Enums


class Department(StrEnum):
    """Os três departamentos para os quais o atendimento pode ser encaminhado."""

    COMERCIAL = "Comercial"
    FINANCEIRO = "Financeiro"
    SUPORTE = "Suporte"


class SupportStage(StrEnum):
    """Estágios da máquina de estados do pré-diagnóstico de Suporte (N1) e seus desfechos (N1/N2).

    A ordem das perguntas é fixa (ver services/support_flow.py) para garantir
    que o roteiro exigido pelo desafio sempre aconteça, independente do que
    o modelo local "lembraria" de perguntar sozinho.
    """

    ASK_MULTIPLE_DEVICES = "ask_multiple_devices"
    ASK_CHECK_CABLES = "ask_check_cables"
    SUGGEST_RESTART = "suggest_restart"
    ASK_RESOLVED = "ask_resolved"
    CLOSED_RESOLVED = "closed_resolved"
    ESCALATE_N1 = "escalate_n1"
    ESCALATE_N2_VISIT = "escalate_n2_visit"


# endregion

# region Models


class Customer(BaseModel):
    """Representa um cliente identificado na IXC."""

    cpf_cnpj: str | None = None
    id: str
    name: str
    phone: str | None = None
    plan_name: str | None = None
    status: str | None = None


class ChatMessage(BaseModel):
    """Uma mensagem trocada na conversa (histórico enviado ao Ollama)."""

    content: str
    name: str | None = None
    role: Literal["system", "user", "assistant", "tool"]
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ConversationState(BaseModel):
    """Estado completo de uma conversa/atendimento, indexado por `session_id`."""

    created_at: float = Field(default_factory=time.time)
    customer: Customer
    department: Department | None = None
    history: list[ChatMessage] = Field(default_factory=list)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    support_escalation_summary: str | None = None
    support_stage: SupportStage | None = None
    updated_at: float = Field(default_factory=time.time)

    def touch(self) -> None:
        """Atualiza `updated_at` para o horário atual. Não retorna valor."""
        self.updated_at = time.time()


# endregion
