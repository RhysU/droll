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


def apply(
        player: Player,
        world: World,
        randrange: RandRange,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Apply hero to defenders within world, returning a new version."""
    defender, *_ = defenders
    action = getattr(getattr(player.party, hero), defender)
    return action(hero=hero, world=world, randrange=randrange, *defenders)


def defeat_one(
        world: World,
        randrange: RandRange,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats exactly one defender."""
    return __defeat_some(hero=hero,
                         remaining=lambda prior_defenders: prior_defenders - 1,
                         world=world, randrange=randrange, *defenders)


def defeat_all(
        world: World,
        randrange: RandRange,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats all of one type of defender."""
    return __defeat_some(hero=hero, remaining=lambda _: 0,
                         world=world, randrange=randrange, *defenders)


def __decrement_hero(party: Party, hero: str) -> Party:
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise RuntimeError("Require at least one {}".format(hero))
    return party._replace(**{hero: prior_heroes - 1})


# Reduces boilerplate in _defeat_one and _defeat_all
def __defeat_some(
        remaining: typing.Callable[[int], int],
        world: World,
        _: RandRange,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats exactly some defenders."""
    defender, *_ = defenders
    assert defender not in {'chest', 'potion', 'dragon'}, (
        "{} requires nonstandard handling".format(defender))
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=world.level._replace(**{defender: remaining(prior_defenders)}),
    )


def defeat_invalid(
        world: World,
        _: RandRange,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Hero cannot defeat the specified defender.."""
    prior_heroes = getattr(world.party, hero)
    assert prior_heroes >= 1, "Require at least one {}".format(hero)
    defender, *_ = defenders
    raise RuntimeError('Hero {} cannot defeat {}'.format(hero, defender))


def open_one(
        world: World,
        randrange: RandRange,
        hero: str,
        *chests: typing.List[str]
) -> World:
    """Update world after hero opens exactly one chest."""
    return __open_some(hero=hero,
                       remaining=lambda prior_chests: prior_chests - 1,
                       world=world, randrange=randrange, *chests)


def open_all(
        world: World,
        randrange: RandRange,
        hero: str,
        *chests: typing.List[str]
) -> World:
    """Update world after hero opens all chests."""
    return __open_some(hero=hero, remaining=lambda _: 0,
                       world=world, randrange=randrange, *chests)


# Reduces boilerplate in _open_one and _open_all
def __open_some(
        remaining: typing.Callable[[int], int],
        world: World,
        randrange: RandRange,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero opens some chests.

    Notice defenders is required for consistency with defend_{one,all}."""
    defender, *_ = defenders
    assert defender == 'chest', (
        "Special logic does not handle {}".format(defender))
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    remaining_defenders = remaining(prior_defenders)
    world = world._replace(
        party=__decrement_hero(world.party, hero),
        level=world.level._replace(**{defender: remaining_defenders}),
    )
    for _ in range(prior_defenders - remaining_defenders):
        world = draw_treasure(world, randrange)
    return world


# TODO Method signature is off relative to other actions
def quaff(
        world: World,
        _: RandRange,
        hero: str,
        defender: str,
        *revived: typing.List[str]
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    assert defender == 'potion', (
        "Special logic does not handle {}".format(defender))
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    assert len(revived) == prior_defenders, (
        "Require exactly {} to revive".format(prior_defenders))

    party = __decrement_hero(world.party, hero),
    for die in revived:
        party = party.replace(**{die: getattr(party, die) + 1})
    return world._replace(
        party=party,
        level=world.level._replace(**{defender: 0}),
    )


def reroll(
        world: World,
        randrange: RandRange,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero rerolls some number of defenders."""
    assert defenders, "At least one defender must be provided"

    # Remove requested defenders from the level
    level = world.level
    for defender in defenders:
        assert defender not in {'potion', 'dragon'}, (
            "{} cannot be rerolled".format(defender))
        prior_defenders = getattr(world.level, defender)
        assert prior_defenders >= 1, "Expected at least one {}".format(defender)
        level = level._replace(**{defender: prior_defenders - 1})

    # Re-roll the necessary number of dice
    update = roll_level(dice=len(defenders), randrange=randrange)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        level=Level(*tuple(map(operator.add, level, update)))
    )
