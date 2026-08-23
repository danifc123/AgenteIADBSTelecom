"""Orquestração de um turno de chat: classificação, roteamento e execução — camada services.

Regra de negócio: este é o ponto único que decide "o que fazer" com a
mensagem do cliente — a rota HTTP (`api/routes/chat.py`) só chama
`handle_chat_turn` e traduz o resultado para JSON, sem tomar nenhuma
decisão de negócio ela mesma.
"""

from __future__ import annotations

from app.core.session_store import SessionStore
from app.domain.models import ChatMessage, ConversationState, Department, SupportStage
from app.services.ai.classifier import classify_by_keywords, parse_route_to_department_call, parse_tool_call_arguments
from app.services.ai.mcp_client import McpGateway
from app.services.ai.ollama_client import OllamaClient, run_tool_calling_loop
from app.services.ai.prompts import build_classification_prompt, build_comercial_prompt, build_financeiro_prompt
from app.services.support_flow import advance_support_flow, start_support_flow
from app.services.ai.tool_schema import ROUTE_TO_DEPARTMENT_TOOL, filter_tools_for_department

_ACTIVE_SUPPORT_STAGES = frozenset(
    {SupportStage.ASK_MULTIPLE_DEVICES, SupportStage.ASK_CHECK_CABLES, SupportStage.SUGGEST_RESTART, SupportStage.ASK_RESOLVED}
)

_QUICK_REPLIES_BY_STAGE: dict[SupportStage, list[str]] = {
    SupportStage.ASK_MULTIPLE_DEVICES: ["Sim, em vários", "Só nesse aparelho"],
    SupportStage.ASK_CHECK_CABLES: ["Sim, estão ok", "Encontrei um problema"],
    SupportStage.SUGGEST_RESTART: ["Já reiniciei", "Não consigo reiniciar"],
    SupportStage.ASK_RESOLVED: ["Sim, resolveu", "Não, continua"],
}

_CLARIFICATION_MESSAGE = (
    "Desculpe, não entendi bem o que você precisa. Você quer: contratar ou mudar de plano "
    "(Comercial), resolver um problema técnico (Suporte), ou falar sobre boleto/pagamento "
    "(Financeiro)?"
)

# region Helpers privados (ordem alfabética)


async def _classify_department(
    ollama_client: OllamaClient, state: ConversationState, user_message: str
) -> tuple[Department, bool] | None:
    """Classifica o departamento via tool-call do Ollama, com fallback por palavra-chave. Retorna `(Department, is_slow)` ou `None`."""
    system_prompt = build_classification_prompt(state.customer)
    messages = [{"role": "system", "content": system_prompt}, *_history_as_dicts(state.history), {"role": "user", "content": user_message}]

    assistant_message = await ollama_client.chat(messages, tools=[ROUTE_TO_DEPARTMENT_TOOL])
    tool_calls = assistant_message.get("tool_calls") or []

    if tool_calls:
        arguments = parse_tool_call_arguments(tool_calls[0].get("function", {}).get("arguments", {}))
        parsed = parse_route_to_department_call(arguments)
        if parsed is not None:
            return parsed

    keyword_department = classify_by_keywords(user_message)
    if keyword_department is not None:
        is_slow = keyword_department == Department.SUPORTE
        return keyword_department, is_slow

    return None


def _detect_department_switch(user_message: str, current_department: Department) -> Department | None:
    """Detecta por palavra-chave se o cliente está pedindo um departamento diferente do atual.

    Regra de negócio: uma vez que o departamento é definido, o atendimento não pode travar nele
    pro resto da conversa — o cliente precisa poder pedir "quero falar com o financeiro" a
    qualquer momento e ser atendido. Palavra-chave (rápido, sem chamada à IA) é suficiente aqui
    porque os vocabulários dos 3 departamentos são bem distintos.

    Retorna o novo `Department`, ou `None` se não houver sinal de troca.
    """
    detected = classify_by_keywords(user_message)
    if detected is not None and detected != current_department:
        return detected
    return None


def _history_as_dicts(history: list[ChatMessage]) -> list[dict]:
    """Converte o histórico de `ChatMessage` para o formato de mensagens do Ollama. Retorna a lista de dicionários."""
    return [message.model_dump(exclude_none=True) for message in history]


