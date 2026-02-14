# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""All known hero definitions."""

from .crusader import Crusader, Paladin
from .enchantress import Beguiler, Enchantress
from .halfgoblin import Chieftain, HalfGoblin
from .knight import Knight, DragonSlayer
from .minstrel import Minstrel, Bard
from .spellsword import Spellsword, Battlemage

__all__ = (
    Bard.name,
    Battlemage.name,
    Beguiler.name,
    Chieftain.name,
    Crusader.name,
    DragonSlayer.name,
    Enchantress.name,
    HalfGoblin.name,
    Knight.name,
    Minstrel.name,
    Paladin.name,
    Spellsword.name,
)
