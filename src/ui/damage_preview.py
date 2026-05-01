"""Predict damage without mutating state. Shown near the cursor when hovering an attackable enemy."""
from __future__ import annotations

from copy import deepcopy

from src.core.combat import CombatResult, predict_attack
from src.core.game_state import GameState


def predict(state: GameState, attacker_id: int, defender_id: int) -> CombatResult:
    """Return a non-mutating CombatResult prediction on a state snapshot."""
    snapshot = deepcopy(state)
    return predict_attack(snapshot, attacker_id, defender_id)


def format_range(result: CombatResult) -> str:
    """Format the predicted damage as a readable range, e.g. '5–7' or '5–7 / cnt 1–2'."""
    a = result.attack
    main = _fmt(a.damage_min, a.damage_max)
    if result.counter is None:
        return main
    c = result.counter
    return f"{main} / cnt {_fmt(c.damage_min, c.damage_max)}"


def _fmt(lo: int, hi: int) -> str:
    return f"{lo}" if lo == hi else f"{lo}–{hi}"
