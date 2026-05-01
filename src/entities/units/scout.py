"""Scout: fast, far-seeing, fragile light vehicle. Use to harass and reveal the map."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import hp_above, on_terrain
from src.entities.unit import CritPredicate, Unit


class Scout(Unit):
    kind: ClassVar[str] = "scout"
    unit_class: ClassVar[UnitClass] = UnitClass.VEHICLE
    max_hp: ClassVar[int] = 7
    attack: ClassVar[int] = 3
    defense: ClassVar[int] = 0
    move: ClassVar[int] = 7
    cost: ClassVar[int] = 180
    vision_range: ClassVar[int] = 5
    attack_range: ClassVar[tuple[int, int]] = (1, 1)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"archer"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        on_terrain("plains", "road"),
        hp_above(0.8),
    )
    display_letter: ClassVar[str] = "s"
