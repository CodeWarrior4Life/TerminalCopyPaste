"""Usage tracking and milestone coffee prompts."""

import json
import sys
import os
from pathlib import Path

MILESTONES = [500, 1500, 5000]
RECURRING_INTERVAL = 5000  # After 5000, prompt every 5,000
BMAC_URL = "https://buymeacoffee.com/tfvmclmlwp"

MESSAGES = {
    500: "You've pasted 500 image paths with TCP. If it's saving you time, a coffee helps keep the tools coming.",
    1500: "1,500 pastes. TCP is part of your workflow now. Every coffee fuels the next tool.",
    5000: "5,000 pastes. You're a power user. Help me keep building.",
}
DEFAULT_RECURRING_MSG = (
    "You've pasted {count:,} image paths with TCP. Every coffee fuels the next tool."
)


class UsageTracker:
    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            data_dir = self._default_data_dir()
        self._path = Path(data_dir) / "usage.json"
        self._data = self._load()

    @property
    def total_uses(self) -> int:
        return self._data.get("total_uses", 0)

    def increment(self) -> None:
        self._data["total_uses"] = self.total_uses + 1
        self._save()

    def should_prompt(self) -> bool:
        if self._data.get("dismissed_forever", False):
            return False

        uses = self.total_uses
        last = self._data.get("last_prompt_at", 0)

        # Check fixed milestones
        for m in MILESTONES:
            if uses >= m and last < m:
                return True

        # Check recurring milestones after the last fixed one
        if uses >= MILESTONES[-1]:
            max_fixed = MILESTONES[-1]
            # Next recurring milestone after last_prompt_at
            if last < max_fixed:
                return True
            recurring_base = max_fixed + RECURRING_INTERVAL
            while recurring_base <= uses:
                if last < recurring_base:
                    return True
                recurring_base += RECURRING_INTERVAL

        return False

    def get_prompt_message(self) -> str:
        uses = self.total_uses
        last = self._data.get("last_prompt_at", 0)

        for m in MILESTONES:
            if uses >= m and last < m:
                return MESSAGES[m]

        return DEFAULT_RECURRING_MSG.format(count=uses)

    def mark_prompted(self) -> None:
        self._data["last_prompt_at"] = self.total_uses
        self._save()

    def dismiss_forever(self) -> None:
        self._data["dismissed_forever"] = True
        self._save()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"total_uses": 0, "last_prompt_at": 0, "dismissed_forever": False}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

    @staticmethod
    def _default_data_dir() -> str:
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return str(Path(base) / "tcp")
        return str(Path.home() / ".config" / "tcp")
