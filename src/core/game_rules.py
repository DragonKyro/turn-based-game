"""Single entry point for mutating GameState: apply_action(state, action) -> list[Event].

Events are small dicts describing what happened, consumed by the UI (combat popups, victory banner, etc.).
"""
from __future__ import annotations

from src.core.actions import (
    Action,
    ActivateUltimateAction,
    AttackAction,
    BuildAction,
    CaptureAction,
    EndTurnAction,
    MoveAction,
)
from src.core.combat import resolve_attack
from src.core.economy import can_afford, can_place_unit_at
from src.core.fog import recompute_visibility
from src.core.game_state import GameState, VictoryResult
from src.core.pathfinding import attackable_from, reachable
from src.core.turn_manager import end_turn
from src.entities.buildings import BUILDING_REGISTRY
from src.entities.heroes import HERO_REGISTRY
from src.entities.hero import Hero
from src.entities.units import UNIT_REGISTRY


class IllegalAction(ValueError):
    """Raised when an Action violates game rules. Contains a short human-readable reason."""


Event = dict


def apply_action(state: GameState, action: Action) -> list[Event]:
    if isinstance(action, MoveAction):
        return _apply_move(state, action)
    if isinstance(action, AttackAction):
        return _apply_attack(state, action)
    if isinstance(action, CaptureAction):
        return _apply_capture(state, action)
    if isinstance(action, BuildAction):
        return _apply_build(state, action)
    if isinstance(action, ActivateUltimateAction):
        return _apply_ultimate(state, action)
    if isinstance(action, EndTurnAction):
        report = end_turn(state)
        return [{"type": "end_turn", **report}]
    raise IllegalAction(f"Unknown action type: {action!r}")


# --- individual handlers ---

def _apply_move(state: GameState, a: MoveAction) -> list[Event]:
    u = state.units.get(a.unit_id)
    if u is None or not u.is_alive:
        raise IllegalAction(f"Unit {a.unit_id} not found or dead")
    if u.owner_id != state.current_player_id:
        raise IllegalAction("Cannot move an opponent's unit")
    if u.has_moved:
        raise IllegalAction(f"{u.kind} has already moved this turn")
    if a.destination == u.coord:
        u.has_moved = True  # "wait" in place
        return [{"type": "move", "unit_id": u.id, "from": u.coord, "to": u.coord}]

    reach = reachable(state, u)
    if a.destination not in reach:
        raise IllegalAction(f"Destination {a.destination} not in reachable set")

    # update tile occupancy
    state.map.tile(u.coord).unit_id = None
    state.map.tile(a.destination).unit_id = u.id
    old = u.coord
    u.coord = a.destination
    u.has_moved = True

    # refresh fog for the owner since we scouted new tiles
    recompute_visibility(state, u.owner_id)

    return [{"type": "move", "unit_id": u.id, "from": old, "to": a.destination}]


def _apply_attack(state: GameState, a: AttackAction) -> list[Event]:
    attacker = state.units.get(a.unit_id)
    defender = state.units.get(a.target_unit_id)
    if attacker is None or not attacker.is_alive:
        raise IllegalAction("Attacker not found")
    if defender is None or not defender.is_alive:
        raise IllegalAction("Defender not found")
    if attacker.owner_id != state.current_player_id:
        raise IllegalAction("Cannot attack with opponent's unit")
    if attacker.has_acted:
        raise IllegalAction(f"{attacker.kind} has already acted this turn")
    if defender.owner_id == attacker.owner_id:
        raise IllegalAction("Cannot attack own unit")
    reachable_targets = attackable_from(state, attacker, attacker.coord)
    if defender.coord not in reachable_targets:
        raise IllegalAction(f"Target at {defender.coord} not in attack range")

    result = resolve_attack(state, attacker.id, defender.id)
    events: list[Event] = [{"type": "attack", "result": result}]

    for unit in (attacker, defender):
        if not unit.is_alive:
            state.map.tile(unit.coord).unit_id = None
            events.append({"type": "unit_destroyed", "unit_id": unit.id})

    attacker.has_moved = True
    attacker.has_acted = True

    events.extend(_check_victory(state))
    return events


