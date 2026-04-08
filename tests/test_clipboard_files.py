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
