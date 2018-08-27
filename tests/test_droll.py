# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import random

import droll.world


@pytest.fixture(name='state')
def _state():
    return random.Random(4)


def test_game_initial():
    game = droll.world.new_game()
    assert 0 == game.experience
    assert 0 == sum(game.treasure)
    assert (6*3) + (4*3) + 6 == sum(game.chest)


def test_delve_initial(state):
    game = droll.world.new_game()
    delve = droll.world.new_delve(game, state.randrange)
    assert 0 == delve.depth
    assert delve.ability is True
    assert 7 == sum(delve.party)


def test_level_initial(state):
    game = droll.world.new_game()
    delve = droll.world.new_delve(game, state.randrange)
    level = droll.world.next_level(delve, state.randrange)
    assert 1 == level.depth
    assert 1 == sum(level.level)
