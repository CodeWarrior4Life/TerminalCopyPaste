# Any-File Paste Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend TCP so the hotkey pastes filesystem path(s) for ANY non-text clipboard content — Explorer file copies (CF_HDROP) and virtual files from messaging apps (CF_FILEGROUPDESCRIPTORW + CF_FILECONTENTS), not just images.

**Architecture:** Add a new "files" branch to `tcp_core.run()` that runs BEFORE the existing image branch. The image flow is untouched. New clipboard helpers live in `src/clipboard.py`. Blob extraction for virtual files writes to `{tempfile.gettempdir()}/tcp/` via a new helper in `src/file_resolver.py`. Windows-only for v1.1; macOS/Linux return False/None and fall through to existing image handling.

**Tech Stack:** Python 3.10+, `pywin32` (`win32clipboard`, `pythoncom`, `pywintypes`), `tempfile`, existing `pytest` suite.

**Reference spec:** `docs/superpowers/specs/2026-04-08-any-file-paste-design.md`

---

## File Structure

**New files:**
- `tests/test_clipboard_files.py` — tests for the new clipboard file helpers
- `tests/test_file_resolver_blobs.py` — tests for blob save helpers

**Modified files:**
- `src/clipboard.py` — add `has_files_in_clipboard()`, `get_clipboard_files()`, Windows helpers for CF_HDROP + virtual file extraction
- `src/file_resolver.py` — add `get_tcp_temp_dir()`, `save_clipboard_blob()`
- `src/tcp_core.py` — insert new files branch before the image branch
- `tests/test_tcp_core.py` — add priority/regression tests

**Do NOT modify:**
- `src/config.py`, `src/path_format.py`, `src/screenshot_dir.py`, `src/usage.py` — no changes required
- Existing functions in `src/clipboard.py` and `src/file_resolver.py` — only additions

---

## Task 1: Temp dir + blob save helper

**Files:**
- Modify: `src/file_resolver.py` (append to end)
- Test: `tests/test_file_resolver_blobs.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_file_resolver_blobs.py`:

```python
import os
import tempfile
from pathlib import Path
from src.file_resolver import get_tcp_temp_dir, save_clipboard_blob


class TestGetTcpTempDir:
    def test_returns_path_under_system_temp(self):
        d = get_tcp_temp_dir()
        assert d.startswith(tempfile.gettempdir())
        assert d.rstrip("/\\").endswith("tcp")

    def test_creates_dir_if_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        d = get_tcp_temp_dir()
        assert Path(d).is_dir()


class TestSaveClipboardBlob:
    def test_writes_bytes_with_original_name(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        path = save_clipboard_blob("report.pdf", b"%PDF-1.4 fake")
        assert Path(path).name == "report.pdf"
        assert Path(path).read_bytes() == b"%PDF-1.4 fake"

    def test_collision_appends_timestamp_suffix(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        first = save_clipboard_blob("report.pdf", b"A")
        second = save_clipboard_blob("report.pdf", b"B")
        assert first != second
        assert Path(second).name.startswith("report_")
        assert Path(second).name.endswith(".pdf")
        assert Path(first).read_bytes() == b"A"
        assert Path(second).read_bytes() == b"B"

    def test_handles_name_without_extension(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        path = save_clipboard_blob("noext", b"data")
        assert Path(path).name == "noext"
```

- [ ] **Step 2: Run tests — expect FAIL (functions not defined)**

```
python -m pytest tests/test_file_resolver_blobs.py -v
```

Expected: ImportError / AttributeError on `get_tcp_temp_dir`, `save_clipboard_blob`.

- [ ] **Step 3: Implement in `src/file_resolver.py`**

Append to the end of the file:

```python
import tempfile


def get_tcp_temp_dir() -> str:
    """Return the TCP temp dir for extracted clipboard blobs, creating it if missing."""
    d = Path(tempfile.gettempdir()) / "tcp"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def save_clipboard_blob(filename: str, data: bytes) -> str:
    """Write `data` to the TCP temp dir under `filename`. On collision, append a
    timestamp suffix before the extension. Returns the absolute path written."""
    temp_dir = Path(get_tcp_temp_dir())
    target = temp_dir / filename
    if target.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = target.stem
        suffix = target.suffix
        target = temp_dir / f"{stem}_{ts}{suffix}"
    target.write_bytes(data)
    return str(target)
```

