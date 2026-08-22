"""Máquina de estados do pré-diagnóstico de Suporte (N1) com desfecho N1/N2 — camada services.

Regra de negócio: as perguntas de cada estágio são fixas (canned) — isso
garante que o roteiro de diagnóstico exigido pelo desafio sempre aconteça
na ordem certa, sem depender do modelo local "lembrar" de perguntar tudo.
A detecção de sinal de dano físico roda a cada mensagem, em qualquer
estágio: se o cliente mencionar algo como "cabo cortado", o fluxo pula
direto para o desfecho N2 (agendamento de visita técnica), sem insistir em
passos remotos que não fazem sentido pra esse tipo de defeito.
"""

from __future__ import annotations

from app.domain.models import ConversationState, SupportStage
from app.services.ai.classifier import has_physical_damage_signal
from app.services.ai.mcp_client import McpGateway
from app.services.ai.ollama_client import OllamaClient, run_tool_calling_loop
from app.services.ai.prompts import build_post_suporte_upsell_prompt

# region Textos fixos

_QUESTIONS: dict[SupportStage, str] = {
    SupportStage.ASK_MULTIPLE_DEVICES: (
        "Poxa, que chato! 😕 Vou te ajudar a resolver isso rapidinho. Essa lentidão acontece em "
        "mais de um aparelho (celular, TV, notebook), ou só nesse que você está usando agora?"
    ),
    SupportStage.ASK_CHECK_CABLES: (
        "Beleza! Dá uma olhadinha nos cabos do roteador/ONU pra mim — estão bem encaixados, sem "
        "folga ou dano aparente? 🔌"
    ),
    SupportStage.SUGGEST_RESTART: (
        "Vamos tentar uma coisa que resolve boa parte dos casos de lentidão: desligue o roteador "
        "da tomada, aguarde uns 30 segundos (isso dá tempo dele descarregar de verdade) e ligue de "
        "novo. Pode fazer esse teste aí? 🔌"
    ),
    SupportStage.ASK_RESOLVED: "E aí, depois desses passos a internet voltou ao normal? 📶",
}

_N1_ESCALATION_MESSAGE = (
    "Sem problemas! Já registrei seu chamado e nosso time de Suporte vai dar continuidade. "
    "Protocolo: {protocolo}. 📋"
)
_N2_VISIT_MESSAGE = (
    "Entendi — esse tipo de problema precisa de uma visita técnica presencial. Já agendei o "
    "atendimento pra você (protocolo {protocolo}) e nossa equipe vai entrar em contato pra "
    "confirmar o melhor horário. 🛠️"
)
# endregion

# region Helpers privados (ordem alfabética)


async def _escalate_n1(state: ConversationState, mcp_gateway: McpGateway, last_message: str) -> str:
    """Executa o desfecho N1 (fila de suporte remoto): chama a tool e atualiza o estado. Retorna a mensagem ao cliente."""
    summary = f"Diagnóstico remoto não resolveu. Última mensagem do cliente: {last_message}"
    result = await mcp_gateway.call_tool(
        "log_support_escalation", {"customer_id": state.customer.id, "summary": summary}
    )
    state.support_stage = SupportStage.ESCALATE_N1
    state.support_escalation_summary = summary
    protocolo = _extract_protocolo(result, key="chamado")
    return _N1_ESCALATION_MESSAGE.format(protocolo=protocolo)


async def _escalate_n2(state: ConversationState, mcp_gateway: McpGateway, last_message: str) -> str:
    """Executa o desfecho N2 (agendamento de visita técnica): chama a tool e atualiza o estado. Retorna a mensagem ao cliente."""
    summary = f"Sinal de dano físico relatado pelo cliente: {last_message}"
    result = await mcp_gateway.call_tool(
        "schedule_technical_visit",
        {"customer_id": state.customer.id, "preferred_period": "qualquer", "summary": summary},
    )
    state.support_stage = SupportStage.ESCALATE_N2_VISIT
    state.support_escalation_summary = summary
    protocolo = _extract_protocolo(result, key="visita")
    return _N2_VISIT_MESSAGE.format(protocolo=protocolo)


