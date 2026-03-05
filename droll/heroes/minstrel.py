# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Minstrel advancing to Bard."""

from dataclasses import replace
from functools import partial

from .. import special
from ..ability import bard_ability, minstrel_ability
from ..player import Default
from ..regular import defeat_dragon, defeat_dragon_heroes
from ..struct import Dungeon, Party, frozen

__all__ = (
    "Bard",
    "Minstrel",
)

# Mage/thief are interchangeable for dragon defeats
_minstrel_defeat_dragon = partial(
    defeat_dragon,
    hero_validator=partial(
        defeat_dragon_heroes,
        interchangeable=frozenset({Party.MAGE, Party.THIEF}),
    ),
)

# Building block: dragon defeat + mage/thief interchangeability in combat
_minstrel_party = frozen({
    Party.FIGHTER: frozen({
        **Default.party[Party.FIGHTER],
        Dungeon.DRAGON: _minstrel_defeat_dragon,
    }),
    Party.CLERIC: frozen({
        **Default.party[Party.CLERIC],
        Dungeon.DRAGON: _minstrel_defeat_dragon,
    }),
    Party.MAGE: frozen({
        **Default.party[Party.MAGE],
        Dungeon.CHEST: Default.party[Party.THIEF][Dungeon.CHEST],
        Dungeon.DRAGON: _minstrel_defeat_dragon,
    }),
    Party.THIEF: frozen({
        **Default.party[Party.THIEF],
        Dungeon.DRAGON: _minstrel_defeat_dragon,
        Dungeon.OOZE: Default.party[Party.MAGE][Dungeon.OOZE],
    }),
    Party.CHAMPION: frozen({
        **Default.party[Party.CHAMPION],
        Dungeon.DRAGON: _minstrel_defeat_dragon,
    }),
    Party.SCROLL: frozen({
        **Default.party[Party.SCROLL],
        Dungeon.DRAGON: _minstrel_defeat_dragon,
    }),
})

# Defined in terms of Default, not Minstrel, to permit advance(...) closure
Bard = replace(
    Default,
    name="Bard",
    ability=bard_ability,
    advance=(lambda _: Bard),  # Cannot advance further
    party=frozen({
        **_minstrel_party,
        Party.CHAMPION: frozen({
            **_minstrel_party[Party.CHAMPION],
            # Champions defeat one additional monster when attacking monsters
            Dungeon.GOBLIN: special.defeat_all_plus_additional,
            Dungeon.SKELETON: special.defeat_all_plus_additional,
            Dungeon.OOZE: special.defeat_all_plus_additional,
        }),
    }),
)

# Defined after Bard to permit advance(...) closure
Minstrel = replace(
    Default,
    name="Minstrel",
    ability=minstrel_ability,
    advance=(lambda world: Minstrel if world.experience < 5 else Bard),
    party=_minstrel_party,
)
