# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of dice rolling boundary conditions."""

import random

import pytest

import droll.dice
import droll.struct


@pytest.fixture(name="state")
def _state():
    return random.Random(4)


def test_roll_zero_dice(state):
    """Rolling zero dice should return empty results."""
    party = droll.dice.roll_party(dice=0, randrange=state.randrange)
    assert sum(droll.struct.field_values(party)) == 0


def test_roll_dungeon_minimum(state):
    """Roll dungeon with minimum (1) dice."""
    dungeon = droll.dice.roll_dungeon(dice=1, randrange=state.randrange)
    assert sum(droll.struct.field_values(dungeon)) == 1


def test_roll_dungeon_zero_fails(state):
    """Rolling dungeon with zero dice should fail."""
    with pytest.raises(AssertionError):
        droll.dice.roll_dungeon(dice=0, randrange=state.randrange)


def test_roll_party_many_dice(state):
    """Roll party with many dice to ensure no overflow issues."""
    party = droll.dice.roll_party(dice=100, randrange=state.randrange)
    assert sum(droll.struct.field_values(party)) == 100
