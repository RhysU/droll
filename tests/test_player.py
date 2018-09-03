# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import random

import droll.player as player
import droll.world as world


@pytest.fixture(name='world')
def _world():
    return world.new_game()._replace(
        level=world.Level(*([2] * len(world.Level._fields))),
        party=world.Party(*([2] * len(world.Party._fields))),
    )


def test_fighter(world):
    pass


def test_cleric(world):
    pass


def test_mage(world):
    pass


def test_thief(world):
    pass


def test_champion(world):
    pass
