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
    game = droll.world.new_delve(game, state.randrange)
    assert 0 == game.depth
    assert game.ability is True
    assert 7 == sum(game.party)


def test_level_initial(state):
    game = droll.world.new_game()
    game = droll.world.new_delve(game, state.randrange)
    game = droll.world.next_level(game, state.randrange)
    assert 1 == game.depth
    assert 1 == sum(game.level)


def test_treasure(state):
    pre = droll.world.new_game()
    item, post = droll.world.draw_treasure(pre, state.randrange)
    assert item in droll.world.Treasure._fields
    assert sum(pre.treasure) == 0
    assert sum(pre.treasure) == 0
    assert sum(post.treasure) == 1
    assert sum(pre.chest) - sum(post.chest) == 1

    reset = droll.world.replace_treasure(post, item)
    assert pre.treasure == reset.treasure
    assert pre.chest == reset.chest
