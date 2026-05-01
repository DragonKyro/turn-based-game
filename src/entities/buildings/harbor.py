"""Harbor: produces Water units."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.building import Building


class Harbor(Building):
    kind: ClassVar[str] = "harbor"
    display_letter: ClassVar[str] = "P"  # "P" for port — 'H' is the stronghold
    produces_class: ClassVar[UnitClass | None] = UnitClass.WATER
    produces_kinds: ClassVar[tuple[str, ...]] = ("longship", "warship")
