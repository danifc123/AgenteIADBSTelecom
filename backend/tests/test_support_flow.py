"""Testes da máquina de estados do pré-diagnóstico de Suporte: ordem fixa, encerramento e desfecho N1/N2."""

from __future__ import annotations

import pytest

from app.domain.models import ConversationState, Customer, SupportStage
from app.services.support_flow import advance_support_flow, start_support_flow

# region Fake McpGateway


class FakeMcpGateway:
    """Substitui o `McpGateway` real nos testes — registra as tools chamadas, sem tocar em rede/subprocess."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Registra a chamada e devolve um payload de sucesso fictício. Retorna o dicionário de resultado."""
        self.calls.append((name, arguments))
        if name == "log_support_escalation":
            return {"success": True, "chamado": {"id": "N1-001"}}
        if name == "schedule_technical_visit":
            return {"success": True, "visita": {"id": "N2-001", "periodo_preferido": "qualquer", "status": "aberto"}}
        return {"success": True}


# endregion

# region Fake OllamaClient


class FakeOllamaClient:
    """Substitui o `OllamaClient` real nos testes — devolve uma resposta fixa, sem tool_calls, sem tocar rede."""

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Devolve uma mensagem de assistente fixa (sem tool_calls). Retorna o dicionário da mensagem."""
        return {"role": "assistant", "content": "Que ótimo que resolveu! 🎉"}


# endregion

# region Fixtures


@pytest.fixture
def state() -> ConversationState:
    """Estado de conversa novo, para um cliente fictício, sem departamento/estágio definidos ainda."""
    return ConversationState(customer=Customer(id="1", name="Maria"))


# endregion

# region Testes (ordem alfabética)


async def test_advance_support_flow_cannot_skip_stages(state: ConversationState):
    """As perguntas devem acontecer sempre na ordem: dispositivos -> cabos -> reiniciar -> resolveu."""
    gateway = FakeMcpGateway()
    ollama = FakeOllamaClient()
    await start_support_flow(state, "minha internet está lenta", gateway)
    assert state.support_stage == SupportStage.ASK_MULTIPLE_DEVICES

    await advance_support_flow(state, "só nesse aparelho", gateway, ollama, [])
    assert state.support_stage == SupportStage.ASK_CHECK_CABLES

    await advance_support_flow(state, "sim, estão ok", gateway, ollama, [])
    assert state.support_stage == SupportStage.SUGGEST_RESTART

    await advance_support_flow(state, "já reiniciei", gateway, ollama, [])
    assert state.support_stage == SupportStage.ASK_RESOLVED


async def test_advance_support_flow_escalates_to_n1_when_not_resolved(state: ConversationState):
    """Resposta negativa na etapa final deve escalar para N1 e chamar `log_support_escalation`."""
    gateway = FakeMcpGateway()
    ollama = FakeOllamaClient()
    state.support_stage = SupportStage.ASK_RESOLVED

    await advance_support_flow(state, "não, continua lento", gateway, ollama, [])

    assert state.support_stage == SupportStage.ESCALATE_N1
    assert gateway.calls[0][0] == "log_support_escalation"


async def test_advance_support_flow_jumps_to_n2_on_physical_damage_mid_flow(state: ConversationState):
    """Sinal de dano físico em qualquer etapa deve pular direto para o agendamento de visita (N2)."""
    gateway = FakeMcpGateway()
    ollama = FakeOllamaClient()
    state.support_stage = SupportStage.ASK_CHECK_CABLES

    await advance_support_flow(state, "acho que o cabo foi cortado", gateway, ollama, [])

    assert state.support_stage == SupportStage.ESCALATE_N2_VISIT
    assert gateway.calls[0][0] == "schedule_technical_visit"


async def test_advance_support_flow_resolves_without_escalating(state: ConversationState):
    """Resposta afirmativa na etapa final deve encerrar (com sugestão de upgrade via IA) sem escalonar."""
    gateway = FakeMcpGateway()
    ollama = FakeOllamaClient()
    state.support_stage = SupportStage.ASK_RESOLVED

    reply = await advance_support_flow(state, "sim, resolveu, obrigado!", gateway, ollama, [])

    assert state.support_stage == SupportStage.CLOSED_RESOLVED
    assert reply == "Que ótimo que resolveu! 🎉"
    assert gateway.calls == []


async def test_advance_support_flow_negation_containing_affirmative_word_still_escalates(state: ConversationState):
    """'Não resolveu' contém a palavra 'resolveu' — não pode ser lido como afirmativo (bug real encontrado em teste e2e)."""
    gateway = FakeMcpGateway()
    ollama = FakeOllamaClient()
    state.support_stage = SupportStage.ASK_RESOLVED

    await advance_support_flow(state, "não resolveu, continua lento", gateway, ollama, [])

    assert state.support_stage == SupportStage.ESCALATE_N1
    assert gateway.calls[0][0] == "log_support_escalation"


async def test_start_support_flow_skips_straight_to_n2_on_physical_damage(state: ConversationState):
    """Se o cliente já relatar dano físico na primeira mensagem, pula direto para N2, sem perguntas de N1.

    Regressão: essa mensagem inicial precisa de fato chamar `schedule_technical_visit` — não
    basta dizer ao cliente que a visita foi agendada sem registrar isso na IXC.
    """
    gateway = FakeMcpGateway()
    await start_support_flow(state, "o cabo da minha casa foi cortado", gateway)
    assert state.support_stage == SupportStage.ESCALATE_N2_VISIT
    assert gateway.calls[0][0] == "schedule_technical_visit"


async def test_start_support_flow_starts_at_first_stage(state: ConversationState):
    """Sem sinal de dano físico, o fluxo deve começar sempre pela primeira pergunta."""
    gateway = FakeMcpGateway()
    await start_support_flow(state, "minha internet está lenta", gateway)
    assert state.support_stage == SupportStage.ASK_MULTIPLE_DEVICES


# endregion
