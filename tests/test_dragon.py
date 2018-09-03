# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random

import pytest

import droll.player as player
import droll.world as world


@pytest.fixture(name='game')
def _game():
    return world.new_game()._replace(
        level=world.Level(
            goblin=0,
            skeleton=0,
            ooze=0,
            chest=0,
            potion=0,
            dragon=3,
        ),
        party=world.Party(*([2] * len(world.Party._fields))),
    )


@pytest.fixture(name='randrange')
def _randrange():
    return random.Random(4).randrange


def test_successful(game, randrange):
    game = player.apply(player.DEFAULT, game, randrange,
                        'fighter', 'dragon', 'cleric', 'mage')
    assert game.party.fighter == 1
    assert game.party.cleric == 1
    assert game.party.mage == 1
    assert game.level.dragon == 0
    assert game.experience == 1
    assert sum(game.treasure) == 1
