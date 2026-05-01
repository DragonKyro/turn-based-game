"""Grid pathfinding. Dijkstra over per-unit-class terrain costs, with allied pass-through."""
from __future__ import annotations

import heapq

from src.core.coord import neighbors4
from src.core.game_state import GameState
from src.core.types import IMPASSABLE, Coord
from src.entities.unit import Unit


def reachable(state: GameState, unit: Unit) -> dict[Coord, int]:
    """Tiles the unit can reach this turn, mapped to movement-point cost to arrive.

    Enemy units block entry. Allied units may be passed through but cannot be a stopping point
    (they are excluded from the returned dict).
    """
    start = unit.coord
    budget = type(unit).move
    unit_cls = type(unit).unit_class

    dist: dict[Coord, int] = {start: 0}
    frontier: list[tuple[int, Coord]] = [(0, start)]

    while frontier:
        cost_here, c = heapq.heappop(frontier)
        if cost_here > dist.get(c, IMPASSABLE):
            continue
        for n in neighbors4(c):
            if not state.map.in_bounds(n):
                continue
            tile = state.map.tile(n)
            step = tile.terrain.cost_for(unit_cls)
            if step >= IMPASSABLE:
                continue
            # Enemy unit blocks entirely; allied unit allows passage but not a stopping point.
            occupant = state.units.get(tile.unit_id) if tile.unit_id is not None else None
            if occupant is not None and occupant.is_alive and occupant.owner_id != unit.owner_id:
                continue
            new_cost = cost_here + step
            if new_cost > budget:
                continue
            if new_cost < dist.get(n, IMPASSABLE):
                dist[n] = new_cost
                heapq.heappush(frontier, (new_cost, n))

    # Exclude the unit's own tile (it "costs" 0 but doesn't count as a move destination),
    # and exclude tiles occupied by allied units (cannot stop there).
    result: dict[Coord, int] = {}
    for c, cost in dist.items():
        if c == start:
            continue
        tile = state.map.tile(c)
        occupant = state.units.get(tile.unit_id) if tile.unit_id is not None else None
        if occupant is not None and occupant.is_alive:
            continue
        result[c] = cost
    return result


def attackable_from(state: GameState, unit: Unit, origin: Coord) -> set[Coord]:
    """Tiles a unit could attack if it occupied `origin`.

    Uses the unit's attack_range (min, max) as manhattan distance.
    """
    lo, hi = type(unit).attack_range
    out: set[Coord] = set()
    ox, oy = origin
    for dc in range(-hi, hi + 1):
        for dr in range(-hi, hi + 1):
            d = abs(dc) + abs(dr)
            if lo <= d <= hi:
                c = (ox + dc, oy + dr)
                if state.map.in_bounds(c):
                    out.add(c)
    return out
