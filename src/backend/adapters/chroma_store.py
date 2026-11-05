"""VectorStore adapter for ChromaDB, persisted on the local disk."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.domain.models import Chunk, RetrievedChunk, SourceInfo

logger = logging.getLogger(__name__)

_NO_PAGE = 0  # Chroma metadata cannot be None, so 0 means "no page".


class ChromaStore:
    """Chunks + vectors + metadata in one persistent Chroma collection (cosine distance)."""

    def __init__(self, path: Path, collection: str) -> None:
        path.mkdir(parents=True, exist_ok=True)
        # Telemetry off: nothing leaves the computer.
        self._client = chromadb.PersistentClient(
            path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._name = collection
        self._collection = self._open_collection()

    def _open_collection(self) -> Any:
        # We always pass our own embeddings, so Chroma's built-in model is never used.
        return self._client.get_or_create_collection(
            name=self._name,
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,
        )

    def add(self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=[list(e) for e in embeddings],
            metadatas=[
                {
                    "source": c.source,
                    "file_hash": c.file_hash,
                    "chunk_index": c.chunk_index,
                    "page": c.page or _NO_PAGE,
                }
                for c in chunks
            ],
        )
        logger.info("Stored %d chunk(s) from %s", len(chunks), chunks[0].source)

    def query(self, embedding: Sequence[float], k: int) -> list[RetrievedChunk]:
        total = self.count()
        if total == 0:
            return []
        result = self._collection.query(
            query_embeddings=[list(embedding)],
            n_results=min(k, total),
            include=["documents", "metadatas", "distances"],
        )
        retrieved = []
        for chunk_id, text, meta, distance in zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
            strict=True,
        ):
            chunk = Chunk(
                id=chunk_id,
                text=text,
                source=str(meta["source"]),
                file_hash=str(meta["file_hash"]),
                chunk_index=int(meta["chunk_index"]),
                page=int(meta["page"]) or None,
            )
            # Cosine distance = 1 - cosine similarity.
            retrieved.append(RetrievedChunk(chunk=chunk, similarity=1.0 - float(distance)))
        return retrieved

    def exists(self, file_hash: str) -> bool:
        found = self._collection.get(where={"file_hash": file_hash}, limit=1, include=[])
        return bool(found["ids"])

    def list_sources(self) -> list[SourceInfo]:
        metadatas = self._collection.get(include=["metadatas"])["metadatas"] or []
        counts = Counter(str(meta["source"]) for meta in metadatas)
        return [SourceInfo(source=s, chunks=n) for s, n in sorted(counts.items())]

    def count(self) -> int:
        return self._collection.count()

    def delete_source(self, source: str) -> int:
        existing = self._collection.get(where={"source": source}, include=[])["ids"]
        if existing:
            self._collection.delete(ids=existing)
            logger.info("Deleted %d old chunk(s) of %s", len(existing), source)
        return len(existing)

    def reset(self) -> None:
        self._client.delete_collection(self._name)
        self._collection = self._open_collection()
        logger.info("Knowledge base cleared")
