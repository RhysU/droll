# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of Game (at least driving with basic commands)."""

import random

from droll.game import Game, GameState
from droll.player import Default


def test_game_construction():
    Game()
    Game(player=Default)
    Game(random=random.Random(4))


def test_gamestate_truthiness():
    assert GameState.STOP, "STOP must coerce to True."
    assert not GameState.PLAY, "PLAY must coerce to False."
