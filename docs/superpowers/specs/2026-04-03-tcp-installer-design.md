# TCP Installation Wrapper — Design Spec

**Date:** 2026-04-03
**Status:** Approved
**Project:** Terminal Copy Paste (TCP)

---

## 1. Goals

Provide a single-command install experience for TCP on Windows, macOS, and Linux. Two install tracks:

1. **CLI scripts** — for power users who live in the terminal
2. **GUI installer** — Inno Setup `.exe` for Windows end users

Both tracks silently detect and install missing dependencies. No prompting for deps — if something is missing, install it.

## 2. Install Tracks

### 2.1 Windows CLI Track

**Files:** `install.bat`, `install.ps1`

`install.bat` is a thin launcher that calls `install.ps1` with the correct execution policy. This lets users double-click from Explorer without worrying about PowerShell execution policy.

**install.bat behavior:**
```
@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
```

**install.ps1 steps (in order):**

| Step | Action | Detection | Install Method |
|------|--------|-----------|----------------|
| 1 | Python 3.12+ | `python --version` parse major.minor | Download `python-3.13.x-amd64.exe` from python.org, run `/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1` |
| 2 | AutoHotkey v2 | Check `HKLM:\SOFTWARE\AutoHotkey` registry key + `where AutoHotkey64.exe` | Download AHK v2 setup from autohotkey.com, run `/silent` |
| 3 | pip deps | N/A (always run) | `python -m pip install --quiet -r requirements.txt` |
| 4 | Config | Check `%APPDATA%\tcp\config.toml` exists | Copy `config\config.example.toml` to `%APPDATA%\tcp\config.toml` |
| 5 | Startup | Ask user: checkbox `[Y/n] Start TCP on login?` | Create `.lnk` shortcut in `shell:startup` pointing to `tcp.ahk` |
| 6 | Launch | N/A | Start `tcp.ahk` via `Start-Process` |

**One-liner for README:**
```powershell
irm https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.ps1 | iex
```

**Remote-mode behavior:** When `install.ps1` runs via `irm | iex` (no local repo), it must:
- Clone or download the repo to a known location (e.g., `%LOCALAPPDATA%\tcp`)
- Then proceed with the standard install steps from that directory

**Local-mode behavior:** When run from within the cloned repo, use files in place.

### 2.2 Windows GUI Track (Inno Setup)

**Files:** `installer/tcp.iss`

Inno Setup wizard that bundles the repo contents and performs the same install logic as the CLI track. Produces a single `TCPSetup.exe`.

**Wizard pages:**
1. Welcome / License (BSL 1.1)
2. Install location (default: `%LOCALAPPDATA%\tcp`)
3. Options page:
   - [x] Install Python 3.12+ (if not detected) — checked, grayed out if already installed
   - [x] Install AutoHotkey v2 (if not detected) — checked, grayed out if already installed
   - [ ] Start TCP on login — unchecked by default
4. Progress bar (downloads + installs)
5. Finish — "Launch TCP now" checkbox

**Inno Setup [Run] section handles:**
- Python silent install (if needed)
- AHK silent install (if needed)
- `pip install -r requirements.txt`
- Config copy
- Startup shortcut (if checked)
- Launch tcp.ahk (if checked)

**Uninstaller:** Inno Setup auto-generates. Removes TCP files, startup shortcut, and optionally `%APPDATA%\tcp` config dir (prompt user).

### 2.3 macOS Installer

**Files:** `install.sh` (shared with Linux, macOS code path)

**Steps:**

| Step | Action | Detection | Install Method |
|------|--------|-----------|----------------|
| 1 | Homebrew | `which brew` | Install via Homebrew's official one-liner |
| 2 | Python 3.12+ | `python3 --version` parse major.minor | `brew install python@3.13` |
| 3 | pip deps | N/A | `python3 -m pip install --quiet -r requirements.txt` |
| 4 | Config | Check `~/.config/tcp/config.toml` | Copy `config/config.example.toml` |
| 5 | Startup | Ask user: `Start TCP on login? [Y/n]` | Create Launch Agent plist at `~/Library/LaunchAgents/com.crossroadtech.tcp.plist` |

**Note:** macOS has no AHK equivalent. The Python core is installed and usable as `python3 -m src.tcp_core`. A native hotkey shim (Hammerspoon/Karabiner/Swift) is a future project.