Note: `datetime` and `Path` are already imported at the top of `src/file_resolver.py`. Only `tempfile` needs to be added.

- [ ] **Step 4: Run tests — expect PASS**

```
python -m pytest tests/test_file_resolver_blobs.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Run full test suite to confirm no regression**

```
python -m pytest tests/ -v
```

Expected: all existing tests still pass, plus the 5 new ones.

- [ ] **Step 6: Commit**

```
git add src/file_resolver.py tests/test_file_resolver_blobs.py
git commit -m "feat(file_resolver): add temp dir + blob save helpers for v1.1"
```

---

## Task 2: `has_files_in_clipboard` + CF_HDROP read path

**Files:**
- Modify: `src/clipboard.py` (append Windows helpers + cross-platform dispatchers)
- Test: `tests/test_clipboard_files.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_clipboard_files.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```
python -m pytest tests/test_clipboard_files.py -v
```

Expected: ImportError on `has_files_in_clipboard`, `get_clipboard_files`.

- [ ] **Step 3: Implement cross-platform dispatchers + CF_HDROP helper**

Append to `src/clipboard.py`:

```python
def has_files_in_clipboard() -> bool:
    if sys.platform == "win32":
        return _win32_has_files()
    return False


def get_clipboard_files() -> list[str] | None:
    if sys.platform != "win32":
        return None
    paths = _win32_get_hdrop_paths()
    if paths:
        return paths
    return _win32_get_virtual_files()


def _win32_has_files() -> bool:
    import win32clipboard

    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
            return True
        # Virtual file formats are registered by name
        try:
            cf_descriptor = win32clipboard.RegisterClipboardFormat(
                "FileGroupDescriptorW"
            )
            if win32clipboard.IsClipboardFormatAvailable(cf_descriptor):
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _win32_get_hdrop_paths() -> list[str] | None:
    import win32clipboard

    try:
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
            return None
        data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
        # pywin32 returns a tuple of file paths
        paths = [str(p) for p in data]
        return paths if paths else None
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _win32_get_virtual_files() -> list[str] | None:
    # Stub for now; full implementation in Task 3
    return None
```

- [ ] **Step 4: Run tests — expect PASS**

```
python -m pytest tests/test_clipboard_files.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Run full test suite**

```
python -m pytest tests/ -v
```

Expected: no regressions.

- [ ] **Step 6: Commit**

```
git add src/clipboard.py tests/test_clipboard_files.py
git commit -m "feat(clipboard): detect and read CF_HDROP file lists"
```

---

## Task 3: Virtual file extraction (FileGroupDescriptorW + FileContents)

**Files:**
- Modify: `src/clipboard.py` (replace `_win32_get_virtual_files` stub)
- Test: `tests/test_clipboard_files.py` (add tests)

Background: Messaging apps (Telegram, WhatsApp, Outlook) publish attachments via two named clipboard formats. `FileGroupDescriptorW` holds a `FILEGROUPDESCRIPTORW` struct (a count + array of `FILEDESCRIPTORW` records, each with a `cFileName[260]` wide-char filename). `FileContents` holds the file bytes, read with `GetClipboardData` by index — but pywin32 only exposes a single `GetClipboardData` call per format. The reliable route is to parse the descriptor for filenames, then use `GetClipboardData(CF_FILECONTENTS)` which returns the concatenated stream — however pywin32 returns it as a Python `bytes` object for index 0 only, and multi-file support requires IDataObject via `pythoncom`. For v1.1, handle the **single-file case** (the common one for messaging apps) reliably, and document multi-file virtual files as a follow-up.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_clipboard_files.py`:

