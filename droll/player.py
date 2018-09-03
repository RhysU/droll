# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import operator
import typing
from functools import partial

from droll.world import (
    Level, RandRange, Party, World,
    draw_treasure, roll_level
)


# TODO Work very much in progress
def default_player() -> Party:
    """Encodes default hero-vs-enemy capabilities."""
    return Party(
        fighter=Level(
            goblin=partial(defeat_all, hero='fighter'),
            skeleton=partial(defeat_one, hero='fighter'),
            ooze=partial(defeat_one, hero='fighter'),
            chest=partial(open_one, hero='fighter'),
            potion=partial(quaff, hero='fighter'),
            dragon=partial(defeat_invalid, hero='fighter'),
        ),
        cleric=Level(
            goblin=partial(defeat_one, hero='cleric'),
            skeleton=partial(defeat_all, hero='cleric'),
            ooze=partial(defeat_one, hero='cleric'),
            chest=partial(open_one, hero='cleric'),
            potion=partial(quaff, hero='cleric'),
            dragon=partial(defeat_invalid, hero='cleric'),
        ),
        mage=Level(
            goblin=partial(defeat_one, hero='mage'),
            skeleton=partial(defeat_one, hero='mage'),
            ooze=partial(defeat_all, hero='mage'),
            chest=partial(open_one, hero='mage'),
            potion=partial(quaff, hero='mage'),
            dragon=partial(defeat_invalid, hero='mage'),
        ),
        thief=Level(
            goblin=partial(defeat_one, hero='thief'),
            skeleton=partial(defeat_one, hero='thief'),
            ooze=partial(defeat_one, hero='thief'),
            chest=partial(open_all, hero='thief'),
            potion=partial(quaff, hero='thief'),
            dragon=partial(defeat_invalid, hero='thief'),
        ),
        champion=Level(
            goblin=partial(defeat_all, hero='champion'),
            skeleton=partial(defeat_all, hero='champion'),
            ooze=partial(defeat_all, hero='champion'),
            chest=partial(open_all, hero='champion'),
            potion=partial(quaff, hero='champion'),
            dragon=partial(defeat_invalid, hero='champion'),
        ),
        # Technically scrolls could re-roll potions,
        # but doing so would be a really peculiar choice.
        scroll=Level(
            goblin=partial(reroll, hero='scroll'),
            skeleton=partial(reroll, hero='scroll'),
            ooze=partial(reroll, hero='scroll'),
            chest=partial(reroll, hero='scroll'),
            potion=partial(quaff, hero='scroll'),
            dragon=partial(defeat_invalid, hero='scroll'),
        ),
    )


def apply(
        player: Level,
        hero: str,
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Apply hero to defenders within world, returning a new version."""
    defender, *_ = defenders
    action = getattr(getattr(player, hero), defender)
    return action(world=world, randrange=randrange, *defenders)


# Reduces boilerplate in _defeat_one and _defeat_all
def __defeat_some(
        hero: str,
        remaining: typing.Callable[[int], int],
        world: World,
        _: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats exactly some defenders."""
    prior_heroes = getattr(world.party, hero)
    assert prior_heroes >= 1, "Require at least one {}".format(hero)
    defender, *_ = defenders
    assert defender not in {'chest', 'potion', 'dragon'}, (
        "{} requires nonstandard handling".format(defender))
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    return world._replace(
        party=world.party._replace(**{hero: prior_heroes - 1}),
        level=world.level._replace(**{defender: remaining(prior_defenders)}),
    )


def defeat_one(
        hero: str,
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats exactly one defender."""
    return __defeat_some(hero=hero,
                         remaining=lambda prior_defenders: prior_defenders - 1,
                         world=world, randrange=randrange, *defenders)


def defeat_all(
        hero: str,
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats all of one type of defender."""
    return __defeat_some(hero=hero, remaining=lambda _: 0,
                         world=world, randrange=randrange, *defenders)


def defeat_invalid(
        hero: str,
        world: World,
        _: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Hero cannot defeat the specified defender.."""
    prior_heroes = getattr(world.party, hero)
    assert prior_heroes >= 1, "Require at least one {}".format(hero)
    defender, *_ = defenders
    raise RuntimeError('Hero {} cannot defeat {}'.format(hero, defender))


# Reduces boilerplate in _open_one and _open_all
def __open_some(
        hero: str,
        remaining: typing.Callable[[int], int],
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero opens some chests.

    Notice defenders is required for consistency with defend_{one,all}."""
    prior_heroes = getattr(world.party, hero)
    assert prior_heroes >= 1, "Require at least one {}".format(hero)
    defender, *_ = defenders
    assert defender == 'chest', (
        "Special logic does not handle {}".format(defender))
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    remaining_defenders = remaining(prior_defenders)
    world = world._replace(
        party=world.party._replace(**{hero: prior_heroes - 1}),
        level=world.level._replace(**{defender: remaining_defenders}),
    )
    for _ in range(prior_defenders - remaining_defenders):
        world = draw_treasure(world, randrange)
    return world


def open_one(
        hero: str,
        world: World,
        randrange: RandRange,
        *chests: typing.List[str]
) -> World:
    """Update world after hero opens exactly one chest."""
    return __open_some(hero=hero,
                       remaining=lambda prior_chests: prior_chests - 1,
                       world=world, randrange=randrange, *chests)


def open_all(
        hero: str,
        world: World,
        randrange: RandRange,
        *chests: typing.List[str]
) -> World:
    """Update world after hero opens all chests."""
    return __open_some(hero=hero, remaining=lambda _: 0,
                       world=world, randrange=randrange, *chests)


def quaff(
        hero: str,
        world: World,
        _: RandRange,
        defender: str,
        *revived: typing.List[str]
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    prior_heroes = getattr(world.party, hero)
    assert prior_heroes >= 1, "Require at least one {}".format(hero)
    assert defender == 'potion', (
        "Special logic does not handle {}".format(defender))
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    assert len(revived) == prior_defenders, (
        "Require exactly {} to revive".format(prior_defenders))

    party = world.party
    for die in revived:
        party = party.replace(**{die: getattr(party, die) + 1})
    return world._replace(
        party=party,
        level=world.level._replace(**{defender: 0}),
    )


def reroll(
        hero: str,
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero rerolls some number of defenders."""
    prior_heroes = getattr(world.party, hero)
    assert prior_heroes >= 1, "Require at least one {}".format(hero)
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
        level=Level(*tuple(map(operator.add, level, update)))
    )
