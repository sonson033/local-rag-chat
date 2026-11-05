"""File loaders: bytes in, `Document`s out.

All loaders work on bytes (not paths), so browser uploads and files from disk
go through exactly the same code path.
"""

from __future__ import annotations

import io
import logging
from collections.abc import Iterable
from pathlib import PurePath

from docx import Document as DocxFile
from pypdf import PdfReader

from backend.domain.errors import DocumentLoadError, UnsupportedFileError
from backend.domain.models import Document
from backend.ports import DocumentLoader

logger = logging.getLogger(__name__)


class PdfLoader:
    """Extracts text page by page, so answers can cite `page N`."""

    extensions = (".pdf",)

    def load(self, data: bytes, source: str) -> list[Document]:
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:  # pypdf raises many different exception types
            raise DocumentLoadError(f"Could not read PDF: {exc}") from exc

        documents = [
            Document(text=text, source=source, page=number)
            for number, text in enumerate(pages, start=1)
            if text.strip()
        ]
        if not documents:
            raise DocumentLoadError(
                "No text found in PDF. It is probably a scanned image and needs OCR."
            )
        return documents


class DocxLoader:
    """Reads paragraphs and table cells from Word files (.docx has no fixed pages)."""

    extensions = (".docx",)

    def load(self, data: bytes, source: str) -> list[Document]:
        try:
            docx = DocxFile(io.BytesIO(data))
        except Exception as exc:
            raise DocumentLoadError(f"Could not read DOCX: {exc}") from exc

        lines = [p.text for p in docx.paragraphs if p.text.strip()]
        for table in docx.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    lines.append(" | ".join(cells))
        return [Document(text="\n".join(lines), source=source)]


class TextLoader:
    """Plain text formats: Markdown, TXT and CSV are read as they are."""

    extensions = (".md", ".txt", ".csv")
    _encodings = ("utf-8-sig", "cp1252", "latin-1")

    def load(self, data: bytes, source: str) -> list[Document]:
        for encoding in self._encodings:
            try:
                return [Document(text=data.decode(encoding), source=source)]
            except UnicodeDecodeError:
                continue
        # latin-1 can decode any byte sequence, so this is unreachable in practice.
        raise DocumentLoadError("Could not decode text file.")


class LoaderRegistry:
    """Picks the right loader based on the file extension (Open/Closed: add loaders, don't edit)."""

    def __init__(self, loaders: Iterable[DocumentLoader]) -> None:
        self._by_extension: dict[str, DocumentLoader] = {}
        for loader in loaders:
            for extension in loader.extensions:
                self._by_extension[extension.lower()] = loader

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_extension))

    def is_supported(self, file_name: str) -> bool:
        return PurePath(file_name).suffix.lower() in self._by_extension

    def load(self, data: bytes, source: str) -> list[Document]:
        """Load a file with the loader that matches its extension."""
        extension = PurePath(source).suffix.lower()
        loader = self._by_extension.get(extension)
        if loader is None:
            raise UnsupportedFileError(
                f"Unsupported file type '{extension or '(none)'}'. "
                f"Supported: {', '.join(self.supported_extensions)}"
            )
        documents = loader.load(data, source)
        logger.debug("Loaded %s: %d document(s)", source, len(documents))
        return documents


def default_registry() -> LoaderRegistry:
    """The registry with all built-in loaders."""
    return LoaderRegistry([PdfLoader(), DocxLoader(), TextLoader()])
