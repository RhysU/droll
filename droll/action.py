# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import operator
import typing

from .world import (Level, RandRange, Party, World,
                    defeated_monsters, draw_treasure, roll_level)


class ActionError(RuntimeError):
    """Indicates attempts to take impossible actions."""
    pass


def defeat_one(
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero defeats exactly one defender."""
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=__decrement_defender(world.level, target)
    )


def __decrement_hero(party: Party, hero: str) -> Party:
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise ActionError("Require at least one hero {}".format(hero))
    return party._replace(**{hero: prior_heroes - 1})


def __decrement_defender(level: Level, defender: str) -> Level:
    prior_defenders = getattr(level, defender)
    if not prior_defenders:
        raise ValueError("Require at least one defender {}".format(defender))
    return level._replace(**{defender: prior_defenders - 1})


def defeat_all(
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero defeats all of one type of defender."""
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=__eliminate_defenders(world.level, target)
    )


def __eliminate_defenders(level: Level, defender: str) -> Level:
    prior_defenders = getattr(level, defender)
    if not prior_defenders:
        raise ActionError("Require at least one defender {}".format(defender))
    return level._replace(**{defender: 0})


def open_one(
        world: World, randrange: RandRange, hero: str, target: str,
        after_monsters=True,
) -> World:
    """Update world after hero opens exactly one chest."""
    if after_monsters and not defeated_monsters(world.level):
        raise ActionError("Monsters must be defeated before opening.")
    return draw_treasure(world, randrange)._replace(
        party=__decrement_hero(world.party, hero),
        level=__decrement_defender(world.level, target)
    )


def open_all(
        world: World, randrange: RandRange, hero: str, target: str,
        after_monsters=True,
) -> World:
    """Update world after hero opens all chests."""
    if after_monsters and not defeated_monsters(world.level):
        raise ActionError("Monsters must be defeated before opening.")
    howmany = getattr(world.level, target)
    if not howmany:
        raise ActionError("At least 1 {} required".format(target))
    for _ in range(howmany):
        world = draw_treasure(world, randrange)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=__eliminate_defenders(world.level, target),
    )


def quaff(
        world: World, randrange: RandRange, hero: str, target: str, *revivable,
        after_monsters=True
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(world.level, target)
    if not howmany:
        raise ActionError("At least 1 {} required".format(target))
    if len(revivable) != howmany:
        raise ActionError("Require exactly {} to revive".format(howmany))
    if after_monsters and not defeated_monsters(world.level):
        raise ActionError("Monsters must be defeated before quaffing.")
    party = __decrement_hero(world.party, hero)
    for revived in revivable:
        party = party._replace(**{revived: getattr(party, revived) + 1})
    return world._replace(
        party=party,
        level=__eliminate_defenders(world.level, target)
    )


def reroll(
        world: World, randrange: RandRange, hero: str, *targets
) -> World:
    """Update world after hero rerolls some number of targets."""
    if not targets:
        raise ActionError('At least one target must be re-rolled.')

    # Remove requested target from the level
    reduced = world.level
    for target in targets:
        if target in {'potion', 'dragon'}:
            raise ActionError("{} cannot be rerolled".format(target))
        reduced = __decrement_defender(reduced, target)

    # Re-roll the necessary number of dice then add to anything left fixed
    increased = roll_level(dice=len(targets), randrange=randrange)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=Level(*tuple(map(operator.add, reduced, increased)))
    )


# TODO Does defeating a dragon but losing a level retain the dragon experience?


def defeat_dragon(
        world: World, randrange: RandRange, hero: str, target: str, *others,
        disallowed_heroes: typing.Iterable[str] = ('scroll'),
        min_length: int = 3,
        min_heroes: int = 3
) -> World:
    """Update world after hero defeats a dragon using three different heroes.

    Additional required heroes are specified within variable-length others."""
    # Simple prerequisites for attempting to defeat the dragon
    if world.level.dragon < min_length:
        raise ActionError("Enemy {} only comes at length {}"
                          .format(target, min_length))
    if sum(world.level) != world.level.dragon:
        raise ActionError("Enemy {} only comes after all others defeated."
                          .format(target))
    if len(others) != min_heroes - 1:
        raise ActionError("A total of {} heroes must be specified."
                          .format(min_heroes))

    # Confirm required number of distinct heroes available
    party = __decrement_hero(world.party, hero)
    distinct_heroes = {hero}
    for other in others:
        party = __decrement_hero(party, other)
        distinct_heroes.add(other)
    if len(distinct_heroes) != min_heroes:
        raise ActionError("The {} heroes must all be distinct")
    if distinct_heroes & set(disallowed_heroes):
        raise ActionError("Heroes {} cannot defeat {}"
                          .format(disallowed_heroes, target))

    # Attempt was successful, so update experience and treasure
    return draw_treasure(world, randrange)._replace(
        experience=world.experience + 1,
        party=party,
        level=__eliminate_defenders(world.level, target)
    )
