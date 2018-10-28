# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions."""
import collections

from . import player

# TODO Implement the following initial characters
# TODO Implement promotion after 5 experience points
# Spellsword -> Battlemage
# Crusader -> Paladin
# Knight -> Dragon Slayer
# Mercenary -> Commander
# Enchantress -> Beguiler
# Occultist -> Necromancer
# Minstrel -> Bard
# Half-goblin -> Chieftan

KNOWN = collections.OrderedDict([
    ('Default', player.DEFAULT),
])
