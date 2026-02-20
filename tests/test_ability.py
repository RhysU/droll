# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for the ability module."""

import pytest

import droll.struct
from droll.ability import default_ability

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_consume_ability_when_unavailable():
    """Cannot consume ability that is already used."""
    w = droll.struct.World(ability=False)
    with pytest.raises(droll.struct.DrollError):
        default_ability(w, _UNUSED, "ability")


def test_default_ability_rejects_target():
    """Default ability rejects any target."""
    w = droll.struct.World(ability=True)
    with pytest.raises(droll.struct.DrollError):
        default_ability(w, _UNUSED, "ability", "fighter")
