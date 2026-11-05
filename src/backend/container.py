"""Dependency injection: the only place that knows which concrete classes are used.

`build_backend()` wires the real adapters (Ollama + Chroma).
`create_api()` accepts any objects that fulfil the ports, which is how the tests
inject fakes. Swapping a technology means changing this file, not the services.
"""

from __future__ import annotations

import logging

import ollama

from backend.adapters.chroma_store import ChromaStore
from backend.adapters.ollama_embedder import OllamaEmbedder
from backend.adapters.ollama_llm import OllamaLLM
from backend.api import BackendAPI
from backend.config import Settings
from backend.ingestion.loaders import default_registry
from backend.ports import Embedder, LLMClient, VectorStore
from backend.services.ingestion_service import IngestionService
from backend.services.qa_service import QAService

logger = logging.getLogger(__name__)


def create_api(
    settings: Settings, embedder: Embedder, store: VectorStore, llm: LLMClient
) -> BackendAPI:
    """Build services and the API facade from the given port implementations."""
    ingestion = IngestionService(
        registry=default_registry(),
        embedder=embedder,
        store=store,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        base_dir=settings.project_root,
    )
    qa = QAService(
        embedder=embedder,
        store=store,
        llm=llm,
        default_model=settings.chat_model,
        top_k=settings.top_k,
        history_messages=settings.history_messages,
    )
    return BackendAPI(settings=settings, ingestion=ingestion, qa=qa, store=store, llm=llm)


def build_backend(settings: Settings | None = None) -> BackendAPI:
    """Production wiring: local Ollama + persistent ChromaDB."""
    settings = settings or Settings.from_env()
    client = ollama.Client(host=settings.ollama_host)
    logger.info(
        "Backend: chat=%s embed=%s db=%s",
        settings.chat_model,
        settings.embed_model,
        settings.db_path,
    )
    return create_api(
        settings,
        embedder=OllamaEmbedder(client, settings.embed_model),
        store=ChromaStore(settings.db_path, settings.collection),
        llm=OllamaLLM(client),
    )
