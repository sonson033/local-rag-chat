"""Ports: the interfaces the services depend on (Ports & Adapters / hexagonal architecture).

The services only know these Protocols. The concrete classes (adapters) for Ollama and
ChromaDB live in `backend.adapters`. Because of this:
- tests can plug in fast, deterministic fakes (no Ollama needed),
- an adapter can be swapped (e.g. Chroma -> FAISS, Ollama -> llama.cpp) without
  touching any service code.

`typing.Protocol` uses structural typing: a class "implements" a port just by having
the right methods. No inheritance needed.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol

from backend.domain.models import Chunk, Document, RetrievedChunk, SourceInfo

Message = dict[str, str]  # {"role": "user" | "assistant" | "system", "content": "..."}


class DocumentLoader(Protocol):
    """Turns the bytes of one file type into Documents."""

    extensions: tuple[str, ...]

    def load(self, data: bytes, source: str) -> list[Document]: ...


class Embedder(Protocol):
    """Turns text into vectors. Documents and queries may be embedded differently."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    """Stores chunks with their vectors and finds the most similar ones."""

    def add(self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]) -> None: ...

    def query(self, embedding: Sequence[float], k: int) -> list[RetrievedChunk]: ...

    def exists(self, file_hash: str) -> bool: ...

    def list_sources(self) -> list[SourceInfo]: ...

    def count(self) -> int: ...

    def delete_source(self, source: str) -> int: ...

    def reset(self) -> None: ...


class LLMClient(Protocol):
    """A chat model that can stream its answer."""

    def stream_chat(self, messages: Sequence[Message], model: str) -> Iterator[str]: ...

    def list_models(self, include_embedding: bool = False) -> list[str]: ...

    def is_available(self) -> bool: ...
