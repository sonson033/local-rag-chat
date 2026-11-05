"""Embedder adapter for a local Ollama embedding model (default: nomic-embed-text)."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import ollama

logger = logging.getLogger(__name__)

# nomic-embed-text was trained with task prefixes. Using them gives better retrieval:
# documents and questions are embedded "for their role" in the search.
_NOMIC_PREFIXES = ("search_document: ", "search_query: ")


class OllamaEmbedder:
    """Calls Ollama's `/api/embed` in batches of 32 texts."""

    def __init__(self, client: ollama.Client, model: str, batch_size: int = 32) -> None:
        self._client = client
        self._model = model
        self._batch_size = batch_size
        self._use_prefixes = "nomic" in model

    def _prefix(self, kind: int) -> str:
        return _NOMIC_PREFIXES[kind] if self._use_prefixes else ""

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = list(texts[start : start + self._batch_size])
            response = self._client.embed(model=self._model, input=batch)
            vectors.extend(list(vector) for vector in response.embeddings)
        logger.debug("Embedded %d text(s) with %s", len(texts), self._model)
        return vectors

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed([self._prefix(0) + text for text in texts])

    def embed_query(self, text: str) -> list[float]:
        return self._embed([self._prefix(1) + text])[0]
