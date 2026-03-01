# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""All known hero definitions."""

from types import MappingProxyType

from .crusader import Crusader, Paladin
from .enchantress import Beguiler, Enchantress
from .halfgoblin import Chieftain, HalfGoblin
from .knight import Knight, DragonSlayer
from .mercenary import Mercenary, Commander
from .minstrel import Minstrel, Bard
from .occultist import Occultist, Necromancer
from .spellsword import Spellsword, Battlemage

__all__ = (
    "AVAILABLE",
    Bard.name,
    Battlemage.name,
    Beguiler.name,
    Chieftain.name,
    Commander.name,
    Crusader.name,
    DragonSlayer.name,
    Enchantress.name,
    HalfGoblin.name,
    Knight.name,
    Mercenary.name,
    Minstrel.name,
    Necromancer.name,
    Occultist.name,
    Paladin.name,
    Spellsword.name,
)

AVAILABLE = MappingProxyType(
    {
        Crusader.name: Crusader,
        Enchantress.name: Enchantress,
        HalfGoblin.name: HalfGoblin,
        Knight.name: Knight,
        Mercenary.name: Mercenary,
        Minstrel.name: Minstrel,
        Occultist.name: Occultist,
        Spellsword.name: Spellsword,
    }
)
