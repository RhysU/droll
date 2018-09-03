# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import operator

from .world import Level, RandRange, Party, World, draw_treasure, roll_level


class ActionError(RuntimeError):
    """Indicates attempts to take impossible actions."""
    pass


def defeat_invalid(
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Raise because the hero cannot defeat the specified target."""
    raise ActionError('Hero {} cannot defeat {}'.format(hero, target))


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
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero opens exactly one chest."""
    return draw_treasure(world, randrange)._replace(
        party=__decrement_hero(world.party, hero),
        level=__decrement_defender(world.level, target)
    )


def open_all(
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero opens all chests."""
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
        world: World, randrange: RandRange, hero: str, target: str, *revived
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(world.level, target)
    if not howmany:
        raise ActionError("At least 1 {} required".format(target))
    if not len(revived) == howmany:
        raise ActionError("Require exactly {} to revive".format(howmany))
    party = __decrement_hero(world.party, hero)
    for die in revived:
        party = party._replace(**{die: getattr(party, die) + 1})
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
