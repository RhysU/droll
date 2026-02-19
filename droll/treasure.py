# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with treasure inventory management."""

from dataclasses import replace

from .dice import RandRange
from .error import DrollError
from .struct import Treasure, World, field_items, field_values

__all__ = (
    "draw_treasure",
    "replace_treasure",
)


def _draw(reserve: Treasure, randrange: RandRange) -> str:
    """Draw a random treasure from the reserve, weighted by counts."""
    total = sum(field_values(reserve))
    if not total:
        raise RuntimeError("No items remaining in the reserve")
    choice = randrange(0, total)
    cumulative = 0
    for name, count in field_items(reserve):
        cumulative += count
        if choice < cumulative:
            return name
    raise RuntimeError("Unreachable")


def draw_treasure(world: World, randrange: RandRange) -> World:
    """Draw a single item from the reserve into the player's treasures."""
    drawn = _draw(reserve=world.reserve, randrange=randrange)
    return replace(
        world,
        treasure=replace(
            world.treasure, **{drawn: getattr(world.treasure, drawn) + 1}
        ),
        reserve=replace(
            world.reserve, **{drawn: getattr(world.reserve, drawn) - 1}
        ),
    )


def replace_treasure(world: World, item: str) -> World:
    """Replace a single item from the player's treasures into the reserve."""
    prior_count = getattr(world.treasure, item)
    if not prior_count:
        raise DrollError(f"'{item}' not in player's treasure.")
    return replace(
        world,
        treasure=replace(world.treasure, **{item: prior_count - 1}),
        reserve=replace(
            world.reserve, **{item: getattr(world.reserve, item) + 1}
        ),
    )
