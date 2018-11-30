# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from using treasure."""

import random

import pytest

import droll.error as error
import droll.player as player
import droll.struct as struct
import droll.world as world


@pytest.fixture(name='game')
def _game():
    return world.new_world()._replace(
        dungeon=struct.Dungeon(*([2] * len(struct.Dungeon._fields))),
        party=struct.Party(*([0] * len(struct.Party._fields))),
    )


@pytest.fixture(name='randrange')
def _randrange():
    return random.Random(4).randrange


def test_elixir(game, randrange):
    game = game._replace(treasure=game.treasure._replace(elixir=1))
    game = player.apply(player.Default, game, randrange, 'elixir', 'cleric')
    assert game.party.cleric == 1
    assert game.treasure.elixir == 0

    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange, 'elixir', 'mage')


def test_bait(game, randrange):
    game = game._replace(treasure=game.treasure._replace(bait=2))
    game = player.apply(player.Default, game, randrange, 'bait', 'dragon')
    assert game.treasure.bait == 1
    assert game.dungeon.goblin == 0
    assert game.dungeon.skeleton == 0
    assert game.dungeon.ooze == 0
    assert game.dungeon.dragon == 8

    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, randrange, 'bait')


# Should behave identically to test_fighter inside test_player.py,
def helper_sword(identifier, game):
    """Test sword when referred to via identifier (e.g. 'sword', 'fighter'."""
    game = game._replace(treasure=game.treasure._replace(sword=2))
    game = player.apply(player.Default, game, None, identifier, 'goblin')
    assert game.treasure.sword == 1
    assert game.party.fighter == 0
    assert game.dungeon.goblin == 0

    game = player.apply(player.Default, game, None, identifier, 'ooze')
    assert game.treasure.sword == 0
    assert game.party.fighter == 0
    assert game.dungeon.ooze == 1

    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, None, identifier, 'ooze')


def test_sword_via_fighter(game):
    helper_sword('fighter', game)


def test_sword_via_itself(game):
    helper_sword('sword', game)
