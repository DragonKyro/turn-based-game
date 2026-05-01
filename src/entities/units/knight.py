"""Knight: mounted vehicle unit. Strong vs Longships on the coast."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import hp_above, on_terrain
from src.entities.unit import CritPredicate, Unit


class Knight(Unit):
    kind: ClassVar[str] = "knight"
    unit_class: ClassVar[UnitClass] = UnitClass.VEHICLE
    max_hp: ClassVar[int] = 12
    attack: ClassVar[int] = 7
    defense: ClassVar[int] = 2
    move: ClassVar[int] = 5
    cost: ClassVar[int] = 300
    vision_range: ClassVar[int] = 2
    attack_range: ClassVar[tuple[int, int]] = (1, 1)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"longship"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        on_terrain("plains", "road"),  # cavalry charge on open ground
        hp_above(0.75),
    )
    display_letter: ClassVar[str] = "K"
