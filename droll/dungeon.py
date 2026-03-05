# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with dungeon state and dungeon mechanics."""

from typing import Optional

from .struct import DrollError, Dungeon, DungeonState, frozen

__all__ = (
    "DRAGON_BLOCKING_THRESHOLD",
    "blocking_dragon",
    "decrement_dungeon",
    "defeated_dungeon",
    "defeated_monsters",
    "eliminate_dungeon",
    "finished_dungeon",
    "increment_dungeon",
)

# A dragon blocks progress when this many or more dragon dice are present.
DRAGON_BLOCKING_THRESHOLD = 3


def defeated_monsters(dungeon: Optional[DungeonState]) -> bool:
    """Are all non-dragon monsters on this dungeon defeated?"""
    return (dungeon is None) or (
        dungeon[Dungeon.GOBLIN] + dungeon[Dungeon.SKELETON] + dungeon[Dungeon.OOZE]
    ) == 0


def defeated_dungeon(dungeon: Optional[DungeonState]) -> bool:
    """Are all monsters and any dragon on this dungeon defeated?"""
    return (dungeon is None) or (
        defeated_monsters(dungeon) and dungeon[Dungeon.DRAGON] < DRAGON_BLOCKING_THRESHOLD
    )


def blocking_dragon(dungeon: DungeonState) -> bool:
    """Is a dragon blocking progress to the next level?"""
    return defeated_monsters(dungeon) and not defeated_dungeon(dungeon)


def finished_dungeon(dungeon: Optional[DungeonState]) -> bool:
    """Has the player exhausted all possible actions for this dungeon?

    In contrast to defeated_dungeon(...), returns True if chests/etc remain."""
    return (dungeon is None) or (
        (sum(dungeon.values()) - dungeon[Dungeon.DRAGON] == 0)
        and not blocking_dragon(dungeon)
    )


def decrement_dungeon(dungeon: DungeonState, target: Dungeon) -> DungeonState:
    """Decrease the count of the specified target type by one."""
    prior_targets = dungeon[target]
    if not prior_targets:
        raise DrollError(f"At least 1 {target.value} required in dungeon.")
    return frozen({**dungeon, target: prior_targets - 1})


def increment_dungeon(dungeon: DungeonState, target: Dungeon) -> DungeonState:
    """Increase the count of the specified target type by one."""
    return frozen({**dungeon, target: dungeon[target] + 1})


def eliminate_dungeon(dungeon: DungeonState, target: Dungeon) -> DungeonState:
    """Remove all targets of the specified type from the dungeon."""
    prior_targets = dungeon[target]
    if not prior_targets:
        raise DrollError(f"At least 1 {target.value} required in dungeon.")
    return frozen({**dungeon, target: 0})
