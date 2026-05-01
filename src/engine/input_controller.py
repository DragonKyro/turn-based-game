"""Translate grid clicks into Actions, given the current selection and the reachable set.

This module is the only place that knows about the "select -> show range -> click -> act"
UX. Input logic lives here instead of scattered across the arcade view.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.core.actions import Action, AttackAction, CaptureAction, MoveAction
from src.core.coord import manhattan
from src.core.game_state import GameState
from src.core.pathfinding import attackable_from
from src.core.types import Coord


@dataclass
class ClickResult:
    """What the controller decided. Action may be None when the click only changes selection."""
    actions: list[Action]
    new_selection: int | None         # unit_id after the click
    new_selection_coord: Coord | None  # stays in sync for drawing the range overlay


def interpret_click(
    state: GameState,
    selected_unit_id: int | None,
    clicked: Coord,
    reachable_tiles: dict[Coord, int] | None,
) -> ClickResult:
    """Decide what the click means.

    Branches:
      - No selection + clicked own not-yet-moved unit -> select it.
      - Selection + click on reachable empty tile -> MoveAction.
      - Selection + click on adjacent-after-move enemy -> attempt Move+Attack (simple v1 path: if
        already adjacent, just AttackAction; otherwise Move then attack is staged in two clicks).
      - Selection + click on enemy-owned capturable building the selected infantry stands on -> CaptureAction.
      - Selection + click on own selected unit tile -> Wait (move-in-place).
      - Otherwise -> clear selection.
    """
    clicked_unit = state.unit_at(clicked)
    clicked_building = state.building_at(clicked)

    # Nothing selected yet.
    if selected_unit_id is None:
        if clicked_unit:
            # Own unit that can still act: select it normally (range overlays computed below).
            # Enemy unit OR own-spent unit: select for viewing only (panel shows stats).
            return ClickResult(
                actions=[], new_selection=clicked_unit.id,
                new_selection_coord=clicked_unit.coord,
            )
        return ClickResult(actions=[], new_selection=None, new_selection_coord=None)

    selected = state.units.get(selected_unit_id)
    if selected is None or not selected.is_alive:
        return ClickResult(actions=[], new_selection=None, new_selection_coord=None)

    # Allow clicking another of our own units to reselect.
    if clicked_unit and clicked_unit.owner_id == state.current_player_id and clicked_unit.id != selected.id:
        if not clicked_unit.has_acted:
            return ClickResult(actions=[], new_selection=clicked_unit.id, new_selection_coord=clicked_unit.coord)

    # Attacking / move-then-attack in one click.
    if clicked_unit and clicked_unit.owner_id != state.current_player_id:
        if not selected.has_acted:
            # 1) Already in range from current tile — straight attack.
            attack_set = attackable_from(state, selected, selected.coord)
            if clicked in attack_set:
                return ClickResult(
                    actions=[AttackAction(unit_id=selected.id, target_unit_id=clicked_unit.id)],
                    new_selection=None,
                    new_selection_coord=None,
                )
            # 2) Find a reachable tile from which the target IS in range. If one exists,
            #    queue a Move into that tile followed by the Attack — one click, two actions.
            if reachable_tiles and not selected.has_moved:
                best: Coord | None = None
                best_cost = 10**9
                for tile, cost in reachable_tiles.items():
                    if clicked in attackable_from(state, selected, tile):
                        if cost < best_cost:
                            best = tile
                            best_cost = cost
                if best is not None:
                    return ClickResult(
                        actions=[
                            MoveAction(unit_id=selected.id, destination=best),
                            AttackAction(unit_id=selected.id, target_unit_id=clicked_unit.id),
                        ],
                        new_selection=None,
                        new_selection_coord=None,
                    )
        # Can't reach an attack position — show the enemy's stats instead.
        return ClickResult(
            actions=[], new_selection=clicked_unit.id,
            new_selection_coord=clicked_unit.coord,
        )

    # Capture: infantry stands on a capturable building.
    if (
        clicked == selected.coord
        and clicked_building is not None
        and clicked_building.owner_id != selected.owner_id
        and selected.kind == "infantry"
        and not selected.has_acted
    ):
        return ClickResult(
            actions=[CaptureAction(unit_id=selected.id, building_id=clicked_building.id)],
            new_selection=None,
            new_selection_coord=None,
        )

    # Waiting in place (clicking self).
    if clicked == selected.coord and not selected.has_moved:
        return ClickResult(
            actions=[MoveAction(unit_id=selected.id, destination=selected.coord)],
            new_selection=None,
            new_selection_coord=None,
        )

    # Moving to a reachable empty tile.
    if reachable_tiles is not None and clicked in reachable_tiles and not selected.has_moved:
        return ClickResult(
            actions=[MoveAction(unit_id=selected.id, destination=clicked)],
            new_selection=None,
            new_selection_coord=None,
        )

    # Anything else: clear selection.
    _ = manhattan  # silence unused import in v1
    return ClickResult(actions=[], new_selection=None, new_selection_coord=None)
