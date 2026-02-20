# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Mercenary advancing to Commander."""

from dataclasses import replace

from .. import dice, special, struct
from ..ability import commander_ability, mercenary_ability
from ..player import Default

__all__ = (
    "Commander",
    "Mercenary",
)

_commander_ability = commander_ability
_mercenary_ability = mercenary_ability


def _mercenary_roll_party(
    count: int, randrange: dice.RandRange
) -> tuple[struct.Party, struct.Regroup]:
    """Roll a new Party, adding one bonus scroll discarded at next regroup."""
    party, regroup = dice.roll_party(dice=count, randrange=randrange)
    return (
        replace(party, scroll=party.scroll + 1),
        replace(regroup, discard=replace(regroup.discard, scroll=1)),
    )


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
            goblin=special.defeat_all_plus_additional,
            skeleton=special.defeat_one_plus_additional,
            ooze=special.defeat_one_plus_additional,
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
