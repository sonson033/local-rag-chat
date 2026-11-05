"""Use case "Answering": question -> embed -> retrieve top-k -> prompt -> stream answer."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence

from backend.domain.models import Answer, RetrievedChunk
from backend.ports import Embedder, LLMClient, Message, VectorStore
from backend.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

NO_DOCUMENTS_MESSAGE = "No documents are indexed yet. Add files in the sidebar first."


class QAService:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        llm: LLMClient,
        default_model: str,
        top_k: int,
        history_messages: int = 6,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._llm = llm
        self._default_model = default_model
        self._top_k = top_k
        self._history_messages = history_messages

    def retrieve(self, question: str, k: int | None = None) -> list[RetrievedChunk]:
        """Find the k chunks whose vectors are most similar to the question's vector."""
        embedding = self._embedder.embed_query(question)
        return self._store.query(embedding, k or self._top_k)

    def build_messages(
        self, question: str, sources: Sequence[RetrievedChunk], history: Sequence[Message]
    ) -> list[Message]:
        """System rules + short chat memory + the context-enriched question.

        Only the last N messages are kept: enough for follow-up questions,
        small enough for the context window of a small local model.
        The history contains the plain questions/answers, not old context blocks.
        """
        chat = [
            {"role": m["role"], "content": m["content"]}
            for m in history
            if m.get("role") in ("user", "assistant")
        ]
        recent = chat[-self._history_messages :] if self._history_messages > 0 else []
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            *recent,
            {"role": "user", "content": build_user_prompt(question, sources)},
        ]

    def answer(
        self,
        question: str,
        history: Sequence[Message] = (),
        model: str | None = None,
        k: int | None = None,
    ) -> Answer:
        """Retrieve context now, return a lazy token stream for the answer."""
        model = model or self._default_model
        if self._store.count() == 0:
            return Answer(stream=iter([NO_DOCUMENTS_MESSAGE]), sources=[], model=model)

        sources = self.retrieve(question, k)
        logger.info(
            "Retrieved %d chunk(s) for %r (best similarity %.2f)",
            len(sources),
            question,
            sources[0].similarity if sources else 0.0,
        )
        messages = self.build_messages(question, sources, history)
        stream: Iterator[str] = self._llm.stream_chat(messages, model)
        return Answer(stream=stream, sources=sources, model=model)
