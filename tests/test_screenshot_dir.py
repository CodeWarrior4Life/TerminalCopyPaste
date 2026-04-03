import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from src.screenshot_dir import get_screenshot_dir
from src.config import TCPConfig


class TestGetScreenshotDir:
    def test_returns_config_override_when_set(self):
        config = TCPConfig(save_dir="C:/MyScreenshots")
        result = get_screenshot_dir(config)
        assert result == "C:/MyScreenshots"

    def test_config_override_expands_user(self):
        config = TCPConfig(save_dir="~/screenshots")
        result = get_screenshot_dir(config)
        assert "~" not in result
        assert result.endswith("screenshots")

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_reads_registry(self):
        config = TCPConfig(save_dir="")
        result = get_screenshot_dir(config)
        assert os.path.isabs(result)

    def test_fallback_when_registry_fails(self):
        config = TCPConfig(save_dir="")
        with patch("src.screenshot_dir._windows_screenshot_dir", side_effect=OSError):
            with patch("sys.platform", "win32"):
                result = get_screenshot_dir(config)
                assert "Screenshots" in result or "Pictures" in result
