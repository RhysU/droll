# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with rolling dungeon and party dice."""

from .struct import (
    Dungeon,
    DungeonState,
    Party,
    PartyState,
    RandRange,
    Regroup,
    frozen,
)

__all__ = (
    "roll_dungeon",
    "roll_party",
)


def _roll(dice: int, start: int, stop: int, randrange: RandRange) -> list[int]:
    """Roll dice returning counts for outcomes in the range [start, stop)."""
    assert dice >= 0, "Dice count must be non-negative"
    result = [0] * (stop - start)
    for _ in range(dice):
        result[randrange(start, stop)] += 1
    return result


def roll_dungeon(dice: int, randrange: RandRange) -> DungeonState:
    """Roll a new Dungeon using given number of dice.

    Any implementation must follow type signature of RollDungeon.
    On Dungeon N one should account for the number of extant dragons."""
    assert dice >= 1, f"At least one dice required (requested {dice})"
    return frozen(dict(zip(Dungeon, _roll(dice, 0, len(Dungeon), randrange))))


def roll_party(dice: int, randrange: RandRange) -> tuple[PartyState, Regroup]:
    """Roll a new Party using given number of dice.

    Any implementation must follow type signature of RollParty."""
    return (
        frozen(dict(zip(Party, _roll(dice, 0, len(Party), randrange)))),
        Regroup(),
    )
