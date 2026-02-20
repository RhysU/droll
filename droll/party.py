# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with party state and party mechanics."""

from dataclasses import replace

from .struct import DrollError, Party, Regroup

__all__ = (
    "decrement_party",
    "decrement_regroup",
    "increment_party",
)


def decrement_party(party: Party, hero: str) -> Party:
    """Decrease the count of the specified hero type by one."""
    if party is None:
        raise DrollError("No party currently active.")
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise DrollError(f"At least 1 {hero} required.")
    return replace(party, **{hero: prior_heroes - 1})


def decrement_regroup(regroup: Regroup, hero: str) -> Regroup:
    """Decrement the regroup discard counter for hero, if positive."""
    prior = getattr(regroup.discard, hero, 0)
    return replace(
        regroup, discard=replace(regroup.discard, **{hero: max(0, prior - 1)})
    )


def increment_party(party: Party, hero: str) -> Party:
    """Increase the count of the specified hero type by one."""
    if party is None:
        raise DrollError("No party currently active.")
    return replace(party, **{hero: getattr(party, hero) + 1})
