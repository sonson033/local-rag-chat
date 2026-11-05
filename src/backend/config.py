"""Application settings, read once from environment variables / a `.env` file.

Why a frozen dataclass?
- One typed object instead of `os.getenv` calls scattered across the code.
- Frozen = settings cannot change silently at runtime.
- Tests can create their own `Settings(...)` without touching the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# src/backend/config.py -> parents[2] is the project root (where app.py lives).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve(path: str | Path, root: Path) -> Path:
    """Resolve relative paths against the project root, not the current working directory.

    This way `./chroma_db` always means the same folder, no matter where
    `streamlit run` was started from.
    """
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else (root / candidate).resolve()


@dataclass(frozen=True)
class Settings:
    """All tunable values of the application (defaults match `.env.example`)."""

    ollama_host: str = "http://localhost:11434"
    chat_model: str = "llama3.2"
    embed_model: str = "nomic-embed-text"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 4
    db_path: Path = field(default_factory=lambda: PROJECT_ROOT / "chroma_db")
    docs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "documents")
    collection: str = "documents"
    project_root: Path = PROJECT_ROOT
    history_messages: int = 6

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be positive.")
        if not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be >= 0 and smaller than CHUNK_SIZE.")
        if self.top_k <= 0:
            raise ValueError("TOP_K must be positive.")

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> Settings:
        """Build settings from environment variables (after loading `.env` if present)."""
        load_dotenv(env_file or PROJECT_ROOT / ".env")
        return cls(
            ollama_host=os.getenv("OLLAMA_HOST", cls.ollama_host),
            chat_model=os.getenv("CHAT_MODEL", cls.chat_model),
            embed_model=os.getenv("EMBED_MODEL", cls.embed_model),
            chunk_size=int(os.getenv("CHUNK_SIZE", cls.chunk_size)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", cls.chunk_overlap)),
            top_k=int(os.getenv("TOP_K", cls.top_k)),
            db_path=_resolve(os.getenv("DB_PATH", "./chroma_db"), PROJECT_ROOT),
            docs_dir=_resolve(os.getenv("DOCS_DIR", "./data/documents"), PROJECT_ROOT),
            collection=os.getenv("COLLECTION", cls.collection),
        )

    def resolve_path(self, path: str | Path) -> Path:
        """Resolve a user-given path (e.g. from the sidebar) against the project root."""
        return _resolve(path, self.project_root)
