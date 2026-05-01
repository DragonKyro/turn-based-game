"""Embercrown entry point."""
from __future__ import annotations

import arcade

from src.config import WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from src.engine.menu_view import MenuView


def main() -> None:
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()
