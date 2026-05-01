"""Level: a fully-constructed starting GameState."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.game_state import GameState


@dataclass
class Level:
    name: str
    initial_state: GameState
    victory_type: str  # "capture_strongholds" | "rout"
