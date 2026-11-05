from backend.api import BackendAPI
from backend.container import create_api
from tests.conftest import HANDBOOK, FakeLLM, InMemoryVectorStore


def test_index_uploaded_and_list_sources(api: BackendAPI):
    report = api.index_uploaded("handbook.md", HANDBOOK.encode())

    assert report.added == ["handbook.md"]
    assert [s.source for s in api.list_sources()] == ["handbook.md"]
    assert api.index_uploaded("handbook.md", HANDBOOK.encode()).skipped == ["handbook.md"]


def test_upload_name_is_reduced_to_file_name(api: BackendAPI):
    report = api.index_uploaded("../../etc/handbook.md", HANDBOOK.encode())
    assert report.added == ["handbook.md"]


def test_index_folder_relative_to_project_root(api: BackendAPI, settings):
    folder = settings.project_root / "data" / "documents"
    folder.mkdir(parents=True)
    (folder / "handbook.md").write_text(HANDBOOK)

    report = api.index_folder("data/documents")

    assert report.added == ["data/documents/handbook.md"]


def test_invalid_folder_is_reported_not_raised(api: BackendAPI):
    report = api.index_folder("does/not/exist")
    assert report.summary() == "0 new, 0 already indexed, 1 failed"
    assert "not found" in report.failed[0].error


def test_ask_returns_stream_and_sources(api: BackendAPI):
    api.index_uploaded("handbook.md", HANDBOOK.encode())

    stream, sources = api.ask("How many vacation days?", history=[], k=1)

    assert len(sources) == 1
    assert "28" in "".join(stream)


def test_stats_and_reset(api: BackendAPI, settings):
    api.index_uploaded("handbook.md", HANDBOOK.encode())
    stats = api.stats()
    assert stats.files == 1 and stats.chunks > 0
    assert stats.chunk_size == settings.chunk_size

    api.reset()

    assert api.stats().chunks == 0
    assert api.list_sources() == []


def test_health_ok(api: BackendAPI):
    assert api.health().ok


def test_health_when_ollama_is_down(settings, embedder):
    api = create_api(settings, embedder, InMemoryVectorStore(), FakeLLM(available=False))
    health = api.health()
    assert not health.ollama_running and not health.ok


def test_health_reports_missing_models(settings, embedder):
    api = create_api(settings, embedder, InMemoryVectorStore(), FakeLLM(models=["mistral"]))
    assert api.health().missing_models == ["llama3.2", "nomic-embed-text"]


def test_list_models_puts_default_first_and_hides_embedders(settings, embedder):
    llm = FakeLLM(models=["mistral", "llama3.2", "nomic-embed-text"])
    api = create_api(settings, embedder, InMemoryVectorStore(), llm)
    assert api.list_models() == ["llama3.2", "mistral"]
