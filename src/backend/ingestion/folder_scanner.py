"""Find all supported files in a folder on the local computer."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

logger = logging.getLogger(__name__)


def _is_hidden(path: Path, root: Path) -> bool:
    """True for hidden files/folders (`.git`, `.DS_Store`) and Office lock files (`~$x.docx`)."""
    return any(part.startswith((".", "~$")) for part in path.relative_to(root).parts)


def scan_folder(folder: Path, extensions: Iterable[str]) -> list[Path]:
    """Return all files below `folder` (recursive) with a supported extension, sorted.

    Raises:
        FileNotFoundError: the folder does not exist.
        NotADirectoryError: the path is a file, not a folder.
    """
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder}")

    allowed = {extension.lower() for extension in extensions}
    files = sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in allowed and not _is_hidden(path, folder)
    )
    logger.info("Found %d supported file(s) in %s", len(files), folder)
    return files
