"""Cliente Ollama e loop de tool-calling — camada services.

Regra de negócio: o loop tem um limite de rounds (`ollama_max_tool_rounds`)
para nunca deixar o atendimento preso caso o modelo entre num ciclo de
chamar ferramentas repetidamente sem concluir.
"""

from __future__ import annotations

import json

import httpx

from app.core.config import Settings, get_settings
from app.core.logging_config import get_logger
from app.services.ai.classifier import parse_tool_call_arguments
from app.services.ai.mcp_client import McpGateway
from app.services.ai.tool_schema import CUSTOMER_SCOPED_TOOLS

logger = get_logger(__name__)

# region OllamaClient


class OllamaClient:
    """Cliente HTTP para o endpoint `/api/chat` do Ollama."""

    def __init__(self, settings: Settings) -> None:
        self._model = settings.ollama_model
        headers = {"Authorization": f"Bearer {settings.ollama_api_key}"} if settings.ollama_api_key else {}
        self._client = httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=settings.ollama_timeout_seconds, headers=headers
        )

    async def aclose(self) -> None:
        """Fecha a conexão HTTP subjacente. Não retorna valor."""
        await self._client.aclose()

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Envia o histórico de mensagens ao Ollama, com as tools disponíveis. Retorna a mensagem de resposta do modelo.

        Regra de negócio: `think="low"` é obrigatório para modelos raciocinadores tipo o
        gpt-oss — sem um nível explícito, o raciocínio interno do modelo (em inglês) vazava
        direto no texto de resposta ao cliente (bug real encontrado em teste). Passar
        `think=True/False` é ignorado pelo gpt-oss especificamente; precisa ser a string
        "low"/"medium"/"high". Modelos sem suporte a "thinking" (ex: qwen2.5:7b local)
        simplesmente ignoram o campo.
        """
        payload: dict = {"model": self._model, "messages": messages, "stream": False, "think": "low"}
        if tools:
            payload["tools"] = tools

        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        body = response.json()
        return body["message"]


# endregion

# region Factory

_ollama_client: OllamaClient | None = None


def get_ollama_client() -> OllamaClient:
    """Retorna a instância única de `OllamaClient` da aplicação (singleton em processo)."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient(get_settings())
    return _ollama_client


# endregion

# region Loop de tool-calling


async def run_tool_calling_loop(
    ollama_client: OllamaClient,
    mcp_gateway: McpGateway,
    messages: list[dict],
    tools: list[dict],
    max_rounds: int,
    customer_id: str,
) -> str:
    """Executa o loop de tool-calling (chama Ollama, executa tools via MCP, repete até obter resposta final).

    Regra de negócio de segurança: `customer_id` nunca vem do modelo — é
    injetado aqui, a partir da sessão já identificada, para toda tool
    marcada como `CUSTOMER_SCOPED_TOOLS` (o schema exposto ao Ollama nem
    contém esse campo, ver tool_schema.py).

    Retorna o texto final da resposta do assistente.
    """
    working_messages = list(messages)

    for round_number in range(max_rounds):
        assistant_message = await ollama_client.chat(working_messages, tools)
        tool_calls = assistant_message.get("tool_calls") or []

        if not tool_calls:
            return assistant_message.get("content", "")

        working_messages.append(assistant_message)

        for call in tool_calls:
            function = call.get("function", {})
            name = function.get("name", "")
            arguments = parse_tool_call_arguments(function.get("arguments", {}))
            if name in CUSTOMER_SCOPED_TOOLS:
                arguments["customer_id"] = customer_id
            logger.info("ollama_tool_call", tool=name, round=round_number)

            result = await mcp_gateway.call_tool(name, arguments)
            working_messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})

    logger.error("ollama_tool_loop_exhausted", max_rounds=max_rounds)
    return "Desculpe, tive dificuldade para concluir essa solicitação agora. Pode tentar reformular?"


# endregion
