"""Minimal "move and poke" AI for the second player.

Strategy, per unit (in deterministic id order):
    1. If a target is in attack range from the current coord, attack it.
    2. Otherwise compute the reachable set. Choose the reachable tile with the smallest
       manhattan distance to the nearest enemy. Move there.
    3. If after moving an enemy is in attack range, attack.
    4. If the unit stands on a capturable enemy building and it's an infantry, capture.

After all units act, spend gold on affordable units from owned production buildings (cheapest
first, prefer building toward the enemy HQ direction via tile choice), then end turn.

This is intentionally dumb. It plays the game loop end-to-end — it does not play well.
"""
from __future__ import annotations

from src.core.actions import AttackAction, BuildAction, CaptureAction, EndTurnAction, MoveAction
from src.core.coord import manhattan
from src.core.game_rules import IllegalAction, apply_action
from src.core.game_state import GameState
from src.core.pathfinding import attackable_from, reachable
from src.entities.unit import Unit
from src.entities.units import UNIT_REGISTRY


def take_turn(state: GameState) -> list[dict]:
    """Play out the current AI player's entire turn and end it. Returns accumulated events."""
    ai_id = state.current_player_id
    events: list[dict] = []

    # Act with each unit we own, in id order.
    for uid in sorted(uid for uid, u in state.units.items() if u.owner_id == ai_id and u.is_alive):
        unit = state.units.get(uid)
        if unit is None or not unit.is_alive or unit.has_acted:
            continue
        events += _unit_take_turn(state, unit)

    # Then try to buy things. Cheap units first.
    events += _ai_production(state, ai_id)

    # Always end the turn.
    try:
        events += apply_action(state, EndTurnAction())
    except IllegalAction:
        pass
    return events


def _unit_take_turn(state: GameState, unit: Unit) -> list[dict]:
    events: list[dict] = []
    ai_id = unit.owner_id

    # Target: nearest enemy.
    enemies = [u for u in state.units.values() if u.is_alive and u.owner_id != ai_id]
    if not enemies:
        # No enemies left to shoot. Try capturing instead.
        events += _maybe_capture(state, unit)
        return events

    target = min(enemies, key=lambda e: manhattan(unit.coord, e.coord))

    # 1. Attack from current position if possible.
    if not unit.has_acted:
        atk_set = attackable_from(state, unit, unit.coord)
        if target.coord in atk_set and target.owner_id != ai_id:
            try:
                events += apply_action(state, AttackAction(unit_id=unit.id, target_unit_id=target.id))
                return events
            except IllegalAction:
                pass

    # 2. Move toward the target if we haven't moved.
    if not unit.has_moved:
        reach = reachable(state, unit)
        if reach:
            # Prefer destinations from which we can attack the target this turn.
            attackable_destinations = [
                (c, cost) for c, cost in reach.items()
                if target.coord in attackable_from(state, unit, c)
            ]
            if attackable_destinations:
                # Among those, closest by cost (arrive with most HP / cheapest).
                dest = min(attackable_destinations, key=lambda p: p[1])[0]
            else:
                # Just step toward the target.
                dest = min(reach.keys(), key=lambda c: manhattan(c, target.coord))
            try:
                events += apply_action(state, MoveAction(unit_id=unit.id, destination=dest))
            except IllegalAction:
                pass

    # 3. If we can now attack, do.
    if not unit.has_acted and unit.is_alive:
        atk_set = attackable_from(state, unit, unit.coord)
        if target.coord in atk_set and target.is_alive:
            try:
                events += apply_action(state, AttackAction(unit_id=unit.id, target_unit_id=target.id))
            except IllegalAction:
                pass

    # 4. Try capture if we ended on an enemy building.
    events += _maybe_capture(state, unit)
    return events


def _maybe_capture(state: GameState, unit: Unit) -> list[dict]:
    if unit.kind != "infantry" or unit.has_acted:
        return []
    b = state.building_at(unit.coord)
    if b is None or b.owner_id == unit.owner_id:
        return []
    try:
        return apply_action(state, CaptureAction(unit_id=unit.id, building_id=b.id))
    except IllegalAction:
        return []


def _ai_production(state: GameState, ai_id: int) -> list[dict]:
    """Spend gold on cheap units from owned production buildings until we can't afford any."""
    events: list[dict] = []
    # Try each building; for each, pick the cheapest producible kind we can afford.
    # Repeat until no progress is made (each building can only spawn once per turn since the
    # tile gets occupied by the new unit).
    for b in list(state.buildings.values()):
        if b.owner_id != ai_id or not type(b).produces_kinds or b.has_produced:
            continue
        gold = state.players[ai_id].gold
        affordable = [
            (k, UNIT_REGISTRY[k].cost)
            for k in type(b).produces_kinds
            if k in UNIT_REGISTRY and UNIT_REGISTRY[k].cost <= gold
        ]
        if not affordable:
            continue
        # Pick cheapest.
        kind = min(affordable, key=lambda p: p[1])[0]
        try:
            events += apply_action(state, BuildAction(building_id=b.id, unit_kind=kind))
        except IllegalAction:
            continue
    return events
