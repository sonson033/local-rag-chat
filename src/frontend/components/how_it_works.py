"""'How it works' tab: explains the RAG pipeline and shows the live settings (for the demo)."""

from __future__ import annotations

import streamlit as st

from backend.api import BackendAPI

PIPELINE = """
```
 INDEXING (once per file)
 ┌──────┐   ┌───────┐   ┌───────┐   ┌───────┐
 │ Load │──▶│ Split │──▶│ Embed │──▶│ Store │
 └──────┘   └───────┘   └───────┘   └───────┘
  PDF/DOCX   chunks      vectors     ChromaDB

 ANSWERING (every question)
 ┌─────┐   ┌──────────┐   ┌──────────┐   ┌──────┐
 │ Ask │──▶│ Retrieve │──▶│ Generate │──▶│ Cite │
 └─────┘   └──────────┘   └──────────┘   └──────┘
  question  top-k chunks   local LLM      [1] [2]
```
"""


def render_how_it_works(api: BackendAPI) -> None:
    stats = api.stats()
    st.header("ℹ️ How it works")
    st.markdown(
        "**RAG = Retrieval-Augmented Generation.** The model does not need to know your "
        "documents. We *retrieve* the relevant parts first and give them to the model "
        "together with your question. Everything runs locally on this computer."
    )
    st.markdown(PIPELINE)

    indexing, answering = st.columns(2)
    with indexing:
        st.subheader("1 · Indexing")
        st.markdown(
            f"""
1. **Load** – read text from PDF (page by page), DOCX, Markdown, TXT or CSV.
2. **Split** – cut the text into chunks of ~{stats.chunk_size} characters with
   {stats.chunk_overlap} characters overlap, ending at sentence boundaries.
3. **Embed** – `{stats.embed_model}` turns every chunk into a vector (a list of numbers
   that captures its meaning).
4. **Store** – vectors, text, file name and page go into ChromaDB on disk.
   Files that are already indexed (same content hash) are skipped.
"""
        )
    with answering:
        st.subheader("2 · Answering")
        st.markdown(
            f"""
1. **Ask** – your question is embedded with the same model.
2. **Retrieve** – ChromaDB returns the *k* chunks with the highest cosine similarity.
3. **Generate** – `{st.session_state.get("model", stats.chat_model)}` answers using
   **only** these chunks. If the answer is not there, it says so.
4. **Cite** – the answer references the chunks as [1], [2] … – open **📎 Sources** to
   check them.
"""
        )

    st.subheader("Current settings")
    st.table(
        hide_index=True,
        data={
            "Setting": [
                "Chat model (default)",
                "Embedding model",
                "Chunk size",
                "Chunk overlap",
                "k (default / selected)",
                "Chunks in knowledge base",
                "Indexed files",
                "Vector DB path",
            ],
            "Value": [
                stats.chat_model,
                stats.embed_model,
                f"{stats.chunk_size} characters",
                f"{stats.chunk_overlap} characters",
                f"{stats.top_k} / {st.session_state.get('top_k', stats.top_k)}",
                str(stats.chunks),
                str(stats.files),
                stats.db_path,
            ],
        },
    )
