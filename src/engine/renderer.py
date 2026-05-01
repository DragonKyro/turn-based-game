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
from src.engine import sprites


def draw_terrain(state: GameState, vis: list[list[VisState]] | None) -> None:
    """Fill each tile with its terrain color. Greyed when EXPLORED, black when HIDDEN."""
    for coord, tile in state.map.tiles.items():
        col, row = coord
        vstate = _vis_at(vis, col, row)
        if vstate == VisState.HIDDEN:
            color = COLORS["background"]
        else:
            color = COLORS.get(tile.terrain.name, COLORS["plains"])
            if vstate == VisState.EXPLORED:
                color = _darken(color, 0.55)
        arcade.draw_lbwh_rectangle_filled(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, color
        )
        arcade.draw_lbwh_rectangle_outline(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["grid_line"], 1
        )


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


def draw_units(state: GameState, vis: list[list[VisState]] | None, active_player_id: int) -> None:
    for u in state.units.values():
        if not u.is_alive:
            continue
        col, row = u.coord
        vstate = _vis_at(vis, col, row)
        if u.owner_id != active_player_id and vstate != VisState.VISIBLE:
            continue
        if vstate == VisState.HIDDEN:
            continue
        cx, cy = grid_to_pixel(u.coord, TILE_SIZE)
        dimmed = u.has_acted and u.owner_id == active_player_id
        sprites.draw_unit(u, cx, cy, dimmed)


def _darken(color: tuple[int, ...], factor: float) -> tuple[int, int, int]:
    r, g, b = color[:3]
    return (int(r * factor), int(g * factor), int(b * factor))


def _vis_at(vis: list[list[VisState]] | None, col: int, row: int) -> VisState:
    if vis is None:
        return VisState.VISIBLE
    return vis[col][row]
