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
