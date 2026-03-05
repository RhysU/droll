# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Occultist advancing to Necromancer."""

from dataclasses import replace
from functools import partial

from ..ability import necromancer_ability, occultist_ability
from ..player import Default
from ..regular import defeat_dragon, defeat_dragon_heroes
from ..struct import Dungeon, Party, frozen

__all__ = (
    "Necromancer",
    "Occultist",
)

# Cleric/mage are interchangeable for dragon defeats
_occultist_defeat_dragon = partial(
    defeat_dragon,
    hero_validator=partial(
        defeat_dragon_heroes,
        interchangeable=frozenset({Party.CLERIC, Party.MAGE}),
    ),
)

# Defined in terms of Default, not Occultist, to permit advance(...) closure
Necromancer = replace(
    Default,
    name="Necromancer",
    ability=necromancer_ability,
    advance=(lambda _: Necromancer),
    party=frozen({
        Party.FIGHTER: frozen({
            **Default.party[Party.FIGHTER],
            Dungeon.DRAGON: _occultist_defeat_dragon,
        }),
        Party.CLERIC: frozen({
            **Default.party[Party.CLERIC],
            Dungeon.DRAGON: _occultist_defeat_dragon,
            Dungeon.OOZE: Default.party[Party.MAGE][Dungeon.OOZE],
        }),
        Party.MAGE: frozen({
            **Default.party[Party.MAGE],
            Dungeon.DRAGON: _occultist_defeat_dragon,
            Dungeon.SKELETON: Default.party[Party.CLERIC][Dungeon.SKELETON],
        }),
        Party.THIEF: frozen({
            **Default.party[Party.THIEF],
            Dungeon.DRAGON: _occultist_defeat_dragon,
        }),
        Party.CHAMPION: frozen({
            **Default.party[Party.CHAMPION],
            Dungeon.DRAGON: _occultist_defeat_dragon,
        }),
        Party.SCROLL: frozen({
            **Default.party[Party.SCROLL],
            Dungeon.DRAGON: _occultist_defeat_dragon,
        }),
    }),
)

# Defined after Necromancer to permit advance(...) closure
Occultist = replace(
    Default,
    name="Occultist",
    ability=occultist_ability,
    advance=(lambda world: Occultist if world.experience < 5 else Necromancer),
    party=Necromancer.party,
)
