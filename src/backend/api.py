"""Public API of the backend – the ONLY module the frontend imports.

A facade: a small, stable set of methods that hides services, ports and adapters.
If the backend later moves behind FastAPI, each method becomes an HTTP endpoint
and the frontend only needs a thin HTTP client with the same method names.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from pathlib import Path

from backend.config import Settings
from backend.domain.models import (
    FailedFile,
    HealthStatus,
    IngestionReport,
    RetrievedChunk,
    SourceInfo,
    Stats,
)
from backend.ports import LLMClient, Message, VectorStore
from backend.services.ingestion_service import IngestionService, ProgressCallback
from backend.services.qa_service import QAService

logger = logging.getLogger(__name__)

# Re-exported so the frontend can use these types without importing internals.
__all__ = [
    "BackendAPI",
    "FailedFile",
    "HealthStatus",
    "IngestionReport",
    "Message",
    "ProgressCallback",
    "RetrievedChunk",
    "Settings",
    "SourceInfo",
    "Stats",
    "build_backend",
]


class BackendAPI:
    def __init__(
        self,
        settings: Settings,
        ingestion: IngestionService,
        qa: QAService,
        store: VectorStore,
        llm: LLMClient,
    ) -> None:
        self.settings = settings
        self._ingestion = ingestion
        self._qa = qa
        self._store = store
        self._llm = llm

    # --- status -----------------------------------------------------------------------
    def health(self) -> HealthStatus:
        """Is Ollama running and are the configured models pulled?"""
        if not self._llm.is_available():
            return HealthStatus(ollama_running=False)
        installed = set(self._llm.list_models(include_embedding=True))
        wanted = (self.settings.chat_model, self.settings.embed_model)
        missing = [m for m in wanted if m.removesuffix(":latest") not in installed]
        return HealthStatus(ollama_running=True, missing_models=missing)

    def list_models(self) -> list[str]:
        """Local chat models (embedding-only models filtered out), default model first."""
        try:
            models = self._llm.list_models()
        except Exception:
            logger.exception("Could not list models")
            models = []
        default = self.settings.chat_model
        return [default, *[m for m in models if m != default]]

    def list_sources(self) -> list[SourceInfo]:
        return self._store.list_sources()

    def stats(self) -> Stats:
        s = self.settings
        return Stats(
            chunks=self._store.count(),
            files=len(self._store.list_sources()),
            chat_model=s.chat_model,
            embed_model=s.embed_model,
            chunk_size=s.chunk_size,
            chunk_overlap=s.chunk_overlap,
            top_k=s.top_k,
            db_path=str(s.db_path),
            docs_dir=str(s.docs_dir),
        )

    # --- indexing ---------------------------------------------------------------------
    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return self._ingestion.supported_extensions

    def index_uploaded(self, name: str, data: bytes) -> IngestionReport:
        """Index a file uploaded in the browser (identified by its file name)."""
        return self._ingestion.ingest_bytes(data, Path(name).name)

    def index_folder(
        self, path: str | Path, progress: ProgressCallback | None = None
    ) -> IngestionReport:
        """Index every supported file in a local folder (relative paths = project root).

        An invalid folder is reported as a failed entry instead of raising.
        """
        folder = self.settings.resolve_path(path)
        try:
            return self._ingestion.ingest_folder(folder, progress)
        except (FileNotFoundError, NotADirectoryError) as exc:
            return IngestionReport(failed=[FailedFile(source=str(folder), error=str(exc))])

    # --- answering --------------------------------------------------------------------
    def ask(
        self,
        question: str,
        history: Sequence[Message] = (),
        model: str | None = None,
        k: int | None = None,
    ) -> tuple[Iterator[str], list[RetrievedChunk]]:
        """Return (lazy token stream, retrieved sources) for a question."""
        answer = self._qa.answer(question, history=history, model=model, k=k)
        return answer.stream, answer.sources

    def reset(self) -> None:
        """Delete all chunks from the knowledge base."""
        self._store.reset()


def build_backend(settings: Settings | None = None) -> BackendAPI:
    """Create the production backend (imported lazily to avoid a circular import)."""
    from backend.container import build_backend as _build

    return _build(settings)
