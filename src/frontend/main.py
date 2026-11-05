"""Page layout: config, health check, sidebar and tabs."""

from __future__ import annotations

import logging

import streamlit as st

from backend.api import BackendAPI, build_backend
from frontend import state
from frontend.components.chat import render_chat
from frontend.components.how_it_works import render_how_it_works
from frontend.components.sidebar import render_sidebar


@st.cache_resource(show_spinner="Starting backend…")
def get_api() -> BackendAPI:
    """Create the backend exactly once per server process (not on every rerun)."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    return build_backend()


def _check_health(api: BackendAPI) -> None:
    """Stop with a clear message if Ollama is down; warn if a model is missing."""
    health = api.health()
    if not health.ollama_running:
        st.error(
            f"Ollama is not reachable at {api.settings.ollama_host}. "
            "Start Ollama with: `ollama serve`"
        )
        st.stop()
    for model in health.missing_models:
        st.warning(f"Model '{model}' is not installed. Run: `ollama pull {model}`")


def main() -> None:
    st.set_page_config(page_title="Local RAG Chat", page_icon="📚", layout="wide")
    api = get_api()
    _check_health(api)
    state.init_state(api.settings)

    render_sidebar(api)
    chat_tab, how_tab = st.tabs(["💬 Chat", "ℹ️ How it works"])
    with chat_tab:
        render_chat(api)
    with how_tab:
        render_how_it_works(api)
