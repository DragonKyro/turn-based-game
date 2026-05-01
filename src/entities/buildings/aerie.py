"""Aerie: produces Air units."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.building import Building


class Aerie(Building):
    kind: ClassVar[str] = "aerie"
    display_letter: ClassVar[str] = "A"
    produces_class: ClassVar[UnitClass | None] = UnitClass.AIR
    produces_kinds: ClassVar[tuple[str, ...]] = ("wyvern",)
