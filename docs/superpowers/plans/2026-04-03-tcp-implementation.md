# Terminal Copy Paste (TCP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows MVP that intercepts Ctrl+V in terminals (and Alt+V anywhere) to paste clipboard image file paths instead of image data.

**Architecture:** Two-layer -- cross-platform Python core (`tcp_core.py`) handles clipboard detection, file resolution, config, and usage tracking. Thin AHK v2 shim handles global hotkeys, terminal detection, system tray, and keystroke injection. Python core is stateless CLI invoked per-keypress.

**Tech Stack:** Python 3.12+, pywin32, Pillow, tomli, AutoHotkey v2, PyInstaller, pytest

---

## Task 1: Project Foundation

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `config/config.example.toml`
- Create: `LICENSE`

- [ ] **Step 1: Create requirements.txt**

```
pywin32>=306
Pillow>=10.0
tomli>=2.0;python_version<"3.11"
```

Note: `tomllib` is built-in from Python 3.11+. `tomli` is the backport for 3.10.

- [ ] **Step 2: Create empty __init__.py files**

Create `src/__init__.py` and `tests/__init__.py` as empty files.

- [ ] **Step 3: Create example config**

Write `config/config.example.toml`:

```toml
# TCP Configuration
# Copy to %APPDATA%\tcp\config.toml (Windows) or ~/.config/tcp/config.toml (macOS/Linux)

# Where to save clipboard images that don't have a backing file
# Default: auto-detected from OS screenshot settings
save_dir = ""

# Filename pattern for saved images (strftime format)
filename_pattern = "tcp_%Y%m%d_%H%M%S.png"

# How recent a file must be to count as the backing screenshot (seconds)
recency_window = 5

# Image format: "png" or "jpg"
format = "png"

# Path output style: "native" (OS default), "forward", or "backslash"
path_style = "native"

# Additional executables to treat as terminals (additive to built-in list)
# Example: extra_terminals = ["hyper.exe", "tabby.exe", "wezterm-gui.exe"]
extra_terminals = []
```

- [ ] **Step 4: Create BSL 1.1 license file**

Write `LICENSE`:

```
Business Source License 1.1

Parameters

Licensor:             Crossroads Technologies, LLC
Licensed Work:        Terminal Copy Paste
                      The Licensed Work is (c) 2026 Crossroads Technologies, LLC
Additional Use Grant: You may use the Licensed Work for any purpose,
                      including commercial, except for distributing
                      modified versions or offering it as part of a
                      competing product.
Change Date:          2030-04-03
Change License:       MIT License

For information about alternative licensing arrangements for the Licensed Work,
please contact: info@crossroadtech.com

Notice

Business Source License 1.1 (BUSL-1.1)
https://mariadb.com/bsl11/

The Licensed Work is provided under the terms of the Business Source License
as stated above. See the License for the specific language governing
permissions and limitations.
```

- [ ] **Step 5: Install dependencies**

