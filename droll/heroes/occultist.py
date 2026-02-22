# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Occultist advancing to Necromancer."""

from dataclasses import replace
from functools import partial

from ..ability import necromancer_ability, occultist_ability
from ..player import Default
from ..regular import defeat_dragon, defeat_dragon_heroes

__all__ = (
    "Necromancer",
    "Occultist",
)

# Cleric/mage are interchangeable for dragon defeats
_occultist_defeat_dragon = partial(
    defeat_dragon,
    hero_validator=partial(
        defeat_dragon_heroes,
        interchangeable=frozenset({"cleric", "mage"}),
    ),
)

# Defined in terms of Default, not Occultist, to permit advance(...) closure
Necromancer = replace(
    Default,
    name="Necromancer",
    ability=necromancer_ability,
    advance=(lambda _: Necromancer),
    party=replace(
        Default.party,
        fighter=replace(
            Default.party.fighter,
            dragon=_occultist_defeat_dragon,
        ),
        cleric=replace(
            Default.party.cleric,
            dragon=_occultist_defeat_dragon,
            ooze=Default.party.mage.ooze,
        ),
        mage=replace(
            Default.party.mage,
            dragon=_occultist_defeat_dragon,
            skeleton=Default.party.cleric.skeleton,
        ),
        thief=replace(
            Default.party.thief,
            dragon=_occultist_defeat_dragon,
        ),
        champion=replace(
            Default.party.champion,
            dragon=_occultist_defeat_dragon,
        ),
        scroll=replace(
            Default.party.scroll,
            dragon=_occultist_defeat_dragon,
        ),
    ),
)

# Defined after Necromancer to permit advance(...) closure
Occultist = replace(
    Default,
    name="Occultist",
    ability=occultist_ability,
    advance=(lambda world: Occultist if world.experience < 5 else Necromancer),
    party=Necromancer.party,
)
