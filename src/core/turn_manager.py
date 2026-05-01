"""Turn rotation: resets per-unit flags, rotates current_player, awards income, bumps turn count."""
from __future__ import annotations

from src.core.economy import award_income
from src.core.fog import recompute_visibility
from src.core.game_state import GameState


def end_turn(state: GameState) -> dict:
    """Advance to the next player's turn. Returns a small report for the UI."""
    current = state.current_player_id

    # clear flags on *previous* player's units (the one that just finished)
    for u in state.units_of(current):
        u.has_moved = False
        u.has_acted = False

    # rotate to next player
    player_ids = sorted(state.players.keys())
    idx = player_ids.index(current)
    next_id = player_ids[(idx + 1) % len(player_ids)]
    wrapped = (idx + 1) == len(player_ids)
    if wrapped:
        state.turn_number += 1
    state.current_player_id = next_id

    # income for the incoming player
    gained = award_income(state, next_id)

    # clear the incoming player's stale action flags too (defensive — usually already clean)
    for u in state.units_of(next_id):
        u.has_moved = False
        u.has_acted = False

    # refresh fog for the incoming player
    recompute_visibility(state, next_id)

    return {
        "previous_player": current,
        "current_player": next_id,
        "turn_number": state.turn_number,
        "income_awarded": gained,
    }
