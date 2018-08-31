# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import random

import droll.player

@pytest.fixture(name='party')
def _party():
    return droll.player.Party(*([1] * len(droll.player.Party._fields)))

def test_fighter(party):
    pass

def test_cleric(party):
    pass

def test_mage(party):
    pass

def test_thief(party):
    pass

def test_champion(party):
    pass
