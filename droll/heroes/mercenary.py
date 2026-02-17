# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Mercenary advancing to Commander."""
from __future__ import annotations

from dataclasses import replace
import functools

from .. import action
from .. import dice
from .. import error
from .. import struct
from ..player import Default

__all__ = (
    "Commander",
    "Mercenary",
)


def _mercenary_roll_party(
    count: int, randrange: dice.RandRange
) -> tuple[struct.Party, struct.Regroup]:
    """Roll a new Party, adding one bonus scroll discarded at next regroup."""
    party, regroup = dice.roll_party(dice=count, randrange=randrange)
    return (
        replace(party, scroll=party.scroll + 1),
        replace(regroup, discard=replace(regroup.discard, scroll=1)),
    )


def _mercenary_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: str | None = None,
    *additional,
) -> struct.World:
    """Defeat any 2 monsters."""
    if target is None:
        raise error.DrollError(f"Must specify target for {noun}.")
    # Temporarily add a champion to be consumed by defeat_one_plus_additional
    world = replace(
        world, party=action.increment_party(world.party, "champion")
    )
    world = action.defeat_one_plus_additional(
        world, randrange, "champion", target, *additional
    )
    return action.consume_ability(world)


def _commander_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: str | None = None,
    *additional,
) -> struct.World:
    """Rerolls any number of Party and Dungeon dice."""
    if target is None:
        raise error.DrollError(
            f"Must specify at least one target to reroll for {noun}."
        )
    # Temporarily add a scroll to be consumed by reroll
    world = replace(world, party=action.increment_party(world.party, "scroll"))
    world = action.reroll(
        world, randrange, "scroll", target, *additional, allow_dragon=True
    )
    return action.consume_ability(world)


# Defined in terms of Default, not Mercenary, to permit advance(...) closure
Commander = replace(
    Default,
    name="Commander",
    ability=_commander_ability,
    advance=(lambda _: Commander),
    roll=replace(Default.roll, party=_mercenary_roll_party),
    party=replace(
        Default.party,
        fighter=replace(
            Default.party.fighter,
            goblin=action.defeat_all_plus_additional,
            skeleton=action.defeat_one_plus_additional,
            ooze=action.defeat_one_plus_additional,
        ),
    ),
)

# Defined after Commander to permit advance(...) closure
Mercenary = replace(
    Default,
    name="Mercenary",
    ability=_mercenary_ability,
    advance=(lambda world: Mercenary if world.experience < 5 else Commander),
    roll=replace(Default.roll, party=_mercenary_roll_party),
)
