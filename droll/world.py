# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with game state and world mechanics."""

import collections
import copy
import functools
import itertools
import typing

from .error import DrollError

Dungeon = collections.namedtuple('Dungeon', (
    'goblin',
    'skeleton',
    'ooze',
    'chest',
    'potion',
    'dragon',
))


def defeated_monsters(dungeon: Dungeon) -> bool:
    """Are all non-dragon monsters on this dungeon defeated?"""
    return (dungeon is None) or 0 == (dungeon.goblin +
                                      dungeon.skeleton +
                                      dungeon.ooze)


def defeated_dungeon(dungeon: Dungeon) -> bool:
    """Are all monsters and any dragon on this dungeon defected?"""
    return (dungeon is None) or (defeated_monsters(dungeon) and
                                 dungeon.dragon < 3)


def blocking_dragon(dungeon: Dungeon) -> bool:
    """Is a dragon blocking progress to the next level?"""
    return defeated_monsters(dungeon) and not defeated_dungeon(dungeon)


def exhausted_dungeon(dungeon: Dungeon) -> bool:
    """Has the player exhausted all possible actions for this dungeon?

    In contrast to defeated_dungeon(...), returns True if chests/etc remain."""
    return (dungeon is None) or ((0 == sum(dungeon) - dungeon.dragon) and
                                 not blocking_dragon(dungeon))


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


def roll_dungeon(dice: int, randrange: RandRange) -> Dungeon:
    """Roll a new Dungeon using given number of dice.

    On Dungeon N one should account for the number of extant dragons."""
    assert dice >= 1, "At least one dice required (requested {})".format(dice)
    return Dungeon(*_roll(dice, 0, len(Dungeon._fields), randrange))


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
    'dungeon',
    'party',
    'ability',
    'treasure',
    'reserve',
))


def new_game() -> World:
    """Establish a new game independent of a delve/dungeon."""
    return World(
        delve=0,
        depth=None,
        experience=0,
        ability=None,
        dungeon=None,
        party=None,
        treasure=copy.deepcopy(TREASURE_INITIAL),
        reserve=copy.deepcopy(RESERVE_INITIAL),
    )


def next_delve(
        world: World,
        randrange: RandRange,
        transformer: typing.Callable[[Party], Party],
        *,
        _party_dice=7
) -> World:
    """Establish new delve within a game, optionally transforming the party."""
    if world.delve >= 3:
        raise DrollError("At most three delves are permitted.")
    return world._replace(
        delve=(world.delve if world.delve else 0) + 1,
        depth=0,
        ability=True,
        dungeon=None,
        party=roll_party(dice=_party_dice, randrange=randrange),
    )


def next_dungeon(
        world: World, randrange: RandRange, *,
        _max_depth=10,
        _dungeon_dice=7
) -> World:
    """Move one dungeon deeper in the dungeon, retaining any partial dragons.

    If necessary, a ring of invisibility will be used to sneak past a dragon.
    Adheres to the specified number of dice available in the game."""
    if not defeated_monsters(world.dungeon):
        raise DrollError('Must defeat enemies to proceed to next dungeon.')

    if not defeated_dungeon(world.dungeon):
        try:
            world = apply_ring(world)
        except DrollError:
            raise DrollError("Dragon remains but a ring of"
                             " invisibility is not in hand.")

    # Success above, so update the world in anticipation of the next dungeon
    next_depth = (world.depth if world.depth else 0) + 1
    if next_depth > _max_depth:
        raise DrollError("The maximum depth is {}".format(_max_depth))
    prior_dragons = 0 if world.dungeon is None else world.dungeon.dragon
    dungeon = roll_dungeon(dice=min(_dungeon_dice - prior_dragons, next_depth),
                           randrange=randrange)
    dungeon = dungeon._replace(dragon=dungeon.dragon + prior_dragons)
    return world._replace(depth=next_depth, dungeon=dungeon)


def retire(world: World) -> World:
    """Retire to the tavern after completing the present dungeon.

    If monsters or a dragon remains, either ring of invisibility or
    a town portal will be used when available."""
    if world.depth == 0:
        raise DrollError("Descend at least once prior to retiring.")

    if not defeated_monsters(world.dungeon):
        try:
            world = apply_portal(world)
        except DrollError:
            raise DrollError('Monsters remain but no town portal in hand.')
    elif blocking_dragon(world.dungeon):
        # First attempt to use a ring then a portal (because portals are +2)
        try:
            world = apply_ring(world)
        except DrollError:
            try:
                world = apply_portal(world)
            except DrollError:
                raise DrollError("Dragon remains but neither a ring of"
                                 " invisibility nor a town portal in hand.")

    # TODO Upgrade hero's ability after hitting 5 experience points
    # Success above, so update the world in anticipation of the next delve
    return world._replace(
        depth=0,
        experience=world.experience + world.depth,
        dungeon=None,
    )


def retreat(world: World) -> World:
    """Retreat to the tavern without completing the present dungeon."""
    if world.depth == 0:
        raise DrollError("Descend at least once prior to retreating.")
    if defeated_dungeon(world.dungeon):
        raise DrollError("Why retreat when you could instead retire?")

    return world._replace(
        depth=0,
        dungeon=None,
    )


def score(world: World) -> int:
    """Compute the present score for the game, including all treasure."""
    return (
            world.experience +
            sum(world.treasure) +  # Each piece of treasure is +1 point
            world.treasure.portal +  # Portals are each +1 point (2 total)
            2 * (world.treasure.scale // 2)  # Pairs of scales are +2 points
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
        raise DrollError("'{}' not in player's treasure".format(item))
    return world._replace(
        treasure=world.treasure._replace(
            **{item: prior_count - 1}),
        reserve=world.reserve._replace(
            **{item: getattr(world.reserve, item) + 1})
    )


def apply_ring(world: World, *, noun: str = 'ring') -> World:
    """Attempt to use a ring of invisibility towards sneaking past a dragon."""
    if not blocking_dragon(world.dungeon):
        raise DrollError('A dragon must be present to use a {}'.format(noun))
    world = replace_treasure(world, noun)
    return world._replace(dungeon=world.dungeon._replace(dragon=0))


def apply_portal(world: World, *, noun: str = 'portal') -> World:
    """Attempt to use a town portal towards retiring to town."""
    # No need to reset monsters/dragon as dungeon will be wholly replaced
    if defeated_dungeon(world.dungeon):
        raise DrollError('No need to apply {} when dungeon clear'.format(noun))
    return replace_treasure(world, 'portal')._replace(
        dungeon=Dungeon(*([0] * len(Dungeon._fields)))
    )
