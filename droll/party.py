# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with party state and party mechanics."""

from dataclasses import replace

from .struct import DrollError, Party, Regroup, field_names

__all__ = (
    "decrement_party",
    "decrement_regroup",
    "increment_party",
)

_PARTY_FIELDS = frozenset(field_names(Party))


def _check_party_member(hero: str) -> None:
    if hero not in _PARTY_FIELDS:
        raise DrollError(f"Unknown party member '{hero}'.")


def decrement_party(party: Party, hero: str) -> Party:
    """Decrease the count of the specified hero type by one."""
    _check_party_member(hero)
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise DrollError(f"At least 1 {hero} required in party.")
    return replace(party, **{hero: prior_heroes - 1})


def decrement_regroup(regroup: Regroup, hero: str) -> Regroup:
    """Decrement the regroup discard counter for hero, if positive."""
    _check_party_member(hero)
    prior = getattr(regroup.discard, hero, 0)
    return replace(
        regroup, discard=replace(regroup.discard, **{hero: max(0, prior - 1)})
    )


def increment_party(party: Party, hero: str) -> Party:
    """Increase the count of the specified hero type by one."""
    _check_party_member(hero)
    return replace(party, **{hero: getattr(party, hero) + 1})
