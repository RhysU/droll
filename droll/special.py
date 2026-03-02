# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality for hero-specific special actions."""

from dataclasses import replace

from .dungeon import defeated_monsters
from .party import increment_party
from .regular import defeat_all, defeat_one
from .struct import DrollError, RandRange, World

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
    if defeated_monsters(world.dungeon):
        if additional:
            raise DrollError(
                f"Additional target '{additional[0]}' given but no monsters left."
            )
        return world

    if not additional:
        raise DrollError("Monsters remain so one additional target required.")
    if len(additional) > 1:
        raise DrollError(
            f"Only one additional target allowed"
            f" but {len(additional)} provided."
        )

    return defeat_one(
        world=replace(world, party=increment_party(world.party, hero)),
        randrange=randrange,
        hero=hero,
        targets=additional,
    )


def defeat_all_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    targets: tuple[str, ...],
) -> World:
    """Update world after hero handles all of one target type plus one more."""
    if not targets:
        raise DrollError("At least 1 target required.")
    world = defeat_all(
        world=world, randrange=randrange, hero=hero, targets=targets[:1]
    )
    return _defeat_plus_additional(world, randrange, hero, targets[1:])


def defeat_one_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    targets: tuple[str, ...],
) -> World:
    """Update world after hero handles one target plus one more."""
    if not targets:
        raise DrollError("At least 1 target required.")
    world = defeat_one(
        world=world, randrange=randrange, hero=hero, targets=targets[:1]
    )
    return _defeat_plus_additional(world, randrange, hero, targets[1:])


def convert_dungeon_to_party(
    world: World,
    source: str,
    destination: str,
    max_count: int,
) -> World:
    """Convert dungeon dice into party dice with regroup discard.

    Converts min(available, max_count) of source into destination."""
    count = min(getattr(world.dungeon, source), max_count)
    if count < 1:
        raise DrollError(f"No {source} in dungeon to convert.")
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
