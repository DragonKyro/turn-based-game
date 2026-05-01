"""Warship: heavier ranged water unit. Slower than longships but hits harder at long range."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import on_terrain
from src.entities.unit import CritPredicate, Unit


class Warship(Unit):
    kind: ClassVar[str] = "warship"
    unit_class: ClassVar[UnitClass] = UnitClass.WATER
    max_hp: ClassVar[int] = 14
    attack: ClassVar[int] = 8
    defense: ClassVar[int] = 2
    move: ClassVar[int] = 4
    cost: ClassVar[int] = 600
    vision_range: ClassVar[int] = 3
    attack_range: ClassVar[tuple[int, int]] = (3, 5)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"longship", "harbor"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        on_terrain("sea"),
    )
    display_letter: ClassVar[str] = "w"
