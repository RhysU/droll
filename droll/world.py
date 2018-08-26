# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import functools
import itertools
import typing

Level = collections.namedtuple('Level', (
    'goblin',
    'skeleton',
    'ooze',
    'chest',
    'potion',
    'dragon',
))

RandRange = typing.Callable[[int, int], int]


def __roll(
        dice: int,
        start: int,
        stop: int,
        randrange: RandRange
) -> typing.List[int]:
    assert dice >= 0
    result = [0] * (stop - start)
    for _ in range(dice):
        result[randrange(start, stop)] += 1
    return result


def roll_level(dice: int, randgen: RandRange) -> Level:
    """Roll a new Level using given number of dice.

    On Level N one should account for the number of extant dragons.
    random.Random.randgen or random.randgen are accepted for randomness."""
    return Level(*__roll(dice, 0, len(Level._fields), randgen))


Party = collections.namedtuple('Party', (
    'fighter',
    'cleric',
    'mage',
    'thief',
    'champion',
    'scroll',
))


def roll_party(dice: int, randgen: RandRange) -> Party:
    """Roll a new Party using given number of dice.

    random.Random.randgen or random.randgen are accepted for randomness."""
    return Party(*__roll(dice, 0, len(Party._fields), randgen))


_TREASURE = collections.OrderedDict(
    sword=3,
    talisman=3,
    sceptre=3,
    tools=3,
    scroll=3,
    elixir=3,
    bait=4,
    portal=4,
    ring=4,
    scale=6,
)

Treasure = collections.namedtuple('Treasure', _TREASURE.keys())

TREASURE_INITIAL = Treasure(*_TREASURE.values())

Choice = typing.Callable[[typing.Sequence[typing.Any]], typing.Any]


def add_treasure(
        treasure: Treasure,
        chest: Treasure,
        choice: Choice,
) -> typing.Tuple[Treasure, Treasure]:
    seq = functools.reduce(
        itertools.chain,
        (itertools.repeat(t, chest[i])
         for i, t in enumerate(Treasure._fields)),
        [])
    drawn = choice(tuple(seq))
    # TODO Remove from chest
    # TODO Update treasure
    return drawn


World = collections.namedtuple('World', (
    'experience',
    'ability',
    'level',
    'party',
    'treasure',
    'chest',
))
