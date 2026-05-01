"""Barracks: produces Land units."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.building import Building


class Barracks(Building):
    kind: ClassVar[str] = "barracks"
    display_letter: ClassVar[str] = "B"
    produces_class: ClassVar[UnitClass | None] = UnitClass.LAND
    produces_kinds: ClassVar[tuple[str, ...]] = ("infantry",)
