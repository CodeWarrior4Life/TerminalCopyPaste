import sys
import pytest
from unittest.mock import patch, MagicMock
from src.clipboard import has_image_in_clipboard, get_clipboard_image


class TestHasImageInClipboard:
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_returns_bool(self):
        result = has_image_in_clipboard()
        assert isinstance(result, bool)

    def test_returns_false_when_clipboard_empty(self):
        with patch("src.clipboard._win32_has_image", return_value=False):
            with patch("sys.platform", "win32"):
                assert has_image_in_clipboard() is False

    def test_returns_true_when_image_present(self):
        with patch("src.clipboard._win32_has_image", return_value=True):
            with patch("sys.platform", "win32"):
                assert has_image_in_clipboard() is True


class TestGetClipboardImage:
    def test_returns_none_when_no_image(self):
        with patch("src.clipboard._win32_get_image", return_value=None):
            with patch("sys.platform", "win32"):
                assert get_clipboard_image() is None

    def test_returns_pil_image_when_present(self):
        from PIL import Image

        fake_img = Image.new("RGB", (100, 100), "red")
        with patch("src.clipboard._win32_get_image", return_value=fake_img):
            with patch("sys.platform", "win32"):
                result = get_clipboard_image()
                assert result is not None
                assert result.size == (100, 100)
