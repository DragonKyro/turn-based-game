"""HUD with cached arcade.Text objects (avoids the per-frame draw_text perf cost).

Each Text is created once and mutated via `.text` / `.color` each frame.
"""
from __future__ import annotations

import arcade

from src.config import COLORS
from src.core.game_state import GameState


class HUD:
    def __init__(self, window_height: int) -> None:
        self.window_height = window_height
        self.top_banner = arcade.Text(
            "", 10, window_height - 22, COLORS["text"], font_size=14, bold=True,
        )
        self.controls = arcade.Text(
            "Click: select/move/attack  E: end turn  U: ultimate  Esc: menu  Arrows: pan",
            10, window_height - 50, COLORS["text_dim"], font_size=11,
        )
        self.banner = arcade.Text("", 10, 4, COLORS["text"], font_size=13)

    def draw(self, state: GameState, view_player_id: int, banner_text: str | None) -> None:
        p = state.players[view_player_id]
        banner = (
            f"Turn {state.turn_number}   |   "
            f"{p.name} ({p.faction})   |   "
            f"Gold: {p.gold}g"
            + ("   [AI]" if p.is_ai else "")
        )
        self.top_banner.text = banner
        self.top_banner.color = COLORS["player1"] if view_player_id == 1 else COLORS["player2"]
        arcade.draw_lbwh_rectangle_filled(0, self.window_height - 28, 640, 28, COLORS["ui_panel"])
        self.top_banner.draw()
        self.controls.draw()

        if banner_text:
            arcade.draw_lbwh_rectangle_filled(0, 0, 900, 24, COLORS["ui_panel"])
            self.banner.text = banner_text
            self.banner.draw()


class VictoryOverlay:
    def __init__(self, window_width: int, window_height: int) -> None:
        self.window_width = window_width
        self.window_height = window_height
        self.title = arcade.Text(
            "", window_width // 2, window_height // 2 + 20,
            COLORS["hero_accent"], font_size=48, anchor_x="center", bold=True,
        )
        self.reason = arcade.Text(
            "", window_width // 2, window_height // 2 - 20,
            COLORS["text"], font_size=18, anchor_x="center",
        )
        self.hint = arcade.Text(
            "Press Esc to return to menu",
            window_width // 2, window_height // 2 - 60,
            COLORS["text_dim"], font_size=14, anchor_x="center",
        )

    def draw(self, state: GameState) -> None:
        if state.victory is None:
            return
        winner = state.players.get(state.victory.winner_id)
        name = winner.name if winner else f"Player {state.victory.winner_id}"
        arcade.draw_lbwh_rectangle_filled(0, 0, self.window_width, self.window_height, (0, 0, 0, 200))
        self.title.text = f"{name} wins!"
        self.title.draw()
        self.reason.text = f"Reason: {state.victory.reason}"
        self.reason.draw()
        self.hint.draw()
