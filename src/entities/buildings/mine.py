"""Mine: neutral-capturable currency building. Generates gold each turn for its owner."""
from __future__ import annotations

from typing import ClassVar

from src.entities.building import Building


class Mine(Building):
    kind: ClassVar[str] = "mine"
    display_letter: ClassVar[str] = "M"
    gold_per_turn: ClassVar[int] = 150
