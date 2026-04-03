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
