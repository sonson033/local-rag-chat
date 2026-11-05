"""Sidebar: model and k selection, indexing (folder + upload), status and reset."""

from __future__ import annotations

import streamlit as st

from backend.api import BackendAPI, IngestionReport
from frontend import state


def _show_report(report: IngestionReport) -> None:
    """Summary line plus one error box per failed file."""
    if report.failed and not report.added:
        st.warning(report.summary())
    else:
        st.success(report.summary())
    for failed in report.failed:
        st.error(f"**{failed.source}**: {failed.error}")


def _model_settings(api: BackendAPI) -> None:
    models = api.list_models()
    if st.session_state[state.MODEL] not in models:
        st.session_state[state.MODEL] = models[0]
    st.selectbox(
        "Local model",
        models,
        key=state.MODEL,
        help="Chat models installed in Ollama (`ollama list`). Embedding models are hidden.",
    )
    st.slider(
        "Chunks to retrieve (k)",
        min_value=1,
        max_value=10,
        key=state.TOP_K,
        help="How many of the most similar text chunks are given to the model as context.",
    )


def _folder_section(api: BackendAPI) -> None:
    st.markdown("**From your computer**")
    folder = st.text_input(
        "Folder path",
        key=state.FOLDER,
        help="Absolute path, or relative to the project folder (e.g. data/documents/sample).",
    )
    if st.button("Scan & index folder", width="stretch"):
        bar = st.progress(0.0, text="Scanning folder…")

        def progress(done: int, total: int, name: str) -> None:
            bar.progress(done / total, text=f"Indexed {done}/{total}: {name}")

        report = api.index_folder(folder, progress)
        bar.empty()
        _show_report(report)


def _upload_section(api: BackendAPI) -> None:
    st.markdown("**Upload**")
    files = st.file_uploader(
        "Upload files",
        type=[ext.lstrip(".") for ext in api.supported_extensions],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if st.button("Index uploads", width="stretch", disabled=not files):
        report = IngestionReport()
        bar = st.progress(0.0, text="Indexing uploads…")
        for done, file in enumerate(files, start=1):
            report.merge(api.index_uploaded(file.name, file.getvalue()))
            bar.progress(done / len(files), text=f"Indexed {done}/{len(files)}: {file.name}")
        bar.empty()
        _show_report(report)


def _status(api: BackendAPI) -> None:
    sources = api.list_sources()
    chunks = sum(s.chunks for s in sources)
    st.markdown(f"**Knowledge base:** {chunks} chunks from {len(sources)} file(s)")
    if sources:
        with st.expander("Indexed files", expanded=len(sources) <= 6):
            for source in sources:
                st.markdown(f"- `{source.source}` ({source.chunks})")


def render_sidebar(api: BackendAPI) -> None:
    with st.sidebar:
        st.header("📂 Your documents")
        _model_settings(api)
        st.divider()
        _folder_section(api)
        st.divider()
        _upload_section(api)
        st.divider()
        # Rendered after the indexing buttons, so it already shows the new files.
        _status(api)
        if st.button("🗑️ Clear knowledge base", width="stretch"):
            api.reset()
            state.clear_chat()
            st.rerun()
