# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Enchantress advancing to Beguiler."""

from dataclasses import replace
from functools import partial

from .. import regular
from ..ability import beguiler_ability, enchantress_ability
from ..player import Default
from ..struct import Dungeon, Party, frozen

__all__ = (
    "Beguiler",
    "Enchantress",
)

# Scrolls act as wildcards for dragon defeats
_beguiler_defeat_dragon = partial(
    regular.defeat_dragon,
    hero_validator=partial(
        regular.defeat_dragon_heroes,
        disallowed_heroes=frozenset(),
        wildcard=frozenset({Party.SCROLL}),
    ),
)

# Defined in terms of Default, not Enchantress, to permit advance(...) closure
Beguiler = replace(
    Default,
    name="Beguiler",
    ability=beguiler_ability,
    advance=(lambda _: Beguiler),
    party=frozen({
        **Default.party,
        # Scrolls act offensively (defeat enemies, not re-roll)
        Party.SCROLL: frozen({
            Dungeon.GOBLIN: regular.defeat_all,
            Dungeon.SKELETON: regular.defeat_all,
            Dungeon.OOZE: regular.defeat_all,
            Dungeon.CHEST: regular.open_all,
            Dungeon.POTION: regular.quaff,
            Dungeon.DRAGON: _beguiler_defeat_dragon,
        }),
    }),
)

# Defined after Beguiler to permit advance(...) closure
Enchantress = replace(
    Default,
    name="Enchantress",
    ability=enchantress_ability,
    advance=(lambda world: Enchantress if world.experience < 5 else Beguiler),
    party=Beguiler.party,
)
