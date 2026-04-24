# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.1.1] - 2026-04-24

### Fixed
- `requirements.txt` now guards `pywin32` with `sys_platform == "win32"` so `pip install` works on macOS and Linux (the Python core has always been cross-platform per spec §3).
- `install.sh` correctly uses Homebrew's Python 3.13 after `brew install python@3.13` by prepending the keg's `libexec/bin` to `PATH` (unversioned `python3` is not symlinked by default on macOS).
- Removed macOS LaunchAgent / Linux `.desktop` autostart generation from `install.sh`. The Python core is a stateless per-keypress CLI (spec §3.1); running it at login executed once and exited. Login startup will return alongside the macOS/Linux hotkey shims.

## [1.1.0] - 2026-04-10

### Added
- Any-file paste: files copied from Explorer or messaging apps paste as paths
- System-wide mutex to prevent duplicate TCP instances

### Fixed
- Replaced character-by-character `SendInput "{Raw}"` with clipboard swap + Ctrl+V for instant path pasting
- Streamlined installer: silent wizard, proper TCP icon, AHK exe launch

## [1.0.0] - 2026-04-03

### Added
- Smart Ctrl+V: pastes image file path in terminals, normal paste everywhere else
- Alt+V force override: paste image path in any window
- Automatic screenshot directory detection (Windows registry, known defaults)
- Clipboard image detection and extraction (Windows, macOS, Linux)
- File resolver: matches recent screenshots or saves clipboard images
- Path formatting with native/forward/backslash styles and auto-quoting
- Usage tracking with milestone coffee prompts
- Configuration via `%APPDATA%\tcp\config.toml`
- Built-in terminal detection (Windows Terminal, PowerShell, CMD, VS Code, Warp, Alacritty, Git Bash)
- Custom terminal support via `extra_terminals` config
- AutoHotkey v2 shim with tray icon and hotkey management
- Windows GUI installer (Inno Setup) with auto-dependency installation
- Windows CLI installer (`install.bat` / `install.ps1`)
- macOS/Linux Bash installer with distro detection
- Custom app and tray icons
- Stop-ExistingTCP: cleanly terminates running sessions before install/upgrade

### Fixed
- Clipboard-swap approach for Ctrl+V (no synthetic keystrokes)
- AHK `{Raw}` and `{Blind}` to prevent ghost modifier keys
- AHK working directory resolution
- BMP header offset detection for Linux clipboard
