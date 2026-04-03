# Terminal Copy Paste (TCP) -- Design Specification

**Version:** 1.0
**Date:** 2026-04-03
**Status:** Approved

---

## 1. Problem Statement

Terminals cannot paste images. When a user has an image in their clipboard (from Win+Shift+S, browser copy, etc.), pressing Ctrl+V in a terminal either does nothing or pastes garbage. Meanwhile, AI coding tools (Claude Code, Codex CLI, Aider, etc.) increasingly accept image paths as input but run in terminal environments. The user must manually navigate to the screenshot folder, find the file, and copy its path -- every single time.

No existing tool solves this completely. The space is fragmented across ~12 tools, each limited to a specific platform (Windows OR macOS OR Linux) or environment (VS Code terminals only, tmux only, Explorer only). See `02_Projects/Terminal Copy Paste/Research/TCP - Competitive Landscape & Market Gap.md` for the full competitive analysis.

## 2. Solution

TCP intercepts a global hotkey (Alt+B) and pastes the **file path** of the current clipboard image into the active terminal window. One keypress. Works in any terminal, on any OS.

## 3. Architecture

Two-layer design with clean separation:

```
+---------------------------------------+
|  Platform-specific hotkey shim        |  <- thin, replaceable
|  Windows: AutoHotkey v2 (~20 lines)   |
|  macOS:   Hammerspoon (future)        |
|  Linux:   sxhkd + xdotool (future)   |
+---------------------------------------+
|  Python core (cross-platform)         |  <- all real logic
|  - Clipboard inspection               |
|  - Image saving                       |
|  - Screenshot folder detection        |
|  - Path formatting (OS-native)        |
|  - Config management                  |
|  - Usage tracking + coffee prompts    |
+---------------------------------------+
```

### 3.1 Python Core (`tcp_core.py`)

Stateless CLI invoked per-keypress:

```
python tcp_core.py -> prints absolute path to stdout -> exits
```

- Exit code 0: success, path on stdout
- Exit code 1: no image in clipboard, nothing on stdout
- Exit code 2: error (message on stderr)

No daemon. No long-running process. Invoked fresh each time by the shim.

### 3.2 Platform Shim

The shim's responsibilities:
1. Register global hotkey (Alt+B)
2. On keypress: run `python tcp_core.py`, capture stdout
3. If exit 0: type the captured path into the active window via keystroke simulation
4. If exit 1: do nothing (optionally beep/tooltip)
5. Manage system tray (Windows) or menu bar (macOS)

On Windows, AHK's `SendInput` is the most reliable keystroke injection method across terminal emulators (Windows Terminal, Warp, PowerShell, CMD, Git Bash).

### 3.3 Why This Split

- Python core is 100% cross-platform and independently testable
- Shim swap = cross-platform support (no logic reimplementation)
- No IPC, no sockets, no shared state -- just stdin/stdout
- Each layer uses the best tool for its job

## 4. Clipboard Detection & File Resolution

Decision tree executed on each invocation:

### Step 1: Check for image in clipboard

| Platform | API | Check for |
|----------|-----|-----------|
| Windows | `win32clipboard` (pywin32) | `CF_DIB` or `CF_BITMAP` format |
| macOS | `AppKit.NSPasteboard` | `NSPasteboardTypePNG` / `NSPasteboardTypeTIFF` |
| Linux | `xclip -selection clipboard -t TARGETS` | `image/png` |

No image found -> exit code 1.

### Step 2: Check for backing file

Win+Shift+S (and similar tools) save to a known folder AND put the image on the clipboard. Strategy: find the newest image file in the screenshots folder that was modified within the **recency window** (default: 5 seconds).

- Match found -> return that file's path (no duplicate saving)
- No match -> fall through to Step 3

### Step 3: Save clipboard image to disk

Extract image data from clipboard, save as PNG to the screenshots folder.

Naming convention: `tcp_{YYYYMMDD}_{HHmmss}.png`

Return path to the new file.

### Screenshot Folder Detection

| Platform | Source | Fallback |
|----------|--------|----------|
| Windows | Registry `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders` key `{B7BEDE81-DF94-4682-A7D8-57A52620B86F}` | `~/Pictures/Screenshots` |
| macOS | `defaults read com.apple.screencapture location` | `~/Desktop` |
| Linux | `xdg-user-dirs` for `XDG_SCREENSHOTS_DIR` | `~/Pictures/Screenshots` |

All overridable via config file.

## 5. Configuration

Single config file at platform-appropriate location:

- Windows: `%APPDATA%\tcp\config.toml`
- macOS/Linux: `~/.config/tcp/config.toml`

```toml
# Where to save clipboard images that don't have a backing file
# Default: auto-detected from OS screenshot settings
save_dir = ""

# Filename pattern for saved images (strftime format)
filename_pattern = "tcp_%Y%m%d_%H%M%S.png"

# How recent a file must be to count as the backing screenshot (seconds)
recency_window = 5

# Image format
format = "png"  # png | jpg

# Path output style
# "native" = OS default (backslash on Windows, forward on Unix)
path_style = "native"
```

Config is optional. TCP works with sensible defaults when no config file exists.

## 6. System Tray (Windows)

