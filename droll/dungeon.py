# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with dungeon state and dungeon mechanics."""

from dataclasses import replace
from typing import Optional

from .struct import DrollError, Dungeon, field_values

__all__ = (
    "blocking_dragon",
    "decrement_dungeon",
    "defeated_dungeon",
    "defeated_monsters",
    "eliminate_dungeon",
    "finished_dungeon",
    "increment_dungeon",
)


def defeated_monsters(dungeon: Optional[Dungeon]) -> bool:
    """Are all non-dragon monsters on this dungeon defeated?"""
    return (dungeon is None) or (
        dungeon.goblin + dungeon.skeleton + dungeon.ooze
    ) == 0


def defeated_dungeon(dungeon: Optional[Dungeon]) -> bool:
    """Are all monsters and any dragon on this dungeon defeated?"""
    return (dungeon is None) or (
        defeated_monsters(dungeon) and dungeon.dragon < 3
    )


def blocking_dragon(dungeon: Dungeon) -> bool:
    """Is a dragon blocking progress to the next level?"""
    return defeated_monsters(dungeon) and not defeated_dungeon(dungeon)


def finished_dungeon(dungeon: Optional[Dungeon]) -> bool:
    """Has the player exhausted all possible actions for this dungeon?

    In contrast to defeated_dungeon(...), returns True if chests/etc remain."""
    return (dungeon is None) or (
        (sum(field_values(dungeon)) - dungeon.dragon == 0)
        and not blocking_dragon(dungeon)
    )


def decrement_dungeon(dungeon: Dungeon, target: str) -> Dungeon:
    """Decrease the count of the specified target type by one."""
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise DrollError(f"At least 1 {target} required in dungeon.")
    return replace(dungeon, **{target: prior_targets - 1})


def increment_dungeon(dungeon: Dungeon, target: str) -> Dungeon:
    """Increase the count of the specified target type by one."""
    prior_targets = getattr(dungeon, target, 0)
    return replace(dungeon, **{target: prior_targets + 1})


def eliminate_dungeon(dungeon: Dungeon, target: str) -> Dungeon:
    """Remove all targets of the specified type from the dungeon."""
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise DrollError(f"At least 1 {target} required in dungeon.")
    return replace(dungeon, **{target: 0})
