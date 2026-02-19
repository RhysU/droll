# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with treasure inventory management."""

from dataclasses import replace

from .dice import RandRange
from .error import DrollError
from .struct import Artifacts, Treasure, field_items, field_values

__all__ = (
    "draw_treasure",
    "replace_treasure",
)


def _draw(box: Artifacts, randrange: RandRange) -> str:
    """Draw a random treasure from the box, weighted by counts."""
    total = sum(field_values(box))
    if not total:
        raise RuntimeError("No items remaining in the box")
    choice = randrange(0, total)
    cumulative = 0
    for name, count in field_items(box):
        cumulative += count
        if choice < cumulative:
            return name
    raise RuntimeError("Unreachable")


def draw_treasure(treasure: Treasure, randrange: RandRange) -> Treasure:
    """Draw a single item from the box into the player's own artifacts."""
    drawn = _draw(box=treasure.box, randrange=randrange)
    return replace(
        treasure,
        own=replace(
            treasure.own, **{drawn: getattr(treasure.own, drawn) + 1}
        ),
        box=replace(
            treasure.box, **{drawn: getattr(treasure.box, drawn) - 1}
        ),
    )


def replace_treasure(treasure: Treasure, item: str) -> Treasure:
    """Replace a single item from the player's own artifacts into the box."""
    prior_count = getattr(treasure.own, item)
    if not prior_count:
        raise DrollError(f"'{item}' not in player's treasure.")
    return replace(
        treasure,
        own=replace(treasure.own, **{item: prior_count - 1}),
        box=replace(
            treasure.box, **{item: getattr(treasure.box, item) + 1}
        ),
    )
