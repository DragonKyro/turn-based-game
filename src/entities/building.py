"""Building base + flavours: Production (spawns units), Currency (gold), Stronghold (HQ, both)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.core.types import Coord, UnitClass


@dataclass
class Building:
    id: int
    coord: Coord
    owner_id: int | None  # None = neutral / capturable
    capture_progress: int = 0

    kind: ClassVar[str] = ""
    display_letter: ClassVar[str] = "?"
    capture_threshold: ClassVar[int] = 20
    gold_per_turn: ClassVar[int] = 0
    is_hq: ClassVar[bool] = False
    vision_range: ClassVar[int] = 2

    produces_class: ClassVar[UnitClass | None] = None
    produces_kinds: ClassVar[tuple[str, ...]] = ()

    def can_produce(self, unit_kind: str) -> bool:
        return unit_kind in self.produces_kinds
