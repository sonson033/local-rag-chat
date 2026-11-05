"""LLM adapter for local chat models served by Ollama."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence

import ollama

from backend.ports import Message

logger = logging.getLogger(__name__)

# Model families / name parts that only produce embeddings and cannot chat.
_EMBEDDING_HINTS = ("embed", "bert", "minilm", "bge")


def normalize_model_name(name: str) -> str:
    """`llama3.2:latest` -> `llama3.2` (Ollama treats both as the same model)."""
    return name.removesuffix(":latest")


class OllamaLLM:
    """Streams chat answers and lists the models installed with `ollama pull`."""

    def __init__(self, client: ollama.Client, temperature: float = 0.1) -> None:
        self._client = client
        # Low temperature: we want faithful answers from the context, not creativity.
        self._options = {"temperature": temperature}

    def stream_chat(self, messages: Sequence[Message], model: str) -> Iterator[str]:
        logger.info("Asking %s with %d message(s)", model, len(messages))
        stream = self._client.chat(
            model=model, messages=list(messages), stream=True, options=self._options
        )
        for part in stream:
            content = part.message.content
            if content:
                yield content

    def list_models(self, include_embedding: bool = False) -> list[str]:
        models = []
        for model in self._client.list().models:
            name = normalize_model_name(model.model or "")
            family = (model.details.family if model.details else "") or ""
            is_embedding = any(h in f"{name} {family}".lower() for h in _EMBEDDING_HINTS)
            if name and (include_embedding or not is_embedding):
                models.append(name)
        return sorted(models)

    def is_available(self) -> bool:
        try:
            self._client.list()
        except Exception as exc:  # connection refused, timeout, ...
            logger.warning("Ollama is not reachable: %s", exc)
            return False
        return True
