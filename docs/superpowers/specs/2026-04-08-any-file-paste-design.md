# TCP v1.1 — Any-File Paste Spec

**Date:** 2026-04-08
**Status:** Approved, ready for planning
**Scope:** Extend TCP to paste paths for ANY non-text clipboard content, not just images.

## Goal

Today TCP only intercepts clipboard images (CF_DIB). Extend it so that when the clipboard holds **files** (Explorer copies) or **virtual files** (PDF pasted from Telegram/WhatsApp, Outlook attachments, etc.), TCP pastes their filesystem path(s) instead of the blob. Text clipboard behavior is unchanged — AHK falls through to normal Ctrl+V.

**Guiding constraint:** Do not break what already works. The image path is a separate code path and must remain untouched in behavior and output.

## Behavior — Priority Order

When the hotkey fires, TCP evaluates in this order and stops at the first match:

1. **Text in clipboard** → TCP exits 1 with no output. AHK falls through to normal Ctrl+V. *(unchanged)*
2. **Files (CF_HDROP)** → paste existing path(s) directly, no saving. Handles both Explorer copies and any app that drops a real temp path into CF_HDROP.
3. **Virtual files (CF_FILEGROUPDESCRIPTORW + CF_FILECONTENTS)** → extract each blob to `{tempfile.gettempdir()}/tcp/`, paste the extracted path(s).
4. **Image (CF_DIB)** → existing flow, unchanged. Save to `screenshot_dir`, paste formatted path.
5. **Nothing usable** → exit 1, no output. *(unchanged)*

Files take priority over images because an app could publish both (image preview + original file) — the file is the higher-fidelity artifact the user actually wants.

## Multi-File Output

When the clipboard holds multiple files, TCP pastes all paths joined by **newlines** (`\n`). Each path is run individually through the existing `format_path()` so quoting, escaping, WSL path conversion, and the configured format style all apply per-path. The join happens after formatting.

## Storage Location for Extracted Blobs

Extracted virtual files go to `{tempfile.gettempdir()}/tcp/`:
- Windows: `%TEMP%\tcp\`
- macOS: `$TMPDIR/tcp/`
- Linux: `/tmp/tcp/`

Directory created lazily on first extraction. Original filename from the FileGroupDescriptor is preserved when available. On name collision, append a timestamp suffix (`report.pdf` → `report_20260408_143022.pdf`).

**Cleanup:** None. OS temp cleanup handles the long tail. Never delete during a TCP run — a path could still be live in the user's terminal.

**Screenshots remain in `screenshot_dir`.** The image flow does not move to temp. This is a separate path.

## Module Changes

### `src/clipboard.py`
Add:
- `has_files_in_clipboard() -> bool` — true if CF_HDROP or (CF_FILEGROUPDESCRIPTORW + CF_FILECONTENTS) present.
- `get_clipboard_files() -> list[str] | None` — returns a list of filesystem paths. First tries CF_HDROP (real paths, no extraction). Falls back to extracting virtual files to `{tempdir}/tcp/` and returning those paths. Returns `None` if no files and no virtual files.

Windows-only for v1.1. macOS and Linux stubs return `False` / `None` — those platforms already handle file paste natively and this is a Windows-specific pain point. Documented as a follow-up for v1.2.

Existing `has_image_in_clipboard()` and `get_clipboard_image()` are untouched.

### `src/file_resolver.py`
Add:
- `get_tcp_temp_dir() -> str` — returns `{tempfile.gettempdir()}/tcp/`, creates it if missing.
- `save_clipboard_blob(filename: str, data: bytes) -> str` — writes bytes to the temp dir under the given filename, handles collision with timestamp suffix, returns the saved path.

Existing `find_recent_screenshot()` and `save_clipboard_image()` are untouched.

### `src/tcp_core.py`
New branch inserted **before** the existing image branch:

```python
# Step 0: Files/virtual files (new)
if has_files_in_clipboard():
    paths = get_clipboard_files()
    if paths:
        formatted = "\n".join(format_path(p, config) for p in paths)
        tracker.increment()
        if tracker.should_prompt():
            _show_coffee_prompt(tracker)
        return 0, formatted

# Step 1-2: Image (unchanged)
if not has_image_in_clipboard():
    return 1, ""
...
```

Usage tracking fires for file pastes the same as image pastes — it's still a TCP action.

### `src/path_format.py`
No changes. Called once per path.

### `src/config.py`
No changes. No new config keys for v1.1 — the temp directory is OS-standard and doesn't need to be user-configurable.

## Tests

New tests in `tests/test_clipboard_files.py` and additions to `tests/test_tcp_core.py`:

**Positive cases:**
- CF_HDROP single file → path pasted as-is through `format_path`
- CF_HDROP multiple files → newline-joined, each formatted individually
- Virtual file with descriptor name → extracted to `{tempdir}/tcp/` with original filename
- Virtual file, name collision → timestamp suffix appended
- Virtual file, multiple blobs → all extracted, all paths returned
- Files branch increments usage tracker

**Regression cases (must not break):**
- Image-only clipboard → existing image flow still runs, saves to `screenshot_dir`, not temp
- Text-only clipboard → exit 1, no output
- Empty clipboard → exit 1, no output
- macOS/Linux → `has_files_in_clipboard()` returns False, falls through to image path

**Priority:**
- Clipboard with both image preview AND file → file path wins

## Out of Scope

- Non-Windows file clipboard support — defer to v1.2
- Cleanup of `{tempdir}/tcp/` — OS handles it
- Clipboard formats with neither a path nor extractable content (raw HTML fragments, custom app formats) — TCP exits 1, AHK falls through
- Configurable temp directory location
- Any changes to the image flow

## Risks

- **Regression in image flow.** Mitigation: the new branch is inserted before and is fully isolated; all existing image tests must pass unchanged.
- **Virtual file extraction on Windows uses COM / IDataObject.** Mitigation: wrap in try/except, return None on any failure so TCP falls through gracefully rather than erroring.
- **File priority could surprise users copying an image from an app that also publishes it as a file.** Mitigation: document in README. This is the correct behavior — the file is the original.
