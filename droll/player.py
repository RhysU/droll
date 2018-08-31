# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import typing

from droll.world import Level, Party, World


_DEFEAT_NONSTANDARD = set(['chest', 'potion', 'dragon'])


# Reduces boilerplate in _defeat_one and _defeat_all
def _defeat_some(
        remaining: typing.Callable[[int], int],
        world: World,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Update world after regular hero defeats exactly some defenders."""
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


def _defeat_one(world: World, hero: str, *defenders: typing.List[str]) -> World:
    """Update world after regular hero defeats exactly one defender."""
    return _defeat_some(remaining=lambda prior_defenders: prior_defenders - 1,
                        world=world, hero=hero, *defenders)


def _defeat_all(world: World, hero: str, *defenders: typing.List[str]) -> World:
    """Update world after regular hero defeats all of one type of defender."""
    return _defeat_some(remaining=lambda _: 0,
                        world=world, hero=hero, *defenders)


# Reduces boilerplate in _open_one and _open_all
def _open_some(
        remaining: typing.Callable[[int], int],
        world: World,
        hero: str,
        *defenders: typing.List[str]
) -> World:
    """Update world after regular hero open exactly some chests."""
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


def _open_one(world: World, hero: str, *defenders: typing.List[str]) -> World:
    """Update world after regular hero opens exactly one chest."""
    return _open_some(remaining=lambda prior_chests: prior_chests - 1,
                      world=world, hero=hero, *chests)


def _open_all(world: World, hero: str, *chests: typing.List[str]) -> World:
    """Update world after regular hero opens all chests."""
    return _open_some(remaining=lambda _: 0,
                      world=world, hero=hero, *chests)


# Encodes default hero-vs-enemy capabilities
_MANY_DEFAULT = Party(
    fighter=Level(
        goblin=False,
        skeleton=False,
        ooze=False,
        chest=False,
        potion=True,
        dragon=False,
    ),
    cleric=Level(
        goblin=False,
        skeleton=False,
        ooze=False,
        chest=False,
        potion=True,
        dragon=False,
    ),
    mage=Level(
        goblin=False,
        skeleton=False,
        ooze=True,
        chest=False,
        potion=True,
        dragon=False,
    ),
    thief=Level(
        goblin=False,
        skeleton=False,
        ooze=False,
        chest=True,
        potion=True,
        dragon=False,
    ),
    champion=Level(
        goblin=False,
        skeleton=False,
        ooze=False,
        chest=True,
        potion=True,
        dragon=False,
    ),
    scroll=Level(
        goblin=None,
        skeleton=False,
        ooze=False,
        chest=False,
        potion=True,
        dragon=False,
    ),
)
