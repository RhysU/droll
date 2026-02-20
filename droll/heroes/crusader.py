# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Crusader advancing to Paladin."""

from dataclasses import replace
from functools import partial

from .. import regular, struct
from ..ability import crusader_ability, paladin_ability
from ..player import Default

__all__ = (
    "Crusader",
    "Paladin",
)

_crusader_ability = crusader_ability
_paladin_ability = paladin_ability

# Fighter/cleric are interchangeable for dragon defeats
_crusader_defeat_dragon = partial(
    regular.defeat_dragon,
    defeat_dragon_heroes=partial(
        regular.defeat_dragon_heroes,
        interchangeable=frozenset({"fighter", "cleric"}),
    ),
)

# Defined in terms of Default, not Crusader, to permit advance(...) closure
Paladin = replace(
    Default,
    name="Paladin",
    ability=_paladin_ability,
    advance=(lambda _: Paladin),
    party=struct.Party(
        fighter=replace(
            Default.party.fighter,
            dragon=_crusader_defeat_dragon,
            skeleton=Default.party.cleric.skeleton,
        ),
        cleric=replace(
            Default.party.cleric,
            dragon=_crusader_defeat_dragon,
            goblin=Default.party.fighter.goblin,
        ),
        mage=replace(
            Default.party.mage,
            dragon=_crusader_defeat_dragon,
        ),
        thief=replace(
            Default.party.thief,
            dragon=_crusader_defeat_dragon,
        ),
        champion=replace(
            Default.party.champion,
            dragon=_crusader_defeat_dragon,
        ),
        scroll=replace(
            Default.party.scroll,
            dragon=_crusader_defeat_dragon,
        ),
    ),
)

# Defined after Paladin to permit advance(...) closure
Crusader = replace(
    Paladin,
    name="Crusader",
    ability=_crusader_ability,
    advance=(lambda world: Crusader if world.experience < 5 else Paladin),
    party=Paladin.party,
)
