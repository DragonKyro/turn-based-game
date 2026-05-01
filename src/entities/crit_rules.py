"""Reusable crit predicates. Attach tuples of these to a Unit subclass's `positional_crit_conditions`.

Each predicate takes (attacker, state) and returns True when the crit condition is met.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.coord import manhattan

if TYPE_CHECKING:
    from src.core.game_state import GameState
    from src.entities.unit import Unit


def adjacent_to_commander(attacker: "Unit", state: "GameState") -> bool:
    """Crit when the attacker is adjacent (distance 1) to their own hero."""
    hero_id = state.players[attacker.owner_id].hero_id
    if hero_id is None:
        return False
    hero = state.units.get(hero_id)
    if hero is None:
        return False
    return manhattan(attacker.coord, hero.coord) == 1


def on_terrain(*names: str):
    """Crit when the attacker stands on one of the named terrain types."""
    name_set = frozenset(names)

    def _pred(attacker: "Unit", state: "GameState") -> bool:
        tile = state.map.tile(attacker.coord)
        return tile.terrain.name in name_set

    return _pred


def hp_above(threshold_ratio: float):
    """Crit when the attacker's HP ratio is above `threshold_ratio` (0..1)."""

    def _pred(attacker: "Unit", _state: "GameState") -> bool:
        return attacker.hp_ratio > threshold_ratio

    return _pred
