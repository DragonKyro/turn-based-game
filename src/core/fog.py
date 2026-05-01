"""Per-player fog of war. Visible tiles are those within sight of any owned unit or building.

Simple LOS rule: a tile with `terrain.blocks_vision=True` is only seen when the observer is
manhattan-adjacent (distance <= 1). Everything else is seen out to the observer's vision_range.
"""
from __future__ import annotations

from src.core.coord import manhattan
from src.core.game_state import GameState
from src.core.types import Coord, VisState


def recompute_visibility(state: GameState, player_id: int) -> None:
    player = state.players[player_id]
    width = state.map.width
    height = state.map.height

    # demote currently-VISIBLE tiles to EXPLORED
    for col in range(width):
        for row in range(height):
            if player.visibility[col][row] == VisState.VISIBLE:
                player.visibility[col][row] = VisState.EXPLORED

    def _see(c: Coord) -> None:
        col, row = c
        if 0 <= col < width and 0 <= row < height:
            player.visibility[col][row] = VisState.VISIBLE

    # promote tiles in sight of each owned unit/building
    for u in state.units_of(player_id):
        _mark_sight(state, u.coord, type(u).vision_range, _see)
    for b in state.buildings_of(player_id):
        _mark_sight(state, b.coord, type(b).vision_range, _see)


def _mark_sight(state: GameState, origin: Coord, vision_range: int, mark) -> None:
    ox, oy = origin
    for dc in range(-vision_range, vision_range + 1):
        for dr in range(-vision_range, vision_range + 1):
            d = abs(dc) + abs(dr)
            if d > vision_range:
                continue
            c = (ox + dc, oy + dr)
            if not state.map.in_bounds(c):
                continue
            tile = state.map.tile(c)
            if tile.terrain.blocks_vision and manhattan(origin, c) > 1:
                # Obstructing terrain: only visible when adjacent.
                continue
            mark(c)
