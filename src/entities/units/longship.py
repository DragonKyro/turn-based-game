"""Longship: water unit with ranged attack. Strong vs Infantry (raids from the sea)."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import on_terrain
from src.entities.unit import CritPredicate, Unit


class Longship(Unit):
    kind: ClassVar[str] = "longship"
    unit_class: ClassVar[UnitClass] = UnitClass.WATER
    max_hp: ClassVar[int] = 12
    attack: ClassVar[int] = 6
    defense: ClassVar[int] = 1
    move: ClassVar[int] = 5
    cost: ClassVar[int] = 400
    vision_range: ClassVar[int] = 3
    attack_range: ClassVar[tuple[int, int]] = (2, 3)  # ranged, no counter from adjacent
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"infantry"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        on_terrain("sea"),  # at home in deep water
    )
    display_letter: ClassVar[str] = "L"
