# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Mercenary advancing to Commander."""

from dataclasses import replace

from .. import dice, special
from ..ability import commander_ability, mercenary_ability
from ..player import Default
from ..struct import Dungeon, Party, RandRange, PartyState, Regroup, frozen

__all__ = (
    "Commander",
    "Mercenary",
)


def _mercenary_roll_party(
    count: int, randrange: RandRange
) -> tuple[PartyState, Regroup]:
    """Roll a new Party, adding one bonus scroll discarded on regroup."""
    party, regroup = dice.roll_party(dice=count, randrange=randrange)
    return (
        frozen({**party, Party.SCROLL: party[Party.SCROLL] + 1}),
        replace(regroup, discard=frozen({**regroup.discard, Party.SCROLL: 1})),
    )


# Defined in terms of Default, not Mercenary, to permit advance(...) closure
Commander = replace(
    Default,
    name="Commander",
    ability=commander_ability,
    advance=(lambda _: Commander),
    roll=replace(Default.roll, party=_mercenary_roll_party),
    party=frozen({
        **Default.party,
        Party.FIGHTER: frozen({
            **Default.party[Party.FIGHTER],
            Dungeon.GOBLIN: special.defeat_all_plus_additional,
            Dungeon.SKELETON: special.defeat_one_plus_additional,
            Dungeon.OOZE: special.defeat_one_plus_additional,
        }),
    }),
)

# Defined after Commander to permit advance(...) closure
Mercenary = replace(
    Default,
    name="Mercenary",
    ability=mercenary_ability,
    advance=(lambda world: Mercenary if world.experience < 5 else Commander),
    roll=replace(Default.roll, party=_mercenary_roll_party),
)
