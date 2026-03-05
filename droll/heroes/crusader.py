# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Crusader advancing to Paladin."""

from dataclasses import replace
from functools import partial

from .. import regular
from ..ability import crusader_ability, paladin_ability
from ..player import Default
from ..struct import Dungeon, Party, frozen

__all__ = (
    "Crusader",
    "Paladin",
)

# Fighter/cleric are interchangeable for dragon defeats
_crusader_defeat_dragon = partial(
    regular.defeat_dragon,
    hero_validator=partial(
        regular.defeat_dragon_heroes,
        interchangeable=frozenset({Party.FIGHTER, Party.CLERIC}),
    ),
)

# Defined in terms of Default, not Crusader, to permit advance(...) closure
Paladin = replace(
    Default,
    name="Paladin",
    ability=paladin_ability,
    advance=(lambda _: Paladin),
    party=frozen({
        Party.FIGHTER: frozen({
            **Default.party[Party.FIGHTER],
            Dungeon.DRAGON: _crusader_defeat_dragon,
            Dungeon.SKELETON: Default.party[Party.CLERIC][Dungeon.SKELETON],
        }),
        Party.CLERIC: frozen({
            **Default.party[Party.CLERIC],
            Dungeon.DRAGON: _crusader_defeat_dragon,
            Dungeon.GOBLIN: Default.party[Party.FIGHTER][Dungeon.GOBLIN],
        }),
        Party.MAGE: frozen({
            **Default.party[Party.MAGE],
            Dungeon.DRAGON: _crusader_defeat_dragon,
        }),
        Party.THIEF: frozen({
            **Default.party[Party.THIEF],
            Dungeon.DRAGON: _crusader_defeat_dragon,
        }),
        Party.CHAMPION: frozen({
            **Default.party[Party.CHAMPION],
            Dungeon.DRAGON: _crusader_defeat_dragon,
        }),
        Party.SCROLL: frozen({
            **Default.party[Party.SCROLL],
            Dungeon.DRAGON: _crusader_defeat_dragon,
        }),
    }),
)

# Defined after Paladin to permit advance(...) closure
Crusader = replace(
    Paladin,
    name="Crusader",
    ability=crusader_ability,
    advance=(lambda world: Crusader if world.experience < 5 else Paladin),
    party=Paladin.party,
)
