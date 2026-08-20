"""Llamadas al LLM forzando salida estructurada, con reintento/backoff compartido.

Dos proveedores intercambiables vía config.LLM_PROVIDER:
- 'ollama' (por defecto): modelo local, salida forzada con JSON Schema nativo de Ollama.
- 'anthropic': Claude API, salida forzada con tool use (tool_choice).
"""
import json
import logging
from typing import Any, Optional

import httpx

import config
from .utils import retry_call

logger = logging.getLogger(__name__)

_anthropic_client: Optional[Any] = None


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic()
    return _anthropic_client


def _call_anthropic(prompt: str, tool: dict, max_tokens: int) -> dict[str, Any]:
    import anthropic

    no_retry = ()
    if hasattr(anthropic, "AuthenticationError"):
        no_retry = (anthropic.AuthenticationError,)

    def _do_call():
        client = _get_anthropic_client()
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=max_tokens,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == tool["name"]:
                return block.input
        raise RuntimeError(f"Claude no devolvió una llamada a la tool '{tool['name']}'")

    return retry_call(
        _do_call, max_retries=config.MAX_RETRIES, base=config.BACKOFF_BASE, no_retry=no_retry
    )


def _call_ollama(prompt: str, tool: dict, max_tokens: int, think: bool) -> dict[str, Any]:
    def _do_call():
        response = httpx.post(
            f"{config.OLLAMA_HOST}/api/chat",
            json={
                "model": config.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "format": tool["input_schema"],
                "stream": False,
                "think": think,
                "options": {
                    "temperature": 0,
                    "num_ctx": config.OLLAMA_NUM_CTX,
                    "num_predict": max_tokens,
                },
            },
            timeout=600,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return json.loads(content)

    return retry_call(_do_call, max_retries=config.MAX_RETRIES, base=config.BACKOFF_BASE)


def call_tool(
    prompt: str, tool: dict, *, max_tokens: int = 4096, think: bool = False
) -> dict[str, Any]:
    """Llama al LLM configurado forzando una salida que respete `tool['input_schema']`.

    `think` solo aplica al proveedor Ollama: activa el modo de razonamiento del
    modelo (más lento, mejor para tareas de síntesis/creatividad como `report`;
    se deja desactivado por defecto para no penalizar `extract`, que llama una
    vez por vídeo).
    """
    if config.LLM_PROVIDER == "ollama":
        return _call_ollama(prompt, tool, max_tokens, think)
    return _call_anthropic(prompt, tool, max_tokens)


def embed(text: str) -> list[float]:
    """Calcula el embedding de `text` vía Ollama (config.OLLAMA_EMBED_MODEL).

    Los embeddings siempre pasan por Ollama, independientemente de LLM_PROVIDER:
    Claude API no expone un endpoint de embeddings.
    """
    def _do_call():
        response = httpx.post(
            f"{config.OLLAMA_HOST}/api/embed",
            json={"model": config.OLLAMA_EMBED_MODEL, "input": text},
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    return retry_call(_do_call, max_retries=config.MAX_RETRIES, base=config.BACKOFF_BASE)
