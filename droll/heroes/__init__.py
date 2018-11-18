# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions."""
import collections

from .knight import Knight, DragonSlayer
from .spellsword import Spellsword, Battlemage
from ..player import Default

KNOWN = collections.OrderedDict([
    ('Default', Default),
    ('Knight', Knight),
    ('Spellsword', Spellsword),
])
