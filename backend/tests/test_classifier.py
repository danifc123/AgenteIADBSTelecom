"""Testes do classificador por palavra-chave: frases variadas -> departamento esperado."""

from __future__ import annotations

import pytest

from app.domain.models import Department
from app.services.ai.classifier import classify_by_keywords, has_physical_damage_signal

# region Casos de teste

_CASES: tuple[tuple[str, Department | None], ...] = (
    ("minha internet tá muito lenta", Department.SUPORTE),
    ("net tá bem devagar hoje", None),  # sem palavra-chave conhecida — cai no fallback do Ollama
    ("internet caiu de novo", Department.SUPORTE),
    ("sem sinal aqui em casa", Department.SUPORTE),
    ("quero um boleto", Department.FINANCEIRO),
    ("preciso da segunda via da fatura", Department.FINANCEIRO),
    ("quero contratar um plano de internet", Department.COMERCIAL),
    ("queria mais velocidade, dá pra fazer upgrade?", Department.COMERCIAL),
    ("bom dia", None),
)

# endregion

# region Testes


@pytest.mark.parametrize("message,expected", _CASES)
def test_classify_by_keywords(message: str, expected: Department | None):
    """Cada frase deve cair no departamento esperado (ou `None`, quando não há palavra-chave conhecida)."""
    assert classify_by_keywords(message) == expected


def test_has_physical_damage_signal_detects_cut_cable():
    """Menção a cabo cortado deve ser detectada como sinal de dano físico."""
    assert has_physical_damage_signal("acho que o cabo foi cortado aqui fora") is True


def test_has_physical_damage_signal_ignores_generic_slowness():
    """Reclamação genérica de lentidão não deve ser tratada como dano físico."""
    assert has_physical_damage_signal("minha internet está lenta") is False


def test_has_physical_damage_signal_detects_vague_cabling_problem():
    """'Cabo com problema' (sem palavra de dano explícita) ainda é sinal de N2 — cabeamento
    nunca se resolve com reinício, mesmo quando o cliente não sabe descrever o defeito."""
    assert has_physical_damage_signal("meu cabo está com um problema") is True


def test_has_physical_damage_signal_does_not_escalate_vague_device_problem():
    """'Roteador com problema' (vago, sem palavra de dano) NÃO deve pular pro N2 — um
    equipamento (ao contrário de cabeamento) costuma se resolver com reinício (fluxo N1)."""
    assert has_physical_damage_signal("meu roteador está com um problema") is False


# endregion