```python
import struct
from unittest.mock import patch, MagicMock


def _make_filegroupdescriptorw(filenames: list[str]) -> bytes:
    """Build a minimal FILEGROUPDESCRIPTORW blob: UINT cItems, then
    FILEDESCRIPTORW[cItems] where cFileName is a 260-wchar array at offset 72."""
    # FILEDESCRIPTORW is 592 bytes on Windows. Offsets:
    #   0   DWORD dwFlags
    #   4   CLSID clsid (16 bytes)
    #   20  SIZEL sizel (8 bytes)
    #   28  POINTL pointl (8 bytes)
    #   36  DWORD dwFileAttributes
    #   40  FILETIME ftCreationTime (8)
    #   48  FILETIME ftLastAccessTime (8)
    #   56  FILETIME ftLastWriteTime (8)
    #   64  DWORD nFileSizeHigh
    #   68  DWORD nFileSizeLow
    #   72  WCHAR cFileName[260]  -> 520 bytes
    # Total: 72 + 520 = 592
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
            side_effect=lambda name: {"FileGroupDescriptorW": 49159, "FileContents": 49158}[name]
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
```

- [ ] **Step 2: Run tests — expect FAIL (stub returns None)**

```
python -m pytest tests/test_clipboard_files.py::TestVirtualFileExtraction -v
```

Expected: `test_single_pdf_extracted_to_temp` FAILS (stub returns None).

- [ ] **Step 3: Replace the stub in `src/clipboard.py`**

Replace `_win32_get_virtual_files` with the real implementation:

```python
def _win32_get_virtual_files() -> list[str] | None:
    """Extract virtual files from clipboard (FileGroupDescriptorW + FileContents)
    to the TCP temp dir. Handles the single-file case common in messaging apps."""
    import win32clipboard
    import struct
    from src.file_resolver import save_clipboard_blob

    try:
        cf_descriptor = win32clipboard.RegisterClipboardFormat("FileGroupDescriptorW")
        cf_contents = win32clipboard.RegisterClipboardFormat("FileContents")
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(cf_descriptor):
            return None
        descriptor_blob = win32clipboard.GetClipboardData(cf_descriptor)
        if not descriptor_blob:
            return None

        # Parse FILEGROUPDESCRIPTORW: UINT cItems, then FILEDESCRIPTORW[cItems]
        (count,) = struct.unpack_from("<I", descriptor_blob, 0)
        if count < 1:
            return None
        # Each FILEDESCRIPTORW is 592 bytes; cFileName is at offset 72, 260 wchars
        filenames = []
        record_size = 592
        name_offset = 72
        name_byte_len = 260 * 2
        for i in range(count):
            base = 4 + i * record_size
            raw_name = descriptor_blob[base + name_offset : base + name_offset + name_byte_len]
            # Null-terminated UTF-16LE
            name = raw_name.decode("utf-16-le", errors="replace").split("\x00", 1)[0]
            if name:
                filenames.append(name)

        if not filenames:
            return None

        # pywin32's GetClipboardData for FileContents returns the first stream's bytes.
        # Multi-file virtual paste requires IDataObject; defer to v1.2.
        contents = win32clipboard.GetClipboardData(cf_contents)
        if contents is None:
            return None

        saved = save_clipboard_blob(filenames[0], contents)
        return [saved]
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
```

- [ ] **Step 4: Run tests — expect PASS**

```
python -m pytest tests/test_clipboard_files.py -v
```

Expected: all virtual file tests pass.

- [ ] **Step 5: Run full suite**

```
python -m pytest tests/ -v
```

Expected: no regressions.

- [ ] **Step 6: Commit**

```
git add src/clipboard.py tests/test_clipboard_files.py
git commit -m "feat(clipboard): extract virtual files to temp dir (single-file)"
```

---

## Task 4: Wire files branch into `tcp_core.run`

