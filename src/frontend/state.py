"""All `st.session_state` keys and their initialisation in ONE place.

Streamlit re-runs the whole script on every click. Plain variables are lost on each
rerun; `st.session_state` survives. Keeping all keys here avoids typos and makes the
UI state easy to understand.
"""

from __future__ import annotations

from typing import Any, TypedDict

import streamlit as st

from backend.api import RetrievedChunk, Settings

MESSAGES = "messages"
MODEL = "model"
TOP_K = "top_k"
FOLDER = "folder_path"


class ChatMessage(TypedDict, total=False):
    role: str  # "user" | "assistant"
    content: str
    sources: list[RetrievedChunk]
    meta: str  # e.g. "llama3.2 · 3.4 s"


def init_state(settings: Settings) -> None:
    """Set defaults once per browser session (setdefault never overwrites)."""
    defaults: dict[str, Any] = {
        MESSAGES: [],
        MODEL: settings.chat_model,
        TOP_K: settings.top_k,
        FOLDER: str(settings.docs_dir),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def messages() -> list[ChatMessage]:
    return st.session_state[MESSAGES]


def add_message(message: ChatMessage) -> None:
    st.session_state[MESSAGES].append(message)


def clear_chat() -> None:
    st.session_state[MESSAGES] = []
