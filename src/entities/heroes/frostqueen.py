"""Frostqueen — Frostmoor's champion. Ultimate: restore full HP to all allies within 2 tiles."""
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from src.core.coord import manhattan
from src.core.types import UnitClass
from src.entities.crit_rules import hp_above
from src.entities.hero import Hero
from src.entities.unit import CritPredicate

if TYPE_CHECKING:
    from src.core.game_state import GameState

_ULTIMATE_RADIUS = 2


class Frostqueen(Hero):
    kind: ClassVar[str] = "frostqueen"
    unit_class: ClassVar[UnitClass] = UnitClass.LAND
    max_hp: ClassVar[int] = 13
    attack: ClassVar[int] = 6
    defense: ClassVar[int] = 2
    move: ClassVar[int] = 3
    cost: ClassVar[int] = 0
    vision_range: ClassVar[int] = 3
    attack_range: ClassVar[tuple[int, int]] = (1, 2)  # slight ranged poke
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset()
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        hp_above(0.9),
    )
    display_letter: ClassVar[str] = "F"

    def activate_ultimate(self, state: "GameState") -> list[dict]:
        effects: list[dict] = []
        for unit in state.units.values():
            if unit.owner_id != self.owner_id:
                continue
            if manhattan(unit.coord, self.coord) <= _ULTIMATE_RADIUS and unit.hp < unit.max_hp:
                healed = unit.max_hp - unit.hp
                unit.hp = unit.max_hp
                effects.append({"type": "heal", "unit_id": unit.id, "amount": healed})
        self.ultimate_charge = 0
        self.has_moved = True
        self.has_acted = True
        return effects
