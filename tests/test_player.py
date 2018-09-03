# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import random

import droll.player as player
import droll.world as world


@pytest.fixture(name='game')
def _game():
    return world.new_game()._replace(
        level=world.Level(*([2] * len(world.Level._fields))),
        party=world.Party(*([2] * len(world.Party._fields))),
    )


@pytest.fixture(name='randrange')
def _randrange():
    return random.Random(4).randrange


def test_fighter(game):
    game = player.apply(player.DEFAULT, game, None, 'fighter', 'goblin')
    assert game.party.fighter == 1
    assert game.level.goblin == 0
    game = player.apply(player.DEFAULT, game, None, 'fighter', 'ooze')
    assert game.party.fighter == 0
    assert game.level.ooze == 1


def test_cleric(game):
    game = player.apply(player.DEFAULT, game, None, 'cleric', 'skeleton')
    assert game.party.cleric == 1
    assert game.level.skeleton == 0
    game = player.apply(player.DEFAULT, game, None, 'cleric', 'ooze')
    assert game.party.cleric == 0
    assert game.level.ooze == 1


def test_mage(game):
    game = player.apply(player.DEFAULT, game, None, 'mage', 'ooze')
    assert game.party.mage == 1
    assert game.level.ooze == 0
    game = player.apply(player.DEFAULT, game, None, 'mage', 'goblin')
    assert game.party.mage == 0
    assert game.level.goblin == 1


def test_thief(game, randrange):
    game = player.apply(player.DEFAULT, game, randrange, 'thief', 'chest')
    assert game.party.thief == 1
    assert game.level.chest == 0
    assert sum(game.treasure) == 2


def test_champion(game):
    pass


def test_scroll(game):
    pass
