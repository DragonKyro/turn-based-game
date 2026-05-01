"""Simple rectangular button for menu screens. Hover + click with cached Text."""
from __future__ import annotations

from dataclasses import dataclass

import arcade

from src.config import COLORS


@dataclass
class Button:
    label: str
    left: float
    bottom: float
    width: float
    height: float
    on_click: object  # Callable[[], None]; avoids importing Callable for brevity
    fill: tuple[int, int, int] = COLORS["ui_panel"]
    fill_hover: tuple[int, int, int] = COLORS["hero_accent"]
    text_color: tuple[int, int, int] = COLORS["text"]
    text_color_hover: tuple[int, int, int] = (30, 20, 10)
    border_color: tuple[int, int, int] = COLORS["ui_border"]
    border_color_hover: tuple[int, int, int] = COLORS["hero_accent"]

    def __post_init__(self) -> None:
        self._text = arcade.Text(
            self.label,
            self.left + self.width / 2,
            self.bottom + self.height / 2 - 8,
            self.text_color,
            font_size=16,
            anchor_x="center",
            bold=True,
        )
        self._hovered = False

    # --- geometry / state ---

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.left + self.width and self.bottom <= y <= self.bottom + self.height

    def set_hovered(self, hovered: bool) -> None:
        self._hovered = hovered

    # --- events ---

    def on_click_if_inside(self, x: float, y: float) -> bool:
        if self.contains(x, y):
            self.on_click()  # type: ignore[misc]
            return True
        return False

    # --- draw ---

    def draw(self) -> None:
        fill = self.fill_hover if self._hovered else self.fill
        border = self.border_color_hover if self._hovered else self.border_color
        tc = self.text_color_hover if self._hovered else self.text_color
        arcade.draw_lbwh_rectangle_filled(self.left, self.bottom, self.width, self.height, fill)
        arcade.draw_lbwh_rectangle_outline(self.left, self.bottom, self.width, self.height, border, 3)
        self._text.color = tc
        self._text.draw()