def _extract_protocolo(tool_result: dict, key: str) -> str:
    """Extrai um identificador de protocolo do retorno da tool, com fallback seguro. Retorna a string do protocolo."""
    if not tool_result.get("success"):
        return "em processamento"
    return str(tool_result.get(key, {}).get("id", "em processamento"))


async def _suggest_upgrade_after_resolution(
    state: ConversationState, mcp_gateway: McpGateway, ollama_client: OllamaClient, commercial_tools: list[dict]
) -> str:
    """Comemora a resolução e, se fizer sentido, sugere um plano melhor com dados reais do cliente/catálogo.

    Regra de negócio: a decisão de sugerir (ou não) um upgrade é feita pelo modelo, mas só com base
    no que `get_customer_plan`/`list_plans` retornarem de verdade — nunca inventa plano ou preço.
    """
    messages = [
        {"role": "system", "content": build_post_suporte_upsell_prompt(state.customer)},
        {"role": "user", "content": "Consegui resolver o problema de lentidão seguindo as instruções, obrigado!"},
    ]
    return await run_tool_calling_loop(
        ollama_client, mcp_gateway, messages, commercial_tools, max_rounds=3, customer_id=state.customer.id
    )


def _is_affirmative(text: str) -> bool:
    """Verifica se a resposta livre do cliente é afirmativa (ex: 'sim', 'resolveu'). Retorna `True`/`False`.

    Bug real encontrado em teste ponta a ponta: checar só "resolveu" como
    substring dava falso positivo em "NÃO resolveu" (a palavra "resolveu"
    está lá dentro!). Por isso a negação é checada primeiro e vence — só
    then o texto é considerado afirmativo.
    """
    normalized = text.lower()
    has_negation = any(word in normalized for word in ("não", "nao", "num "))
    if has_negation:
        return False
    return any(word in normalized for word in ("sim", "resolveu", "melhorou", "funcionou", "ok"))


# endregion

# region Fluxo público (ordem alfabética)


async def advance_support_flow(
    state: ConversationState,
    user_message: str,
    mcp_gateway: McpGateway,
    ollama_client: OllamaClient,
    commercial_tools: list[dict],
) -> str:
    """Avança a máquina de estados de Suporte a partir da resposta do cliente. Retorna a próxima mensagem ao cliente."""
    if has_physical_damage_signal(user_message):
        return await _escalate_n2(state, mcp_gateway, user_message)

    current_stage = state.support_stage

    if current_stage == SupportStage.ASK_MULTIPLE_DEVICES:
        state.support_stage = SupportStage.ASK_CHECK_CABLES
        return _QUESTIONS[SupportStage.ASK_CHECK_CABLES]

    if current_stage == SupportStage.ASK_CHECK_CABLES:
        state.support_stage = SupportStage.SUGGEST_RESTART
        return _QUESTIONS[SupportStage.SUGGEST_RESTART]

    if current_stage == SupportStage.SUGGEST_RESTART:
        state.support_stage = SupportStage.ASK_RESOLVED
        return _QUESTIONS[SupportStage.ASK_RESOLVED]

    if current_stage == SupportStage.ASK_RESOLVED:
        if _is_affirmative(user_message):
            state.support_stage = SupportStage.CLOSED_RESOLVED
            return await _suggest_upgrade_after_resolution(state, mcp_gateway, ollama_client, commercial_tools)
        return await _escalate_n1(state, mcp_gateway, user_message)

    # Estado inesperado: nunca trava o atendimento, escala por segurança.
    return await _escalate_n1(state, mcp_gateway, user_message)


async def start_support_flow(state: ConversationState, triggering_message: str, mcp_gateway: McpGateway) -> str:
    """Inicia o fluxo de pré-diagnóstico de Suporte. Retorna a primeira pergunta ao cliente.

    Se a própria mensagem que disparou o Suporte já tiver sinal de dano físico, pula direto
    para o desfecho N2 (reaproveitando `_escalate_n2`, que de fato chama a ferramenta de
    agendamento — nunca promete uma visita sem realmente registrá-la na IXC).
    """
    if has_physical_damage_signal(triggering_message):
        return await _escalate_n2(state, mcp_gateway, triggering_message)
    state.support_stage = SupportStage.ASK_MULTIPLE_DEVICES
    return _QUESTIONS[SupportStage.ASK_MULTIPLE_DEVICES]


# endregion
