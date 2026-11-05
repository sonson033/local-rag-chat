from backend.prompts import NOT_FOUND_MESSAGE, SYSTEM_PROMPT
from backend.services.qa_service import NO_DOCUMENTS_MESSAGE
from tests.conftest import HANDBOOK


def test_no_documents_means_no_llm_call(qa_service, llm):
    answer = qa_service.answer("How many vacation days?")

    assert "".join(answer.stream) == NO_DOCUMENTS_MESSAGE
    assert answer.sources == []
    assert llm.received == []


def test_retrieval_finds_the_relevant_chunk(qa_service, ingestion_service):
    ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")

    sources = qa_service.retrieve("How many vacation days do employees get per year?", k=1)

    assert "28 vacation days" in sources[0].chunk.text
    assert 0 < sources[0].similarity <= 1


def test_prompt_has_rules_numbered_context_and_question(qa_service, ingestion_service, llm):
    ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")

    answer = qa_service.answer("How many vacation days?", k=2)
    text = "".join(answer.stream)  # the LLM is only called while streaming

    messages = llm.received[0]
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert "[1] (handbook.md)" in messages[-1]["content"]
    assert "[2] (handbook.md)" in messages[-1]["content"]
    assert messages[-1]["content"].rstrip().endswith("cite the block numbers.")
    assert "Question: How many vacation days?" in messages[-1]["content"]
    assert text.strip() == llm.answer
    assert len(answer.sources) == 2


def test_system_prompt_enforces_grounding():
    assert NOT_FOUND_MESSAGE in SYSTEM_PROMPT
    assert "ONLY" in SYSTEM_PROMPT
    assert "same language" in SYSTEM_PROMPT


def test_history_is_limited_to_last_six_messages(qa_service, ingestion_service, llm):
    ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(10)
    ]

    list(qa_service.answer("And the core hours?", history=history).stream)

    messages = llm.received[0]
    assert [m["content"] for m in messages[1:-1]] == ["m4", "m5", "m6", "m7", "m8", "m9"]


def test_chosen_model_is_used(qa_service, ingestion_service, llm):
    ingestion_service.ingest_bytes(HANDBOOK.encode(), "handbook.md")
    answer = qa_service.answer("Vacation?", model="mistral")
    list(answer.stream)
    assert llm.used_models == ["mistral"]
    assert answer.model == "mistral"
