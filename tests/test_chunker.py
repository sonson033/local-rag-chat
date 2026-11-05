from backend.domain.models import Document
from backend.ingestion.chunker import chunk_documents, split_text

TEXT = " ".join(f"This is sentence number {i} of the test text." for i in range(40))


def test_chunks_respect_max_size():
    chunks = split_text(TEXT, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)


def test_chunks_end_at_sentence_boundaries():
    for chunk in split_text(TEXT, chunk_size=200, overlap=50):
        assert chunk.endswith(".")
        assert chunk.startswith("This is sentence")


def test_consecutive_chunks_overlap():
    chunks = split_text(TEXT, chunk_size=200, overlap=60)
    for previous, current in zip(chunks, chunks[1:], strict=False):
        last_sentence = previous.split(". ")[-1]
        assert last_sentence.rstrip(".") in current


def test_no_overlap_when_zero():
    chunks = split_text(TEXT, chunk_size=200, overlap=0)
    assert "".join(c.replace(" ", "") for c in chunks) == TEXT.replace(" ", "")


def test_no_empty_chunks():
    assert split_text("   \n\n  \n", chunk_size=100, overlap=10) == []
    assert all(c.strip() for c in split_text("A.\n\n\nB.\n", chunk_size=100, overlap=10))


def test_very_long_sentence_is_hard_split():
    long_word = "x" * 450
    chunks = split_text(long_word, chunk_size=200, overlap=50)
    assert all(0 < len(c) <= 200 for c in chunks)
    assert chunks[0][-50:] == chunks[1][:50]  # overlap inside the hard split


def test_line_breaks_are_kept_for_markdown():
    chunks = split_text("# Title\n- item one\n- item two", chunk_size=100, overlap=10)
    assert chunks == ["# Title\n- item one\n- item two"]


def test_invalid_overlap_raises():
    import pytest

    with pytest.raises(ValueError):
        split_text("abc", chunk_size=100, overlap=100)


def test_chunk_documents_keeps_pages_and_deterministic_ids():
    docs = [
        Document(text="Page one text.", source="a.pdf", page=1),
        Document(text="Page two text.", source="a.pdf", page=2),
    ]
    chunks = chunk_documents(docs, file_hash="abc", chunk_size=100, overlap=10)
    assert [c.id for c in chunks] == ["abc:0", "abc:1"]
    assert [c.page for c in chunks] == [1, 2]
    assert chunks[1].location == "a.pdf – page 2"
