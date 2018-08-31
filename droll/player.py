# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import typing

from droll.world import Level, RandRange, Party, World


_DEFEAT_NONSTANDARD = set(['chest', 'potion', 'dragon'])


# Reduces boilerplate in _defeat_one and _defeat_all
def _defeat_some(
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
    assert defender not in _DEFEAT_NONSTANDARD, (
            "{} requires nonstandard handling".format(defender))
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    return world._replace(
            party=world.party._replace(**{hero: prior_heroes - 1}),
            level=world.level._replace(**{defender: remaining(prior_defenders)}),
    )


def _defeat_one(
        hero: str,
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats exactly one defender."""
    return _defeat_some(hero=hero,
                        remaining=lambda prior_defenders: prior_defenders - 1,
                        world=world, randrange=randrange, *defenders)


def _defeat_all(
        hero: str,
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero defeats all of one type of defender."""
    return _defeat_some(hero=hero, remaining=lambda _: 0,
                        world=world, randrange=randrange, *defenders)


# Reduces boilerplate in _open_one and _open_all
def _open_some(
        hero: str,
        remaining: typing.Callable[[int], int],
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero opens some chests."""
    prior_heroes = getattr(world.party, hero)
    assert prior_heroes >= 1, "Require at least one {}".format(hero)
    defender, *_ = defenders
    assert defender == 'chest', "Special logic does not handle {}".format(defender)
    prior_defenders = getattr(world.level, defender)
    assert prior_defenders >= 1, "Expected at least one {}".format(defender)
    remaining_defenders = remaining(prior_defenders)
    world = world._replace(
            party=world.party._replace(**{hero: prior_heroes - 1}),
            level=world.level._replace(**{defender: remaining_defenders}),
    )
    for _ in range(prior_defenders - remaining_defenders):
        world = droll.world.draw_treasure(world, randrange)
    return world


def _open_one(
        hero: str,
        world: World,
        randrange: RandRange,
        *defenders: typing.List[str]
) -> World:
    """Update world after hero opens exactly one chest."""
    return _open_some(hero=hero,
                      remaining=lambda prior_chests: prior_chests - 1,
                      world=world, randrange=randrange, *chests)


def _open_all(
        hero: str,
        world: World,
        randrange: RandRange,
        *chests: typing.List[str]
) -> World:
    """Update world after hero opens all chests."""
    return _open_some(hero=hero, remaining=lambda _: 0,
                      world=world, randrange=randrange, *chests)

# TODO Quaffing one potions, including scrolls
# TODO Quaffing all potions, including scrolls
# TODO No explicit defeat of the dragon


# Encodes default hero-vs-enemy capabilities
_MANY_DEFAULT = Party(
    fighter=Level(
        goblin=_defeat_all,
        skeleton=_defeat_one,
        ooze=_defeat_one,
        chest=_open_one,
        potion=None,
        dragon=None,
    ),
    cleric=Level(
        goblin=_defeat_one,
        skeleton=_defeat_all,
        ooze=_defeat_one,
        chest=_open_one,
        potion=None,
        dragon=None,
    ),
    mage=Level(
        goblin=_defeat_one,
        skeleton=_defeat_one,
        ooze=_defeat_all,
        chest=_open_one,
        potion=None,
        dragon=None,
    ),
    thief=Level(
        goblin=_defeat_one,
        skeleton=_defeat_one,
        ooze=_defeat_one,
        chest=_open_all,
        potion=None,
        dragon=None,
    ),
    champion=Level(
        goblin=_defeat_all,
        skeleton=_defeat_all,
        ooze=_defeat_all,
        chest=_open_all,
        potion=None,
        dragon=None,
    ),
    scroll=Level(
        goblin=None,
        skeleton=None,
        ooze=None,
        chest=None,
        potion=None,
        dragon=None,
    ),
)
