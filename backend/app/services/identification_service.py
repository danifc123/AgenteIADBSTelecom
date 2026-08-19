"""Orquestração do fluxo de identificação do cliente — camada services.

Regra de negócio: a identificação é sempre a primeira etapa do atendimento
— cria a sessão e já devolve a saudação personalizada, para a tela de chat
abrir sem precisar de uma segunda chamada.
"""

from __future__ import annotations

from app.core.session_store import SessionStore
from app.domain.models import ChatMessage, ConversationState, Customer
from app.services.mcp_client import McpGateway

# region Exceptions


class CustomerNotFoundError(Exception):
    """O contato informado não corresponde a nenhum cliente cadastrado na IXC."""


# endregion

# region Fluxo público


async def identify_and_greet(contact: str, mcp_gateway: McpGateway, session_store: SessionStore) -> tuple[ConversationState, str]:
    """Identifica o cliente pelo contato informado, cria a sessão e monta a saudação. Retorna `(estado, saudação)`."""
    result = await mcp_gateway.call_tool("identify_customer", {"contact": contact})

    if not result.get("success"):
        raise CustomerNotFoundError(result.get("message", "Cliente não encontrado."))

    customer = Customer(**result["customer"])
    state = ConversationState(customer=customer)
    await session_store.create(state)

    greeting = f"Olá, {customer.name}! Sou o assistente virtual da DBS TELECOM. Como posso te ajudar hoje?"
    await session_store.append_message(state.session_id, ChatMessage(role="assistant", content=greeting))

    return state, greeting


# endregion
