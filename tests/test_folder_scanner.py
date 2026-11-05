import pytest

from backend.ingestion.folder_scanner import scan_folder

EXTENSIONS = (".md", ".txt", ".pdf")


def test_scans_recursively_and_filters(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "sub" / "b.TXT").write_text("b")
    (tmp_path / "image.png").write_bytes(b"x")

    files = scan_folder(tmp_path, EXTENSIONS)
    assert [f.relative_to(tmp_path).as_posix() for f in files] == ["a.md", "sub/b.TXT"]


def test_ignores_hidden_files_and_folders(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "notes.md").write_text("x")
    (tmp_path / ".hidden.md").write_text("x")
    (tmp_path / "~$lock.txt").write_text("x")
    (tmp_path / "visible.md").write_text("x")

    assert [f.name for f in scan_folder(tmp_path, EXTENSIONS)] == ["visible.md"]


def test_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        scan_folder(tmp_path / "nope", EXTENSIONS)


def test_file_instead_of_folder_raises(tmp_path):
    file = tmp_path / "a.md"
    file.write_text("x")
    with pytest.raises(NotADirectoryError):
        scan_folder(file, EXTENSIONS)
