"""Armazenamento de sessão de conversa, camada core (transversal).

Regra de negócio: guarda o estado da conversa em memória, indexado por
`session_id`. Suficiente para o MVP (assume um único processo/worker) —
não substitui um banco de dados numa evolução com múltiplos workers.
"""

from __future__ import annotations

import asyncio

from app.domain.models import ChatMessage, ConversationState

# Limita o histórico enviado ao Ollama para não deixar o contexto crescer
# sem limite numa conversa longa.
MAX_HISTORY_MESSAGES = 20

# region SessionStore


class SessionStore:
    """Store em memória de `ConversationState`, guardado por `asyncio.Lock`."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._sessions: dict[str, ConversationState] = {}

    async def append_message(self, session_id: str, message: ChatMessage) -> None:
        """Adiciona uma mensagem ao histórico da sessão, truncando ao limite. Não retorna valor."""
        async with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return
            state.history.append(message)
            if len(state.history) > MAX_HISTORY_MESSAGES:
                state.history = state.history[-MAX_HISTORY_MESSAGES:]
            state.touch()

    async def create(self, state: ConversationState) -> ConversationState:
        """Registra uma nova conversa no store. Retorna o próprio `ConversationState`."""
        async with self._lock:
            self._sessions[state.session_id] = state
        return state

    async def get(self, session_id: str) -> ConversationState | None:
        """Busca a conversa pelo `session_id`. Retorna o estado ou `None` se não existir."""
        async with self._lock:
            return self._sessions.get(session_id)

    async def save(self, state: ConversationState) -> None:
        """Persiste (sobrescreve) o estado da conversa no store. Não retorna valor."""
        state.touch()
        async with self._lock:
            self._sessions[state.session_id] = state


# endregion

# region Factory

_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Retorna a instância única de `SessionStore` da aplicação (singleton em processo)."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store


# endregion
