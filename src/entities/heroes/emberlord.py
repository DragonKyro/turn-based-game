"""Emberlord — Emberdyne's champion. Ultimate: burn all enemies within 2 tiles for 3 damage."""
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from src.core.coord import manhattan
from src.core.types import UnitClass
from src.entities.crit_rules import adjacent_to_commander
from src.entities.hero import Hero
from src.entities.unit import CritPredicate

if TYPE_CHECKING:
    from src.core.game_state import GameState

_ULTIMATE_RADIUS = 2
_ULTIMATE_DAMAGE = 3


class Emberlord(Hero):
    kind: ClassVar[str] = "emberlord"
    unit_class: ClassVar[UnitClass] = UnitClass.LAND
    max_hp: ClassVar[int] = 14
    attack: ClassVar[int] = 7
    defense: ClassVar[int] = 2
    move: ClassVar[int] = 3
    cost: ClassVar[int] = 0  # heroes aren't bought
    vision_range: ClassVar[int] = 3
    attack_range: ClassVar[tuple[int, int]] = (1, 1)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset()
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        adjacent_to_commander,  # no-op for the hero themself, harmless
    )
    display_letter: ClassVar[str] = "E"

    def activate_ultimate(self, state: "GameState") -> list[dict]:
        effects: list[dict] = []
        for unit in list(state.units.values()):
            if unit.owner_id == self.owner_id:
                continue
            if manhattan(unit.coord, self.coord) <= _ULTIMATE_RADIUS:
                unit.hp = max(0, unit.hp - _ULTIMATE_DAMAGE)
                effects.append({"type": "damage", "unit_id": unit.id, "amount": _ULTIMATE_DAMAGE})
        self.ultimate_charge = 0
        self.has_moved = True
        self.has_acted = True
        return effects
