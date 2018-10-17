# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with rolling dungeon and party dice."""

import typing

from . import struct

RandRange = typing.Callable[[int, int], int]
RollDungeon = typing.Callable[[int, RandRange], struct.Dungeon]
RollParty = typing.Callable[[int, RandRange], struct.Party]


def _roll(
        dice: int,
        start: int,
        stop: int,
        randrange: RandRange
) -> typing.List[int]:
    assert dice >= 0, "At least one die must be requested"
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
        *_roll(dice, 0, len(struct.Dungeon._fields), randrange))


def roll_party(dice: int, randrange: RandRange) -> struct.Party:
    """Roll a new Party using given number of dice.

    Any implementation must follow type signature of RollParty."""
    return struct.Party(*_roll(dice, 0, len(struct.Party._fields), randrange))
