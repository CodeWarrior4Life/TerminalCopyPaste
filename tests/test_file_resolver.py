import os
import time
import pytest
from PIL import Image
from src.file_resolver import find_recent_screenshot, save_clipboard_image
from src.config import TCPConfig


class TestFindRecentScreenshot:
    def test_finds_recent_file(self, tmp_path):
        img_path = tmp_path / "screenshot.png"
        Image.new("RGB", (100, 100), "blue").save(str(img_path))
        result = find_recent_screenshot(str(tmp_path), recency_window=5)
        assert result == str(img_path)

    def test_returns_none_for_old_file(self, tmp_path):
        img_path = tmp_path / "old_screenshot.png"
        Image.new("RGB", (100, 100), "blue").save(str(img_path))
        # Set mtime to 60 seconds ago
        old_time = time.time() - 60
        os.utime(str(img_path), (old_time, old_time))
        result = find_recent_screenshot(str(tmp_path), recency_window=5)
        assert result is None

    def test_returns_none_for_empty_dir(self, tmp_path):
        result = find_recent_screenshot(str(tmp_path), recency_window=5)
        assert result is None

    def test_ignores_non_image_files(self, tmp_path):
        txt_path = tmp_path / "notes.txt"
        txt_path.write_text("not an image")
        result = find_recent_screenshot(str(tmp_path), recency_window=5)
        assert result is None

    def test_returns_newest_when_multiple(self, tmp_path):
        old_img = tmp_path / "old.png"
        Image.new("RGB", (10, 10), "red").save(str(old_img))
        old_time = time.time() - 2
        os.utime(str(old_img), (old_time, old_time))

        new_img = tmp_path / "new.png"
        Image.new("RGB", (10, 10), "green").save(str(new_img))

        result = find_recent_screenshot(str(tmp_path), recency_window=5)
        assert result == str(new_img)


class TestSaveClipboardImage:
    def test_saves_png(self, tmp_path):
        img = Image.new("RGB", (100, 100), "red")
        config = TCPConfig(format="png")
        path = save_clipboard_image(img, str(tmp_path), config)
        assert path.endswith(".png")
        assert os.path.exists(path)
        saved = Image.open(path)
        assert saved.size == (100, 100)

    def test_saves_jpg(self, tmp_path):
        img = Image.new("RGB", (100, 100), "red")
        config = TCPConfig(format="jpg")
        path = save_clipboard_image(img, str(tmp_path), config)
        assert path.endswith(".jpg")
        assert os.path.exists(path)

    def test_creates_dir_if_missing(self, tmp_path):
        save_dir = str(tmp_path / "subdir" / "screenshots")
        img = Image.new("RGB", (100, 100), "red")
        config = TCPConfig(format="png")
        path = save_clipboard_image(img, save_dir, config)
        assert os.path.exists(path)

    def test_filename_matches_pattern(self, tmp_path):
        img = Image.new("RGB", (100, 100), "red")
        config = TCPConfig(format="png", filename_pattern="tcp_%Y%m%d_%H%M%S.png")
        path = save_clipboard_image(img, str(tmp_path), config)
        filename = os.path.basename(path)
        assert filename.startswith("tcp_")
        assert filename.endswith(".png")
