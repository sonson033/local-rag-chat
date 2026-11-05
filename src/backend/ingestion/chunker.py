"""Split documents into overlapping chunks that end at sentence boundaries.

Why chunks at all? An embedding of a whole 50-page PDF is too "blurry" to match a
specific question, and it would not fit into the prompt. Small chunks (~1000 chars)
are precise and cheap to put into the LLM context.

Why overlap? A fact can sit on the border of two chunks. Repeating the last ~200
characters of the previous chunk keeps that context together.

Why cut at sentence ends? A chunk that stops mid-sentence loses meaning, both for
the embedding and for the LLM that reads it.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from backend.domain.models import Chunk, Document

# A sentence ends with . ! or ? followed by whitespace.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_into_units(text: str) -> list[str]:
    """Split text into sentences/lines, each keeping its trailing separator.

    Line breaks are kept, so Markdown lists and headings stay readable.
    """
    units: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        sentences = [s for s in _SENTENCE_END.split(line) if s]
        units.extend(sentence + " " for sentence in sentences[:-1])
        units.append(sentences[-1] + "\n")
    return units


def _hard_split(unit: str, chunk_size: int, overlap: int) -> list[str]:
    """Fallback for a single "sentence" longer than a chunk (e.g. a table row dump)."""
    step = chunk_size - overlap
    pieces = []
    for start in range(0, len(unit), step):
        pieces.append(unit[start : start + chunk_size])
        if start + chunk_size >= len(unit):
            break
    return pieces


def _overlap_tail(units: list[str], overlap: int) -> list[str]:
    """The last whole units of a chunk whose total length fits into `overlap`."""
    tail: list[str] = []
    length = 0
    for unit in reversed(units):
        if length + len(unit) > overlap:
            break
        tail.insert(0, unit)
        length += len(unit)
    return tail


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split one text into chunks of at most `chunk_size` characters with sentence overlap."""
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    units: list[str] = []
    for unit in _split_into_units(text):
        units.extend(_hard_split(unit, chunk_size, overlap) if len(unit) > chunk_size else [unit])

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for unit in units:
        if current and current_len + len(unit) > chunk_size:
            chunks.append("".join(current).strip())
            current = _overlap_tail(current, overlap)
            current_len = sum(len(u) for u in current)
            # Drop overlap units if the next unit would not fit otherwise.
            while current and current_len + len(unit) > chunk_size:
                current_len -= len(current.pop(0))
        current.append(unit)
        current_len += len(unit)
    if current:
        chunks.append("".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def chunk_documents(
    documents: Iterable[Document], file_hash: str, chunk_size: int, overlap: int
) -> list[Chunk]:
    """Chunk all documents of one file. IDs are deterministic: `<file_hash>:<index>`.

    Deterministic IDs mean re-indexing the same file overwrites instead of duplicating.
    Chunks never span two PDF pages, so every chunk has exactly one page number.
    """
    chunks: list[Chunk] = []
    for document in documents:
        for text in split_text(document.text, chunk_size, overlap):
            index = len(chunks)
            chunks.append(
                Chunk(
                    id=f"{file_hash}:{index}",
                    text=text,
                    source=document.source,
                    file_hash=file_hash,
                    chunk_index=index,
                    page=document.page,
                )
            )
    return chunks
