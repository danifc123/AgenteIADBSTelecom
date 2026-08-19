"""Conversão de tools MCP para o formato esperado pelo Ollama, e filtragem por departamento — camada services.

Regra de negócio: cada departamento só enxerga as tools relevantes pra ele.
Isso reduz a chance de o modelo local chamar a ferramenta errada (ex:
`get_boleto` durante uma conversa de Suporte) e também reduz o tamanho do
prompt enviado a cada turno.
"""

from __future__ import annotations

from mcp import Tool

from app.domain.models import Department

# region Pseudo-tool de roteamento

# Esta tool não é servida pelo MCP — é definida aqui porque é uma decisão
# de orquestração (não uma integração externa), forçada como primeira
# chamada do modelo antes de saber o departamento do atendimento.
ROUTE_TO_DEPARTMENT_TOOL = {
    "type": "function",
    "function": {
        "name": "route_to_department",
        "description": (
            "Classifica a solicitação do cliente em um dos três departamentos da DBS TELECOM. "
            "Chame esta ferramenta OBRIGATORIAMENTE como primeira ação de cada novo atendimento, "
            "antes de responder qualquer coisa ao cliente. Nunca invente um departamento fora da "
            "lista permitida."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "enum": ["Comercial", "Suporte", "Financeiro"],
                    "description": "O departamento responsável por atender a solicitação.",
                },
                "reason": {
                    "type": "string",
                    "description": "Explicação curta de por que esse departamento foi escolhido.",
                },
                "is_slow_internet_issue": {
                    "type": "boolean",
                    "description": "True somente se o departamento for Suporte E a reclamação for de lentidão/internet lenta.",
                },
            },
            "required": ["department", "reason", "is_slow_internet_issue"],
        },
    },
}

# endregion

# region Filtro por departamento

# Suporte não aparece aqui: o atendimento de Suporte é conduzido pela
# máquina de estados determinística (services/support_flow.py), não pelo
# loop livre de tool-calling do Ollama — por isso não tem tools MCP
# liberadas nesta lista.
DEPARTMENT_TOOL_ALLOWLIST: dict[Department, set[str]] = {
    Department.COMERCIAL: {"list_plans", "get_customer_plan"},
    Department.FINANCEIRO: {"get_boleto"},
}

# Tools cujo `customer_id` NUNCA deve ser preenchido pelo modelo — o
# orquestrador injeta o id do cliente já identificado na sessão antes de
# executar a chamada (ver ollama_client.run_tool_calling_loop). Regra de
# negócio de segurança/correção: o modelo não tem (e não deve ter) como
# saber o id interno do cliente — deixar isso a cargo dele arrisca tanto
# alucinar um id errado (vazando dado de outro cliente) quanto omitir o
# campo (a tool falha por falta de parâmetro).
CUSTOMER_SCOPED_TOOLS = frozenset({"get_boleto", "get_customer_plan", "log_support_escalation", "schedule_technical_visit"})

# endregion

# region Conversores (ordem alfabética)


def filter_tools_for_department(tools: list[dict], department: Department | None) -> list[dict]:
    """Filtra as tools (formato Ollama) para as do departamento, removendo `customer_id` do schema visível ao modelo."""
    if department is None:
        return [ROUTE_TO_DEPARTMENT_TOOL]
    allowed_names = DEPARTMENT_TOOL_ALLOWLIST.get(department, set())
    return [_strip_customer_id_param(tool) for tool in tools if tool["function"]["name"] in allowed_names]


def mcp_tool_to_ollama_format(tool: Tool) -> dict:
    """Converte uma `Tool` do MCP para o formato de tool esperado pelo Ollama. Retorna o dicionário convertido."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


def mcp_tools_to_ollama_format(tools: list[Tool]) -> list[dict]:
    """Converte uma lista de `Tool` do MCP para o formato Ollama. Retorna a lista convertida."""
    return [mcp_tool_to_ollama_format(tool) for tool in tools]


def _strip_customer_id_param(tool: dict) -> dict:
    """Remove `customer_id` do schema de uma tool sensível ao cliente, se presente. Retorna uma cópia da tool."""
    name = tool["function"]["name"]
    if name not in CUSTOMER_SCOPED_TOOLS:
        return tool

    parameters = tool["function"].get("parameters") or {}
    properties = {k: v for k, v in (parameters.get("properties") or {}).items() if k != "customer_id"}
    required = [field for field in (parameters.get("required") or []) if field != "customer_id"]

    return {
        "type": tool["type"],
        "function": {
            **tool["function"],
            "parameters": {**parameters, "properties": properties, "required": required},
        },
    }


# endregion
