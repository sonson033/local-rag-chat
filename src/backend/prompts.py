"""Prompt templates. Kept in one place so they are easy to read, tune and test.

The system prompt is the "grounding contract": the model may only use the numbered
context blocks, must cite them, and must admit when the answer is not there.
"""

from __future__ import annotations

from collections.abc import Sequence

from backend.domain.models import RetrievedChunk

NOT_FOUND_MESSAGE = "I couldn't find that in your documents."

SYSTEM_PROMPT = f"""You are a helpful assistant that answers questions about the user's documents.

Rules:
1. Use ONLY the information in the numbered context blocks provided with the question.
   Do not use your own knowledge.
2. If the answer is not in the context, reply exactly: "{NOT_FOUND_MESSAGE}"
3. Cite your sources with the block numbers in square brackets, e.g. [1] or [2][3],
   right after the sentence that uses them.
4. Answer in the same language as the question.
5. Be concise and precise. Quote numbers, dates and names exactly as in the context."""


def format_context(sources: Sequence[RetrievedChunk]) -> str:
    """Numbered context blocks: `[1] (file – page 2)` followed by the chunk text."""
    return "\n\n".join(
        f"[{number}] ({item.chunk.location})\n{item.chunk.text}"
        for number, item in enumerate(sources, start=1)
    )


def build_user_prompt(question: str, sources: Sequence[RetrievedChunk]) -> str:
    """The final user message: context first, then the question."""
    return (
        f"Context:\n{format_context(sources)}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above and cite the block numbers."
    )
