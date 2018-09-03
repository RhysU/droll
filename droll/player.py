# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections
import operator
import typing

from droll.world import (
    Level, RandRange, Party, World,
    draw_treasure, roll_level
)

# Placeholder for further expansion
Player = collections.namedtuple('Player', (
    'party',
))


def default_player() -> Player:
    """Encodes default hero-vs-enemy capabilities."""
    return Player(
        party=Party(
            fighter=Level(
                goblin=defeat_all,
                skeleton=defeat_one,
                ooze=defeat_one,
                chest=open_one,
                potion=quaff,
                dragon=defeat_invalid,
            ),
            cleric=Level(
                goblin=defeat_one,
                skeleton=defeat_all,
                ooze=defeat_one,
                chest=open_one,
                potion=quaff,
                dragon=defeat_invalid,
            ),
            mage=Level(
                goblin=defeat_one,
                skeleton=defeat_one,
                ooze=defeat_all,
                chest=open_one,
                potion=quaff,
                dragon=defeat_invalid,
            ),
            thief=Level(
                goblin=defeat_one,
                skeleton=defeat_one,
                ooze=defeat_one,
                chest=open_all,
                potion=quaff,
                dragon=defeat_invalid,
            ),
            champion=Level(
                goblin=defeat_all,
                skeleton=defeat_all,
                ooze=defeat_all,
                chest=open_all,
                potion=quaff,
                dragon=defeat_invalid,
            ),
            # Technically scrolls could re-roll potions,
            # but doing so would be a really peculiar choice.
            scroll=Level(
                goblin=reroll,
                skeleton=reroll,
                ooze=reroll,
                chest=reroll,
                potion=quaff,
                dragon=defeat_invalid,
            ),
        ),
    )


def play(
        player: Player,
        world: World,
        randrange: RandRange,
        hero: str,
        target: str,
        *additional: typing.List[str]
) -> World:
    """Apply hero to target within world, returning a new version."""
    # Lookup appropriate action logic
    action = getattr(getattr(player.party, hero), target)

    # Invoke action, using that not all methods take additional arguments
    additional.insert(0, target)
    return action(world=world, randrange=randrange, hero=hero, *additional)


def __decrement_hero(party: Party, hero: str) -> Party:
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise RuntimeError("Require at least one hero {}".format(hero))
    return party._replace(**{hero: prior_heroes - 1})


def __decrement_defender(level: Level, defender: str) -> Level:
    prior_defenders = getattr(level, defender)
    if not prior_defenders:
        raise RuntimeError("Require at least one defender {}".format(defender))
    return level._replace(**{defender: prior_defenders - 1})


def __eliminate_defenders(level: Level, defender: str) -> Level:
    prior_defenders = getattr(level, defender)
    if not prior_defenders:
        raise RuntimeError("Require at least one defender {}".format(defender))
    return level._replace(**{defender: 0})


def defeat_one(
        world: World, _randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero defeats exactly one defender."""
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=__decrement_defender(world.level, target)
    )


def defeat_all(
        world: World, _randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero defeats all of one type of defender."""
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=__eliminate_defenders(world.level, target)
    )


def defeat_invalid(
        _world: World, _randrange: RandRange, hero: str, target: str
) -> World:
    """Hero cannot defeat the specified defender.."""
    raise RuntimeError('Hero {} cannot defeat {}'.format(hero, target))


def open_one(
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero opens exactly one chest."""
    return draw_treasure(world, randrange)._replace(
        party=__decrement_hero(world.party, hero),
        level=__decrement_defender(world.level, target)
    )


def open_all(
        world: World,
        randrange: RandRange,
        hero: str,
        target: str,
) -> World:
    """Update world after hero opens all chests."""
    howmany = getattr(world.level, target)
    if not howmany:
        raise RuntimeError("At least 1 {} required".format(target))
    for _ in range(howmany):
        world = draw_treasure(world, randrange)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=__eliminate_defenders(world.level, target),
    )


def quaff(
        world: World,
        _: RandRange,
        hero: str,
        target: str,
        *revived: typing.List[str]
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(world.level, target)
    if not howmany:
        raise RuntimeError("At least 1 {} required".format(target))
    if not len(revived) == howmany:
        raise RuntimeError("Require exactly {} to revive".format(howmany))
    party = __decrement_hero(world.party, hero)
    for die in revived:
        party = party.replace(**{die: getattr(party, die) + 1})
    return world._replace(
        party=party,
        level=__eliminate_defenders(world.level, target)
    )


def reroll(
        world: World,
        randrange: RandRange,
        hero: str,
        target: str,
        *targets: typing.List[str]
) -> World:
    """Update world after hero rerolls some number of targets."""
    # Push target onto the front of targets all are processed identically
    targets.insert(0, target)

    # Remove requested target from the level
    reduced = world.level
    for target in targets:
        if target in {'potion', 'dragon'}:
            raise RuntimeError("{} cannot be rerolled".format(target))
        reduced = __decrement_defender(reduced, target)

    # Re-roll the necessary number of dice then add to anything left fixed
    increased = roll_level(dice=len(targets), randrange=randrange)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=Level(*tuple(map(operator.add, reduced, increased)))
    )
