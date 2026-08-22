"""Classificação de departamento: parsing da tool-call do Ollama + fallback por palavra-chave — camada services.

Regra de negócio: o classificador nunca pode travar o atendimento. Se o
Ollama não chamar `route_to_department` corretamente (falha comum em
modelos locais pequenos), o fallback por palavra-chave garante que o
cliente sempre seja roteado para algum departamento.
"""

from __future__ import annotations

import json

from app.domain.models import Department

# region Palavras-chave (fallback)

_KEYWORDS: dict[Department, tuple[str, ...]] = {
    Department.FINANCEIRO: (
        "boleto", "fatura", "segunda via", "pagamento", "pagar", "vencimento", "cobranca", "cobrança",
        "financeiro",
    ),
    Department.SUPORTE: (
        "lenta", "lento", "sem internet", "caiu", "nao conecta", "não conecta", "sem sinal",
        "internet ruim", "instavel", "instável", "sem conexao", "sem conexão", "wifi nao funciona",
        "suporte",
    ),
    Department.COMERCIAL: (
        "contratar", "plano novo", "mudar de plano", "mudar plano", "upgrade", "assinar",
        "quero um plano", "quero internet", "preco", "preço", "valores dos planos", "comercial",
    ),
}

# Sinais de dano físico no equipamento/cabeamento — usados por support_flow.py
# para pular direto para o desfecho N2 (visita técnica), em qualquer estágio.
# Dividido em dois conjuntos (palavra de dano + substantivo de equipamento) em
# vez de frases exatas, porque o cliente raramente escreve a frase "perfeita"
# ("o cabo foi cortado" não bate com a frase fixa "cabo cortado").
_PHYSICAL_DAMAGE_INDICATORS: tuple[str, ...] = (
    "cortad", "rompid", "quebrad", "queimo", "queimad", "roeu", "roido", "roído",
    "sem luz", "sem energia", "sem nenhuma luz",
)
_PHYSICAL_EQUIPMENT_NOUNS: tuple[str, ...] = (
    "cabo", "fibra", "fio", "roteador", "modem", "ont", "equipamento", "aparelho",
)

# endregion

# region Classificação (ordem alfabética)


def classify_by_keywords(message: str) -> Department | None:
    """Classifica o departamento por palavra-chave, usado como fallback. Retorna o `Department` ou `None`."""
    normalized = message.lower()
    for department, keywords in _KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return department
    return None


def has_physical_damage_signal(message: str) -> bool:
    """Verifica se a mensagem menciona sinal de dano físico no equipamento/cabeamento. Retorna `True`/`False`."""
    normalized = message.lower()
    has_damage_word = any(word in normalized for word in _PHYSICAL_DAMAGE_INDICATORS)
    has_equipment_word = any(word in normalized for word in _PHYSICAL_EQUIPMENT_NOUNS)
    return has_damage_word and has_equipment_word


def parse_route_to_department_call(arguments: dict) -> tuple[Department, bool] | None:
    """Interpreta os argumentos da tool-call `route_to_department`. Retorna `(Department, is_slow_internet_issue)` ou `None` se inválido."""
    raw_department = arguments.get("department")
    try:
        department = Department(raw_department)
    except ValueError:
        return None
    is_slow_internet_issue = bool(arguments.get("is_slow_internet_issue", False))
    return department, is_slow_internet_issue


def parse_tool_call_arguments(raw_arguments: str | dict) -> dict:
    """Normaliza os argumentos de uma tool-call do Ollama, que podem vir como string JSON ou dict. Retorna o dicionário."""
    if isinstance(raw_arguments, dict):
        return raw_arguments
    try:
        return json.loads(raw_arguments)
    except (json.JSONDecodeError, TypeError):
        return {}


# endregion