**Files:**
- Modify: `src/tcp_core.py`
- Test: `tests/test_tcp_core.py` (add priority + regression tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_tcp_core.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect FAIL (import errors on new helpers)**

```
python -m pytest tests/test_tcp_core.py::TestFilesBranch -v
```

Expected: FAIL — `has_files_in_clipboard` not imported into `tcp_core`.

- [ ] **Step 3: Modify `src/tcp_core.py`**

Add imports at the top (next to existing clipboard import):

```python
from src.clipboard import (
    has_image_in_clipboard,
    get_clipboard_image,
    has_files_in_clipboard,
    get_clipboard_files,
)
```

Then insert the new files branch inside `run()`, immediately after `config = load_config()` loads and BEFORE `if not has_image_in_clipboard()`:

```python
        # Step 0: Files/virtual files (v1.1). Runs before image path so apps
        # that publish both an image preview AND a file yield the file.
        if has_files_in_clipboard():
            file_paths = get_clipboard_files()
            if file_paths:
                formatted = "\n".join(format_path(p, config) for p in file_paths)
                tracker = UsageTracker(data_dir=data_dir)
                tracker.increment()
                if tracker.should_prompt():
                    _show_coffee_prompt(tracker)
                return 0, formatted
            # get_clipboard_files returned None -> fall through to image path

        if not has_image_in_clipboard():
            return 1, ""
```

Leave the rest of `run()` exactly as-is.

- [ ] **Step 4: Run new tests — expect PASS**

```
python -m pytest tests/test_tcp_core.py::TestFilesBranch -v
```

Expected: 7 passed.

- [ ] **Step 5: Run FULL test suite — no regressions**

```
python -m pytest tests/ -v
```

Expected: all 45 pre-existing tests still pass, plus all new tests (file_resolver blobs + clipboard files + tcp_core files branch).

- [ ] **Step 6: Commit**

```
git add src/tcp_core.py tests/test_tcp_core.py
git commit -m "feat(core): add files branch to run() with image fallback"
```

---

## Task 5: Manual smoke test on Windows + README note

**Files:**
- Modify: `README.md` (add feature note)
- Manual: real clipboard scenarios

- [ ] **Step 1: Manual smoke tests on Windows**

Run these by hand, confirm each works:

1. **Explorer single file:** Open Explorer, right-click a file, Copy. In a terminal with the AHK script loaded, press Alt+B. Expect: file's full path pasted.
2. **Explorer multi-file:** Select 3 files in Explorer, Copy. Press Alt+B. Expect: 3 paths newline-separated.
3. **Telegram PDF:** Right-click a PDF attachment in Telegram Desktop → Copy. Press Alt+B. Expect: path under `%TEMP%\tcp\` (e.g. `C:\Users\...\AppData\Local\Temp\tcp\report.pdf`) pasted, and the file exists on disk.
4. **WhatsApp image:** Copy an image from WhatsApp Desktop. Press Alt+B. Expect: image saved per existing flow (screenshot_dir), not temp — because apps that copy images via CF_DIB don't publish CF_HDROP/virtual files for them.
5. **Screenshot (Snipping Tool):** Take a screenshot, Press Alt+B. Expect: existing behavior, saved to screenshot_dir. (Regression check.)
6. **Plain text:** Copy "hello world". Press Alt+B. Expect: AHK falls through to normal Ctrl+V and "hello world" is pasted. (Regression check.)

If any scenario fails, note it and fix before proceeding.

- [ ] **Step 2: Update README**

Find the feature list in `README.md` and update the tagline to mention any-file support. Minimal change — add one bullet or sentence:

```
- Paste any copied file as a path: Explorer copies paste their existing path(s); attachments from Telegram/WhatsApp/Outlook are extracted to %TEMP%\tcp\ and their path pasted. Multiple files are newline-separated.
```

- [ ] **Step 3: Commit README update**

```
git add README.md
git commit -m "docs: document v1.1 any-file paste support"
```

- [ ] **Step 4: Final full-suite run**

```
python -m pytest tests/ -v
```

Expected: all tests pass.

---

## Self-Review Notes

- **Spec coverage:** All spec sections mapped — Task 1 covers temp dir + blob save; Task 2 covers CF_HDROP + dispatcher; Task 3 covers virtual files; Task 4 covers tcp_core wiring and priority/regression; Task 5 covers manual validation + docs.
- **Image flow untouched:** `get_clipboard_image`, `save_clipboard_image`, `find_recent_screenshot`, and the existing image branch in `run()` are not modified. Task 4 Step 3 explicitly inserts the new branch *before* the existing one and leaves everything else intact.
- **Priority:** Task 4 test `test_files_take_priority_over_image` locks in files-over-image ordering.
- **Multi-file virtual files:** Single-file only for v1.1 (spec allows this; multi-file requires IDataObject via pythoncom — documented as v1.2 follow-up in Task 3 background note).
- **No placeholders:** Every test and every implementation block contains actual code.
