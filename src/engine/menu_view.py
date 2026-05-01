"""Title screen. Press Enter to start a match on the default level."""
from __future__ import annotations

import arcade

from src.config import COLORS, DEFAULT_LEVEL, WINDOW_HEIGHT, WINDOW_WIDTH


class MenuView(arcade.View):
    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]

    def on_draw(self) -> None:
        self.clear()
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        arcade.draw_text(
            "EMBERCROWN",
            cx, cy + 80,
            COLORS["hero_accent"],
            font_size=56, anchor_x="center", bold=True,
        )
        arcade.draw_text(
            "A turn-based tactics skirmish",
            cx, cy + 30,
            COLORS["text_dim"],
            font_size=16, anchor_x="center",
        )
        arcade.draw_text(
            "Press [ENTER] to begin    |    [ESC] to quit",
            cx, cy - 40,
            COLORS["text"],
            font_size=18, anchor_x="center",
        )

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        if symbol == arcade.key.ENTER:
            from src.engine.game_view import GameView  # local import: engine → engine avoids early arcade-heavy loads
            self.window.show_view(GameView(DEFAULT_LEVEL))
        elif symbol == arcade.key.ESCAPE:
            self.window.close()
