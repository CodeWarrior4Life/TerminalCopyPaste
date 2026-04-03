"""Detect the OS screenshot save directory."""

import os
import sys
from pathlib import Path

from src.config import TCPConfig


def get_screenshot_dir(config: TCPConfig) -> str:
    if config.save_dir:
        expanded = Path(config.save_dir).expanduser()
        # If no tilde was present, return the original string unchanged to
        # preserve the caller's path-separator convention.
        if "~" not in config.save_dir:
            return config.save_dir
        return str(expanded)

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
        return str(Path(os.path.expandvars(value)))


def _macos_screenshot_dir() -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            capture_output=True,
            text=True,
            timeout=5,
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