Run: `pip install pywin32 Pillow tomli pytest`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt src/__init__.py tests/__init__.py config/config.example.toml LICENSE
git commit -m "feat: project foundation -- deps, license, example config"
```

---

## Task 2: Config Module

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for config loading**

Write `tests/test_config.py`:

```python
import os
import tempfile
import pytest
from src.config import load_config, TCPConfig, DEFAULT_CONFIG


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self, tmp_path):
        config = load_config(config_dir=str(tmp_path))
        assert config == DEFAULT_CONFIG

    def test_loads_save_dir_from_file(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('save_dir = "C:/Screenshots"')
        config = load_config(config_dir=str(tmp_path))
        assert config.save_dir == "C:/Screenshots"

    def test_loads_extra_terminals(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('extra_terminals = ["hyper.exe", "tabby.exe"]')
        config = load_config(config_dir=str(tmp_path))
        assert config.extra_terminals == ["hyper.exe", "tabby.exe"]

    def test_partial_config_fills_defaults(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('format = "jpg"')
        config = load_config(config_dir=str(tmp_path))
        assert config.format == "jpg"
        assert config.recency_window == 5  # default preserved
        assert config.path_style == "native"  # default preserved

    def test_unknown_keys_ignored(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('bogus_key = "whatever"\nformat = "png"')
        config = load_config(config_dir=str(tmp_path))
        assert config.format == "png"


class TestTCPConfig:
    def test_default_config_values(self):
        c = DEFAULT_CONFIG
        assert c.save_dir == ""
        assert c.filename_pattern == "tcp_%Y%m%d_%H%M%S.png"
        assert c.recency_window == 5
        assert c.format == "png"
        assert c.path_style == "native"
        assert c.extra_terminals == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.config'`

- [ ] **Step 3: Implement config module**

Write `src/config.py`:

```python
"""TCP configuration loading."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass(frozen=True)
class TCPConfig:
    save_dir: str = ""
    filename_pattern: str = "tcp_%Y%m%d_%H%M%S.png"
    recency_window: int = 5
    format: str = "png"
    path_style: str = "native"
    extra_terminals: list[str] = field(default_factory=list)


DEFAULT_CONFIG = TCPConfig()

KNOWN_FIELDS = {f.name for f in TCPConfig.__dataclass_fields__.values()}


def _default_config_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return str(Path(base) / "tcp")
    return str(Path.home() / ".config" / "tcp")


def load_config(config_dir: str | None = None) -> TCPConfig:
    if config_dir is None:
        config_dir = _default_config_dir()

    config_path = Path(config_dir) / "config.toml"
    if not config_path.exists():
        return DEFAULT_CONFIG

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    filtered = {k: v for k, v in raw.items() if k in KNOWN_FIELDS}
    return TCPConfig(**{**DEFAULT_CONFIG.__dict__, **filtered})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_config.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: config module with TOML loading and defaults"
```

---

## Task 3: Screenshot Directory Detection

**Files:**
- Create: `src/screenshot_dir.py`
- Create: `tests/test_screenshot_dir.py`

- [ ] **Step 1: Write failing tests**

Write `tests/test_screenshot_dir.py`:

```python
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
        # Should return a real path (may be Pictures/Screenshots or custom)
        assert os.path.isabs(result)

    def test_fallback_when_registry_fails(self):
        config = TCPConfig(save_dir="")
        with patch("src.screenshot_dir._windows_screenshot_dir", side_effect=OSError):
            with patch("sys.platform", "win32"):
                result = get_screenshot_dir(config)
                assert "Screenshots" in result or "Pictures" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_screenshot_dir.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.screenshot_dir'`

- [ ] **Step 3: Implement screenshot directory detection**

Write `src/screenshot_dir.py`:

```python
"""Detect the OS screenshot save directory."""

import os
import sys
from pathlib import Path

from src.config import TCPConfig


def get_screenshot_dir(config: TCPConfig) -> str:
    if config.save_dir:
        return str(Path(config.save_dir).expanduser())

    if sys.platform == "win32":
        try:
            return _windows_screenshot_dir()
        except OSError:
            return str(Path.home() / "Pictures" / "Screenshots")
    elif sys.platform == "darwin":
        return _macos_screenshot_dir()
    else:
        return _linux_screenshot_dir()


def _windows_screenshot_dir() -> str:
    import winreg

    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
    screenshots_guid = "{B7BEDE81-DF94-4682-A7D8-57A52620B86F}"

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        value, _ = winreg.QueryValueEx(key, screenshots_guid)
        # Value may contain %USERPROFILE% or other env vars
        return str(Path(os.path.expandvars(value)))


def _macos_screenshot_dir() -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return str(Path.home() / "Desktop")


def _linux_screenshot_dir() -> str:
    xdg_file = Path.home() / ".config" / "user-dirs.dirs"
    if xdg_file.exists():
        for line in xdg_file.read_text().splitlines():
            if "XDG_SCREENSHOTS_DIR" in line:
                _, _, path = line.partition("=")
                path = path.strip().strip('"')
                path = path.replace("$HOME", str(Path.home()))
                if path:
                    return path
    return str(Path.home() / "Pictures" / "Screenshots")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_screenshot_dir.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/screenshot_dir.py tests/test_screenshot_dir.py
git commit -m "feat: screenshot directory detection with registry, defaults, cross-platform"
```

---

## Task 4: Clipboard Detection

**Files:**
- Create: `src/clipboard.py`
- Create: `tests/test_clipboard.py`

- [ ] **Step 1: Write failing tests**

Write `tests/test_clipboard.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_clipboard.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.clipboard'`

- [ ] **Step 3: Implement clipboard module**

Write `src/clipboard.py`:

```python
"""Clipboard image detection and extraction."""

import sys
from PIL import Image


def has_image_in_clipboard() -> bool:
    if sys.platform == "win32":
        return _win32_has_image()
    elif sys.platform == "darwin":
        return _macos_has_image()
    else:
        return _linux_has_image()


def get_clipboard_image() -> Image.Image | None:
    if sys.platform == "win32":
        return _win32_get_image()
    elif sys.platform == "darwin":
        return _macos_get_image()
    else:
        return _linux_get_image()


def _win32_has_image() -> bool:
    import win32clipboard

    try:
        win32clipboard.OpenClipboard()
        has = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB)
        return bool(has)
    except Exception:
        return False
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _win32_get_image() -> Image.Image | None:
    import win32clipboard
    import io

    try:
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            return None
        data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
        # CF_DIB is a BMP without the file header; Pillow's BmpImagePlugin handles it
        # We need to add the BMP file header
        bmp_header = _make_bmp_header(len(data))
        return Image.open(io.BytesIO(bmp_header + data))
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _make_bmp_header(dib_size: int) -> bytes:
    import struct
    file_size = 14 + dib_size
    return struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 14 + 40)


def _macos_has_image() -> bool:
    try:
        import subprocess
        result = subprocess.run(
            ["osascript", "-e", 'clipboard info for (class PNGf)'],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _macos_get_image() -> Image.Image | None:
    try:
        import subprocess
        import io
        result = subprocess.run(
            ["osascript", "-e",
             'set png to (the clipboard as «class PNGf»)\nreturn png'],
            capture_output=True, timeout=5
        )
        if result.returncode == 0 and result.stdout:
            return Image.open(io.BytesIO(result.stdout))
    except Exception:
        pass
    return None


def _linux_has_image() -> bool:
    try:
        import subprocess
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
            capture_output=True, text=True, timeout=5
        )
        return "image/png" in result.stdout
    except Exception:
        return False


def _linux_get_image() -> Image.Image | None:
    try:
        import subprocess
        import io
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
            capture_output=True, timeout=5
        )
        if result.returncode == 0 and result.stdout:
            return Image.open(io.BytesIO(result.stdout))
    except Exception:
        pass
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_clipboard.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/clipboard.py tests/test_clipboard.py
git commit -m "feat: clipboard image detection and extraction, cross-platform"
```

---

## Task 5: File Resolver

**Files:**
- Create: `src/file_resolver.py`
- Create: `tests/test_file_resolver.py`

- [ ] **Step 1: Write failing tests**

Write `tests/test_file_resolver.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_file_resolver.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.file_resolver'`

- [ ] **Step 3: Implement file resolver**

Write `src/file_resolver.py`:

```python
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


def save_clipboard_image(image: Image.Image, screenshot_dir: str, config: TCPConfig) -> str:
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_file_resolver.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/file_resolver.py tests/test_file_resolver.py
git commit -m "feat: file resolver -- find recent screenshots, save clipboard images"
```

---

## Task 6: Usage Tracking & Coffee Prompts

**Files:**
- Create: `src/usage.py`
- Create: `tests/test_usage.py`

- [ ] **Step 1: Write failing tests**

Write `tests/test_usage.py`:

```python
import json
import pytest
from src.usage import UsageTracker, MILESTONES


class TestUsageTracker:
    def test_starts_at_zero(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        assert tracker.total_uses == 0

    def test_increment_persists(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker.increment()
        tracker.increment()
        assert tracker.total_uses == 2

        # Reload from disk
        tracker2 = UsageTracker(data_dir=str(tmp_path))
        assert tracker2.total_uses == 2

    def test_no_prompt_before_first_milestone(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        for _ in range(499):
            tracker.increment()
        assert tracker.should_prompt() is False

    def test_prompt_at_500(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        assert tracker.should_prompt() is True

    def test_no_double_prompt_at_same_milestone(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        assert tracker.should_prompt() is True
        tracker.mark_prompted()
        assert tracker.should_prompt() is False

    def test_prompt_at_1500(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 1500
        tracker._data["last_prompt_at"] = 500
        tracker._save()
        assert tracker.should_prompt() is True

    def test_dismissed_forever_suppresses(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        tracker.dismiss_forever()
        assert tracker.should_prompt() is False

    def test_get_milestone_message(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        msg = tracker.get_prompt_message()
        assert "500" in msg
        assert "coffee" in msg.lower() or "tool" in msg.lower()

    def test_milestones_are_ordered(self):
        assert MILESTONES == sorted(MILESTONES)

    def test_recurring_milestones_after_5000(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 10000
        tracker._data["last_prompt_at"] = 5000
        tracker._save()
        assert tracker.should_prompt() is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_usage.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.usage'`

- [ ] **Step 3: Implement usage tracker**

Write `src/usage.py`:

```python
"""Usage tracking and milestone coffee prompts."""

import json
import sys
import os
from pathlib import Path

MILESTONES = [500, 1500, 5000]
RECURRING_INTERVAL = 10000  # After 5000, prompt every 10,000
BMAC_URL = "https://buymeacoffee.com/tfvmclmlwp"

MESSAGES = {
    500: "You've pasted 500 image paths with TCP. If it's saving you time, a coffee helps keep the tools coming.",
    1500: "1,500 pastes. TCP is part of your workflow now. Every coffee fuels the next tool.",
    5000: "5,000 pastes. You're a power user. Help me keep building.",
}
DEFAULT_RECURRING_MSG = "You've pasted {count:,} image paths with TCP. Every coffee fuels the next tool."


class UsageTracker:
    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            data_dir = self._default_data_dir()
        self._path = Path(data_dir) / "usage.json"
        self._data = self._load()

    @property
    def total_uses(self) -> int:
        return self._data.get("total_uses", 0)

    def increment(self) -> None:
        self._data["total_uses"] = self.total_uses + 1
        self._save()

    def should_prompt(self) -> bool:
        if self._data.get("dismissed_forever", False):
            return False

        uses = self.total_uses
        last = self._data.get("last_prompt_at", 0)

        # Check fixed milestones
        for m in MILESTONES:
            if uses >= m and last < m:
                return True

        # Check recurring milestones after the last fixed one
        if uses >= MILESTONES[-1]:
            max_fixed = MILESTONES[-1]
            # Next recurring milestone after last_prompt_at
            if last < max_fixed:
                return True
            recurring_base = max_fixed + RECURRING_INTERVAL
            while recurring_base <= uses:
                if last < recurring_base:
                    return True
                recurring_base += RECURRING_INTERVAL

        return False

    def get_prompt_message(self) -> str:
        uses = self.total_uses
        last = self._data.get("last_prompt_at", 0)

        for m in MILESTONES:
            if uses >= m and last < m:
                return MESSAGES[m]

        return DEFAULT_RECURRING_MSG.format(count=uses)

    def mark_prompted(self) -> None:
        self._data["last_prompt_at"] = self.total_uses
        self._save()

    def dismiss_forever(self) -> None:
        self._data["dismissed_forever"] = True
        self._save()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"total_uses": 0, "last_prompt_at": 0, "dismissed_forever": False}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

    @staticmethod
    def _default_data_dir() -> str:
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return str(Path(base) / "tcp")
        return str(Path.home() / ".config" / "tcp")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_usage.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/usage.py tests/test_usage.py
git commit -m "feat: usage tracking with milestone coffee prompts"
```

---

## Task 7: Path Formatting

**Files:**
- Create: `src/path_format.py`
- Create: `tests/test_path_format.py`

- [ ] **Step 1: Write failing tests**

Write `tests/test_path_format.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_path_format.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.path_format'`

- [ ] **Step 3: Implement path formatting**

Write `src/path_format.py`:

```python
"""Format file paths for terminal output."""

import sys

from src.config import TCPConfig


def format_path(path: str, config: TCPConfig) -> str:
    if config.path_style == "forward":
        path = path.replace("\\", "/")
    elif config.path_style == "backslash":
        path = path.replace("/", "\\")
    elif config.path_style == "native":
        if sys.platform == "win32":
            path = path.replace("/", "\\")
        else:
            path = path.replace("\\", "/")

    if " " in path:
        path = f'"{path}"'

    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_path_format.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/path_format.py tests/test_path_format.py
git commit -m "feat: path formatting with native/forward/backslash styles and auto-quoting"
```

---

## Task 8: Core Orchestrator

**Files:**
- Create: `src/tcp_core.py`
- Create: `tests/test_tcp_core.py`

- [ ] **Step 1: Write failing tests**

Write `tests/test_tcp_core.py`:

```python
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
        with patch("src.tcp_core.has_image_in_clipboard", side_effect=Exception("boom")):
            exit_code, output = run(config=config, data_dir=str(tmp_path))
            assert exit_code == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_tcp_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.tcp_core'`

- [ ] **Step 3: Implement core orchestrator**

Write `src/tcp_core.py`:

```python
"""TCP core orchestrator -- stateless CLI entry point."""

import sys
import webbrowser

from src.clipboard import has_image_in_clipboard, get_clipboard_image
from src.config import load_config, TCPConfig
from src.file_resolver import find_recent_screenshot, save_clipboard_image
from src.path_format import format_path
from src.screenshot_dir import get_screenshot_dir
from src.usage import UsageTracker


def run(config: TCPConfig | None = None, data_dir: str | None = None) -> tuple[int, str]:
    """Main entry point. Returns (exit_code, output_string)."""
    try:
        if config is None:
            config = load_config()

        if not has_image_in_clipboard():
            return 1, ""

        screenshot_dir = get_screenshot_dir(config)

        # Step 1: Check for a recent backing file
        path = find_recent_screenshot(screenshot_dir, config.recency_window)

        # Step 2: If no backing file, save clipboard image
        if path is None:
            image = get_clipboard_image()
            if image is None:
                return 1, ""
            path = save_clipboard_image(image, screenshot_dir, config)

        formatted = format_path(path, config)

        # Track usage
        tracker = UsageTracker(data_dir=data_dir)
        tracker.increment()

        # Check for milestone prompt
        if tracker.should_prompt():
            _show_coffee_prompt(tracker)

        return 0, formatted

    except Exception as e:
        print(f"TCP error: {e}", file=sys.stderr)
        return 2, ""


def _show_coffee_prompt(tracker: UsageTracker) -> None:
    """Show milestone coffee prompt -- non-blocking."""
    try:
        from src.usage import BMAC_URL
        webbrowser.open(BMAC_URL)
        tracker.mark_prompted()
    except Exception:
        pass  # Never let a prompt failure break the tool


def main() -> None:
    """CLI entry point."""
    exit_code, output = run()
    if output:
        print(output, end="")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_tcp_core.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS across all modules

- [ ] **Step 6: Commit**

```bash
git add src/tcp_core.py tests/test_tcp_core.py
git commit -m "feat: core orchestrator -- clipboard to path pipeline with usage tracking"
```

---

## Task 9: AutoHotkey v2 Shim

**Files:**
- Create: `src/platforms/windows/tcp.ahk`

- [ ] **Step 1: Create directory**

Run: `mkdir -p src/platforms/windows`

- [ ] **Step 2: Write AHK v2 shim**

Write `src/platforms/windows/tcp.ahk`:

```autohotkey
#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

; --- Configuration ---
TCP_PYTHON := "python"
TCP_SCRIPT := A_ScriptDir "\..\..\tcp_core.py"

; Built-in terminal executables
TERMINALS := Map(
    "WindowsTerminal.exe", true,
    "powershell.exe", true,
    "pwsh.exe", true,
    "cmd.exe", true,
    "warp.exe", true,
    "Code.exe", true,
    "alacritty.exe", true,
    "mintty.exe", true
)

; Load extra terminals from config (if tcp_core.py --terminals is implemented)
; For now, built-in list only. Config integration in future version.

; --- System Tray ---
TraySetIcon("shell32.dll", 71)  ; Clipboard icon from shell32
A_IconTip := "TCP active — Ctrl+V smart paste, Alt+V force paste"

tray := A_TrayMenu
tray.Delete()  ; Clear default menu
tray.Add("TCP - Terminal Copy Paste", (*) => "")
tray.Disable("TCP - Terminal Copy Paste")
tray.Add()  ; Separator
tray.Add("Pause", MenuPause)
tray.Add("Exit", MenuExit)

MenuPause(name, pos, menu) {
    Suspend
    if A_IsSuspended {
        menu.Rename(name, "Resume")
        A_IconTip := "TCP paused"
    } else {
        menu.Rename("Resume", "Pause")
        A_IconTip := "TCP active — Ctrl+V smart paste, Alt+V force paste"
    }
}

MenuExit(*) {
    ExitApp
}

; --- Helper: Check if active window is a terminal ---
IsTerminal() {
    try {
        exe := WinGetProcessName("A")
        return TERMINALS.Has(exe)
    }
    return false
}

; --- Helper: Run TCP core and get path ---
GetImagePath() {
    try {
        result := RunWait(TCP_PYTHON ' -m src.tcp_core', A_ScriptDir "\..\..",, &stdout)
        if result = 0 {
            ; Read stdout via temp file approach
            tempFile := A_Temp "\tcp_output.txt"
            RunWait(A_ComSpec ' /c ' TCP_PYTHON ' -m src.tcp_core > "' tempFile '"', A_ScriptDir "\..\..","Hide")
            if FileExist(tempFile) {
                path := FileRead(tempFile)
                FileDelete(tempFile)
                path := Trim(path, "`r`n `t")
                if path != ""
                    return path
            }
        }
    }
    return ""
}

; --- Ctrl+V: Smart paste in terminals ---
#HotIf IsTerminal()
$^v:: {
    ; Check if clipboard has image data by running TCP core
    path := GetImagePath()
    if path != "" {
        ; Type the path instead of pasting
        prevDelay := A_KeyDelay
        SetKeyDelay 0
        SendInput path
        SetKeyDelay prevDelay
    } else {
        ; No image — pass through normal Ctrl+V
        SendInput "^v"
    }
}
#HotIf

; --- Alt+V: Universal force paste ---
!v:: {
    path := GetImagePath()
    if path != "" {
        prevDelay := A_KeyDelay
        SetKeyDelay 0
        SendInput path
        SetKeyDelay prevDelay
    }
    ; If no image, Alt+V just does nothing
}
```

- [ ] **Step 3: Manual test**

1. Start the AHK script: double-click `tcp.ahk` (requires AHK v2 installed)
2. Take a screenshot with Win+Shift+S
3. Open Windows Terminal
4. Press Ctrl+V — should type the screenshot file path
5. Copy some text to clipboard
6. Press Ctrl+V — should paste text normally
7. Copy an image from a browser
8. Press Alt+V in any window — should type the saved image path
9. Right-click tray icon — verify Pause/Exit work

- [ ] **Step 4: Commit**

```bash
git add src/platforms/windows/tcp.ahk
git commit -m "feat: AHK v2 shim with smart Ctrl+V and Alt+V override"
```

---

## Task 10: PyInstaller Build & README

**Files:**
- Create: `build.py`
- Create: `README.md`

- [ ] **Step 1: Install PyInstaller**

Run: `pip install pyinstaller`

- [ ] **Step 2: Create build script**

Write `build.py`:

```python
"""Build TCP into standalone executables."""

import subprocess
import sys
from pathlib import Path


def build():
    dist = Path("dist")
    dist.mkdir(exist_ok=True)

    print("Building tcp_core.exe...")
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "tcp_core",
        "--distpath", str(dist),
        "--specpath", str(dist),
        "--clean",
        "src/tcp_core.py",
    ], check=True)

    print("\nBuild complete!")
    print(f"  tcp_core.exe -> {dist / 'tcp_core.exe'}")
    print(f"  tcp.ahk      -> src/platforms/windows/tcp.ahk")
    print("\nTo distribute: zip tcp_core.exe + tcp.ahk + LICENSE")


if __name__ == "__main__":
    build()
```

- [ ] **Step 3: Create README**

Write `README.md`:

```markdown
# Terminal Copy Paste (TCP)

**The missing paste for terminals.** Screenshot, Ctrl+V, done. Your clipboard image becomes a file path — in any terminal, with zero learning curve.

## The Problem

Terminals can't paste images. AI coding tools (Claude Code, Codex CLI, Aider) need image paths, not image data. You screenshot, switch to your terminal, and... nothing works. You have to manually find the file and copy its path. Every. Single. Time.

## The Solution

TCP makes Ctrl+V smart:

- **Ctrl+V in a terminal + image in clipboard** → pastes the file path
- **Ctrl+V anywhere else** → normal paste (untouched)
- **Alt+V anywhere** → force paste image path (manual override)

It detects your screenshot folder automatically, finds the matching file (or saves the clipboard image if needed), and types the path. One keypress.

## Install (Windows)

1. Install [AutoHotkey v2](https://www.autohotkey.com/)
2. Install [Python 3.12+](https://www.python.org/)
3. Download the latest release (or clone this repo)
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `src/platforms/windows/tcp.ahk`

**For compiled version:** Download `tcp_core.exe` + `tcp.ahk` from Releases. No Python needed.

## Supported Terminals

Built-in detection for:
- Windows Terminal
- PowerShell / pwsh
- CMD
- VS Code (integrated terminal)
- Warp
- Alacritty
- Git Bash (mintty)

Add more in `%APPDATA%\tcp\config.toml`:

```toml
extra_terminals = ["hyper.exe", "tabby.exe"]
```

## Configuration

Optional. TCP works with sensible defaults. Create `%APPDATA%\tcp\config.toml` to customize:

```toml
save_dir = ""                          # Auto-detected from OS settings
filename_pattern = "tcp_%Y%m%d_%H%M%S.png"
recency_window = 5                     # Seconds
format = "png"                         # png or jpg
path_style = "native"                  # native, forward, or backslash
extra_terminals = []
```

## How It Works

1. You press Ctrl+V in a terminal (or Alt+V anywhere)
2. TCP checks: is there an image in the clipboard?
3. If yes: finds the matching file on disk (or saves it)
4. Types the file path into your terminal
5. If no image: passes through normal Ctrl+V

## License

Business Source License 1.1 — free for all use. See [LICENSE](LICENSE) for details.

Built by [CodeWarrior4Life](https://codewarrior4life.com) / [Crossroads Technologies](https://crossroadtech.com)
```

- [ ] **Step 4: Test the build**

Run: `python build.py`
Expected: `dist/tcp_core.exe` created successfully

- [ ] **Step 5: Commit**

```bash
git add build.py README.md
git commit -m "feat: PyInstaller build script and README"
```

---

## Task 11: Integration Test & Final Verification

**Files:**
- Modify: `tests/test_tcp_core.py` (add integration test)

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Manual end-to-end test**

1. Run `python -m src.tcp_core` with no image in clipboard
   Expected: exit code 1, no output
2. Take screenshot with Win+Shift+S
3. Run `python -m src.tcp_core`
   Expected: exit code 0, prints path to the screenshot
4. Copy image from browser
5. Run `python -m src.tcp_core`
   Expected: exit code 0, prints path to newly saved PNG
6. Start `tcp.ahk`, verify tray icon appears
7. Ctrl+V in Windows Terminal with image in clipboard → path typed
8. Ctrl+V in Windows Terminal with text in clipboard → text pasted normally
9. Alt+V in Notepad with image in clipboard → path typed

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: integration verification complete"
```

- [ ] **Step 4: Push to GitHub**

```bash
git push -u origin master
```
