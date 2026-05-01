"""Stronghold: player HQ. Produces infantry, also generates gold, and is the victory target."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.building import Building


class Stronghold(Building):
    kind: ClassVar[str] = "stronghold"
    display_letter: ClassVar[str] = "H"
    is_hq: ClassVar[bool] = True
    gold_per_turn: ClassVar[int] = 200
    vision_range: ClassVar[int] = 3
    produces_class: ClassVar[UnitClass | None] = UnitClass.LAND
    produces_kinds: ClassVar[tuple[str, ...]] = ("infantry",)
