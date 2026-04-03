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
