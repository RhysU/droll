# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Half-Goblin advancing to Chieftain."""

from dataclasses import replace
from functools import partial

from .. import regular, struct
from ..ability import chieftain_ability, halfgoblin_ability
from ..player import Default

__all__ = (
    "Chieftain",
    "HalfGoblin",
)

# You may open chests and quaff potions at any time during the monster phase
_halfgoblin_open_one = partial(
    regular.open_one,
    after_monsters=False,
)
_halfgoblin_open_all = partial(
    regular.open_all,
    after_monsters=False,
)
_halfgoblin_quaff = partial(
    regular.quaff,
    after_monsters=False,
)

# Defined in terms of Default, not Half-Goblin, to permit advance(...) closure
Chieftain = replace(
    Default,
    name="Chieftain",
    ability=chieftain_ability,
    advance=(lambda _: Chieftain),
    party=replace(
        Default.party,
        fighter=replace(
            Default.party.fighter,
            chest=_halfgoblin_open_one,
            potion=_halfgoblin_quaff,
        ),
        cleric=replace(
            Default.party.cleric,
            chest=_halfgoblin_open_one,
            potion=_halfgoblin_quaff,
        ),
        mage=replace(
            Default.party.mage,
            chest=_halfgoblin_open_one,
            potion=_halfgoblin_quaff,
        ),
        thief=replace(
            Default.party.thief,
            chest=_halfgoblin_open_all,
            potion=_halfgoblin_quaff,
        ),
        champion=replace(
            Default.party.champion,
            chest=_halfgoblin_open_all,
            potion=_halfgoblin_quaff,
        ),
        scroll=replace(
            Default.party.scroll,
            potion=_halfgoblin_quaff,
        ),
    ),
)

# Defined after Chieftain to permit advance(...) closure
HalfGoblin = replace(
    Default,
    name="HalfGoblin",
    ability=halfgoblin_ability,
    advance=(lambda world: HalfGoblin if world.experience < 5 else Chieftain),
    party=Chieftain.party,
)
