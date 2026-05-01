"""Arcade camera wrappers. World camera pans over the map; UI camera stays fixed in screen space.

Important: arcade 3.x `Camera2D.position` is the **center** of the viewport in world coords
(not the bottom-left). Setting `position = (map_w*tile/2, map_h*tile/2)` centers the map.
Use `camera.unproject((screen_x, screen_y))` for screen → world conversion.
"""
from __future__ import annotations

import arcade

from src.config import TILE_SIZE

_PAN_STEP = TILE_SIZE


class Cameras:
    def __init__(self) -> None:
        self.world = arcade.Camera2D()
        self.ui = arcade.Camera2D()

    def pan(self, dx: float, dy: float) -> None:
        x, y = self.world.position
        self.world.position = (x + dx, y + dy)

    def center_on(self, map_width_tiles: int, map_height_tiles: int) -> None:
        """Center the world camera on the middle of the map."""
        cx = (map_width_tiles * TILE_SIZE) / 2
        cy = (map_height_tiles * TILE_SIZE) / 2
        self.world.position = (cx, cy)

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        """Convert a screen-pixel coordinate into world-pixel coordinates."""
        v = self.world.unproject((x, y))
        return (v.x, v.y)

    @property
    def pan_step(self) -> float:
        return _PAN_STEP
