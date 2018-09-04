# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from using treasure."""

import random

import pytest

import droll.error as error
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


def test_elixir(game, randrange):
    game = game._replace(treasure=game.treasure._replace(elixir=1))
    game = player.apply(player.DEFAULT, game, randrange, 'elixir', 'cleric')
    assert game.party.cleric == 3
    assert game.treasure.elixir == 0

    with pytest.raises(error.DrollError):
        player.apply(player.DEFAULT, game, randrange, 'elixir', 'mage')
