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

from src.core.actions import AttackAction, BuildAction, EndTurnAction, MoveAction
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

    # Candidate targets: enemy units + enemy/neutral buildings.
    enemies = [u for u in state.units.values() if u.is_alive and u.owner_id != ai_id]
    hostile_buildings = [b for b in state.buildings.values() if b.owner_id != ai_id]

    target_coord, target_action = _pick_target(unit, enemies, hostile_buildings)
    if target_coord is None:
        return events

    # 1. Attack from current position if possible.
    if not unit.has_acted:
        atk_set = attackable_from(state, unit, unit.coord)
        if target_coord in atk_set:
            try:
                events += apply_action(state, target_action(unit.id))
                return events
            except IllegalAction:
                pass

    # 2. Move toward the target if we haven't moved.
    if not unit.has_moved:
        reach = reachable(state, unit)
        if reach:
            attackable_destinations = [
                (c, cost) for c, cost in reach.items()
                if target_coord in attackable_from(state, unit, c)
            ]
            if attackable_destinations:
                dest = min(attackable_destinations, key=lambda p: p[1])[0]
            else:
                dest = min(reach.keys(), key=lambda c: manhattan(c, target_coord))
            try:
                events += apply_action(state, MoveAction(unit_id=unit.id, destination=dest))
            except IllegalAction:
                pass

    # 3. If we can now attack, do.
    if not unit.has_acted and unit.is_alive:
        atk_set = attackable_from(state, unit, unit.coord)
        if target_coord in atk_set:
            try:
                events += apply_action(state, target_action(unit.id))
            except IllegalAction:
                pass

    return events


def _pick_target(unit: Unit, enemies: list, hostile_buildings: list):
    """Pick a target coord + the action factory to attack it.

    Prefers the nearest enemy unit; falls back to the nearest hostile building if no
    enemy units are visible. Returns (coord_or_None, factory)."""
    nearest_unit = min(enemies, key=lambda e: manhattan(unit.coord, e.coord)) if enemies else None
    nearest_bld = min(hostile_buildings, key=lambda b: manhattan(unit.coord, b.coord)) if hostile_buildings else None

    if nearest_unit is not None and nearest_bld is not None:
        if manhattan(unit.coord, nearest_unit.coord) <= manhattan(unit.coord, nearest_bld.coord) + 2:
            return nearest_unit.coord, (lambda uid: AttackAction(unit_id=uid, target_unit_id=nearest_unit.id))
        return nearest_bld.coord, (lambda uid: AttackAction(unit_id=uid, target_building_id=nearest_bld.id))
    if nearest_unit is not None:
        return nearest_unit.coord, (lambda uid: AttackAction(unit_id=uid, target_unit_id=nearest_unit.id))
    if nearest_bld is not None:
        return nearest_bld.coord, (lambda uid: AttackAction(unit_id=uid, target_building_id=nearest_bld.id))
    return None, None


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
