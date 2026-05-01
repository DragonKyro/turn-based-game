"""Load and validate a level from JSON into a `Level` (with a fully-populated GameState).

See `src/data/levels/schema.md` for the file format.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config import LEVELS_DIR
from src.core.game_state import GameState
from src.core.player import Player
from src.core.types import Coord
from src.entities.buildings import BUILDING_REGISTRY
from src.entities.heroes import HERO_REGISTRY
from src.entities.units import UNIT_REGISTRY
from src.world.level import Level
from src.world.map import Map
from src.world.terrain_types import TERRAIN_REGISTRY
from src.world.tile import Tile


class LevelLoadError(ValueError):
    """Raised when a level file is malformed. Message should name the file + location of the issue."""


def load_level(name: str, levels_dir: Path | None = None) -> Level:
    """Load a level by bare name (no extension) from `LEVELS_DIR` or the given override."""
    root = levels_dir or LEVELS_DIR
    path = root / f"{name}.json"
    if not path.exists():
        raise LevelLoadError(f"Level file not found: {path}")

    with path.open(encoding="utf-8") as f:
        raw = json.load(f)

    return _build_level(raw, source=str(path))


def _build_level(raw: dict[str, Any], source: str) -> Level:
    try:
        name = raw["name"]
        width = int(raw["width"])
        height = int(raw["height"])
        terrain_rows: list[str] = raw["terrain"]
        terrain_legend: dict[str, str] = raw["terrain_legend"]
        player_specs: list[dict] = raw["players"]
        building_specs: list[dict] = raw.get("buildings", [])
        unit_specs: list[dict] = raw.get("units", [])
        victory = raw.get("victory", {}).get("type", "capture_strongholds")
    except KeyError as e:
        raise LevelLoadError(f"{source}: missing top-level key {e}") from None

    if len(terrain_rows) != height:
        raise LevelLoadError(
            f"{source}: `terrain` has {len(terrain_rows)} rows but height={height}"
        )

    # --- build map ---
    m = Map(width=width, height=height)
    # terrain_rows[0] is the TOP visual row. We flip to bottom-left origin: row = height-1-row_index.
    for visual_row, row_str in enumerate(terrain_rows):
        if len(row_str) != width:
            raise LevelLoadError(
                f"{source}: row {visual_row} has {len(row_str)} glyphs but width={width}"
            )
        grid_row = height - 1 - visual_row
        for col, glyph in enumerate(row_str):
            terrain_name = terrain_legend.get(glyph)
            if terrain_name is None:
                raise LevelLoadError(
                    f"{source}: unknown terrain glyph {glyph!r} at visual row {visual_row}, col {col}"
                )
            terrain = TERRAIN_REGISTRY.get(terrain_name)
            if terrain is None:
                raise LevelLoadError(
                    f"{source}: terrain legend maps {glyph!r} -> {terrain_name!r}, "
                    f"but that terrain isn't defined in TERRAIN_REGISTRY"
                )
            m.tiles[(col, grid_row)] = Tile(terrain=terrain)

    # --- players ---
    players: dict[int, Player] = {}
    hero_kind_by_player: dict[int, str] = {}
    for ps in player_specs:
        p = Player(
            id=int(ps["id"]),
            name=str(ps["name"]),
            faction=str(ps["faction"]),
            gold=int(ps.get("start_gold", 0)),
            is_ai=bool(ps.get("is_ai", False)),
        )
        p.init_visibility(width, height)
        players[p.id] = p
        if "hero" in ps:
            hero_kind_by_player[p.id] = ps["hero"]

    # --- buildings ---
    buildings = {}
    next_id = 1
    for bs in building_specs:
        kind = bs["kind"]
        coord: Coord = tuple(bs["coord"])  # type: ignore[assignment]
        if not m.in_bounds(coord):
            raise LevelLoadError(f"{source}: building {kind!r} at out-of-bounds coord {coord}")
        cls = BUILDING_REGISTRY.get(kind)
        if cls is None:
            raise LevelLoadError(f"{source}: unknown building kind {kind!r}")
        owner = bs.get("owner")
        b = cls(id=next_id, coord=coord, owner_id=owner)
        buildings[next_id] = b
        m.tiles[coord].building_id = next_id
        next_id += 1

    # --- units (and heroes) ---
    units = {}
    for us in unit_specs:
        kind = us["kind"]
        coord = tuple(us["coord"])
        owner = int(us["owner"])
        if not m.in_bounds(coord):
            raise LevelLoadError(f"{source}: unit {kind!r} at out-of-bounds coord {coord}")
        if owner not in players:
            raise LevelLoadError(f"{source}: unit {kind!r} references unknown owner {owner}")

        cls = UNIT_REGISTRY.get(kind) or HERO_REGISTRY.get(kind)
        if cls is None:
            raise LevelLoadError(f"{source}: unknown unit/hero kind {kind!r}")

        is_hero = kind in HERO_REGISTRY
        if is_hero:
            u = cls(id=next_id, owner_id=owner, coord=coord, hp=cls.max_hp)
            players[owner].hero_id = next_id
        else:
            u = cls(id=next_id, owner_id=owner, coord=coord, hp=cls.max_hp)

        # Tile occupancy check — no stacking.
        if m.tiles[coord].unit_id is not None:
            raise LevelLoadError(f"{source}: two units placed on the same tile {coord}")
        m.tiles[coord].unit_id = next_id

        units[next_id] = u
        next_id += 1

    # Sanity: every player's declared hero kind was actually placed.
    for pid, hkind in hero_kind_by_player.items():
        if players[pid].hero_id is None:
            raise LevelLoadError(
                f"{source}: player {pid} declares hero {hkind!r} but no such unit is placed on the map"
            )

    # --- starting state ---
    first_player_id = player_specs[0]["id"]
    state = GameState(
        map=m,
        players=players,
        units=units,
        buildings=buildings,
        current_player_id=first_player_id,
        turn_number=1,
        next_entity_id=max(next_id, 1000),
    )

    return Level(name=name, initial_state=state, victory_type=victory)
