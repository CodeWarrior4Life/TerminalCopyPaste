import sys
import pytest
from src.path_format import format_path
from src.config import TCPConfig


class TestFormatPath:
    def test_native_on_windows_uses_backslash(self):
        config = TCPConfig(path_style="native")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sys, "platform", "win32")
            result = format_path("C:/Users/test/image.png", config)
            assert result == "C:\\Users\\test\\image.png"

    def test_native_on_unix_uses_forward_slash(self):
        config = TCPConfig(path_style="native")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sys, "platform", "linux")
            result = format_path("/home/test/image.png", config)
            assert result == "/home/test/image.png"

    def test_forward_style_forces_forward_slashes(self):
        config = TCPConfig(path_style="forward")
        result = format_path("C:\\Users\\test\\image.png", config)
        assert result == "C:/Users/test/image.png"

    def test_backslash_style_forces_backslashes(self):
        config = TCPConfig(path_style="backslash")
        result = format_path("C:/Users/test/image.png", config)
        assert result == "C:\\Users\\test\\image.png"

    def test_quotes_path_with_spaces(self):
        config = TCPConfig(path_style="native")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sys, "platform", "win32")
            result = format_path("C:/My Drive/Projects/image.png", config)
            assert result.startswith('"')
            assert result.endswith('"')

    def test_no_quotes_without_spaces(self):
        config = TCPConfig(path_style="native")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sys, "platform", "win32")
            result = format_path("C:/Users/test/image.png", config)
            assert not result.startswith('"')
