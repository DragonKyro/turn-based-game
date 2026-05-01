"""Options screen reachable from the main menu.

Toggles settings via clickable rows and persists them via `Options.save()`.
"""
from __future__ import annotations

import arcade

from src.config import COLORS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.core.options import Options
from src.ui.button import Button


class OptionsView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        self.options = Options.load()

        self._title = arcade.Text(
            "OPTIONS",
            WINDOW_WIDTH // 2, WINDOW_HEIGHT - 120,
            COLORS["hero_accent"], font_size=48, anchor_x="center", bold=True,
        )

        btn_w, btn_h = 360, 50
        btn_x = WINDOW_WIDTH // 2 - btn_w // 2
        y = WINDOW_HEIGHT // 2 + 40

        self._fight_btn = Button(
            label=self._fight_label(),
            left=btn_x, bottom=y, width=btn_w, height=btn_h,
            on_click=self._toggle_fight_scene,
        )
        self._back_btn = Button(
            label="Back to menu",
            left=btn_x, bottom=y - 90, width=btn_w, height=btn_h,
            on_click=self._back,
        )
        self._buttons = [self._fight_btn, self._back_btn]

    def _fight_label(self) -> str:
        return "Fight scene:  ON" if self.options.show_fight_scene else "Fight scene:  OFF"

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]

    def on_draw(self) -> None:
        self.clear()
        self._title.draw()
        for b in self._buttons:
            b.draw()

    def on_mouse_motion(self, x: int, y: int, _dx: int, _dy: int) -> None:
        for b in self._buttons:
            b.set_hovered(b.contains(x, y))

    def on_mouse_press(self, x: int, y: int, _button: int, _mods: int) -> None:
        for b in self._buttons:
            if b.on_click_if_inside(x, y):
                return

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self._back()

    def _toggle_fight_scene(self) -> None:
        self.options.show_fight_scene = not self.options.show_fight_scene
        self.options.save()
        # Rebuild the button with the new label text.
        self._fight_btn = Button(
            label=self._fight_label(),
            left=self._fight_btn.left, bottom=self._fight_btn.bottom,
            width=self._fight_btn.width, height=self._fight_btn.height,
            on_click=self._toggle_fight_scene,
        )
        self._buttons[0] = self._fight_btn

    def _back(self) -> None:
        from src.engine.menu_view import MenuView
        self.window.show_view(MenuView())