def _apply_capture(state: GameState, a: CaptureAction) -> list[Event]:
    u = state.units.get(a.unit_id)
    b = state.buildings.get(a.building_id)
    if u is None or not u.is_alive:
        raise IllegalAction("Capturing unit not found")
    if b is None:
        raise IllegalAction("Building not found")
    if u.owner_id != state.current_player_id:
        raise IllegalAction("Not your unit")
    if u.coord != b.coord:
        raise IllegalAction("Unit must stand on the building to capture")
    if u.kind != "infantry":
        raise IllegalAction("Only infantry can capture")
    if b.owner_id == u.owner_id:
        raise IllegalAction("Already owned by this player")
    if u.has_acted:
        raise IllegalAction("Unit has already acted this turn")

    b.capture_progress += u.hp  # capture faster with full HP
    u.has_moved = True
    u.has_acted = True

    events: list[Event] = [
        {"type": "capture_progress", "building_id": b.id,
         "progress": b.capture_progress, "threshold": type(b).capture_threshold}
    ]
    if b.capture_progress >= type(b).capture_threshold:
        b.owner_id = u.owner_id
        b.capture_progress = 0
        events.append({"type": "building_captured", "building_id": b.id, "new_owner_id": u.owner_id})
        events.extend(_check_victory(state))

    # capturing the tile reveals new area for the new owner
    recompute_visibility(state, u.owner_id)
    return events


def _apply_build(state: GameState, a: BuildAction) -> list[Event]:
    b = state.buildings.get(a.building_id)
    if b is None:
        raise IllegalAction("Building not found")
    if b.owner_id != state.current_player_id:
        raise IllegalAction("Not your building")
    if not type(b).produces_kinds:
        raise IllegalAction(f"{b.kind} does not produce units")
    if not b.can_produce(a.unit_kind):
        raise IllegalAction(f"{b.kind} cannot produce {a.unit_kind}")
    if not can_place_unit_at(state, b.coord):
        raise IllegalAction("Building tile is occupied")

    # Heroes are not buyable; only UNIT_REGISTRY kinds.
    unit_cls = UNIT_REGISTRY.get(a.unit_kind)
    if unit_cls is None:
        if a.unit_kind in HERO_REGISTRY:
            raise IllegalAction("Heroes cannot be produced")
        raise IllegalAction(f"Unknown unit kind {a.unit_kind!r}")
    cost = unit_cls.cost
    if not can_afford(state, b.owner_id, cost):
        raise IllegalAction(f"Not enough gold for {a.unit_kind} (need {cost})")

    new_id = state.allocate_id()
    unit = unit_cls(id=new_id, owner_id=b.owner_id, coord=b.coord, hp=unit_cls.max_hp)
    unit.has_moved = True  # freshly built units cannot move/act this turn
    unit.has_acted = True
    state.units[new_id] = unit
    state.map.tile(b.coord).unit_id = new_id
    state.players[b.owner_id].gold -= cost

    recompute_visibility(state, b.owner_id)
    return [{"type": "unit_built", "unit_id": new_id, "kind": a.unit_kind, "coord": b.coord}]


def _apply_ultimate(state: GameState, a: ActivateUltimateAction) -> list[Event]:
    h = state.units.get(a.hero_id)
    if not isinstance(h, Hero):
        raise IllegalAction("Target is not a hero")
    if h.owner_id != state.current_player_id:
        raise IllegalAction("Not your hero")
    if h.has_acted:
        raise IllegalAction("Hero has already acted this turn")
    if not h.can_activate_ultimate():
        raise IllegalAction("Ultimate not ready")

    effects = h.activate_ultimate(state)
    events: list[Event] = [{"type": "ultimate", "hero_id": h.id, "effects": effects}]

    # Clean up any units dropped to 0 HP by the ultimate
    for u in list(state.units.values()):
        if not u.is_alive and state.map.tile(u.coord).unit_id == u.id:
            state.map.tile(u.coord).unit_id = None
            events.append({"type": "unit_destroyed", "unit_id": u.id})

    events.extend(_check_victory(state))
    return events


# --- victory detection ---

def _check_victory(state: GameState) -> list[Event]:
    if state.victory is not None:
        return []

    # rout: any player with no living units loses
    for pid, p in state.players.items():
        living = any(True for _ in state.units_of(pid))
        if not living:
            others = [o for o in state.players if o != pid]
            if others:
                state.victory = VictoryResult(winner_id=others[0], reason="rout")
                return [{"type": "victory", "winner_id": others[0], "reason": "rout"}]

    # capture_strongholds: a player loses when they no longer own any HQ
    hq_owners = {
        b.owner_id for b in state.buildings.values()
        if type(b).is_hq and b.owner_id is not None
    }
    living_with_hq = [pid for pid in state.players if pid in hq_owners]
    if len(living_with_hq) == 1 and len(state.players) > 1:
        state.victory = VictoryResult(winner_id=living_with_hq[0], reason="capture_strongholds")
        return [{"type": "victory", "winner_id": living_with_hq[0], "reason": "capture_strongholds"}]

    _ = BUILDING_REGISTRY  # silence unused import when BUILDING_REGISTRY isn't referenced here
    return []