AHK provides built-in system tray support:

- **Icon:** TCP branding icon in the system tray
- **Tooltip:** "TCP active -- Alt+B to paste image path"
- **Right-click menu:**
  - Pause / Resume (toggles hotkey listening)
  - Exit
- **Startup:** Optional "Run at login" via Start Menu shortcut or Registry `Run` key. User opts in via tray menu or first-run prompt.

macOS equivalent: menu bar icon via Hammerspoon (future).
Linux: optional tray via `yad` or similar (future).

The Python core has no awareness of the tray. Clean separation.

## 7. Usage Tracking & Monetization

### 7.1 Usage Counter

File alongside config:
- Windows: `%APPDATA%\tcp\usage.json`
- macOS/Linux: `~/.config/tcp/usage.json`

```json
{
  "total_uses": 1247,
  "last_prompt_at": 500,
  "dismissed_forever": false
}
```

Incremented on every successful path paste (exit code 0). Persists across restarts.

### 7.2 Milestone Coffee Prompts

| Uses | Message |
|------|---------|
| 500 | "You've pasted 500 image paths with TCP. If it's saving you time, a coffee helps keep the tools coming." |
| 1,500 | "1,500 pastes. TCP is part of your workflow now. Every coffee fuels the next tool." |
| 5,000 | "5,000 pastes. You're a power user. Help me keep building." |
| 10,000+ | Every 10,000 thereafter (20k, 30k...) |

### 7.3 Prompt Behavior

- Opens default browser to Buy Me a Coffee page
- Shows a non-blocking system notification (Windows toast / macOS notification center)
- Includes "Don't show again" option (sets `dismissed_forever: true` in usage.json)
- Never prompts more than once per milestone
- Prompt fires on the next Alt+B press after crossing the milestone, not during active use
- Tool always works regardless of prompt state -- no feature lockouts, no degraded mode

### 7.4 Messaging Philosophy

The prompts position support as funding the **ecosystem of tools**, not paying for TCP specifically: "keeps the tools coming" / "fuels the next tool." This aligns with the CodeWarrior4Life / Crossroads Technologies portfolio strategy.

## 8. Licensing

**Business Source License 1.1**

```
Licensor: Crossroads Technologies, LLC
Licensed Work: Terminal Copy Paste
Additional Use Grant: You may use the Licensed Work for any purpose,
  including commercial, except for distributing modified versions
  or offering it as part of a competing product.
Change Date: 4 years from each release
Change License: MIT
```

Rationale:
- Source-available: users can audit the code (important for a tool that registers global hotkeys)
- Free for all use including commercial/enterprise internal use
- Prevents forking to strip coffee prompts and redistributing
- 4-year auto-convert to MIT signals good faith
- No license key system, no tiered pricing, no admin overhead
- Enforcement: DMCA takedown for violations (simple GitHub form)

## 9. Distribution

### 9.1 Windows (Primary)

- Compiled Python core via PyInstaller -> `tcp_core.exe`
- Compiled AHK script -> `tcp.exe` (or bundled with AHK runtime)
- Single zip download: `tcp.exe` + `tcp_core.exe` + `LICENSE`
- Published on: project website, GitHub Releases

### 9.2 macOS (Future)

- Python core (same code, no compilation needed if Python installed)
- Hammerspoon shim script
- Homebrew tap (stretch goal)

### 9.3 Linux (Future)

- Python core + sxhkd config + xdotool dependency
- AUR package or .deb (stretch goal)

## 10. File Structure (Repo)

```
TerminalCopyPaste/
  src/
    tcp_core.py          # Cross-platform Python core
    platforms/
      windows/
        tcp.ahk          # AHK v2 hotkey shim
      macos/
        tcp.lua          # Hammerspoon shim (future)
      linux/
        tcp_sxhkd.sh     # sxhkd + xdotool shim (future)
  config/
    config.example.toml  # Example config
  assets/
    tcp-icon.ico         # Windows tray icon
    tcp-icon.png         # General icon
  docs/
    superpowers/
      specs/             # Design specs
  tests/
    test_tcp_core.py     # Core logic tests
  LICENSE                # BSL 1.1
  README.md              # Usage, install, config docs
  .gitignore
  .gitleaks.toml
  CLAUDE.md              # (gitignored) Vault identity
```

## 11. Testing Strategy

- **Unit tests** for the Python core: clipboard detection mocking, file resolution, config loading, path formatting, usage counter logic
- **Integration tests** on Windows: actual clipboard -> actual file -> actual path output
- **Manual test matrix:** Windows Terminal, PowerShell, CMD, Git Bash, Warp, VS Code terminal
- **Platform tests** added as macOS/Linux shims are built

## 12. MVP Scope

**In scope (v1.0):**
- Python core with full clipboard detection + file resolution
- Windows AHK shim with system tray
- Config file support
- Usage tracking + coffee prompts
- BSL license
- PyInstaller-compiled Windows binary
- README with install/usage docs

**Out of scope (future):**
- macOS Hammerspoon shim
- Linux sxhkd shim
- Installer / setup wizard
- Auto-update mechanism
- Clipboard history (paste 2nd-most-recent screenshot)
- Configurable hotkey (Alt+B is hardcoded in v1)
