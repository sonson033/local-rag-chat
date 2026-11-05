"""Shared test fixtures: fakes for every port, so no test needs Ollama or ChromaDB.

- FakeEmbedder: deterministic bag-of-words vectors -> texts sharing words are similar.
- FakeLLM: records the messages it received and streams a fixed answer.
- InMemoryVectorStore: a tiny cosine-similarity store implementing the VectorStore port.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from backend.config import Settings
from backend.container import create_api
from backend.domain.models import Chunk, RetrievedChunk, SourceInfo
from backend.ingestion.loaders import default_registry
from backend.ports import Message
from backend.services.ingestion_service import IngestionService
from backend.services.qa_service import QAService

DIMENSIONS = 64


class FakeEmbedder:
    """Hashes every word into one of 64 buckets and normalises the vector."""

    def __init__(self) -> None:
        self.calls = 0

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in re.findall(r"\w+", text.lower()):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % DIMENSIONS
            vector[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls += 1
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.calls += 1
        return self._vector(text)


class FakeLLM:
    """Streams a fixed answer word by word and remembers what it was asked."""

    def __init__(
        self,
        answer: str = "Employees get 28 vacation days [1].",
        models: list[str] | None = None,
        available: bool = True,
    ) -> None:
        self.answer = answer
        self.models = models if models is not None else ["llama3.2", "nomic-embed-text"]
        self.available = available
        self.received: list[Sequence[Message]] = []
        self.used_models: list[str] = []

    def stream_chat(self, messages: Sequence[Message], model: str) -> Iterator[str]:
        self.received.append(messages)
        self.used_models.append(model)
        for word in self.answer.split(" "):
            yield word + " "

    def list_models(self, include_embedding: bool = False) -> list[str]:
        if include_embedding:
            return list(self.models)
        return [m for m in self.models if "embed" not in m]

    def is_available(self) -> bool:
        return self.available


class InMemoryVectorStore:
    """Brute-force cosine search over a dict – enough for tests."""

    def __init__(self) -> None:
        self.items: dict[str, tuple[Chunk, list[float]]] = {}

    def add(self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]) -> None:
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self.items[chunk.id] = (chunk, list(embedding))

    def query(self, embedding: Sequence[float], k: int) -> list[RetrievedChunk]:
        def cosine(a: Sequence[float], b: Sequence[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b, strict=True))
            norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
            return dot / norm if norm else 0.0

        scored = [RetrievedChunk(c, cosine(embedding, e)) for c, e in self.items.values()]
        return sorted(scored, key=lambda r: r.similarity, reverse=True)[:k]

    def exists(self, file_hash: str) -> bool:
        return any(c.file_hash == file_hash for c, _ in self.items.values())

    def list_sources(self) -> list[SourceInfo]:
        counts: dict[str, int] = {}
        for chunk, _ in self.items.values():
            counts[chunk.source] = counts.get(chunk.source, 0) + 1
        return [SourceInfo(s, n) for s, n in sorted(counts.items())]

    def count(self) -> int:
        return len(self.items)

    def delete_source(self, source: str) -> int:
        ids = [i for i, (c, _) in self.items.items() if c.source == source]
        for chunk_id in ids:
            del self.items[chunk_id]
        return len(ids)

    def reset(self) -> None:
        self.items.clear()


HANDBOOK = """# Company Handbook

## Vacation
Employees get 28 vacation days per year. Unused days expire on 31 March of the next year.

## Working hours
Core hours are from 10:00 to 15:00. The weekly working time is 38 hours.
"""


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        chunk_size=200,
        chunk_overlap=40,
        top_k=2,
        db_path=tmp_path / "db",
        docs_dir=tmp_path / "docs",
        project_root=tmp_path,
    )


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def ingestion_service(
    settings: Settings, embedder: FakeEmbedder, store: InMemoryVectorStore
) -> IngestionService:
    return IngestionService(
        registry=default_registry(),
        embedder=embedder,
        store=store,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        base_dir=settings.project_root,
    )


@pytest.fixture
def qa_service(
    settings: Settings, embedder: FakeEmbedder, store: InMemoryVectorStore, llm: FakeLLM
) -> QAService:
    return QAService(
        embedder=embedder,
        store=store,
        llm=llm,
        default_model=settings.chat_model,
        top_k=settings.top_k,
        history_messages=settings.history_messages,
    )


@pytest.fixture
def api(settings, embedder, store, llm):
    return create_api(settings, embedder=embedder, store=store, llm=llm)
