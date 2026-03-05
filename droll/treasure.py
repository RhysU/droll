# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with treasure inventory management."""

from dataclasses import replace

from .struct import (
    Artifact,
    ArtifactCounts,
    DrollError,
    RandRange,
    Treasure,
    frozen,
)

__all__ = (
    "draw_treasure",
    "replace_treasure",
)


def _draw(box: ArtifactCounts, randrange: RandRange) -> Artifact:
    """Draw a random treasure from the box, weighted by counts."""
    total = sum(box.values())
    if not total:
        raise DrollError("No items remaining in the box")
    choice = randrange(0, total)
    cumulative = 0
    for artifact, count in box.items():
        cumulative += count
        if choice < cumulative:
            return artifact
    raise RuntimeError("Unreachable")


def draw_treasure(treasure: Treasure, randrange: RandRange) -> Treasure:
    """Draw a single item from the box into the player's own artifacts."""
    drawn = _draw(box=treasure.box, randrange=randrange)
    return replace(
        treasure,
        own=frozen({**treasure.own, drawn: treasure.own[drawn] + 1}),
        box=frozen({**treasure.box, drawn: treasure.box[drawn] - 1}),
    )


def replace_treasure(treasure: Treasure, item: Artifact) -> Treasure:
    """Replace a single item from the player's own artifacts into the box."""
    if item not in treasure.own:
        raise DrollError(f"'{item.value}' is not a valid treasure type.")
    prior_count = treasure.own[item]
    if not prior_count:
        raise DrollError(f"'{item.value}' not in player's treasure.")
    return replace(
        treasure,
        own=frozen({**treasure.own, item: prior_count - 1}),
        box=frozen({**treasure.box, item: treasure.box[item] + 1}),
    )
