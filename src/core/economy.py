"""Income ticks and production-purchase validation."""
from __future__ import annotations

from src.core.game_state import GameState
from src.core.types import Coord


def award_income(state: GameState, player_id: int) -> int:
    """Add gold from every owned income-generating building. Returns total awarded."""
    total = 0
    for b in state.buildings.values():
        if b.owner_id != player_id:
            continue
        gold = type(b).gold_per_turn
        if gold > 0:
            total += gold
    state.players[player_id].gold += total
    return total


def can_afford(state: GameState, player_id: int, cost: int) -> bool:
    return state.players[player_id].gold >= cost


def can_place_unit_at(state: GameState, coord: Coord) -> bool:
    """A tile is eligible to spawn a new unit if it is in bounds and has no living unit on it."""
    if not state.map.in_bounds(coord):
        return False
    tile = state.map.tile(coord)
    if tile.unit_id is None:
        return True
    occupant = state.units.get(tile.unit_id)
    return occupant is None or not occupant.is_alive
