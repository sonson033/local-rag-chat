"""Chat tab: history, question input, streamed answer with sources."""

from __future__ import annotations

import logging
import time

import streamlit as st

from backend.api import BackendAPI, RetrievedChunk
from frontend import state

logger = logging.getLogger(__name__)

PREVIEW_CHARS = 400


def _render_sources(sources: list[RetrievedChunk]) -> None:
    if not sources:
        return
    with st.expander("📎 Sources"):
        for number, item in enumerate(sources, start=1):
            st.markdown(f"**[{number}] {item.chunk.location}** (similarity {item.similarity:.2f})")
            preview = item.chunk.text[:PREVIEW_CHARS]
            if len(item.chunk.text) > PREVIEW_CHARS:
                preview += " …"
            st.text(preview)


def _render_message(message: state.ChatMessage) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        _render_sources(message.get("sources", []))
        if message.get("meta"):
            st.caption(message["meta"])


def _answer(api: BackendAPI, question: str) -> None:
    """Ask the backend and stream the answer into an assistant bubble."""
    model = st.session_state[state.MODEL]
    history = [{"role": m["role"], "content": m["content"]} for m in state.messages()]
    started = time.perf_counter()
    with st.chat_message("assistant"):
        try:
            stream, sources = api.ask(
                question, history=history, model=model, k=st.session_state[state.TOP_K]
            )
            text = st.write_stream(stream)
        except Exception as exc:  # Ollama stopped, model missing, ...
            logger.exception("Answering failed")
            st.error(f"Could not get an answer: {exc}")
            return
        meta = f"{model} · {time.perf_counter() - started:.1f} s"
        _render_sources(sources)
        st.caption(meta)

    content = text if isinstance(text, str) else "".join(map(str, text))
    state.add_message({"role": "user", "content": question})
    state.add_message({"role": "assistant", "content": content, "sources": sources, "meta": meta})


def render_chat(api: BackendAPI) -> None:
    st.title("📚 Local RAG Chat")
    st.caption("Ask anything about your documents – runs 100% offline on localhost.")

    # Container first, input after: new messages appear above the input box.
    conversation = st.container()
    question = st.chat_input("Ask a question about your documents…")

    with conversation:
        for message in state.messages():
            _render_message(message)

        if not question:
            if not state.messages():
                st.info("Index a folder or upload files in the sidebar, then ask a question.")
            return

        with st.chat_message("user"):
            st.markdown(question)

        if api.stats().chunks == 0:
            with st.chat_message("assistant"):
                st.warning(
                    "No documents are indexed yet. Scan a folder or upload files in the "
                    "sidebar first."
                )
            return

        _answer(api, question)
