"""Predict damage without mutating state. Shown near the cursor when hovering an attackable enemy."""
from __future__ import annotations

from copy import deepcopy

from src.core.combat import CombatResult, resolve_attack
from src.core.game_state import GameState


def predict(state: GameState, attacker_id: int, defender_id: int) -> CombatResult:
    """Run resolve_attack against a deep copy of state so the live game is unaffected."""
    snapshot = deepcopy(state)
    return resolve_attack(snapshot, attacker_id, defender_id)
