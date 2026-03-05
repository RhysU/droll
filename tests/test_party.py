# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for party module helpers."""

import pytest

from droll.party import decrement_party, decrement_regroup, increment_party
from droll.struct import DrollError, Party, Regroup, make_party


def test_decrement_party():
    """Decrementing a positive hero count yields one fewer."""
    party = make_party(fighter=2, cleric=1)
    result = decrement_party(party, Party.FIGHTER)
    assert result[Party.FIGHTER] == 1


def test_decrement_party_zero_target():
    """Cannot decrement a hero that is already zero."""
    party = make_party(fighter=0, cleric=1)
    with pytest.raises(DrollError):
        decrement_party(party, Party.FIGHTER)


def test_increment_party():
    """Incrementing a hero count yields one more."""
    party = make_party(fighter=1)
    result = increment_party(party, Party.FIGHTER)
    assert result[Party.FIGHTER] == 2


def test_decrement_regroup_positive():
    """Decrementing a positive discard counter yields one fewer."""
    regroup = Regroup(discard=make_party(thief=2))
    result = decrement_regroup(regroup, Party.THIEF)
    assert result.discard[Party.THIEF] == 1


def test_decrement_regroup_zero():
    """Decrementing a zero discard counter stays at zero."""
    regroup = Regroup(discard=make_party(thief=0))
    result = decrement_regroup(regroup, Party.THIEF)
    assert result.discard[Party.THIEF] == 0
