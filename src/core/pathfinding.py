"""Grid pathfinding. Dijkstra over per-unit-class terrain costs, with allied pass-through."""
from __future__ import annotations

import heapq

from src.core.coord import neighbors4
from src.core.game_state import GameState
from src.core.types import IMPASSABLE, Coord, VisState
from src.entities.unit import Unit


def reachable(state: GameState, unit: Unit,
              respect_fog: bool = True) -> dict[Coord, int]:
    """Tiles the unit can reach this turn, mapped to movement-point cost to arrive.

    Enemy units block entry. Allied units may be passed through but cannot be a stopping point
    (they are excluded from the returned dict).
    """
    start = unit.coord
    budget = type(unit).move
    unit_cls = type(unit).unit_class

    # Fog rule (Wargroove/AW style): a unit cannot step onto a tile that is HIDDEN
    # to its owner's fog-of-war. Explored and visible tiles are fine — you remember
    # where the roads were — but you don't blindly charge into unknown territory.
    player = state.players.get(unit.owner_id)
    vis = player.visibility if (player and respect_fog) else None

    def _is_hidden(c: Coord) -> bool:
        if vis is None:
            return False
        col, row = c
        return vis[col][row] == VisState.HIDDEN

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
            if _is_hidden(n):
                continue  # can't path through fog
            # Enemy unit blocks entirely; allied unit allows passage but not a stopping point.
            occupant = state.units.get(tile.unit_id) if tile.unit_id is not None else None
            if occupant is not None and occupant.is_alive and occupant.owner_id != unit.owner_id:
                continue
            # Buildings owned by others (or neutral) block entry entirely — they have to
            # be attacked to flip ownership. Own buildings are passable.
            building = state.buildings.get(tile.building_id) if tile.building_id is not None else None
            if building is not None and building.owner_id != unit.owner_id:
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


def path_to(state: GameState, unit: Unit, destination: Coord,
            respect_fog: bool = True) -> list[Coord]:
    """Shortest path from `unit.coord` to `destination` as a list of tiles
    (including start and end). Returns [] if the destination is unreachable.

    Used for movement animation: the UI walks a unit sprite along each tile in turn.
    """
    start = unit.coord
    if start == destination:
        return [start]
    budget = type(unit).move
    unit_cls = type(unit).unit_class
    player = state.players.get(unit.owner_id)
    vis = player.visibility if (player and respect_fog) else None

    parent: dict[Coord, Coord] = {}
    dist: dict[Coord, int] = {start: 0}
    frontier: list[tuple[int, Coord]] = [(0, start)]

    while frontier:
        cost_here, c = heapq.heappop(frontier)
        if cost_here > dist.get(c, IMPASSABLE):
            continue
        if c == destination:
            break
        for n in neighbors4(c):
            if not state.map.in_bounds(n):
                continue
            tile = state.map.tile(n)
            step = tile.terrain.cost_for(unit_cls)
            if step >= IMPASSABLE:
                continue
            if vis is not None and vis[n[0]][n[1]] == VisState.HIDDEN:
                continue
            occupant = state.units.get(tile.unit_id) if tile.unit_id is not None else None
            if occupant is not None and occupant.is_alive and occupant.owner_id != unit.owner_id:
                continue
            building = state.buildings.get(tile.building_id) if tile.building_id is not None else None
            if building is not None and building.owner_id != unit.owner_id:
                continue
            new_cost = cost_here + step
            if new_cost > budget:
                continue
            if new_cost < dist.get(n, IMPASSABLE):
                dist[n] = new_cost
                parent[n] = c
                heapq.heappush(frontier, (new_cost, n))

    if destination not in dist:
        return []
    # Backtrace
    path = [destination]
    while path[-1] != start:
        path.append(parent[path[-1]])
    return list(reversed(path))


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
