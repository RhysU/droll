# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Enchantress advancing to Beguiler."""

from dataclasses import replace
from functools import partial

from .. import regular, struct
from ..ability import beguiler_ability, enchantress_ability
from ..player import Default

__all__ = (
    "Beguiler",
    "Enchantress",
)

_beguiler_ability = beguiler_ability
_enchantress_ability = enchantress_ability

# Scrolls act as wildcards for dragon defeats
_beguiler_defeat_dragon = partial(
    regular.defeat_dragon,
    defeat_dragon_heroes=partial(
        regular.defeat_dragon_heroes,
        disallowed_heroes=frozenset(),
        wildcard=frozenset({"scroll"}),
    ),
)

# Defined in terms of Default, not Enchantress, to permit advance(...) closure
Beguiler = replace(
    Default,
    name="Beguiler",
    ability=_beguiler_ability,
    advance=(lambda _: Beguiler),
    party=replace(
        Default.party,
        # Scrolls act offensively (defeat enemies, not re-roll)
        scroll=struct.Dungeon(
            goblin=regular.defeat_all,
            skeleton=regular.defeat_all,
            ooze=regular.defeat_all,
            chest=regular.open_all,
            potion=regular.quaff,
            dragon=_beguiler_defeat_dragon,
        ),
    ),
)

# Defined after Beguiler to permit advance(...) closure
Enchantress = replace(
    Default,
    name="Enchantress",
    ability=_enchantress_ability,
    advance=(lambda world: Enchantress if world.experience < 5 else Beguiler),
    party=Beguiler.party,
)
