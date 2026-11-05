from backend.domain.models import IngestionReport
from scripts.make_sample_pdf import build_pdf
from tests.conftest import HANDBOOK


def test_new_file_is_chunked_embedded_and_stored(ingestion_service, store):
    report = ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")

    assert report.added == ["handbook.md"]
    assert report.chunks_added == store.count() > 1
    assert {s.source for s in store.list_sources()} == {"handbook.md"}


def test_same_content_is_skipped(ingestion_service, embedder):
    ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")
    calls = embedder.calls

    report = ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")

    assert report.skipped == ["handbook.md"]
    assert embedder.calls == calls  # no embedding work for duplicates


def test_changed_file_replaces_old_chunks(ingestion_service, store):
    ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")
    ingestion_service.ingest_bytes(b"Employees get 30 vacation days.", "handbook.md")

    texts = [chunk.text for chunk, _ in store.items.values()]
    assert texts == ["Employees get 30 vacation days."]


def test_failures_are_reported_not_raised(ingestion_service, store):
    report = ingestion_service.ingest_bytes(b"\x89PNG", "image.png")
    empty = ingestion_service.ingest_bytes(b"   ", "empty.txt")

    assert [f.source for f in report.failed] == ["image.png"]
    assert "Unsupported" in report.failed[0].error
    assert empty.failed and store.count() == 0


def test_embedding_failure_keeps_old_version(ingestion_service, store, embedder):
    ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")
    before = store.count()

    def broken(_texts):
        raise ConnectionError("Ollama down")

    embedder.embed_documents = broken
    report = ingestion_service.ingest_bytes(b"New content.", "handbook.md")

    assert report.failed[0].error == "Ollama down"
    assert store.count() == before


def test_folder_ingestion_with_progress(ingestion_service, settings):
    folder = settings.project_root / "docs"
    (folder / "sub").mkdir(parents=True)
    (folder / "handbook.md").write_text(HANDBOOK)
    (folder / "sub" / "policy.pdf").write_bytes(build_pdf([["Travel by train."]]))
    (folder / "ignored.png").write_bytes(b"x")
    progress: list[tuple[int, int, str]] = []

    report = ingestion_service.ingest_folder(folder, lambda *a: progress.append(a))

    assert sorted(report.added) == ["docs/handbook.md", "docs/sub/policy.pdf"]
    assert [p[:2] for p in progress] == [(1, 2), (2, 2)]
    again = ingestion_service.ingest_folder(folder)
    assert again.summary() == "0 new, 2 already indexed, 0 failed"


def test_report_merge_and_summary():
    report = IngestionReport(added=["a"])
    report.merge(IngestionReport(skipped=["b"], chunks_added=3))
    assert report.summary() == "1 new, 1 already indexed, 0 failed"
    assert report.chunks_added == 3
