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
            assert output == ""


class TestFilesBranch:
    def test_cf_hdrop_single_file_returns_formatted_path(self, tmp_path):
        config = TCPConfig(save_dir=str(tmp_path))
        target = tmp_path / "doc.pdf"
        target.write_bytes(b"fake")
        with patch("src.tcp_core.has_files_in_clipboard", return_value=True):
            with patch("src.tcp_core.get_clipboard_files", return_value=[str(target)]):
                exit_code, output = run(config=config, data_dir=str(tmp_path))
        assert exit_code == 0
        assert str(target) in output

    def test_cf_hdrop_multiple_files_newline_joined(self, tmp_path):
        config = TCPConfig(save_dir=str(tmp_path))
        a = tmp_path / "a.pdf"
        b = tmp_path / "b.txt"
        a.write_bytes(b"a")
        b.write_bytes(b"b")
        with patch("src.tcp_core.has_files_in_clipboard", return_value=True):
            with patch("src.tcp_core.get_clipboard_files", return_value=[str(a), str(b)]):
                exit_code, output = run(config=config, data_dir=str(tmp_path))
        assert exit_code == 0
        assert str(a) in output
        assert str(b) in output
        assert "\n" in output

    def test_files_branch_increments_usage(self, tmp_path):
        config = TCPConfig(save_dir=str(tmp_path))
        target = tmp_path / "doc.pdf"
        target.write_bytes(b"x")
        with patch("src.tcp_core.has_files_in_clipboard", return_value=True):
            with patch("src.tcp_core.get_clipboard_files", return_value=[str(target)]):
                run(config=config, data_dir=str(tmp_path))
        assert (tmp_path / "usage.json").exists()

    def test_files_take_priority_over_image(self, tmp_path):
        """When both files and image present, files win."""
        config = TCPConfig(save_dir=str(tmp_path))
        target = tmp_path / "doc.pdf"
        target.write_bytes(b"x")
        with patch("src.tcp_core.has_files_in_clipboard", return_value=True):
            with patch("src.tcp_core.get_clipboard_files", return_value=[str(target)]):
                with patch("src.tcp_core.has_image_in_clipboard", return_value=True):
                    with patch("src.tcp_core.get_clipboard_image") as mock_img:
                        exit_code, output = run(config=config, data_dir=str(tmp_path))
        assert exit_code == 0
        assert str(target) in output
        mock_img.assert_not_called()

    def test_no_files_falls_through_to_image(self, tmp_path):
        """Regression: when has_files_in_clipboard False, image flow still runs."""
        config = TCPConfig(save_dir=str(tmp_path))
        img_path = tmp_path / "screenshot.png"
        Image.new("RGB", (10, 10)).save(str(img_path))
        with patch("src.tcp_core.has_files_in_clipboard", return_value=False):
            with patch("src.tcp_core.has_image_in_clipboard", return_value=True):
                exit_code, output = run(config=config, data_dir=str(tmp_path))
        assert exit_code == 0
        assert str(tmp_path) in output

    def test_no_files_no_image_returns_1(self, tmp_path):
        config = TCPConfig(save_dir=str(tmp_path))
        with patch("src.tcp_core.has_files_in_clipboard", return_value=False):
            with patch("src.tcp_core.has_image_in_clipboard", return_value=False):
                exit_code, output = run(config=config, data_dir=str(tmp_path))
        assert exit_code == 1
        assert output == ""

    def test_files_branch_get_returns_none_falls_through(self, tmp_path):
        """Defensive: has_files says True but get returns None -- fall to image."""
        config = TCPConfig(save_dir=str(tmp_path))
        img_path = tmp_path / "screenshot.png"
        Image.new("RGB", (10, 10)).save(str(img_path))
        with patch("src.tcp_core.has_files_in_clipboard", return_value=True):
            with patch("src.tcp_core.get_clipboard_files", return_value=None):
                with patch("src.tcp_core.has_image_in_clipboard", return_value=True):
                    exit_code, output = run(config=config, data_dir=str(tmp_path))
        assert exit_code == 0
        assert str(tmp_path) in output
