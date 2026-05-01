"""Single entry point for mutating GameState: apply_action(state, action) -> list[Event].

Events are small dicts describing what happened, consumed by the UI (combat popups, victory banner, etc.).
"""
from __future__ import annotations

from src.core.actions import (
    Action,
    ActivateUltimateAction,
    AttackAction,
    BuildAction,
    EndTurnAction,
    MoveAction,
)
from src.core.combat import resolve_attack
from src.core.economy import can_afford
from src.core.fog import recompute_visibility
from src.core.game_state import GameState, VictoryResult
from src.core.pathfinding import attackable_from, path_to, reachable
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

    # Capture the path BEFORE mutating state so the UI can animate the move.
    path = path_to(state, u, a.destination)

    # update tile occupancy
    state.map.tile(u.coord).unit_id = None
    state.map.tile(a.destination).unit_id = u.id
    old = u.coord
    u.coord = a.destination
    u.has_moved = True

    # refresh fog for the owner since we scouted new tiles
    recompute_visibility(state, u.owner_id)

    return [{"type": "move", "unit_id": u.id, "from": old, "to": a.destination,
             "path": path}]


def _apply_attack(state: GameState, a: AttackAction) -> list[Event]:
    attacker = state.units.get(a.unit_id)
    if attacker is None or not attacker.is_alive:
        raise IllegalAction("Attacker not found")
    if attacker.owner_id != state.current_player_id:
        raise IllegalAction("Cannot attack with opponent's unit")
    if attacker.has_acted:
        raise IllegalAction(f"{attacker.kind} has already acted this turn")

    if (a.target_unit_id is None) == (a.target_building_id is None):
        raise IllegalAction("Attack must target exactly one of unit or building")

    if a.target_unit_id is not None:
        return _attack_unit(state, attacker, a.target_unit_id)
    return _attack_building(state, attacker, a.target_building_id)


def _attack_unit(state: GameState, attacker, target_unit_id: int) -> list[Event]:
    defender = state.units.get(target_unit_id)
    if defender is None or not defender.is_alive:
        raise IllegalAction("Defender not found")
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


def _attack_building(state: GameState, attacker, target_building_id: int) -> list[Event]:
    """Wargroove-style capture: attack the building to reduce its HP. At 0 HP ownership
    flips to the attacker and HP resets to max. Buildings never counter-attack."""
    b = state.buildings.get(target_building_id)
    if b is None:
        raise IllegalAction("Target building not found")
    if b.owner_id == attacker.owner_id:
        raise IllegalAction("Cannot attack your own building")

    reachable_targets = attackable_from(state, attacker, attacker.coord)
    if b.coord not in reachable_targets:
        raise IllegalAction(f"Building at {b.coord} not in attack range")

    # Buildings take attacker.attack damage scaled by the attacker's HP ratio.
    raw = max(1, int(round(type(attacker).attack * attacker.hp_ratio)))
    b.hp = max(0, b.hp - raw)

    events: list[Event] = [{
        "type": "building_attacked",
        "building_id": b.id,
        "damage": raw,
        "building_hp": b.hp,
        "building_max_hp": type(b).max_hp,
    }]

    attacker.has_moved = True
    attacker.has_acted = True

    if b.hp == 0:
        prev_owner = b.owner_id
        b.owner_id = attacker.owner_id
        b.hp = type(b).max_hp
        b.has_produced = True   # freshly flipped — can't produce the same turn
        events.append({
            "type": "building_captured",
            "building_id": b.id,
            "new_owner_id": attacker.owner_id,
            "previous_owner_id": prev_owner,
        })
        # The new owner may have gained vision (HQs/mines have vision_range).
        recompute_visibility(state, attacker.owner_id)
        events.extend(_check_victory(state))

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
    if b.has_produced:
        raise IllegalAction(f"{b.kind} has already produced a unit this turn")

    # Heroes are not buyable; only UNIT_REGISTRY kinds.
    unit_cls = UNIT_REGISTRY.get(a.unit_kind)
    if unit_cls is None:
        if a.unit_kind in HERO_REGISTRY:
            raise IllegalAction("Heroes cannot be produced")
        raise IllegalAction(f"Unknown unit kind {a.unit_kind!r}")
    cost = unit_cls.cost
    if not can_afford(state, b.owner_id, cost):
        raise IllegalAction(f"Not enough gold for {a.unit_kind} (need {cost})")

    # Spawn on an adjacent passable empty tile (Wargroove-style). The UI can
    # request a specific neighbor via `a.spawn_coord`; we validate it's in the
    # allowed set. Without a hint we pick the first valid neighbor.
    spawn_candidates = valid_spawn_tiles(state, b.coord, unit_cls.unit_class)
    if a.spawn_coord is not None:
        if a.spawn_coord not in spawn_candidates:
            raise IllegalAction(
                f"Spawn tile {a.spawn_coord} is not a valid adjacent deploy tile"
            )
        spawn_coord = a.spawn_coord
    elif spawn_candidates:
        spawn_coord = spawn_candidates[0]
    else:
        raise IllegalAction(f"No open adjacent tile for {a.unit_kind} to deploy")

    new_id = state.allocate_id()
    unit = unit_cls(id=new_id, owner_id=b.owner_id, coord=spawn_coord, hp=unit_cls.max_hp)
    unit.has_moved = True   # freshly built units cannot move/act this turn
    unit.has_acted = True
    state.units[new_id] = unit
    state.map.tile(spawn_coord).unit_id = new_id
    state.players[b.owner_id].gold -= cost
    b.has_produced = True

    recompute_visibility(state, b.owner_id)
    return [{"type": "unit_built", "unit_id": new_id, "kind": a.unit_kind, "coord": spawn_coord}]


def valid_spawn_tiles(state: GameState, origin, unit_class) -> list[tuple[int, int]]:
    """All 4-adjacent tiles where a unit of `unit_class` could deploy from `origin`.

    Order (N, E, S, W) is stable so the UI can present them in a consistent layout.
    Diagonals are appended as a last-resort fallback used only when the cardinals are all
    blocked (so `valid_spawn_tiles(...)[0]` stays sensible)."""
    col, row = origin
    cardinals: list[tuple[int, int]] = []
    diagonals: list[tuple[int, int]] = []
    for dc, dr in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        c = (col + dc, row + dr)
        if _valid_spawn(state, c, unit_class):
            cardinals.append(c)
    if not cardinals:
        for dc, dr in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
            c = (col + dc, row + dr)
            if _valid_spawn(state, c, unit_class):
                diagonals.append(c)
    return cardinals + diagonals


def _valid_spawn(state: GameState, c, unit_class) -> bool:
    if not state.map.in_bounds(c):
        return False
    tile = state.map.tile(c)
    if not tile.terrain.passable_for(unit_class):
        return False
    occupant = state.units.get(tile.unit_id) if tile.unit_id is not None else None
    return occupant is None or not occupant.is_alive


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
