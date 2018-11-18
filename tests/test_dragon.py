# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from attacking dragons."""

import random

import pytest

import droll.action as action
import droll.error as error
import droll.heroes as heroes
import droll.player as player
import droll.struct as struct
import droll.world as world


@pytest.fixture(name='game')
def _game():
    return world.new_game()._replace(
        dungeon=struct.Dungeon(
            goblin=0,
            skeleton=0,
            ooze=0,
            chest=1,
            potion=2,
            dragon=3,
        ),
        party=struct.Party(*([2] * len(struct.Party._fields))),
    )


@pytest.fixture(name='randrange')
def _randrange():
    return random.Random(4).randrange


def test_successful(game, randrange):
    game = player.apply(player.Default, game, randrange,
                        'fighter', 'dragon', 'cleric', 'mage')
    assert game.party.fighter == 1
    assert game.party.cleric == 1
    assert game.party.mage == 1
    assert game.dungeon.dragon == 0
    assert game.experience == 1
    assert sum(game.treasure) == 1


def test_treasure_slot1(game, randrange):
    game = game._replace(treasure=game.treasure._replace(sword=7))
    game = game._replace(party=game.party._replace(fighter=0))
    game = player.apply(player.Default, game, randrange,  # Notice sword!
                        'fighter', 'dragon', 'cleric', 'mage')
    assert game.treasure.sword == 6
    assert game.party.fighter == 0
    assert game.party.cleric == 1
    assert game.party.mage == 1
    assert game.dungeon.dragon == 0
    assert game.experience == 1
    assert sum(game.treasure) == 7


def test_treasure_slot3(game, randrange):
    game = game._replace(treasure=game.treasure._replace(talisman=7))
    game = game._replace(party=game.party._replace(cleric=0))
    game = player.apply(player.Default, game, randrange,  # Notice talisman!
                        'fighter', 'dragon', 'cleric', 'mage')
    assert game.treasure.talisman == 6
    assert game.party.fighter == 1
    assert game.party.cleric == 0
    assert game.party.mage == 1
    assert game.dungeon.dragon == 0
    assert game.experience == 1
    assert sum(game.treasure) == 7


def test_treasure_slot2(game, randrange):
    game = game._replace(treasure=game.treasure._replace(sceptre=7))
    game = game._replace(party=game.party._replace(mage=0))
    game = player.apply(player.Default, game, randrange,  # Notice talisman!
                        'fighter', 'dragon', 'cleric', 'mage')
    assert game.treasure.sceptre == 6
    assert game.party.fighter == 1
    assert game.party.cleric == 1
    assert game.party.mage == 0
    assert game.dungeon.dragon == 0
    assert game.experience == 1
    assert sum(game.treasure) == 7


def test_monsters_remain(game, randrange):
    game = game._replace(
        dungeon=game.dungeon._replace(goblin=1)
    )
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange,
                     'fighter', 'dragon', 'cleric', 'mage')


def test_too_few_specified(game, randrange):
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange,
                     'fighter', 'dragon', 'cleric')

    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange,
                     'fighter', 'dragon')

    # Dragon Slayer requires only two
    with pytest.raises(error.DrollError):
        player.apply(heroes.DragonSlayer, game, randrange,
                     'fighter', 'dragon')


def test_too_many_specified(game, randrange):
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange,
                     'fighter', 'dragon', 'cleric', 'mage', 'thief')

    # Dragon Slayer requires only two
    with pytest.raises(error.DrollError):
        player.apply(heroes.DragonSlayer, game, randrange,
                     'fighter', 'dragon', 'cleric', 'mage')


def test_only_heroes_accepted(game, randrange):
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange,
                     'fighter', 'dragon', 'cleric', 'foo')


def test_one_scroll(game, randrange):
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange,
                     'fighter', 'dragon', 'cleric', 'scroll')

    # Dragon Slayer requires only two
    with pytest.raises(error.DrollError):
        player.apply(heroes.DragonSlayer, game, randrange,
                     'fighter', 'dragon', 'scroll')


def test_not_enough_distinct(game, randrange):
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange,
                     'fighter', 'dragon', 'mage', 'mage')


# More directly test some hero-vs-dragon logic as it is more complicated.
def test_defeat_dragon_heroes_interchangeable():
    # Less interesting successful cases first
    assert action.defeat_dragon_heroes_interchangeable(
        'cleric', 'thief', 'mage',
        _interchangeable={'fighter'})
    assert action.defeat_dragon_heroes_interchangeable(
        'cleric', 'thief', 'fighter',
        _interchangeable={'fighter'})

    # Less interesting failure cases next
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'cleric', 'thief',
            _interchangeable={'fighter'})
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'cleric', 'fighter',
            _interchangeable={'fighter'})
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'cleric', 'thief', 'champion', 'mage',
            _interchangeable={'fighter'})
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'cleric', 'thief', 'champion', 'fighter',
            _interchangeable={'fighter'})

    # More than two could be interchangeable, but does not appear in the game.
    # Therefore, only two interchangeable case is checked below.

    # More interesting successful cases
    assert action.defeat_dragon_heroes_interchangeable(
        'cleric', 'thief', 'mage',
        _interchangeable={'mage', 'fighter'})
    assert action.defeat_dragon_heroes_interchangeable(
        'cleric', 'fighter', 'mage',
        _interchangeable={'mage', 'fighter'})
    assert action.defeat_dragon_heroes_interchangeable(
        'cleric', 'fighter', 'fighter',
        _interchangeable={'mage', 'fighter'})
    assert action.defeat_dragon_heroes_interchangeable(
        'cleric', 'mage', 'mage',
        _interchangeable={'mage', 'fighter'})

    # More interesting failure cases last
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'mage', 'mage', 'mage',
            _interchangeable={'mage', 'fighter'})
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'fighter', 'fighter', 'fighter',
            _interchangeable={'mage', 'fighter'})
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'fighter', 'mage', 'mage',
            _interchangeable={'mage', 'fighter'})
    with pytest.raises(error.DrollError):
        action.defeat_dragon_heroes_interchangeable(
            'mage', 'fighter', 'fighter',
            _interchangeable={'mage', 'fighter'})
