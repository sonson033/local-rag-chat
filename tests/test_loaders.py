import io

import pytest
from docx import Document as DocxFile

from backend.domain.errors import DocumentLoadError, UnsupportedFileError
from backend.ingestion.loaders import default_registry
from scripts.make_sample_pdf import build_pdf


@pytest.fixture
def registry():
    return default_registry()


def test_supported_extensions(registry):
    assert registry.supported_extensions == (".csv", ".docx", ".md", ".pdf", ".txt")
    assert registry.is_supported("Report.PDF")
    assert not registry.is_supported("image.png")


@pytest.mark.parametrize("name", ["notes.md", "notes.txt", "data.csv"])
def test_text_formats(registry, name):
    docs = registry.load(b"Hello world\nsecond line", name)
    assert docs[0].text.startswith("Hello world")
    assert docs[0].source == name
    assert docs[0].page is None


def test_text_with_non_utf8_encoding(registry):
    docs = registry.load("Größe".encode("cp1252"), "umlaut.txt")
    assert docs[0].text == "Größe"


def test_pdf_is_loaded_page_by_page(registry):
    data = build_pdf([["First page text"], ["Second page text"]])
    docs = registry.load(data, "file.pdf")
    assert [d.page for d in docs] == [1, 2]
    assert "Second page" in docs[1].text


def test_pdf_without_text_fails_clearly(registry):
    data = build_pdf([[]])
    with pytest.raises(DocumentLoadError, match="OCR"):
        registry.load(data, "scan.pdf")


def test_broken_pdf_fails_clearly(registry):
    with pytest.raises(DocumentLoadError):
        registry.load(b"not a pdf", "broken.pdf")


def test_docx_paragraphs_and_tables(registry):
    docx = DocxFile()
    docx.add_paragraph("Paragraph text")
    table = docx.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Key"
    table.cell(0, 1).text = "Value"
    buffer = io.BytesIO()
    docx.save(buffer)

    docs = registry.load(buffer.getvalue(), "file.docx")
    assert "Paragraph text" in docs[0].text
    assert "Key | Value" in docs[0].text


def test_unsupported_extension(registry):
    with pytest.raises(UnsupportedFileError):
        registry.load(b"...", "image.png")