**One-liner for README:**
```bash
curl -fsSL https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.sh | bash
```

### 2.4 Linux Installer

**Files:** `install.sh` (shared with macOS, Linux code path)

**Steps:**

| Step | Action | Detection | Install Method |
|------|--------|-----------|----------------|
| 1 | Python 3.12+ | `python3 --version` parse major.minor | Distro package manager: `apt install python3` / `dnf install python3` / `pacman -S python` |
| 2 | xclip | `which xclip` | `apt install xclip` / `dnf install xclip` / `pacman -S xclip` |
| 3 | pip deps | N/A | `python3 -m pip install --quiet -r requirements.txt` |
| 4 | Config | Check `~/.config/tcp/config.toml` | Copy `config/config.example.toml` |
| 5 | Startup | Ask user: `Start TCP on login? [Y/n]` | Create `.desktop` file in `~/.config/autostart/tcp.desktop` |

**Distro detection:** Read `/etc/os-release` to determine package manager:
- `apt-get`: Debian, Ubuntu, Mint, Pop!_OS
- `dnf`: Fedora, RHEL, CentOS Stream
- `pacman`: Arch, Manjaro, EndeavourOS
- Fallback: print error with manual instructions

**One-liner for README (same as macOS):**
```bash
curl -fsSL https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.sh | bash
```

## 3. Shared Behavior

### 3.1 Remote vs Local Mode

All scripts detect whether they're running from within a cloned repo or via a remote one-liner:

- **Local mode:** `install.ps1`/`install.sh` exists alongside `requirements.txt` → use files in place
- **Remote mode:** No local repo detected → clone to install directory first, then proceed
  - Windows: `%LOCALAPPDATA%\tcp`
  - macOS: `~/Library/Application Support/tcp`
  - Linux: `~/.local/share/tcp`

### 3.2 Idempotency

All scripts are safe to run multiple times:
- Skip deps that are already installed and meet version requirements
- Don't overwrite existing `config.toml` (only copy if missing)
- Don't duplicate startup entries
- Re-running after a partial failure picks up where it left off

### 3.3 Output

- Print a status line for each step: `[OK] Python 3.13.1 found` or `[INSTALL] Installing Python 3.13...`
- Print a summary at the end showing what was installed/skipped
- Errors print in red with clear next-step instructions

### 3.4 Startup Option

- **Windows CLI:** Prompt `Start TCP on login? [Y/n]`
- **Windows GUI:** Checkbox on options page (unchecked by default)
- **macOS/Linux:** Prompt `Start TCP on login? [Y/n]`

Default is **no** (unchecked) across all tracks. User must opt in.

## 4. File Structure

```
install.bat                    # Windows CLI launcher (thin wrapper)
install.ps1                    # Windows CLI installer (PowerShell)
install.sh                     # macOS + Linux CLI installer (Bash)
installer/
  tcp.iss                      # Inno Setup script
  tcp-icon.ico                 # Installer icon (from shell32 clipboard or custom)
```

## 5. README Install Section

The README install section will be updated to:

```markdown
## Install

### Windows (GUI)
Download [TCPSetup.exe](https://github.com/CodeWarrior4Life/TerminalCopyPaste/releases/latest) and run it.

### Windows (CLI)
irm https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.ps1 | iex

### macOS
curl -fsSL https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.sh | bash

### Linux
curl -fsSL https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.sh | bash
```

## 6. Out of Scope

- macOS/Linux hotkey shim (future project — needs Hammerspoon, Karabiner, or native implementation)
- Package manager publishing (winget, brew, apt — future milestone)
- Auto-update mechanism
- Signing the Inno Setup installer (future, requires code signing cert)

## 7. Testing

- **Windows CLI:** Run `install.ps1` on clean Windows VM. Verify Python, AHK, pip deps installed. Verify config created. Verify startup shortcut created when opted in.
- **Windows GUI:** Build `TCPSetup.exe`, run on clean Windows VM. Same verification.
- **macOS:** Run `install.sh` on clean macOS. Verify Python, pip deps. Verify config. Verify Launch Agent.
- **Linux:** Run `install.sh` on Ubuntu, Fedora, Arch. Verify Python, xclip, pip deps. Verify config. Verify autostart desktop file.
- **Idempotency:** Run each installer twice. Second run should skip everything and print `[OK]` for all steps.
