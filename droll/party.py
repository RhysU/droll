# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with party state and party mechanics."""

from dataclasses import replace

from .struct import DrollError, Party, PartyState, Regroup, frozen

__all__ = (
    "decrement_party",
    "decrement_regroup",
    "increment_party",
)


def decrement_party(party: PartyState, hero: Party) -> PartyState:
    """Decrease the count of the specified hero type by one."""
    prior_heroes = party[hero]
    if not prior_heroes:
        raise DrollError(f"At least 1 {hero.value} required in party.")
    return frozen({**party, hero: prior_heroes - 1})


def decrement_regroup(regroup: Regroup, hero: Party) -> Regroup:
    """Decrement the regroup discard counter for hero, if positive."""
    prior = regroup.discard[hero]
    return replace(
        regroup, discard=frozen({**regroup.discard, hero: max(0, prior - 1)})
    )


def increment_party(party: PartyState, hero: Party) -> PartyState:
    """Increase the count of the specified hero type by one."""
    return frozen({**party, hero: party[hero] + 1})
