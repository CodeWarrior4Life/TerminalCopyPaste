import os
import tempfile
from pathlib import Path
from src.file_resolver import get_tcp_temp_dir, save_clipboard_blob


class TestGetTcpTempDir:
    def test_returns_path_under_system_temp(self):
        d = get_tcp_temp_dir()
        assert d.startswith(tempfile.gettempdir())
        assert d.rstrip("/\\").endswith("tcp")

    def test_creates_dir_if_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        d = get_tcp_temp_dir()
        assert Path(d).is_dir()


class TestSaveClipboardBlob:
    def test_writes_bytes_with_original_name(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        path = save_clipboard_blob("report.pdf", b"%PDF-1.4 fake")
        assert Path(path).name == "report.pdf"
        assert Path(path).read_bytes() == b"%PDF-1.4 fake"

    def test_collision_appends_timestamp_suffix(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        first = save_clipboard_blob("report.pdf", b"A")
        second = save_clipboard_blob("report.pdf", b"B")
        assert first != second
        assert Path(second).name.startswith("report_")
        assert Path(second).name.endswith(".pdf")
        assert Path(first).read_bytes() == b"A"
        assert Path(second).read_bytes() == b"B"

    def test_handles_name_without_extension(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        path = save_clipboard_blob("noext", b"data")
        assert Path(path).name == "noext"
