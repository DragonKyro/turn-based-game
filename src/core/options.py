"""User-configurable game options. Persisted to disk so they survive restarts."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from src.config import PROJECT_ROOT

OPTIONS_PATH = PROJECT_ROOT / "saves" / "options.json"


@dataclass
class Options:
    show_fight_scene: bool = True
    fight_scene_duration: float = 2.2  # seconds

    @classmethod
    def load(cls) -> "Options":
        if not OPTIONS_PATH.exists():
            return cls()
        try:
            with OPTIONS_PATH.open(encoding="utf-8") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return cls()

    def save(self) -> None:
        OPTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OPTIONS_PATH.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
