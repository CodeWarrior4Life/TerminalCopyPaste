# Terminal Copy Paste (TCP) — Marketing Copy v1.0.0

---

## GitHub Repo Description

Smart Ctrl+V for terminals: auto-detects screenshot folders and pastes image file paths instead of failing. Alt+V works anywhere. Zero config. Built for AI coding tools (Claude Code, Codex CLI, Aider). Windows.

---

## Twitter/X Thread

**Tweet 1 — Hook**

You screenshot something. Switch to your terminal. Press Ctrl+V.

Nothing happens.

Or worse — garbage characters get dumped into your prompt.

Terminals can't paste images. Never could. You've been manually hunting file paths like it's 2003.

There's a fix for this now.

---

**Tweet 2 — Problem Amplification**

If you use AI coding tools — Claude Code, Codex CLI, Aider — you know the drill.

You capture a screenshot of an error. You need to pass that path to the tool. So you:

1. Open File Explorer
2. Navigate to the screenshot folder
3. Right-click → Copy as path
4. Paste it

Every. Single. Time.

That's 4 steps for something that should be 1 keypress.

---

**Tweet 3 — Solution Introduction**

Terminal Copy Paste (TCP) makes Ctrl+V smart.

Press Ctrl+V in a terminal with an image in your clipboard → it pastes the file path.

Press Ctrl+V anywhere else → normal paste, untouched.

One tool. Zero configuration. No new muscle memory required.

---

**Tweet 4 — Key Feature: Smart Ctrl+V**

How TCP decides what to do:

- Terminal focused + image in clipboard → paste the file path
- Terminal focused + text in clipboard → normal paste
- Not a terminal → normal paste

It detects your screenshot folder automatically. If the file exists on disk, it finds it. If it doesn't, it saves it first. Then types the path.

You just press Ctrl+V like always.

---

**Tweet 5 — Key Feature: Zero Config**

TCP works out of the box. No setup wizard. No config file. No account.

It auto-detects:
- Your OS screenshot folder
- Which window is a terminal
- The most recent matching image

Supports Windows Terminal, PowerShell, CMD, VS Code, Warp, Alacritty, Git Bash, and more.

You can customize via a toml file if you want. You won't need to.

---

**Tweet 6 — Key Feature: Built for AI Tools**

This was built specifically because AI coding tools changed how developers work.

Claude Code, Codex CLI, Aider — they all need image paths in the terminal. Screenshot workflows are now part of coding.

Alt+V is TCP's override: force-paste the image path anywhere, anytime, regardless of which window is focused.

---

**Tweet 7 — Call to Action**

TCP is free. BSL 1.1 license — free for all use.

Windows installer (one-click):
https://github.com/CodeWarrior4Life/TerminalCopyPaste/releases/latest

Or install via PowerShell:
`irm https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.ps1 | iex`

Repo: https://github.com/CodeWarrior4Life/TerminalCopyPaste

---

**Tweet 8 — Engagement Question**

Question for devs using AI coding tools:

What's your current workflow for getting screenshots into Claude Code / Codex / Aider?

Curious how many people are manually copy-pasting paths vs. something more streamlined.

---

## Reddit Posts

### r/commandline

**Title:** I built a tool that makes Ctrl+V work with images in terminals

Terminals can't paste images — that's just accepted as a fact of life. But when you're using AI coding tools (Claude Code, Aider, Codex), you need to pass image paths constantly. Screenshot an error, paste the path, move on. Except the "paste the path" part means finding the file manually every time.

So I built Terminal Copy Paste (TCP).

It intercepts Ctrl+V in terminals. If there's an image in your clipboard, it pastes the file path instead of doing nothing. If there's text, it passes through normally. Ctrl+V behaves exactly like you'd want it to, context-aware.

- **Smart Ctrl+V** — auto-detects whether you're in a terminal and whether your clipboard has an image
- **Alt+V** — force-paste the image path anywhere, no matter what window is focused
- **Zero config** — auto-detects your screenshot folder and which windows are terminals
- **Configurable** — `%APPDATA%\tcp\config.toml` if you want to customize anything

Supports Windows Terminal, PowerShell, CMD, VS Code integrated terminal, Warp, Alacritty, Git Bash.

Free. BSL 1.1 (free for all use).

Repo + installer: https://github.com/CodeWarrior4Life/TerminalCopyPaste

Happy to answer questions about how it works under the hood. It's an AutoHotkey shim on top of a Python core — AHK intercepts the keystrokes, Python handles the clipboard logic and file detection.

---

### r/programming

**Title:** Terminal Copy Paste — smart Ctrl+V that auto-detects images and pastes file paths

