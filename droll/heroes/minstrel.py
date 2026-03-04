# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Minstrel advancing to Bard."""

from dataclasses import replace
from functools import partial

from .. import special, struct
from ..ability import bard_ability, minstrel_ability
from ..player import Default
from ..regular import defeat_dragon, defeat_dragon_heroes

__all__ = (
    "Bard",
    "Minstrel",
)

# Mage/thief are interchangeable for dragon defeats
_minstrel_defeat_dragon = partial(
    defeat_dragon,
    hero_validator=partial(
        defeat_dragon_heroes,
        interchangeable=frozenset({"mage", "thief"}),
    ),
)

# Building block: dragon defeat + mage/thief interchangeability in combat
_Minstrel_Party = struct.Party(
    fighter=replace(
        Default.party.fighter,
        dragon=_minstrel_defeat_dragon,
    ),
    cleric=replace(
        Default.party.cleric,
        dragon=_minstrel_defeat_dragon,
    ),
    mage=replace(
        Default.party.mage,
        chest=Default.party.thief.chest,
        dragon=_minstrel_defeat_dragon,
    ),
    thief=replace(
        Default.party.thief,
        dragon=_minstrel_defeat_dragon,
        ooze=Default.party.mage.ooze,
    ),
    champion=replace(
        Default.party.champion,
        dragon=_minstrel_defeat_dragon,
    ),
    scroll=replace(
        Default.party.scroll,
        dragon=_minstrel_defeat_dragon,
    ),
)

# Defined in terms of Default, not Minstrel, to permit advance(...) closure
Bard = replace(
    Default,
    name="Bard",
    ability=bard_ability,
    advance=(lambda _: Bard),  # Cannot advance further
    party=replace(
        _Minstrel_Party,
        champion=replace(
            _Minstrel_Party.champion,
            # Champions defeat one additional monster when attacking monsters
            goblin=special.defeat_all_plus_additional,
            skeleton=special.defeat_all_plus_additional,
            ooze=special.defeat_all_plus_additional,
        ),
    ),
)

# Defined after Bard to permit advance(...) closure
Minstrel = replace(
    Default,
    name="Minstrel",
    ability=minstrel_ability,
    advance=(lambda world: Minstrel if world.experience < 5 else Bard),
    party=_Minstrel_Party,
)
