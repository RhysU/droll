# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality for hero-specific special action mechanics."""

from dataclasses import replace

from .dice import RandRange
from .dungeon import defeated_monsters
from .error import DrollError
from .struct import World

__all__ = (
    "convert_dungeon_to_party",
    "defeat_all_plus_additional",
    "defeat_one_plus_additional",
)


def _defeat_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    additional: tuple,
) -> World:
    """After the initial defeat, optionally defeat one additional monster."""
    from .action import defeat_one, increment_party

    if defeated_monsters(world.dungeon):
        if additional:
            raise DrollError(
                f"Additional {additional} given but no monsters left."
            )
        return world

    if not additional:
        raise DrollError("Monsters remain so one additional target required.")
    if len(additional) > 1:
        raise DrollError(
            f"Only one additional target allowed but {len(additional)} provided."
        )

    return defeat_one(
        world=replace(world, party=increment_party(world.party, hero)),
        randrange=randrange,
        hero=hero,
        target=additional[0],
    )


def defeat_all_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *additional,
) -> World:
    """Update world after hero handles all of one target type plus one more."""
    from .action import defeat_all

    world = defeat_all(
        world=world, randrange=randrange, hero=hero, target=target
    )
    return _defeat_plus_additional(world, randrange, hero, additional)


def defeat_one_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *additional,
) -> World:
    """Update world after hero handles one target plus one more."""
    from .action import defeat_one

    world = defeat_one(
        world=world, randrange=randrange, hero=hero, target=target
    )
    return _defeat_plus_additional(world, randrange, hero, additional)


def convert_dungeon_to_party(
    world: World,
    source: str,
    destination: str,
    max_count: int,
) -> World:
    """Convert up to max_count dungeon dice into party dice with regroup discard.

    Converts min(available, max_count) of source into destination."""
    count = min(getattr(world.dungeon, source), max_count)
    return replace(
        world,
        dungeon=replace(
            world.dungeon,
            **{source: getattr(world.dungeon, source) - count},
        ),
        party=replace(
            world.party,
            **{destination: getattr(world.party, destination) + count},
        ),
        regroup=replace(
            world.regroup,
            discard=replace(
                world.regroup.discard,
                **{
                    destination: getattr(world.regroup.discard, destination)
                    + count
                },
            ),
        ),
    )