async def _run_department_chat(
    state: ConversationState,
    user_message: str,
    ollama_client: OllamaClient,
    mcp_gateway: McpGateway,
    all_tools: list[dict],
) -> str:
    """Executa o loop de tool-calling para os departamentos Comercial/Financeiro. Retorna o texto de resposta."""
    if state.department == Department.COMERCIAL:
        system_prompt = build_comercial_prompt(state.customer)
    else:
        system_prompt = build_financeiro_prompt(state.customer)

    messages = [{"role": "system", "content": system_prompt}, *_history_as_dicts(state.history), {"role": "user", "content": user_message}]
    tools = filter_tools_for_department(all_tools, state.department)
    return await run_tool_calling_loop(
        ollama_client, mcp_gateway, messages, tools, max_rounds=3, customer_id=state.customer.id
    )


# endregion

# region Fluxo público


async def handle_chat_turn(
    state: ConversationState,
    user_message: str,
    ollama_client: OllamaClient,
    mcp_gateway: McpGateway,
    session_store: SessionStore,
    all_tools: list[dict],
) -> tuple[str, list[str] | None]:
    """Processa uma mensagem do cliente e decide a próxima ação (classificar, diagnosticar, ou responder).

    Retorna `(texto_da_resposta, quick_replies)`.
    """
    await session_store.append_message(state.session_id, ChatMessage(role="user", content=user_message))

    quick_replies: list[str] | None = None

    switched_department = None
    if state.department is not None:
        switched_department = _detect_department_switch(user_message, state.department)

    if switched_department is not None:
        # O cliente pediu outro departamento — vale a qualquer momento, inclusive no meio de um
        # diagnóstico de Suporte em andamento, pra nunca travar num assunto que ele já abandonou.
        state.department = None
        state.support_stage = None
        classification = (switched_department, switched_department == Department.SUPORTE)
        reply, quick_replies = await _route_after_classification(state, user_message, classification, ollama_client, mcp_gateway, all_tools)

    elif state.department == Department.SUPORTE and state.support_stage in _ACTIVE_SUPPORT_STAGES:
        commercial_tools = filter_tools_for_department(all_tools, Department.COMERCIAL)
        reply = await advance_support_flow(state, user_message, mcp_gateway, ollama_client, commercial_tools)
        quick_replies = _QUICK_REPLIES_BY_STAGE.get(state.support_stage) if state.support_stage in _ACTIVE_SUPPORT_STAGES else None

    elif state.department is None:
        classification = await _classify_department(ollama_client, state, user_message)
        reply, quick_replies = await _route_after_classification(state, user_message, classification, ollama_client, mcp_gateway, all_tools)

    else:
        if state.department == Department.SUPORTE:
            # Suporte concluído e sem sinal claro de outro assunto por palavra-chave: reclassifica
            # via IA mesmo assim, em vez de travar no departamento antigo.
            state.department = None
            state.support_stage = None
            classification = await _classify_department(ollama_client, state, user_message)
            reply, quick_replies = await _route_after_classification(state, user_message, classification, ollama_client, mcp_gateway, all_tools)
        else:
            reply = await _run_department_chat(state, user_message, ollama_client, mcp_gateway, all_tools)

    await session_store.append_message(state.session_id, ChatMessage(role="assistant", content=reply))
    await session_store.save(state)
    return reply, quick_replies


async def _route_after_classification(
    state: ConversationState,
    user_message: str,
    classification: tuple[Department, bool] | None,
    ollama_client: OllamaClient,
    mcp_gateway: McpGateway,
    all_tools: list[dict],
) -> tuple[str, list[str] | None]:
    """Aplica o roteamento decidido pela classificação (ou pede esclarecimento se não classificou). Retorna `(resposta, quick_replies)`."""
    if classification is None:
        return _CLARIFICATION_MESSAGE, None

    department, _is_slow = classification
    state.department = department

    if department == Department.SUPORTE:
        reply = await start_support_flow(state, user_message, mcp_gateway)
        quick_replies = _QUICK_REPLIES_BY_STAGE.get(state.support_stage) if state.support_stage in _ACTIVE_SUPPORT_STAGES else None
        return reply, quick_replies

    reply = await _run_department_chat(state, user_message, ollama_client, mcp_gateway, all_tools)
    return reply, None


# endregion
