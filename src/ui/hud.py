"""Minimal HUD: current player banner, gold, turn number, last-action message."""
from __future__ import annotations

import arcade

from src.config import COLORS
from src.core.game_state import GameState


def draw(state: GameState, view_player_id: int, banner: str | None, window_height: int) -> None:
    p = state.players[view_player_id]

    # Top banner: active player, faction, gold, turn
    text = (
        f"Turn {state.turn_number}   |   "
        f"{p.name} ({p.faction})   |   "
        f"Gold: {p.gold}g"
    )
    color = COLORS["player1"] if view_player_id == 1 else COLORS["player2"]
    arcade.draw_lbwh_rectangle_filled(0, window_height - 28, 580, 28, COLORS["ui_panel"])
    arcade.draw_text(text, 10, window_height - 22, color, font_size=14, bold=True)

    if banner:
        arcade.draw_lbwh_rectangle_filled(0, 0, 800, 24, COLORS["ui_panel"])
        arcade.draw_text(banner, 10, 4, COLORS["text"], font_size=13)


def draw_controls(window_height: int) -> None:
    arcade.draw_text(
        "Click: select/move/attack  E: end turn  U: ultimate  Esc: menu  Arrows: pan",
        10, window_height - 50, COLORS["text_dim"], font_size=11,
    )


def draw_victory(state: GameState, window_width: int, window_height: int) -> None:
    if state.victory is None:
        return
    winner = state.players.get(state.victory.winner_id)
    name = winner.name if winner else f"Player {state.victory.winner_id}"
    arcade.draw_lbwh_rectangle_filled(0, 0, window_width, window_height, (0, 0, 0, 200))
    arcade.draw_text(
        f"{name} wins!",
        window_width // 2, window_height // 2 + 20,
        COLORS["hero_accent"], font_size=48, anchor_x="center", bold=True,
    )
    arcade.draw_text(
        f"Reason: {state.victory.reason}",
        window_width // 2, window_height // 2 - 20,
        COLORS["text"], font_size=18, anchor_x="center",
    )
    arcade.draw_text(
        "Press Esc to return to menu",
        window_width // 2, window_height // 2 - 60,
        COLORS["text_dim"], font_size=14, anchor_x="center",
    )
