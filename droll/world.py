# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with world state and world mechanics."""

from dataclasses import replace

from . import dice
from . import error
from . import struct


TREASURE_INITIAL = struct.Treasure()

RESERVE_INITIAL = struct.Treasure(
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


def defeated_monsters(dungeon: struct.Dungeon) -> bool:
    """Are all non-dragon monsters on this dungeon defeated?"""
    return (dungeon is None) or 0 == (
        dungeon.goblin + dungeon.skeleton + dungeon.ooze
    )


def defeated_dungeon(dungeon: struct.Dungeon) -> bool:
    """Are all monsters and any dragon on this dungeon defected?"""
    return (dungeon is None) or (
        defeated_monsters(dungeon) and dungeon.dragon < 3
    )


def _blocking_dragon(dungeon: struct.Dungeon) -> bool:
    """Is a dragon blocking progress to the next level?"""
    return defeated_monsters(dungeon) and not defeated_dungeon(dungeon)


def exhausted_dungeon(dungeon: struct.Dungeon) -> bool:
    """Has the player exhausted all possible actions for this dungeon?

    In contrast to defeated_dungeon(...), returns True if chests/etc remain."""
    return (dungeon is None) or (
        (0 == sum(struct.field_values(dungeon)) - dungeon.dragon)
        and not _blocking_dragon(dungeon)
    )


def new_world() -> struct.World:
    """Establish a new world independent of a delve/dungeon."""
    return struct.World(
        delve=0,
        depth=None,
        experience=0,
        ability=None,
        dungeon=None,
        party=None,
        treasure=TREASURE_INITIAL,
        reserve=RESERVE_INITIAL,
    )


def delve(
    world: struct.World,
    roll_party: dice.RollParty,
    randrange: dice.RandRange,
    *,
    _party_dice: int = 7
) -> struct.World:
    """Establish new delve within a world, optionally transforming the party.

    Argument roll_party can be dice.roll_party but other choices okay."""
    if world.delve >= 3:
        raise error.DrollError("At most three delves are permitted.")
    return replace(
        world,
        delve=(world.delve if world.delve else 0) + 1,
        depth=0,
        ability=True,
        dungeon=None,
        party=roll_party(_party_dice, randrange),
    )


def descend(
    world: struct.World,
    roll_dungeon: dice.RollDungeon,
    randrange: dice.RandRange,
    *,
    _max_depth: int = 10,
    _dungeon_dice: int = 7
) -> struct.World:
    """Move one dungeon deeper in the dungeon, retaining any partial dragons.

    If necessary, a ring of invisibility will be used to sneak past a dragon.
    Argument roll_dungeon can be dice.roll_dungeon but other choices okay
    Adheres to the specified number of dice available in the world."""
    if not defeated_monsters(world.dungeon):
        raise error.DrollError("Must defeat foes to proceed to next dungeon.")

    if not defeated_dungeon(world.dungeon):
        try:
            world = _apply_ring(world)
        except error.DrollError:
            raise error.DrollError(
                "Dragon remains but a ring of" " invisibility is not in hand."
            )

    # Success above, so update the world in anticipation of the next dungeon
    next_depth = (world.depth if world.depth else 0) + 1
    if next_depth > _max_depth:
        raise error.DrollError("The maximum depth is {}".format(_max_depth))
    prior_dragons = 0 if world.dungeon is None else world.dungeon.dragon
    dungeon = roll_dungeon(
        min(_dungeon_dice - prior_dragons, next_depth), randrange
    )
    dungeon = replace(dungeon, dragon=dungeon.dragon + prior_dragons)
    return replace(world, depth=next_depth, dungeon=dungeon)


def retire(world: struct.World) -> struct.World:
    """Retire to the tavern after completing the present dungeon.

    If monsters or a dragon remains, either ring of invisibility or
    a town portal will be used when available."""
    if world.depth == 0:
        raise error.DrollError("Descend at least once prior to retiring.")

    if not defeated_monsters(world.dungeon):
        try:
            world = _apply_portal(world)
        except error.DrollError:
            raise error.DrollError("Monsters remain but no portal in hand.")
    elif _blocking_dragon(world.dungeon):
        # First attempt to use a ring then a portal (because portals are +2)
        try:
            world = _apply_ring(world)
        except error.DrollError:
            try:
                world = _apply_portal(world)
            except error.DrollError:
                raise error.DrollError(
                    "Dragon remains but neither a ring of"
                    " invisibility nor a portal in hand."
                )

    # Success above, so update the world in anticipation of the next delve
    # Upgrading a hero's ability after 5 experience points is done elsewhere.
    return replace(
        world, depth=0, experience=world.experience + world.depth, dungeon=None
    )


def retreat(world: struct.World) -> struct.World:
    """Retreat to the tavern without completing the present dungeon."""
    if world.depth < 1:
        raise error.DrollError("Descend at least once prior to retreating.")
    if defeated_dungeon(world.dungeon):
        raise error.DrollError("Why retreat when you could instead retire?")

    return replace(world, depth=0, dungeon=None)


def score(world: struct.World) -> int:
    """Compute the present score for the world, including all treasure."""
    return (
        world.experience
        + sum(
            struct.field_values(world.treasure)
        )  # Each piece of treasure is +1 point
        + world.treasure.portal  # Portals are +1 extra (2 total each)
        + 2 * (world.treasure.scale // 2)  # Pairs of scales are +2 extra
    )


def _draw(reserve: struct.Treasure, randrange: dice.RandRange) -> str:
    """Draw a random treasure from the reserve, weighted by counts."""
    items = [
        name
        for name, count in struct.field_items(reserve)
        for _ in range(count)
    ]
    assert items, "No items remaining in the reserve"
    return items[randrange(0, len(items))]


def draw_treasure(
    world: struct.World, randrange: dice.RandRange
) -> struct.World:
    """Draw a single item from the reserve into the player's treasures."""
    drawn = _draw(reserve=world.reserve, randrange=randrange)
    treasure = replace(
        world.treasure, **{drawn: getattr(world.treasure, drawn) + 1}
    )
    reserve = replace(
        world.reserve, **{drawn: getattr(world.reserve, drawn) - 1}
    )
    return replace(world, treasure=treasure, reserve=reserve)


def replace_treasure(world: struct.World, item: str) -> struct.World:
    """Replace a single item from the player's treasures into the reserve."""
    prior_count = getattr(world.treasure, item)
    if not prior_count:
        raise error.DrollError("'{}' not in player's treasure".format(item))
    return replace(
        world,
        treasure=replace(world.treasure, **{item: prior_count - 1}),
        reserve=replace(
            world.reserve, **{item: getattr(world.reserve, item) + 1}
        ),
    )


def _apply_ring(world: struct.World, *, noun: str = "ring") -> struct.World:
    """Attempt to use a ring of invisibility towards sneaking past a dragon."""
    if not _blocking_dragon(world.dungeon):
        raise error.DrollError(
            "A dragon must be present to use a {}".format(noun)
        )
    world = replace_treasure(world, noun)
    return replace(world, dungeon=replace(world.dungeon, dragon=0))


def _apply_portal(world: struct.World, *, noun: str = "portal") -> struct.World:
    """Attempt to use a town portal towards retiring to town."""
    # No need to reset monsters/dragon as dungeon will be wholly replaced
    if defeated_dungeon(world.dungeon):
        raise error.DrollError(
            "No need to apply {} when dungeon clear".format(noun)
        )
    return replace(replace_treasure(world, "portal"), dungeon=struct.Dungeon())