Terminals don't paste images. That's fine — they're not supposed to. But AI coding tools have created a new workflow where developers need to pass screenshot paths into terminal sessions constantly, and the manual hunt-for-the-file step is friction that adds up.

I shipped TCP (Terminal Copy Paste) v1.0.0 this week to solve it.

**What it does:**

When you press Ctrl+V in a terminal and there's an image in your clipboard, TCP:
1. Checks if the image matches a recent file in your screenshot folder (within a configurable recency window, default 5 seconds)
2. If a match exists, types the full path
3. If no match, saves the clipboard image to disk, then types the path
4. Falls back to normal paste behavior if no image is present

**Architecture:**

- AutoHotkey v2 shim for keyboard interception (Windows)
- Python core handles clipboard inspection, file detection, and path typing
- TOML config at `%APPDATA%\tcp\config.toml`
- One-click installer or PowerShell one-liner

**Why not just a shell alias or function?**

A shell function can't intercept Ctrl+V at the OS level. It would require explicitly calling a command rather than just pressing paste. The AHK layer is what makes it transparent — same keypress, smarter behavior.

Repo: https://github.com/CodeWarrior4Life/TerminalCopyPaste

Free, BSL 1.1. Feedback welcome.

---

### r/windows

**Title:** Free tool: makes Ctrl+V paste image file paths in terminals instead of doing nothing

If you take a lot of screenshots and use them in terminal apps, this will save you a trip to File Explorer every single time.

**Terminal Copy Paste (TCP)** intercepts Ctrl+V when you're in a terminal. If you have an image on your clipboard, it pastes the file path. If you have text, it pastes normally. Outside of terminals, nothing changes.

Works with: Windows Terminal, PowerShell, CMD, VS Code, Warp, Alacritty, Git Bash. More can be added in a config file.

**Install:**

Option 1 — Download and run the installer:
https://github.com/CodeWarrior4Life/TerminalCopyPaste/releases/latest

Option 2 — PowerShell one-liner:
```
irm https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.ps1 | iex
```

Free. No account. No telemetry. BSL 1.1 license.

Repo: https://github.com/CodeWarrior4Life/TerminalCopyPaste

---

## Hacker News

### Post Title

Show HN: Terminal Copy Paste — smart Ctrl+V that pastes image paths in terminals

### Opening Comment

Hey HN,

I built this after hitting the same friction point repeatedly: I'd screenshot something, switch to a terminal session, and press Ctrl+V out of habit. Nothing. Then I'd have to alt-tab to File Explorer, find the screenshot, copy its path, come back.

When you're working with AI coding tools — Claude Code in particular — this happens constantly. You screenshot an error, a UI state, a diff, and you need that path in the terminal prompt. The manual lookup step is small in isolation but maddening in a flow state.

**What TCP does:**

- Intercepts Ctrl+V at the OS level using an AutoHotkey v2 shim
- Checks if the active window is a terminal (configurable list, sensible defaults)
- Checks the clipboard for image data
- If both: finds the matching file on disk via a recency window match (default: 5 seconds), or saves the clipboard image if no match exists
- Types the file path into the terminal
- Alt+V force-pastes the path anywhere, regardless of focused window

**Technical notes:**

The AHK shim is thin — it just intercepts the keystrokes and hands off to the Python core via subprocess. The Python side handles clipboard inspection (using `pywin32`), file system matching, and typing via AHK's `Send`. The recency window avoids false matches from old screenshots when you have an unrelated image in your clipboard.

Config is optional TOML at `%APPDATA%\tcp\config.toml`. Screenshot folder is auto-detected from Windows registry (the `{B7BEDE81-DF94-4682-A7D8-57A52620B86F}` known folder key). Runs as a background tray process.

**What's next:**

- macOS hotkey shim (the Python core already works cross-platform, just needs a Swift/Hammerspoon layer)
- Linux hotkey shim (xdotool or similar)
- Optional path quoting (for paths with spaces)
- Watcher mode that detects new screenshots and pre-caches the path

**License:** BSL 1.1 — free for all use.

Repo: https://github.com/CodeWarrior4Life/TerminalCopyPaste

---

## Dev.to Article Draft

### Title: I Got Tired of Hunting Screenshot Paths in Terminals. So I Fixed Ctrl+V.

---

There's a small workflow failure that happens dozens of times a day if you use AI coding tools in a terminal.

You take a screenshot. You switch to your terminal. You press Ctrl+V.

Nothing happens.

Terminals don't paste images. That's not a bug — it's just how they work. But it's become a friction point that didn't exist three years ago, because AI tools like Claude Code, Codex CLI, and Aider have made screenshots a core part of the coding workflow. You're capturing errors, UI states, diffs, diagrams — and you need to pass those paths into terminal prompts constantly.

