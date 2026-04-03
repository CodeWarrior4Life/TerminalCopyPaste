import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from src.tcp_core import run
from src.config import TCPConfig


class TestRun:
    def test_returns_0_and_path_when_recent_file_found(self, tmp_path):
        # Create a recent screenshot
        img_path = tmp_path / "screenshot.png"
        Image.new("RGB", (100, 100)).save(str(img_path))

        config = TCPConfig(save_dir=str(tmp_path))
        with patch("src.tcp_core.has_image_in_clipboard", return_value=True):
            exit_code, output = run(config=config, data_dir=str(tmp_path))
            assert exit_code == 0
            assert str(tmp_path) in output

    def test_returns_0_and_saves_when_no_recent_file(self, tmp_path):
        config = TCPConfig(save_dir=str(tmp_path))
        fake_img = Image.new("RGB", (100, 100), "red")

        with patch("src.tcp_core.has_image_in_clipboard", return_value=True):
            with patch("src.tcp_core.find_recent_screenshot", return_value=None):
                with patch("src.tcp_core.get_clipboard_image", return_value=fake_img):
                    exit_code, output = run(config=config, data_dir=str(tmp_path))
                    assert exit_code == 0
                    assert output.endswith(".png")
                    assert os.path.exists(output.strip('"'))

    def test_returns_1_when_no_image_in_clipboard(self, tmp_path):
        config = TCPConfig(save_dir=str(tmp_path))
        with patch("src.tcp_core.has_image_in_clipboard", return_value=False):
            exit_code, output = run(config=config, data_dir=str(tmp_path))
            assert exit_code == 1
            assert output == ""

    def test_increments_usage_on_success(self, tmp_path):
        img_path = tmp_path / "screenshot.png"
        Image.new("RGB", (100, 100)).save(str(img_path))

        config = TCPConfig(save_dir=str(tmp_path))
        with patch("src.tcp_core.has_image_in_clipboard", return_value=True):
            run(config=config, data_dir=str(tmp_path))
            # Check usage file was created and incremented
            usage_file = tmp_path / "usage.json"
            assert usage_file.exists()

    def test_returns_2_on_error(self, tmp_path):
        config = TCPConfig(save_dir=str(tmp_path))
        with patch(
            "src.tcp_core.has_image_in_clipboard", side_effect=Exception("boom")
        ):
            exit_code, output = run(config=config, data_dir=str(tmp_path))
            assert exit_code == 2
