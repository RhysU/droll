# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with game state and world mechanics."""

import collections
import copy
import functools
import itertools
import typing


class WorldError(RuntimeError):
    """Indicates attempts to make impossible world changes.."""
    pass


Level = collections.namedtuple('Level', (
    'goblin',
    'skeleton',
    'ooze',
    'chest',
    'potion',
    'dragon',
))


def defeated_monsters(level: Level) -> bool:
    """Are all non-dragon monsters on this level defeated?"""
    return (level is None) or 0 == (level.goblin + level.skeleton + level.ooze)


def defeated_level(level: Level) -> bool:
    """Are all monsters and any dragon on this level defected?"""
    return (level is None) or (defeated_monsters(level) and level.dragon < 3)


# random.Random.randrange or random.randrange are accepted for randomness.
# Note, too, that a deterministic function may be provided for testing.
RandRange = typing.Callable[[int, int], int]


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


def roll_level(dice: int, randrange: RandRange) -> Level:
    """Roll a new Level using given number of dice.

    On Level N one should account for the number of extant dragons."""
    assert dice >= 1, "At least one dice required (requested {})".format(dice)
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
    """Roll a new Party using given number of dice."""
    return Party(*_roll(dice, 0, len(Party._fields), randrange))


_RESERVE = collections.OrderedDict((
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

Treasure = collections.namedtuple('Treasure', _RESERVE.keys())

RESERVE_INITIAL = Treasure(*_RESERVE.values())

TREASURE_INITIAL = Treasure(*([0] * len(_RESERVE)))

World = collections.namedtuple('World', (
    'delve',
    'depth',
    'experience',
    'ability',
    'level',
    'party',
    'treasure',
    'reserve',
))


def new_game() -> World:
    """Establish a new game independent of a delve/level."""
    return World(
        delve=0,
        depth=None,
        experience=0,
        ability=None,
        level=None,
        party=None,
        treasure=copy.deepcopy(TREASURE_INITIAL),
        reserve=copy.deepcopy(RESERVE_INITIAL),
    )


def new_delve(world: World, randrange: RandRange, *, party_dice=7) -> World:
    """Establish a new delve within an existing game."""
    if world.delve == 3:
        raise WorldError("At most three delves are permitted.")
    return world._replace(
        delve=world.delve + 1,
        depth=0,
        ability=True,
        party=roll_party(dice=party_dice, randrange=randrange),
    )


# TODO next_level understands rings of invisibility
def next_level(
        world: World, randrange: RandRange, *,
        max_depth=10,
        level_dice=7
) -> World:
    """Move one level deeper in the dungeon, retaining any partial dragons.

    Adheres to the specified number of dice available in the game."""
    if not defeated_level(world.level):
        raise WorldError("Current level is not yet complete")
    next_depth = world.depth + 1
    if next_depth > max_depth:
        raise WorldError("The maximum depth is {}".format(max_depth))
    prior_dragons = 0 if world.level is None else world.level.dragon
    level = roll_level(dice=min(level_dice - prior_dragons, next_depth),
                       randrange=randrange)
    level = level._replace(dragon=level.dragon + prior_dragons)
    return world._replace(depth=next_depth, level=level)


# TODO Upgrade hero's ability after hitting 5 experience points
# TODO Retire understands town portals
# TODO Retire understands rings of invisibility
def retire(world: World) -> World:
    """Retire to the tavern after completing the present level."""
    if not defeated_level(world.level):
        raise WorldError("Current level is not yet complete")
    return world._replace(
        depth=0,
        experience=world.depth,
        level=None,
    )


# TODO Dragon bait turns all remaining dungeon dice into dragons
# TODO Elixir can be swapped for any party dice


def score(world: World) -> int:
    """Compute the present score for the game, including all treasure."""
    return (
            world.experience +
            sum(world.treasure) +  # Each piece of treasure is +1 point
            world.treasure.portal +  # Portals are each +1 point (2 total)
            world.treasure.scale // 2  # Pairs of scales are +1 point
    )


# There are likely much, much faster implementations.
def _draw(reserve: Treasure, randrange: RandRange) -> str:
    seq = functools.reduce(
        itertools.chain,
        (itertools.repeat(t, reserve[i])
         for i, t in enumerate(Treasure._fields)),
        [])
    seq = tuple(seq)
    assert len(seq) > 1, "Presently no items remaining in the reserve"
    return seq[randrange(0, len(seq))]


def draw_treasure(world: World, randrange: RandRange) -> World:
    """Draw a single item from the reserve into the player's treasures."""
    drawn = _draw(reserve=world.reserve, randrange=randrange)
    treasure = world.treasure._replace(
        **{drawn: getattr(world.treasure, drawn) + 1})
    reserve = world.reserve._replace(
        **{drawn: getattr(world.reserve, drawn) - 1}
    )
    return world._replace(treasure=treasure, reserve=reserve)


def replace_treasure(world: World, item: str) -> World:
    """Replace a single item from the player's treasures into the reserve."""
    prior_count = getattr(world.treasure, item)
    if not prior_count:
        raise WorldError("'{}' not in player's treasure".format(item))
    return world._replace(
        treasure=world.treasure._replace(
            **{item: prior_count - 1}),
        reserve=world.reserve._replace(
            **{item: getattr(world.reserve, item) + 1})
    )


def __throw_if_no_ring_of_invisibility(world: World) -> World:
    """Attempt to use a ring of invisibility to 'sneak' past a dragon."""
    return replace_treasure(world, 'ring')


def __throw_if_no_town_portal(world: World) -> World:
    """Attempt to use a town portal to retire to town."""
    return replace_treasure(world, 'portal')
