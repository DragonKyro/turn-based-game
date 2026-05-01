"""Main in-match view. Loads a level and renders terrain.

Unit/building rendering, range overlays, and input handling are added in later steps.
"""
from __future__ import annotations

import arcade

from src.config import COLORS
from src.engine import renderer
from src.engine.camera import Cameras
from src.world.level_loader import LevelLoadError, load_level


class GameView(arcade.View):
    def __init__(self, level_name: str) -> None:
        super().__init__()
        self.level_name = level_name
        self.level = None
        self.state = None
        self.cameras = Cameras()
        self.load_error: str | None = None

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]
        try:
            self.level = load_level(self.level_name)
            self.state = self.level.initial_state
            self.cameras.center_on(self.state.map.width, self.state.map.height)
        except LevelLoadError as e:
            self.load_error = str(e)

    def on_draw(self) -> None:
        self.clear()
        if self.load_error:
            arcade.draw_text(
                f"Failed to load level: {self.load_error}",
                20, 40, COLORS["text"], font_size=14,
            )
            return
        assert self.state is not None
        self.cameras.world.use()
        renderer.draw_terrain(self.state)
        renderer.draw_buildings(self.state)
        renderer.draw_units(self.state)

        self.cameras.ui.use()
        arcade.draw_text(
            f"{self.level.name}  —  turn {self.state.turn_number}  "
            f"(active: player {self.state.current_player_id})",
            12, 12, COLORS["text"], font_size=14,
        )
        arcade.draw_text(
            "Esc: menu   Arrows: pan camera",
            12, self.window.height - 22, COLORS["text_dim"], font_size=12,
        )

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            from src.engine.menu_view import MenuView
            self.window.show_view(MenuView())
        elif symbol == arcade.key.LEFT:
            self.cameras.pan(-self.cameras.pan_step, 0)
        elif symbol == arcade.key.RIGHT:
            self.cameras.pan(self.cameras.pan_step, 0)
        elif symbol == arcade.key.UP:
            self.cameras.pan(0, self.cameras.pan_step)
        elif symbol == arcade.key.DOWN:
            self.cameras.pan(0, -self.cameras.pan_step)
