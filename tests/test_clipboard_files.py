import sys
from unittest.mock import patch
from src.clipboard import has_files_in_clipboard, get_clipboard_files


class TestHasFilesInClipboard:
    def test_returns_false_on_macos(self):
        with patch("sys.platform", "darwin"):
            assert has_files_in_clipboard() is False

    def test_returns_false_on_linux(self):
        with patch("sys.platform", "linux"):
            assert has_files_in_clipboard() is False

    def test_returns_true_when_win32_helper_says_so(self):
        with patch("src.clipboard._win32_has_files", return_value=True):
            with patch("sys.platform", "win32"):
                assert has_files_in_clipboard() is True

    def test_returns_false_when_win32_helper_says_no(self):
        with patch("src.clipboard._win32_has_files", return_value=False):
            with patch("sys.platform", "win32"):
                assert has_files_in_clipboard() is False


class TestGetClipboardFiles:
    def test_returns_none_on_macos(self):
        with patch("sys.platform", "darwin"):
            assert get_clipboard_files() is None

    def test_returns_none_on_linux(self):
        with patch("sys.platform", "linux"):
            assert get_clipboard_files() is None

    def test_returns_hdrop_paths_when_present(self):
        fake = [r"C:\Users\me\a.pdf", r"C:\Users\me\b.txt"]
        with patch("src.clipboard._win32_get_hdrop_paths", return_value=fake):
            with patch("src.clipboard._win32_get_virtual_files", return_value=None):
                with patch("sys.platform", "win32"):
                    assert get_clipboard_files() == fake

    def test_falls_back_to_virtual_files_when_no_hdrop(self):
        fake = [r"C:\Temp\tcp\report.pdf"]
        with patch("src.clipboard._win32_get_hdrop_paths", return_value=None):
            with patch("src.clipboard._win32_get_virtual_files", return_value=fake):
                with patch("sys.platform", "win32"):
                    assert get_clipboard_files() == fake

    def test_returns_none_when_neither_present(self):
        with patch("src.clipboard._win32_get_hdrop_paths", return_value=None):
            with patch("src.clipboard._win32_get_virtual_files", return_value=None):
                with patch("sys.platform", "win32"):
                    assert get_clipboard_files() is None


import struct
from unittest.mock import patch, MagicMock


def _make_filegroupdescriptorw(filenames: list[str]) -> bytes:
    """Build a minimal FILEGROUPDESCRIPTORW blob: UINT cItems, then
    FILEDESCRIPTORW[cItems] where cFileName is a 260-wchar array at offset 72."""
    descriptor_size = 592
    body = b""
    for name in filenames:
        rec = bytearray(descriptor_size)
        wname = name.encode("utf-16-le")[: 259 * 2]
        rec[72 : 72 + len(wname)] = wname
        body += bytes(rec)
    return struct.pack("<I", len(filenames)) + body


class TestVirtualFileExtraction:
    def test_single_pdf_extracted_to_temp(self, monkeypatch, tmp_path):
        import tempfile as _t

        monkeypatch.setattr(_t, "gettempdir", lambda: str(tmp_path))

        descriptor = _make_filegroupdescriptorw(["report.pdf"])
        contents = b"%PDF-1.4 fake body"

        fake_clip = MagicMock()
        fake_clip.OpenClipboard = MagicMock()
        fake_clip.CloseClipboard = MagicMock()
        fake_clip.RegisterClipboardFormat = MagicMock(
            side_effect=lambda name: {
                "FileGroupDescriptorW": 49159,
                "FileContents": 49158,
            }[name]
        )
        fake_clip.IsClipboardFormatAvailable = MagicMock(return_value=True)
        fake_clip.GetClipboardData = MagicMock(
            side_effect=lambda fmt: descriptor if fmt == 49159 else contents
        )

        with patch.dict("sys.modules", {"win32clipboard": fake_clip}):
            from src.clipboard import _win32_get_virtual_files

            paths = _win32_get_virtual_files()

        assert paths is not None
        assert len(paths) == 1
        from pathlib import Path

        assert Path(paths[0]).name == "report.pdf"
        assert Path(paths[0]).read_bytes() == contents

    def test_returns_none_when_descriptor_missing(self):
        fake_clip = MagicMock()
        fake_clip.OpenClipboard = MagicMock()
        fake_clip.CloseClipboard = MagicMock()
        fake_clip.RegisterClipboardFormat = MagicMock(return_value=49159)
        fake_clip.IsClipboardFormatAvailable = MagicMock(return_value=False)

        with patch.dict("sys.modules", {"win32clipboard": fake_clip}):
            from src.clipboard import _win32_get_virtual_files

            assert _win32_get_virtual_files() is None

    def test_exception_returns_none(self):
        fake_clip = MagicMock()
        fake_clip.OpenClipboard = MagicMock(side_effect=RuntimeError("boom"))
        fake_clip.CloseClipboard = MagicMock()
        fake_clip.RegisterClipboardFormat = MagicMock(return_value=49159)

        with patch.dict("sys.modules", {"win32clipboard": fake_clip}):
            from src.clipboard import _win32_get_virtual_files

            assert _win32_get_virtual_files() is None
