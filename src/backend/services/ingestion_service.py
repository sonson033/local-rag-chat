"""Use case "Indexing": file -> load -> chunk -> embed -> store.

The service only depends on ports (Embedder, VectorStore) and the loader registry,
never on Ollama or Chroma directly.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from pathlib import Path

from backend.domain.errors import DocumentLoadError
from backend.domain.models import FailedFile, IngestionReport
from backend.ingestion.chunker import chunk_documents
from backend.ingestion.folder_scanner import scan_folder
from backend.ingestion.loaders import LoaderRegistry
from backend.ports import Embedder, VectorStore

logger = logging.getLogger(__name__)

# progress(done, total, current_file) – lets the UI draw a progress bar
# without the backend knowing anything about Streamlit.
ProgressCallback = Callable[[int, int, str], None]


def file_hash(data: bytes) -> str:
    """MD5 of the file content. Used as fingerprint, not for security."""
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


class IngestionService:
    def __init__(
        self,
        registry: LoaderRegistry,
        embedder: Embedder,
        store: VectorStore,
        chunk_size: int,
        chunk_overlap: int,
        base_dir: Path,
    ) -> None:
        self._registry = registry
        self._embedder = embedder
        self._store = store
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._base_dir = base_dir

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return self._registry.supported_extensions

    def ingest_bytes(self, data: bytes, source: str) -> IngestionReport:
        """Index one file. Never raises: problems end up in `report.failed`."""
        report = IngestionReport()
        try:
            digest = file_hash(data)
            if self._store.exists(digest):
                logger.info("Skipping %s: already indexed", source)
                report.skipped.append(source)
                return report

            documents = self._registry.load(data, source)
            chunks = chunk_documents(documents, digest, self._chunk_size, self._chunk_overlap)
            if not chunks:
                raise DocumentLoadError("The file contains no text.")

            # Embed first, then replace: if Ollama fails, the old version stays intact.
            embeddings = self._embedder.embed_documents([c.text for c in chunks])
            replaced = self._store.delete_source(source)
            self._store.add(chunks, embeddings)
        except Exception as exc:  # one bad file must never stop the whole run
            logger.exception("Failed to index %s", source)
            report.failed.append(FailedFile(source=source, error=str(exc) or type(exc).__name__))
            return report

        if replaced:
            logger.info("Updated %s (content changed, %d old chunks replaced)", source, replaced)
        report.added.append(source)
        report.chunks_added = len(chunks)
        return report

    def ingest_file(self, path: Path) -> IngestionReport:
        """Index a file from disk; its source id is the path relative to the project."""
        source = self._source_id(path)
        try:
            data = path.read_bytes()
        except OSError as exc:
            return IngestionReport(failed=[FailedFile(source=source, error=str(exc))])
        return self.ingest_bytes(data, source)

    def ingest_folder(
        self, folder: Path, progress: ProgressCallback | None = None
    ) -> IngestionReport:
        """Index all supported files below `folder`.

        Raises:
            FileNotFoundError / NotADirectoryError: the folder itself is invalid.
        """
        files = scan_folder(folder, self.supported_extensions)
        report = IngestionReport()
        for done, path in enumerate(files, start=1):
            report.merge(self.ingest_file(path))
            if progress:
                progress(done, len(files), path.name)
        logger.info("Folder %s: %s", folder, report.summary())
        return report

    def _source_id(self, path: Path) -> str:
        """Readable but unique id: relative to the project if possible, else absolute."""
        resolved = path.resolve()
        try:
            return resolved.relative_to(self._base_dir.resolve()).as_posix()
        except ValueError:
            return resolved.as_posix()
