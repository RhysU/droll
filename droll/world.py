# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import copy
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


def _roll(
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


def roll_level(dice: int, randrange: RandRange) -> Level:
    """Roll a new Level using given number of dice.

    On Level N one should account for the number of extant dragons.
    random.Random.randrange or random.randrange are accepted for randomness."""
    return Level(*_roll(dice, 0, len(Level._fields), randrange))


Party = collections.namedtuple('Party', (
    'fighter',
    'cleric',
    'mage',
    'thief',
    'champion',
    'scroll',
))


def roll_party(dice: int, randrange: RandRange) -> Party:
    """Roll a new Party using given number of dice.

    random.Random.randrange or random.randrange are accepted for randomness."""
    return Party(*_roll(dice, 0, len(Party._fields), randrange))


_CHEST = collections.OrderedDict((
    ('sword', 3),
    ('talisman', 3),
    ('sceptre', 3),
    ('tools', 3),
    ('scroll', 3),
    ('elixir', 3),
    ('bait', 4),
    ('portal', 4),
    ('ring', 4),
    ('scale', 6),
))

Treasure = collections.namedtuple('Treasure', _CHEST.keys())

CHEST_INITIAL = Treasure(*_CHEST.values())

TREASURE_INITIAL = Treasure(*([0] * len(_CHEST)))

def _draw(chest: Treasure, randrange: RandRange) -> str:
    seq = functools.reduce(
        itertools.chain,
        (itertools.repeat(t, chest[i])
         for i, t in enumerate(Treasure._fields)),
        [])
    seq = tuple(seq)
    return seq[randrange(0, len(seq))]


def draw_treasure(
        treasure: Treasure,
        chest: Treasure,
        randrange: RandRange,
) -> typing.Tuple[Treasure, Treasure]:
    drawn = _draw(chest=chest, randrange=randrange)
    treasure = treasure._replace(**{drawn: getattr(treasure, drawn) + 1})
    chest = chest._replace(**{drawn: getattr(chest, drawn) - 1})
    return treasure, chest


def replace_treasure(
        treasure: Treasure,
        chest: Treasure,
        item: str,
) -> typing.Tuple[Treasure, Treasure]:
    assert getattr(treasure, item) > 1
    treasure = treasure._replace(**{item: getattr(treasure, item) - 1})
    chest = chest._replace(**{item: getattr(chest, item) + 1})
    return treasure, chest


World = collections.namedtuple('World', (
    'depth',
    'experience',
    'ability',
    'level',
    'party',
    'treasure',
    'chest',
))


def new_game() -> World:
    """Establish a new game independent of a delve/level."""
    return World(
        depth=None,
        experience=0,
        ability=None,
        level=None,
        party=None,
        treasure=copy.deepcopy(TREASURE_INITIAL),
        chest=copy.deepcopy(CHEST_INITIAL),
    )


def new_delve(world: World, randrange: RandRange) -> World:
    """Establish a new delve within an existing game."""
    return world._replace(
        depth=0,
        ability=True,
        party=roll_party(dice=7, randrange=randrange),
    )


def next_level(world: World, randrange: RandRange) -> World:
    """Move one level deeper in the dungeon."""
    next_depth = world.depth + 1
    assert next_depth <= 10
    prior_dragons = world.level.dragon
    level = roll_level(dice=(next_depth - prior_dragons), randrange=randrange)
    level = level._replace(dragon=level.dragon + prior_dragons)
    return world._replace(depth=next_depth, level=level)
