# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with world state and world mechanics."""

from dataclasses import replace

from . import struct
from .dungeon import blocking_dragon, defeated_dungeon, defeated_monsters
from .struct import Artifact, Dungeon, DrollError, Party, frozen
from .treasure import replace_treasure

__all__ = (
    "delve",
    "descend",
    "new_world",
    "retire",
    "retreat",
    "score",
)


def new_world() -> struct.World:
    """Establish a new world independent of a delve/dungeon."""
    return struct.World(
        treasure=struct.Treasure(
            box=frozen({
                Artifact.SWORD: 3,
                Artifact.TALISMAN: 3,
                Artifact.SCEPTRE: 3,
                Artifact.TOOLS: 3,
                Artifact.SCROLL: 3,
                Artifact.ELIXIR: 3,
                Artifact.BAIT: 4,
                Artifact.PORTAL: 4,
                Artifact.RING: 4,
                Artifact.SCALE: 6,
            }),
        ),
    )


def delve(
    world: struct.World,
    roll_party: struct.RollParty,
    randrange: struct.RandRange,
    *,
    _party_dice: int = 7,
) -> struct.World:
    """Establish new delve within a world, optionally transforming the party.

    Argument roll_party can be dice.roll_party but other choices okay."""
    if world.delve >= 3:
        raise DrollError("At most 3 delves permitted.")
    party, regroup = roll_party(_party_dice, randrange)
    return replace(
        world,
        delve=world.delve + 1,
        depth=0,
        ability=True,
        regroup=regroup,
        dungeon=None,
        party=party,
    )


def _regroup(world: struct.World) -> struct.World:
    """The regroup phase occurs when descending, retiring, or retreating."""
    return replace(
        world,
        party=frozen({
            p: max(0, world.party[p] - world.regroup.discard[p])
            for p in Party
        }),
        regroup=struct.Regroup(),
    )


def descend(
    world: struct.World,
    roll_dungeon: struct.RollDungeon,
    randrange: struct.RandRange,
    *,
    _max_depth: int = 10,
    _dungeon_dice: int = 7,
) -> struct.World:
    """Move one level deeper in the dungeon, retaining any partial dragons.

    If necessary, a ring of invisibility will be used to sneak past a dragon.
    Argument roll_dungeon can be dice.roll_dungeon but other choices okay
    Adheres to the specified number of dice available in the world."""
    if not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before descending.")

    if not defeated_dungeon(world.dungeon):
        try:
            world = _apply_ring(world)
        except DrollError:
            raise DrollError("Dragon remains but no ring in hand.")

    # Success above, so regroup just prior to descending
    world = _regroup(world)

    # Update the world in anticipation of the next dungeon
    next_depth = world.depth + 1
    if next_depth > _max_depth:
        raise DrollError(f"Maximum depth is {_max_depth}.")
    prior_dragons = 0 if world.dungeon is None else world.dungeon[Dungeon.DRAGON]
    new_dice = max(1, min(_dungeon_dice - prior_dragons, next_depth))
    rolled = roll_dungeon(new_dice, randrange)
    return replace(
        world,
        depth=next_depth,
        dungeon=frozen({**rolled, Dungeon.DRAGON: rolled[Dungeon.DRAGON] + prior_dragons}),
    )


def _escape_dragon(world: struct.World) -> struct.World:
    """Escape a blocking dragon using a ring first, then a portal."""
    try:
        return _apply_ring(world)
    except DrollError:
        try:
            return _apply_portal(world)
        except DrollError:
            raise DrollError("Dragon remains but no ring or portal in hand.")


def retire(world: struct.World) -> struct.World:
    """Retire from the dungeon after clearing all monsters.

    Earns experience equal to the current depth.
    If a dragon blocks, a ring or portal is consumed automatically."""
    if world.depth == 0:
        raise DrollError("Descend at least once prior to retiring.")

    if not defeated_monsters(world.dungeon):
        try:
            world = _apply_portal(world)
        except DrollError:
            raise DrollError("Monsters remain. Defeat them or 'retreat'.")
    elif blocking_dragon(world.dungeon):
        world = _escape_dragon(world)

    # Regroup just prior to retiring
    world = _regroup(world)

    # Update the world in anticipation of the next delve
    return replace(
        world, depth=0, experience=world.experience + world.depth, dungeon=None
    )


def retreat(world: struct.World) -> struct.World:
    """Retreat from the dungeon while monsters remain.

    A town portal, if available, is consumed to earn experience."""
    if world.depth < 1:
        raise DrollError("Descend at least once prior to retreating.")
    if defeated_dungeon(world.dungeon):
        raise DrollError("No monsters to retreat from; use 'retire' to leave the dungeon.")

    experience = world.experience
    try:
        world = _apply_portal(world)
        experience += world.depth
    except DrollError:
        pass

    return replace(_regroup(world), depth=0, experience=experience, dungeon=None)


def score(world: struct.World) -> int:
    """Compute the present score for the world, including all treasure."""
    return (
        world.experience
        + sum(world.treasure.own.values())
        + world.treasure.own[Artifact.PORTAL]  # Portals are +1 extra (2 total each)
        + 2 * (world.treasure.own[Artifact.SCALE] // 2)  # Pairs of scales are +2 extra
    )


def _apply_ring(world: struct.World) -> struct.World:
    """Attempt to use a ring of invisibility towards sneaking past a dragon."""
    if not blocking_dragon(world.dungeon):
        raise DrollError("A dragon must be present to use a ring.")
    world = replace(world, treasure=replace_treasure(world.treasure, Artifact.RING))
    return replace(world, dungeon=frozen({**world.dungeon, Dungeon.DRAGON: 0}))


def _apply_portal(world: struct.World) -> struct.World:
    """Attempt to use a town portal towards retiring to town."""
    # No need to reset monsters/dragon as dungeon will be wholly replaced
    if defeated_dungeon(world.dungeon):
        raise DrollError("No need to apply portal when dungeon clear.")
    return replace(
        world,
        treasure=replace_treasure(world.treasure, Artifact.PORTAL),
        dungeon=struct.empty_dungeon(),
    )
