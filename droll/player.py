# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import typing

from droll.world import Level, Party

# Encodes default hero-vs-enemy capabilities
_MANY_DEFAULT = Party(
    fighter=Level(
        goblin=True,
        skeleton=False,
        ooze=False,
        chest=False,
        potion=True,
        dragon=False,
    ),
    cleric=Level(
        goblin=False,
        skeleton=True,
        ooze=False,
        chest=False,
        potion=True,
        dragon=False,
    ),
    mage=Level(
        goblin=False,
        skeleton=False,
        ooze=True,
        chest=False,
        potion=True,
        dragon=False,
    ),
    thief=Level(
        goblin=False,
        skeleton=False,
        ooze=False,
        chest=True,
        potion=True,
        dragon=False,
    ),
    champion=Level(
        goblin=True,
        skeleton=True,
        ooze=True,
        chest=True,
        potion=True,
        dragon=False,
    ),
    scroll=Level(
        goblin=False,
        skeleton=False,
        ooze=False,
        chest=False,
        potion=True,
        dragon=False,
    ),
)

def survivors(level: Level, defender: str, attacker: str, *, prowess = _MANY_DEFAULT):
    assert defender != 'dragon'  # Special case
    assert attacker != 'scroll'  # Special case
    prior = getattr(level, defender)
    assert prior >= 1
    if getattr(getattr(prowess, attacker), defender):
        return level._replace(**{defender: 0})
    else:
        return level._replace(**{defender: prior -1})
