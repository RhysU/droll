# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of the shell (at least driving with basic commands)."""

import random

from droll import brief
from droll.shell import Shell


def b(s: Shell) -> str:
    """A brief description of the underlying world, abusing internals."""
    return brief(s._world)


def test_simple():
    s = Shell(randrange=random.Random(4).randrange)
    assert s.summary() == "(None)"
    s.preloop()
    assert s.summary() == "(delve=1, depth=1, ability=True, dungeon=(goblin=1), party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), treasure=())"
    # (delve=1, depth=1, ability=True, dungeon=(goblin=1), party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), treasure=())
    # (droll  0) cleric goblin
    #
    # (delve=1, depth=1, ability=True, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), treasure=())
    # (droll  0) descend
    #
    # (delve=1, depth=2, ability=True, dungeon=(goblin=2), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), treasure=())
    # (droll  0) fighter goblin
    #
    # (delve=1, depth=2, ability=True, dungeon=(), party=(cleric=1, mage=1, thief=2, scroll=1), treasure=())
    # (droll  0) descend
    #
    # (delve=1, depth=3, ability=True, dungeon=(ooze=1, chest=1, potion=1), party=(cleric=1, mage=1, thief=2, scroll=1), treasure=())
    # (droll  0) thief ooze
    #
    # (delve=1, depth=3, ability=True, dungeon=(chest=1, potion=1), party=(cleric=1, mage=1, thief=1, scroll=1), treasure=())
    # (droll  0) thief chest
    #
    # (delve=1, depth=3, ability=True, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), treasure=(talisman=1))
    # (droll  1) scroll potion
    # Require exactly 1 to revive
    #
    # (delve=1, depth=3, ability=True, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), treasure=(talisman=1))
    # (droll  1) scroll potion champion
    #
    # (delve=1, depth=3, ability=True, dungeon=(), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1))
    # (droll  1) descend
    #
    # (delve=1, depth=4, ability=True, dungeon=(skeleton=1, ooze=1, potion=2), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1))
    # (droll  1) cleric skeleton
    #
    # (delve=1, depth=4, ability=True, dungeon=(ooze=1, potion=2), party=(mage=1, champion=1), treasure=(talisman=1))
    # (droll  1) mage ooze
    #
    # (delve=1, depth=4, ability=True, dungeon=(potion=2), party=(champion=1), treasure=(talisman=1))
    # (droll  1) champion potion champion fighter
    #
    # (delve=1, depth=4, ability=True, dungeon=(), party=(fighter=1, champion=1), treasure=(talisman=1))
    # (droll  1) descend
    #
    # (delve=1, depth=5, ability=True, dungeon=(goblin=1, skeleton=2, ooze=2), party=(fighter=1, champion=1), treasure=(talisman=1))
    # (droll  1) champion ooze
    #
    # (delve=1, depth=5, ability=True, dungeon=(goblin=1, skeleton=2), party=(fighter=1), treasure=(talisman=1))
    # (droll  1) cleric skeleton
    #
    # (delve=1, depth=5, ability=True, dungeon=(goblin=1), party=(fighter=1), treasure=())
    # (droll  0) fighter goblin
    #
    # (delve=1, depth=5, ability=True, dungeon=(), party=(), treasure=())
    # (droll  0) retire
    #
    # (delve=2, depth=1, experience=5, ability=True, dungeon=(ooze=1), party=(fighter=1, cleric=2, mage=3, scroll=1), treasure=())
    # (droll  5) ^D
