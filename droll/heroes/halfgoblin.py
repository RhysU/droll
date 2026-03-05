# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Half-Goblin advancing to Chieftain."""

from dataclasses import replace
from functools import partial

from .. import regular
from ..ability import chieftain_ability, halfgoblin_ability
from ..player import Default
from ..struct import Dungeon, Party, frozen

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
    party=frozen({
        Party.FIGHTER: frozen({
            **Default.party[Party.FIGHTER],
            Dungeon.CHEST: _halfgoblin_open_one,
            Dungeon.POTION: _halfgoblin_quaff,
        }),
        Party.CLERIC: frozen({
            **Default.party[Party.CLERIC],
            Dungeon.CHEST: _halfgoblin_open_one,
            Dungeon.POTION: _halfgoblin_quaff,
        }),
        Party.MAGE: frozen({
            **Default.party[Party.MAGE],
            Dungeon.CHEST: _halfgoblin_open_one,
            Dungeon.POTION: _halfgoblin_quaff,
        }),
        Party.THIEF: frozen({
            **Default.party[Party.THIEF],
            Dungeon.CHEST: _halfgoblin_open_all,
            Dungeon.POTION: _halfgoblin_quaff,
        }),
        Party.CHAMPION: frozen({
            **Default.party[Party.CHAMPION],
            Dungeon.CHEST: _halfgoblin_open_all,
            Dungeon.POTION: _halfgoblin_quaff,
        }),
        Party.SCROLL: frozen({
            **Default.party[Party.SCROLL],
            Dungeon.POTION: _halfgoblin_quaff,
        }),
    }),
)

# Defined after Chieftain to permit advance(...) closure
HalfGoblin = replace(
    Default,
    name="HalfGoblin",
    ability=halfgoblin_ability,
    advance=(lambda world: HalfGoblin if world.experience < 5 else Chieftain),
    party=Chieftain.party,
)
