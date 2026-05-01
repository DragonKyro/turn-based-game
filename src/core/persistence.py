"""Save / load the full GameState to JSON.

Format is separate from the level JSON — it captures *runtime* state: every unit's current
HP and flags, every building's ownership + capture progress, per-player gold + visibility,
turn number, current player, and any victory result. Terrain and map dimensions go in too
so a save file is self-contained (no dependency on the original level file).

On load, entities are reconstructed via the UNIT_REGISTRY / HERO_REGISTRY / BUILDING_REGISTRY
and TERRAIN_REGISTRY lookup by `kind` string. Unknown kinds raise SaveLoadError.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.game_state import GameState, VictoryResult
from src.core.player import Player
from src.core.types import Coord, VisState
from src.entities.buildings import BUILDING_REGISTRY
from src.entities.hero import Hero
from src.entities.heroes import HERO_REGISTRY
from src.entities.units import UNIT_REGISTRY
from src.world.map import Map
from src.world.terrain_types import TERRAIN_REGISTRY
from src.world.tile import Tile

SAVE_FORMAT_VERSION = 1


class SaveLoadError(RuntimeError):
    pass


# --- Save ------------------------------------------------------------------

def save_to_path(state: GameState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_serialize(state), f, indent=2)


def _serialize(state: GameState) -> dict[str, Any]:
    m = state.map
    return {
        "version": SAVE_FORMAT_VERSION,
        "turn_number": state.turn_number,
        "current_player_id": state.current_player_id,
        "next_entity_id": state.next_entity_id,
        "victory": _serialize_victory(state.victory),
        "map": {
            "width": m.width,
            "height": m.height,
            "terrain": [
                [m.tile((col, row)).terrain.name for col in range(m.width)]
                for row in range(m.height)
            ],
        },
        "players": [_serialize_player(p) for p in state.players.values()],
        "units": [_serialize_unit(u) for u in state.units.values()],
        "buildings": [_serialize_building(b) for b in state.buildings.values()],
    }


def _serialize_victory(v: VictoryResult | None) -> dict | None:
    return None if v is None else {"winner_id": v.winner_id, "reason": v.reason}


def _serialize_player(p: Player) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "faction": p.faction,
        "gold": p.gold,
        "hero_id": p.hero_id,
        "is_ai": p.is_ai,
        # visibility: VisState enum values encoded by name so the file is human-readable.
        "visibility": [[vs.name for vs in col] for col in p.visibility],
    }


def _serialize_unit(u: Any) -> dict[str, Any]:
    payload = {
        "id": u.id,
        "kind": u.kind,
        "owner": u.owner_id,
        "coord": list(u.coord),
        "hp": u.hp,
        "has_moved": u.has_moved,
        "has_acted": u.has_acted,
    }
    if isinstance(u, Hero):
        payload["ultimate_charge"] = u.ultimate_charge
    return payload


def _serialize_building(b: Any) -> dict[str, Any]:
    return {
        "id": b.id,
        "kind": b.kind,
        "owner": b.owner_id,
        "coord": list(b.coord),
        "hp": b.hp,
        "has_produced": b.has_produced,
    }


# --- Load ------------------------------------------------------------------

def load_from_path(path: Path) -> GameState:
    if not path.exists():
        raise SaveLoadError(f"Save file not found: {path}")
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return _deserialize(raw, source=str(path))


def _deserialize(raw: dict[str, Any], source: str) -> GameState:
    version = raw.get("version")
    if version != SAVE_FORMAT_VERSION:
        raise SaveLoadError(
            f"{source}: unsupported save version {version!r} "
            f"(expected {SAVE_FORMAT_VERSION})"
        )

    # Map
    md = raw["map"]
    m = Map(width=md["width"], height=md["height"])
    terrain_rows = md["terrain"]
    for row_idx, row in enumerate(terrain_rows):
        for col_idx, t_name in enumerate(row):
            terrain = TERRAIN_REGISTRY.get(t_name)
            if terrain is None:
                raise SaveLoadError(f"{source}: unknown terrain {t_name!r}")
            m.tiles[(col_idx, row_idx)] = Tile(terrain=terrain)

    # Players
    players: dict[int, Player] = {}
    for pd in raw["players"]:
        p = Player(
            id=int(pd["id"]),
            name=pd["name"],
            faction=pd["faction"],
            gold=int(pd["gold"]),
            hero_id=pd.get("hero_id"),
            is_ai=bool(pd.get("is_ai", False)),
        )
        # Restore visibility grid.
        vis_enc = pd.get("visibility", [])
        if vis_enc:
            p.visibility = [
                [VisState[name] for name in col] for col in vis_enc
            ]
        else:
            p.init_visibility(m.width, m.height)
        players[p.id] = p

    # Buildings
    buildings = {}
    for bd in raw["buildings"]:
        cls = BUILDING_REGISTRY.get(bd["kind"])
        if cls is None:
            raise SaveLoadError(f"{source}: unknown building kind {bd['kind']!r}")
        coord: Coord = tuple(bd["coord"])  # type: ignore[assignment]
        b = cls(
            id=int(bd["id"]),
            coord=coord,
            owner_id=bd.get("owner"),
            # Accept either the new 'hp' key or fall back to max_hp for legacy saves.
            hp=int(bd.get("hp", cls.max_hp)),
            has_produced=bool(bd.get("has_produced", False)),
        )
        buildings[b.id] = b
        m.tiles[coord].building_id = b.id

    # Units
    units = {}
    for ud in raw["units"]:
        kind = ud["kind"]
        cls = UNIT_REGISTRY.get(kind) or HERO_REGISTRY.get(kind)
        if cls is None:
            raise SaveLoadError(f"{source}: unknown unit kind {kind!r}")
        coord = tuple(ud["coord"])
        kwargs = dict(
            id=int(ud["id"]),
            owner_id=int(ud["owner"]),
            coord=coord,
            hp=int(ud["hp"]),
            has_moved=bool(ud.get("has_moved", False)),
            has_acted=bool(ud.get("has_acted", False)),
        )
        if kind in HERO_REGISTRY:
            kwargs["ultimate_charge"] = int(ud.get("ultimate_charge", 0))
        u = cls(**kwargs)
        units[u.id] = u
        m.tiles[coord].unit_id = u.id

    victory = None
    v = raw.get("victory")
    if v:
        victory = VictoryResult(winner_id=int(v["winner_id"]), reason=v["reason"])

    state = GameState(
        map=m,
        players=players,
        units=units,
        buildings=buildings,
        current_player_id=int(raw["current_player_id"]),
        turn_number=int(raw["turn_number"]),
        victory=victory,
        next_entity_id=int(raw.get("next_entity_id", 1000)),
    )
    return state
