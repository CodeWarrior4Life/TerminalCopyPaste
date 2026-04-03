"""Find or save clipboard images on disk."""

import os
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

from src.config import TCPConfig

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def find_recent_screenshot(screenshot_dir: str, recency_window: int = 5) -> str | None:
    dir_path = Path(screenshot_dir)
    if not dir_path.exists():
        return None

    now = time.time()
    candidates = []

    for f in dir_path.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        mtime = f.stat().st_mtime
        if now - mtime <= recency_window:
            candidates.append((mtime, str(f)))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def save_clipboard_image(
    image: Image.Image, screenshot_dir: str, config: TCPConfig
) -> str:
    dir_path = Path(screenshot_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(config.filename_pattern)
    # Ensure correct extension matches format
    if config.format == "jpg" and not timestamp.endswith((".jpg", ".jpeg")):
        timestamp = timestamp.rsplit(".", 1)[0] + ".jpg"
    elif config.format == "png" and not timestamp.endswith(".png"):
        timestamp = timestamp.rsplit(".", 1)[0] + ".png"

    save_path = str(dir_path / timestamp)

    if config.format == "jpg":
        image = image.convert("RGB")  # JPEG doesn't support alpha
        image.save(save_path, "JPEG", quality=95)
    else:
        image.save(save_path, "PNG")

    return save_path
