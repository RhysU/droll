# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for party module helpers."""

import pytest

from droll.error import DrollError
from droll.party import decrement_party, decrement_regroup, increment_party
from droll.struct import Party, Regroup


def test_decrement_party():
    """Decrementing a positive hero count yields one fewer."""
    party = Party(fighter=2, cleric=1)
    result = decrement_party(party, "fighter")
    assert result.fighter == 1


def test_decrement_party_zero_target():
    """Cannot decrement a hero that is already zero."""
    party = Party(fighter=0, cleric=1)
    with pytest.raises(DrollError):
        decrement_party(party, "fighter")


def test_decrement_party_none():
    """Cannot decrement when no party is active."""
    with pytest.raises(DrollError):
        decrement_party(None, "fighter")


def test_increment_party():
    """Incrementing a hero count yields one more."""
    party = Party(fighter=1)
    result = increment_party(party, "fighter")
    assert result.fighter == 2


def test_increment_party_none():
    """Cannot increment when no party is active."""
    with pytest.raises(DrollError):
        increment_party(None, "fighter")


def test_decrement_regroup_positive():
    """Decrementing a positive discard counter yields one fewer."""
    regroup = Regroup(discard=Party(thief=2))
    result = decrement_regroup(regroup, "thief")
    assert result.discard.thief == 1


def test_decrement_regroup_zero():
    """Decrementing a zero discard counter stays at zero."""
    regroup = Regroup(discard=Party(thief=0))
    result = decrement_regroup(regroup, "thief")
    assert result.discard.thief == 0
