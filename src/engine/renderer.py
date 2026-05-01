"""Drawing routines. Each function takes a GameState and reads only what it needs.

Kept as free functions (not a class) to make layer order explicit at the call site in GameView.
"""
from __future__ import annotations

import arcade

from src.config import COLORS, TILE_SIZE
from src.core.coord import grid_to_pixel
from src.core.game_state import GameState


def draw_terrain(state: GameState) -> None:
    """Fill each tile with its terrain color and outline."""
    for coord, tile in state.map.tiles.items():
        col, row = coord
        color = COLORS.get(tile.terrain.name, COLORS["plains"])
        arcade.draw_lbwh_rectangle_filled(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, color
        )
        arcade.draw_lbwh_rectangle_outline(
            col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE, COLORS["grid_line"], 1
        )


def draw_buildings(state: GameState) -> None:
    """Draw each building as a framed square labelled with its letter, tinted by owner."""
    for b in state.buildings.values():
        col, row = b.coord
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


def draw_units(state: GameState) -> None:
    """Draw each living unit as a filled circle with letter; heroes get a gold outline."""
    for u in state.units.values():
        if not u.is_alive:
            continue
        cx, cy = grid_to_pixel(u.coord, TILE_SIZE)
        body_color = _owner_color(u.owner_id)
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
        # HP pip bar below the circle
        _draw_hp_bar(cx, cy - radius - 8, u.hp, u.max_hp)


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
    return (130, 130, 140)  # neutral
