# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Spellsword advancing to Battlemage."""

from dataclasses import replace
from functools import partial

from .. import regular, struct
from ..ability import battlemage_ability, spellsword_ability
from ..player import Default

__all__ = (
    "Battlemage",
    "Spellsword",
)

_battlemage_ability = battlemage_ability
_spellsword_ability = spellsword_ability

# Fighter/mage are interchangeable for dragon defeats
_spellsword_defeat_dragon = partial(
    regular.defeat_dragon,
    defeat_dragon_heroes=partial(
        regular.defeat_dragon_heroes,
        interchangeable=frozenset({"fighter", "mage"}),
    ),
)


# Defined in terms of Default, not Spellsword, to permit advance(...) closure
Battlemage = replace(
    Default,
    name="Battlemage",
    ability=_battlemage_ability,
    advance=(lambda _: Battlemage),
    party=replace(
        Default.party,
        fighter=replace(
            Default.party.fighter,
            dragon=_spellsword_defeat_dragon,
            ooze=Default.party.mage.ooze,
        ),
        cleric=replace(
            Default.party.cleric,
            dragon=_spellsword_defeat_dragon,
        ),
        mage=replace(
            Default.party.mage,
            dragon=_spellsword_defeat_dragon,
            goblin=Default.party.fighter.goblin,
        ),
        thief=replace(
            Default.party.thief,
            dragon=_spellsword_defeat_dragon,
        ),
        champion=replace(
            Default.party.champion,
            dragon=_spellsword_defeat_dragon,
        ),
        scroll=replace(
            Default.party.scroll,
            dragon=_spellsword_defeat_dragon,
        ),
    ),
)

# Defined after Battlemage to permit advance(...) closure
Spellsword = replace(
    Default,
    name="Spellsword",
    ability=_spellsword_ability,
    advance=(lambda world: Spellsword if world.experience < 5 else Battlemage),
    party=Battlemage.party,
)
