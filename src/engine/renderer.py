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
    for coord in tiles:
        col, row = coord
        arcade.draw_lbwh_rectangle_filled(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["move_range"]
        )


def draw_attack_range(tiles: set[Coord]) -> None:
    for coord in tiles:
        col, row = coord
        arcade.draw_lbwh_rectangle_filled(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["attack_range"]
        )


def draw_selection(coord: Coord) -> None:
    col, row = coord
    arcade.draw_lbwh_rectangle_outline(
        col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["selection"], 3
    )


def draw_buildings(state: GameState, vis: list[list[VisState]] | None) -> None:
    for b in state.buildings.values():
        col, row = b.coord
        if _vis_at(vis, col, row) == VisState.HIDDEN:
            continue
        cx, cy = grid_to_pixel(b.coord, TILE_SIZE)
        sprites.draw_building(b, cx, cy)


def draw_units(state: GameState, vis: list[list[VisState]] | None,
               view_player_id: int, anim_time: float) -> None:
    for u in state.units.values():
        if not u.is_alive:
            continue
        col, row = u.coord
        vstate = _vis_at(vis, col, row)
        if u.owner_id != view_player_id and vstate != VisState.VISIBLE:
            continue
        if vstate == VisState.HIDDEN:
            continue
        cx, cy = grid_to_pixel(u.coord, TILE_SIZE)
        dimmed = u.has_acted and u.owner_id == view_player_id
        sprites.draw_unit(u, cx, cy, dimmed, anim_time)


def _darken(color: tuple[int, ...], factor: float) -> tuple[int, int, int]:
    r, g, b = color[:3]
    return (int(r * factor), int(g * factor), int(b * factor))


def _vis_at(vis: list[list[VisState]] | None, col: int, row: int) -> VisState:
    if vis is None:
        return VisState.VISIBLE
    return vis[col][row]
