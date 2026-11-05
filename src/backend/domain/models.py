"""Domain models: the data that flows through the RAG pipeline.

They are plain dataclasses on purpose: no Streamlit, no Ollama, no Chroma types.
Every layer can use them, and they are trivial to create in tests.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import PurePath


@dataclass(frozen=True)
class Document:
    """Raw text extracted from a file. One PDF page = one Document (keeps page numbers)."""

    text: str
    source: str
    page: int | None = None


@dataclass(frozen=True)
class Chunk:
    """A piece of a Document small enough to embed and to put into a prompt."""

    id: str
    text: str
    source: str
    file_hash: str
    chunk_index: int
    page: int | None = None

    @property
    def file_name(self) -> str:
        """Short name for citations, e.g. `company_handbook.md`."""
        return PurePath(self.source).name

    @property
    def location(self) -> str:
        """Human readable location used in prompts and the Sources panel."""
        return f"{self.file_name} – page {self.page}" if self.page else self.file_name


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by vector search, with its cosine similarity (1.0 = identical)."""

    chunk: Chunk
    similarity: float


@dataclass
class Answer:
    """Result of a question: a token stream plus the chunks the answer is grounded on.

    The stream is lazy: the LLM only starts generating when someone iterates it.
    That is what lets the UI render tokens as they arrive.
    """

    stream: Iterator[str]
    sources: list[RetrievedChunk]
    model: str


@dataclass(frozen=True)
class FailedFile:
    """A file that could not be indexed and why."""

    source: str
    error: str


@dataclass
class IngestionReport:
    """Outcome of an indexing run, tracked per file."""

    added: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[FailedFile] = field(default_factory=list)
    chunks_added: int = 0

    def merge(self, other: IngestionReport) -> None:
        """Add the results of another report (used when indexing many files)."""
        self.added.extend(other.added)
        self.skipped.extend(other.skipped)
        self.failed.extend(other.failed)
        self.chunks_added += other.chunks_added

    def summary(self) -> str:
        """One-line summary for the UI."""
        return (
            f"{len(self.added)} new, {len(self.skipped)} already indexed, {len(self.failed)} failed"
        )


@dataclass(frozen=True)
class SourceInfo:
    """One indexed file and how many chunks it produced."""

    source: str
    chunks: int


@dataclass(frozen=True)
class HealthStatus:
    """Is Ollama reachable, and are the configured models pulled?"""

    ollama_running: bool
    missing_models: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.ollama_running and not self.missing_models


@dataclass(frozen=True)
class Stats:
    """Current configuration and size of the knowledge base (for the 'How it works' tab)."""

    chunks: int
    files: int
    chat_model: str
    embed_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    db_path: str
    docs_dir: str
