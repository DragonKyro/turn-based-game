"""Arcade camera wrappers. World camera pans over the map; UI camera stays fixed in screen space."""
from __future__ import annotations

import arcade

from src.config import TILE_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH

_PAN_STEP = TILE_SIZE  # keyboard pan granularity


class Cameras:
    def __init__(self) -> None:
        self.world = arcade.Camera2D()
        self.ui = arcade.Camera2D()

    def pan(self, dx: float, dy: float) -> None:
        x, y = self.world.position
        self.world.position = (x + dx, y + dy)

    def center_on(self, map_width_tiles: int, map_height_tiles: int) -> None:
        """Center the world camera on the map center (useful at level start)."""
        cx = (map_width_tiles * TILE_SIZE) / 2 - WINDOW_WIDTH / 2
        cy = (map_height_tiles * TILE_SIZE) / 2 - WINDOW_HEIGHT / 2
        self.world.position = (cx, cy)

    @property
    def pan_step(self) -> float:
        return _PAN_STEP
