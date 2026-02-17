# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with rolling dungeon and party dice."""

import collections.abc

from dataclasses import fields

from . import struct

__all__ = (
    "RandRange",
    "RollDungeon",
    "RollParty",
    "roll_dungeon",
    "roll_party",
)

RandRange = collections.abc.Callable[[int, int], int]
RollDungeon = collections.abc.Callable[[int, RandRange], struct.Dungeon]
RollParty = collections.abc.Callable[[int, RandRange], tuple[struct.Party, struct.Regroup]]


def _roll(
    dice: int, start: int, stop: int, randrange: RandRange
) -> list[int]:
    """Roll dice and return counts for each outcome in the range [start, stop)."""
    assert dice >= 0, "Dice count must be non-negative"
    result = [0] * (stop - start)
    for _ in range(dice):
        result[randrange(start, stop)] += 1
    return result


def roll_dungeon(dice: int, randrange: RandRange) -> struct.Dungeon:
    """Roll a new Dungeon using given number of dice.

    Any implementation must follow type signature of RollDungeon.
    On Dungeon N one should account for the number of extant dragons."""
    assert dice >= 1, "At least one dice required (requested {})".format(dice)
    return struct.Dungeon(
        *_roll(dice, 0, len(fields(struct.Dungeon)), randrange)
    )


def roll_party(
    dice: int, randrange: RandRange
) -> tuple[struct.Party, struct.Regroup]:
    """Roll a new Party using given number of dice.

    Any implementation must follow type signature of RollParty."""
    return (
        struct.Party(*_roll(dice, 0, len(fields(struct.Party)), randrange)),
        struct.Regroup(),
    )
