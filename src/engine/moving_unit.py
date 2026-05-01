"""Per-unit movement animation. A MovingUnit interpolates along a path over time so
the sprite visibly traverses tiles instead of teleporting to the destination."""
from __future__ import annotations

from dataclasses import dataclass

from src.config import TILE_SIZE
from src.core.coord import grid_to_pixel
from src.core.types import Coord

SECONDS_PER_TILE = 0.09


@dataclass
class MovingUnit:
    unit_id: int
    path: list[Coord]   # includes start AND end; len >= 2
    elapsed: float = 0.0
    duration: float = 0.0

    def __post_init__(self) -> None:
        segments = max(1, len(self.path) - 1)
        self.duration = segments * SECONDS_PER_TILE

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    def tick(self, dt: float) -> None:
        self.elapsed += dt

    def current_pixel(self) -> tuple[float, float]:
        """Interpolated (x, y) pixel position on the current segment."""
        segments = max(1, len(self.path) - 1)
        t = max(0.0, min(1.0, self.elapsed / max(self.duration, 1e-6)))
        pos = t * segments
        idx = int(pos)
        if idx >= segments:
            return grid_to_pixel(self.path[-1], TILE_SIZE)
        local = pos - idx
        a = self.path[idx]
        b = self.path[idx + 1]
        ax, ay = grid_to_pixel(a, TILE_SIZE)
        bx, by = grid_to_pixel(b, TILE_SIZE)
        return (ax + (bx - ax) * local, ay + (by - ay) * local)

    def current_tile(self) -> Coord:
        """Nearest path tile to the current interpolated position. Used to check fog visibility."""
        segments = max(1, len(self.path) - 1)
        t = max(0.0, min(1.0, self.elapsed / max(self.duration, 1e-6)))
        pos = t * segments
        idx = int(pos)
        if idx >= segments:
            return self.path[-1]
        local = pos - idx
        return self.path[idx + 1] if local > 0.5 else self.path[idx]
