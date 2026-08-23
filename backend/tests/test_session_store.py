"""Testes do store de sessão em memória: CRUD básico e limite de histórico."""

from __future__ import annotations

import asyncio

from app.core.session_store import MAX_HISTORY_MESSAGES, SessionStore
from app.domain.models import ChatMessage, ConversationState, Customer

# region Testes (ordem alfabética)


async def test_append_message_truncates_history_at_limit():
    """O histórico não deve crescer além de `MAX_HISTORY_MESSAGES`."""
    store = SessionStore()
    state = await store.create(ConversationState(customer=Customer(id="1", name="Maria")))

    for i in range(MAX_HISTORY_MESSAGES + 10):
        await store.append_message(state.session_id, ChatMessage(role="user", content=f"mensagem {i}"))

    saved = await store.get(state.session_id)
    assert saved is not None
    assert len(saved.history) == MAX_HISTORY_MESSAGES


async def test_concurrent_writes_do_not_corrupt_store():
    """Escritas concorrentes em sessões diferentes não devem se corromper (smoke test de concorrência)."""
    store = SessionStore()
    states = [ConversationState(customer=Customer(id=str(i), name=f"Cliente {i}")) for i in range(20)]

    await asyncio.gather(*(store.create(s) for s in states))

    for s in states:
        saved = await store.get(s.session_id)
        assert saved is not None
        assert saved.customer.id == s.customer.id


async def test_get_returns_none_for_unknown_session():
    """Buscar uma sessão inexistente deve retornar `None`, não levantar exceção."""
    store = SessionStore()
    assert await store.get("sessao-que-nao-existe") is None


# endregion
