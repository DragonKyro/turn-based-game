"""Drawing routines. Each function takes a GameState (+ view context) and reads only what it needs.

Kept as free functions (not a class) to make layer order explicit at the call site in GameView.
Uses the procedural `sprites` module for units and buildings.
"""
from __future__ import annotations

import arcade

from src.config import COLORS, TILE_SIZE
from src.core.coord import grid_to_pixel
from src.core.game_state import GameState
from src.core.types import Coord, VisState
from src.engine import sprites, terrain_sprites


def draw_terrain(state: GameState, vis: list[list[VisState]] | None) -> None:
    """Fill each tile with its terrain color + per-tile texture decoration.

    HIDDEN tiles render solid black (no decoration — we don't know what's there).
    EXPLORED tiles are dimmed; textures are dimmed with them.
    VISIBLE tiles get full color + decoration.
    """
    for coord, tile in state.map.tiles.items():
        col, row = coord
        vstate = _vis_at(vis, col, row)
        if vstate == VisState.HIDDEN:
            arcade.draw_lbwh_rectangle_filled(
                col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["background"]
            )
            arcade.draw_lbwh_rectangle_outline(
                col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["grid_line"], 1
            )
            continue

        fog_factor = 0.55 if vstate == VisState.EXPLORED else 1.0
        base_color = COLORS.get(tile.terrain.name, COLORS["plains"])
        base_color = _apply_fog(base_color, fog_factor)
        arcade.draw_lbwh_rectangle_filled(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, base_color
        )
        # Per-tile decoration (trees/rocks/waves/cobbles/grass)
        terrain_sprites.draw_tile_decoration(coord, tile.terrain.name, fog_factor)
        arcade.draw_lbwh_rectangle_outline(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["grid_line"], 1
        )


def _apply_fog(color: tuple[int, int, int], fog_factor: float) -> tuple[int, int, int]:
    if fog_factor >= 1.0:
        return color
    return (int(color[0] * fog_factor), int(color[1] * fog_factor), int(color[2] * fog_factor))


def draw_move_range(tiles: dict[Coord, int]) -> None:
    """Solid-color outlines (no alpha fill) — avoids the diagonal-seam artifact
    that alpha-blended rectangles produce on some GPU rigs."""
    for coord in tiles:
        col, row = coord
        arcade.draw_lbwh_rectangle_outline(
            col * TILE_SIZE + 2, row * TILE_SIZE + 2,
            TILE_SIZE - 4, TILE_SIZE - 4,
            (90, 170, 255), 2,
        )


def draw_attack_range(tiles: set[Coord]) -> None:
    for coord in tiles:
        col, row = coord
        arcade.draw_lbwh_rectangle_outline(
            col * TILE_SIZE + 2, row * TILE_SIZE + 2,
            TILE_SIZE - 4, TILE_SIZE - 4,
            (230, 80, 80), 2,
        )


def draw_selection(coord: Coord) -> None:
    """Solid gold double-ring on the selected tile — no alpha fill."""
    col, row = coord
    left = col * TILE_SIZE
    bottom = row * TILE_SIZE
    arcade.draw_lbwh_rectangle_outline(
        left, bottom, TILE_SIZE, TILE_SIZE, COLORS["selection"], 4
    )
    arcade.draw_lbwh_rectangle_outline(
        left + 3, bottom + 3, TILE_SIZE - 6, TILE_SIZE - 6, (30, 20, 10), 1
    )


def draw_hover(coord: Coord) -> None:
    """Thin solid outline on the hovered tile."""
    col, row = coord
    arcade.draw_lbwh_rectangle_outline(
        col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, (240, 240, 250), 1
    )


def draw_spawn_ghosts(tiles: list[Coord], pulse: float) -> None:
    """Pulsing gold outlines on valid deploy tiles — border-only so no alpha seams."""
    width = int(2 + 2 * pulse)
    for coord in tiles:
        col, row = coord
        left = col * TILE_SIZE + 4
        bottom = row * TILE_SIZE + 4
        arcade.draw_lbwh_rectangle_outline(
            left, bottom, TILE_SIZE - 8, TILE_SIZE - 8,
            COLORS["hero_accent"], width,
        )


def draw_buildings(state: GameState, vis: list[list[VisState]] | None,
                   view_player_id: int) -> None:
    for b in state.buildings.values():
        col, row = b.coord
        if _vis_at(vis, col, row) == VisState.HIDDEN:
            continue
        cx, cy = grid_to_pixel(b.coord, TILE_SIZE)
        faction = state.players[b.owner_id].faction if b.owner_id in state.players else None
        sprites.draw_building(b, cx, cy, faction_key=faction)
        # Gray-out scrim on our own exhausted production buildings.
        if b.owner_id == view_player_id and b.has_produced:
            arcade.draw_lbwh_rectangle_filled(
                col * TILE_SIZE + 2, row * TILE_SIZE + 2,
                TILE_SIZE - 4, TILE_SIZE - 4,
                (15, 15, 25, 140),
            )


def draw_units(state: GameState, vis: list[list[VisState]] | None,
               view_player_id: int, anim_time: float,
               skip_unit_id: int | None = None) -> None:
    for u in state.units.values():
        if not u.is_alive:
            continue
        if skip_unit_id is not None and u.id == skip_unit_id:
            continue
        col, row = u.coord
        vstate = _vis_at(vis, col, row)
        if u.owner_id != view_player_id and vstate != VisState.VISIBLE:
            continue
        if vstate == VisState.HIDDEN:
            continue
        cx, cy = grid_to_pixel(u.coord, TILE_SIZE)
        dimmed = u.has_acted and u.owner_id == view_player_id
        faction = state.players[u.owner_id].faction
        sprites.draw_unit(u, cx, cy, dimmed, anim_time, faction=faction)


def draw_unit_at(state: GameState, unit_id: int, cx: float, cy: float,
                 anim_time: float) -> None:
    """Render a specific unit at a caller-chosen pixel — used for movement animation."""
    u = state.units.get(unit_id)
    if u is None or not u.is_alive:
        return
    faction = state.players[u.owner_id].faction
    sprites.draw_unit(u, cx, cy, dimmed=False, anim_time=anim_time, faction=faction)


def _darken(color: tuple[int, ...], factor: float) -> tuple[int, int, int]:
    r, g, b = color[:3]
    return (int(r * factor), int(g * factor), int(b * factor))


def _vis_at(vis: list[list[VisState]] | None, col: int, row: int) -> VisState:
    if vis is None:
        return VisState.VISIBLE
    return vis[col][row]