The workaround everyone uses: alt-tab to File Explorer, navigate to the screenshot folder, copy the file path, come back. Four steps, every single time. If you screenshot-heavy, that's a lot of interruptions.

I got tired of it. So I built Terminal Copy Paste (TCP).

---

### The Idea

The fix seemed obvious: Ctrl+V should be context-aware. If I'm in a terminal and I have an image on my clipboard, I probably want the file path, not the image data. If I'm in a text editor, paste normally. If I'm in a browser, paste normally.

The key insight is that the behavior should be invisible. I didn't want a new command to memorize. I wanted Ctrl+V to just do the right thing depending on where I was.

---

### How It Works

TCP has two layers.

**The keyboard layer** is an AutoHotkey v2 script that runs in the background as a tray process. It intercepts Ctrl+V at the OS level. When you press it, AHK checks which window is focused. If it's a terminal, it hands off to the Python core. If it's not, it does nothing and lets the normal paste go through.

**The Python core** handles the logic:

1. Inspect the clipboard — is there image data?
2. If yes: check the OS screenshot folder for a file that matches, using a recency window (default: 5 seconds). If the screenshot was captured in the last 5 seconds, it's almost certainly the one you want.
3. If a match exists: type the full file path into the terminal.
4. If no match exists: save the clipboard image to disk, then type the path.
5. If no image in clipboard: fall back to normal paste behavior.

Alt+V is the override: it force-pastes the image path regardless of which window is focused. Useful when you're pasting into a GUI app that isn't a terminal but still needs a path.

---

### Zero Config by Design

I made a deliberate choice to require no setup. TCP works the moment you install it.

Screenshot folder detection is automatic on every platform — Windows registry keys, macOS defaults, and XDG paths on Linux. No config file needed for the common case.

Terminal detection uses a built-in list of process names: `WindowsTerminal.exe`, `powershell.exe`, `pwsh.exe`, `cmd.exe`, `Code.exe`, `warp.exe`, `alacritty.exe`, `mintty.exe`. You can add more in `%APPDATA%\tcp\config.toml` if your terminal isn't covered.

The config file is optional TOML for users who want to customize anything:

```toml
save_dir = ""                          # Auto-detected from OS settings
filename_pattern = "tcp_%Y%m%d_%H%M%S.png"
recency_window = 5                     # Seconds
format = "png"
path_style = "native"                  # native, forward, or backslash
extra_terminals = ["hyper.exe"]
```

---

### Why AutoHotkey

Keyboard interception at the OS level on Windows comes down to a few options: raw Win32 hooks in C/C++, PowerShell with P/Invoke, or AHK. I chose AHK because it's mature, well-understood in the Windows power-user community, and the v2 API is clean. The shim is about 50 lines. It does one thing: intercept hotkeys and shell out to Python.

The Python core is where the logic lives. That also means it's cross-platform — the core already works on macOS and Linux. The missing piece for those platforms is just the hotkey interception layer (Swift/Hammerspoon for macOS, xdotool for Linux). That's on the roadmap.

---

### What I Learned

The hardest part wasn't the clipboard logic or the file matching — it was getting the AHK keystroke injection right. When TCP types a file path into a terminal, it uses AHK's `Send` function. Early versions had a bug where modifier keys (Ctrl, Shift) from the intercepted hotkey would "leak" into the sent keystrokes, garbling the output. The fix was using `{Raw}` and `{Blind}` mode in AHK to ensure the send is clean.

The second tricky part was the clipboard-swap approach for Ctrl+V passthrough. When TCP determines the paste should be a normal text paste, it needs to let the keypress go through as-is. Getting that right without synthetic keystrokes or double-fires took a few iterations.

---

### What's Next

- macOS support (the Swift hotkey shim is the main missing piece)
- Linux support (xdotool-based shim)
- Optional path quoting for paths with spaces
- Watcher mode — detect new screenshots in real time and pre-cache the path so the first Ctrl+V is instant even if the file write is slow

---

### Try It

TCP is free. BSL 1.1 — free for all use.

**One-click installer:** [TCPSetup.exe](https://github.com/CodeWarrior4Life/TerminalCopyPaste/releases/latest)

**PowerShell one-liner:**
```powershell
irm https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.ps1 | iex
```

**Repo:** https://github.com/CodeWarrior4Life/TerminalCopyPaste

If you use Claude Code, Codex CLI, Aider, or any terminal-heavy workflow, give it a try. It's the kind of tool that becomes invisible after a day — which is exactly what I was going for.

---

If you found this useful, consider [buying me a coffee](https://buymeacoffee.com/tfvmclmlwp) to keep the ideas flowing. ☕
