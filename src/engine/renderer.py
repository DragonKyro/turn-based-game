"""Drawing routines. Each function takes a GameState (+ view context) and reads only what it needs.

Kept as free functions (not a class) to make layer order explicit at the call site in GameView.
"""
from __future__ import annotations

import arcade

from src.config import COLORS, TILE_SIZE
from src.core.coord import grid_to_pixel
from src.core.game_state import GameState
from src.core.types import Coord, VisState


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
        left = col * TILE_SIZE + 4
        bottom = row * TILE_SIZE + 4
        size = TILE_SIZE - 8
        fill = _owner_color(b.owner_id)
        arcade.draw_lbwh_rectangle_filled(left, bottom, size, size, fill)
        arcade.draw_lbwh_rectangle_outline(left, bottom, size, size, COLORS["ui_border"], 2)
        cx, cy = grid_to_pixel(b.coord, TILE_SIZE)
        arcade.draw_text(
            type(b).display_letter,
            cx, cy - 8,
            COLORS["text"],
            font_size=14, anchor_x="center", bold=True,
        )
        # Capture progress pip
        if b.capture_progress > 0:
            ratio = b.capture_progress / type(b).capture_threshold
            w = size * 0.9
            arcade.draw_lbwh_rectangle_filled(
                left + (size - w) / 2, bottom - 6, w * ratio, 3, COLORS["hero_accent"]
            )


def draw_units(state: GameState, vis: list[list[VisState]] | None, active_player_id: int) -> None:
    for u in state.units.values():
        if not u.is_alive:
            continue
        col, row = u.coord
        vstate = _vis_at(vis, col, row)
        # Enemy units are hidden when not VISIBLE.
        if u.owner_id != active_player_id and vstate != VisState.VISIBLE:
            continue
        if vstate == VisState.HIDDEN:
            continue
        cx, cy = grid_to_pixel(u.coord, TILE_SIZE)
        body_color = _owner_color(u.owner_id)
        if u.has_acted and u.owner_id == active_player_id:
            body_color = _darken(body_color, 0.55)
        radius = TILE_SIZE * 0.38
        arcade.draw_circle_filled(cx, cy, radius, body_color)
        outline_color = COLORS["hero_accent"] if u.is_hero else COLORS["ui_border"]
        outline_width = 3 if u.is_hero else 1
        arcade.draw_circle_outline(cx, cy, radius, outline_color, outline_width)
        arcade.draw_text(
            type(u).display_letter,
            cx, cy - 8,
            COLORS["text"],
            font_size=14, anchor_x="center", bold=True,
        )
        _draw_hp_bar(cx, cy - radius - 8, u.hp, u.max_hp)

        # Hero ultimate ready pulse
        if u.is_hero and getattr(u, "ultimate_charge", 0) >= getattr(u, "ultimate_charge_max", 999):
            arcade.draw_circle_outline(cx, cy, radius + 4, COLORS["hero_accent"], 2)


def _draw_hp_bar(cx: float, cy: float, hp: int, max_hp: int) -> None:
    w = TILE_SIZE * 0.7
    h = 4
    left = cx - w / 2
    ratio = max(0.0, min(1.0, hp / max_hp))
    arcade.draw_lbwh_rectangle_filled(left, cy, w, h, COLORS["ui_panel"])
    arcade.draw_lbwh_rectangle_filled(left, cy, w * ratio, h, COLORS["hero_accent"])


def _owner_color(owner_id: int | None) -> tuple[int, int, int]:
    if owner_id == 1:
        return COLORS["player1"]
    if owner_id == 2:
        return COLORS["player2"]
    return (130, 130, 140)


def _darken(color: tuple[int, ...], factor: float) -> tuple[int, int, int]:
    r, g, b = color[:3]
    return (int(r * factor), int(g * factor), int(b * factor))


def _vis_at(vis: list[list[VisState]] | None, col: int, row: int) -> VisState:
    if vis is None:
        return VisState.VISIBLE
    return vis[col][row]
