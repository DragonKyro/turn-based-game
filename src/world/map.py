"""Grid of Tiles indexed by (col, row) with bottom-left origin."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from src.core.types import Coord
from src.world.tile import Tile


@dataclass
class Map:
    width: int
    height: int
    tiles: dict[Coord, Tile] = field(default_factory=dict)

    def in_bounds(self, c: Coord) -> bool:
        col, row = c
        return 0 <= col < self.width and 0 <= row < self.height

    def tile(self, c: Coord) -> Tile:
        return self.tiles[c]

    def iter_coords(self) -> Iterator[Coord]:
        for row in range(self.height):
            for col in range(self.width):
                yield (col, row)
