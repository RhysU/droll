# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of the shell (at least driving with basic commands)."""

import random
import typing

from droll.shell import Shell
from droll.heroes import Default, Knight


def test_initial():
    """Before preloop(...) is run, summary(...) is well-defined."""
    s = Shell()
    assert s.summary() == "(None)"


def test_EOF():
    """Confirm providing EOF exits cmdloop(...)."""
    s = Shell()
    assert not s.cmdqueue
    s.cmdqueue.append('EOF')
    s.cmdloop()
    assert s.lastcmd == ''


# Strategy for testing, further below, will turn docstrings into assertions
def parse_summary_command(text) -> typing.Iterable[typing.Tuple[str, str]]:
    """Parse input like the following into (summary, command) tuples:

    (delve=1, hello
    (droll  0) cleric goblin

    (delve=1, world
    (droll  6) descend
    """
    summaries, commands = [], []
    for line in (x.strip() for x in text.splitlines()):
        if line.startswith('(delve='):
            summaries.append(line)
        elif line.startswith('(droll '):
            command = line[line.index(') ') + 2:]
            commands.append(command)
    return zip(summaries, commands)


# Confirm the parsing helper above is doing hat is required.
def test_summary_command():
    """Confirm parse_summary_command(...) helper working as required."""
    sc = parse_summary_command(parse_summary_command.__doc__)
    s, c = next(sc)
    assert s == "(delve=1, hello"
    assert c == "cleric goblin"
    s, c = next(sc)
    assert s == "(delve=1, world"
    assert c == "descend"
    try:
        s, c = next(sc)
        assert False, "StopIteration expected"
    except StopIteration:
        pass


def test_simple():
    """Runs the following scenario:

    (delve=1, party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), ability=True, treasure=())
    (droll  0) descend

    (delve=1, depth=1, dungeon=(goblin=1), party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), ability=True, treasure=())
    (droll  0) cleric goblin

    (delve=1, depth=1, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), ability=True, treasure=())
    (droll  0) descend

    (delve=1, depth=2, dungeon=(goblin=2), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), ability=True, treasure=())
    (droll  0) fighter goblin

    (delve=1, depth=2, dungeon=(), party=(cleric=1, mage=1, thief=2, scroll=1), ability=True, treasure=())
    (droll  0) descend

    (delve=1, depth=3, dungeon=(ooze=1, chest=1, potion=1), party=(cleric=1, mage=1, thief=2, scroll=1), ability=True, treasure=())
    (droll  0) thief ooze

    (delve=1, depth=3, dungeon=(chest=1, potion=1), party=(cleric=1, mage=1, thief=1, scroll=1), ability=True, treasure=())
    (droll  0) thief chest

    (delve=1, depth=3, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), ability=True, treasure=(talisman=1))
    (droll  1) scroll potion
    Require exactly 1 to revive

    (delve=1, depth=3, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), ability=True, treasure=(talisman=1))
    (droll  1) scroll potion champion

    (delve=1, depth=3, dungeon=(), party=(cleric=1, mage=1, champion=1), ability=True, treasure=(talisman=1))
    (droll  1) descend

    (delve=1, depth=4, dungeon=(skeleton=1, ooze=1, potion=2), party=(cleric=1, mage=1, champion=1), ability=True, treasure=(talisman=1))
    (droll  1) cleric skeleton

    (delve=1, depth=4, dungeon=(ooze=1, potion=2), party=(mage=1, champion=1), ability=True, treasure=(talisman=1))
    (droll  1) mage ooze

    (delve=1, depth=4, dungeon=(potion=2), party=(champion=1), ability=True, treasure=(talisman=1))
    (droll  1) champion potion champion fighter

    (delve=1, depth=4, dungeon=(), party=(fighter=1, champion=1), ability=True, treasure=(talisman=1))
    (droll  1) descend

    (delve=1, depth=5, dungeon=(goblin=1, skeleton=2, ooze=2), party=(fighter=1, champion=1), ability=True, treasure=(talisman=1))
    (droll  1) champion ooze

    (delve=1, depth=5, dungeon=(goblin=1, skeleton=2), party=(fighter=1), ability=True, treasure=(talisman=1))
    (droll  1) talisman skeleton

    (delve=1, depth=5, dungeon=(goblin=1), party=(fighter=1), ability=True, treasure=())
    (droll  0) fighter goblin

    (delve=1, depth=5, dungeon=(), party=(), ability=True, treasure=())
    (droll  0) retire

    (delve=2, experience=5, party=(fighter=1, cleric=2, mage=3, scroll=1), ability=True, treasure=())
    (droll  5) EOF
    """
    # Drive the game according to the script in the above docstring.
    s = Shell(randrange=random.Random(4).randrange, player=Default)
    s.preloop()
    parsed = parse_summary_command(test_simple.__doc__)
    for index, (expected_summary, following_command) in enumerate(parsed):
        assert expected_summary == s.summary(), (
            "Summary mismatch at {}".format(index))
        s.onecmd(following_command)


def test_knight():
    """Runs the following scenario involving unique Knight/Dragonslayer details:

    (delve=1, party=(fighter=1, cleric=2, mage=1, thief=2, champion=1), ability=True, treasure=())
    (droll  0) descend

    (delve=1, depth=1, dungeon=(goblin=1), party=(fighter=1, cleric=2, mage=1, thief=2, champion=1), ability=True, treasure=())
    (droll  0) cleric goblin

    (delve=1, depth=1, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=2, champion=1), ability=True, treasure=())
    (droll  0) descend

    (delve=1, depth=2, dungeon=(goblin=2), party=(fighter=1, cleric=1, mage=1, thief=2, champion=1), ability=True, treasure=())
    (droll  0) fighter goblin

    (delve=1, depth=2, dungeon=(), party=(cleric=1, mage=1, thief=2, champion=1), ability=True, treasure=())
    (droll  0) descend

    (delve=1, depth=3, dungeon=(ooze=1, chest=1, potion=1), party=(cleric=1, mage=1, thief=2, champion=1), ability=True, treasure=())
    (droll  0) thief ooze

    (delve=1, depth=3, dungeon=(chest=1, potion=1), party=(cleric=1, mage=1, thief=1, champion=1), ability=True, treasure=())
    (droll  0) thief chest

    (delve=1, depth=3, dungeon=(potion=1), party=(cleric=1, mage=1, champion=1), ability=True, treasure=(talisman=1))
    (droll  1) descend

    (delve=1, depth=4, dungeon=(skeleton=1, ooze=1, potion=2), party=(cleric=1, mage=1, champion=1), ability=True, treasure=(talisman=1))
    (droll  1) ability

    (delve=1, depth=4, dungeon=(potion=2, dragon=2), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1))
    (droll  1) mage potion mage fighter

    (delve=1, depth=4, dungeon=(dragon=2), party=(fighter=1, cleric=1, mage=1, champion=1), treasure=(talisman=1))
    (droll  1) descend

    (delve=1, depth=5, dungeon=(goblin=1, skeleton=2, ooze=2, dragon=2), party=(fighter=1, cleric=1, mage=1, champion=1), treasure=(talisman=1))
    (droll  1) cleric skeleton

    (delve=1, depth=5, dungeon=(goblin=1, ooze=2, dragon=2), party=(fighter=1, mage=1, champion=1), treasure=(talisman=1))
    (droll  1) mage ooze

    (delve=1, depth=5, dungeon=(goblin=1, dragon=2), party=(fighter=1, champion=1), treasure=(talisman=1))
    (droll  1) fighter goblin

    (delve=1, depth=5, dungeon=(dragon=2), party=(champion=1), treasure=(talisman=1))
    (droll  1) retire

    (delve=2, experience=5, party=(fighter=1, cleric=2, mage=3, champion=1), ability=True, treasure=(talisman=1))
    (droll  6) descend

    (delve=2, depth=1, experience=5, dungeon=(ooze=1), party=(fighter=1, cleric=2, mage=3, champion=1), ability=True, treasure=(talisman=1))
    (droll  6) mage ooze

    (delve=2, depth=1, experience=5, dungeon=(), party=(fighter=1, cleric=2, mage=2, champion=1), ability=True, treasure=(talisman=1))
    (droll  6) descend

    (delve=2, depth=2, experience=5, dungeon=(dragon=2), party=(fighter=1, cleric=2, mage=2, champion=1), ability=True, treasure=(talisman=1))
    (droll  6) descend

    (delve=2, depth=3, experience=5, dungeon=(goblin=1, ooze=1, potion=1, dragon=2), party=(fighter=1, cleric=2, mage=2, champion=1), ability=True, treasure=(talisman=1))
    (droll  6) ability

    (delve=2, depth=3, experience=5, dungeon=(potion=1, dragon=4), party=(fighter=1, cleric=2, mage=2, champion=1), treasure=(talisman=1))
    (droll  6) mage potion thief

    (delve=2, depth=3, experience=5, dungeon=(dragon=4), party=(fighter=1, cleric=2, mage=1, thief=1, champion=1), treasure=(talisman=1))
    (droll  6) cleric dragon thief

    (delve=2, depth=3, experience=6, dungeon=(), party=(fighter=1, cleric=1, mage=1, champion=1), treasure=(talisman=1, portal=1))
    (droll  9) descend

    (delve=2, depth=4, experience=6, dungeon=(skeleton=1, chest=1, potion=1, dragon=1), party=(fighter=1, cleric=1, mage=1, champion=1), treasure=(talisman=1, portal=1))
    (droll  9) fighter skeleton

    (delve=2, depth=4, experience=6, dungeon=(chest=1, potion=1, dragon=1), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1, portal=1))
    (droll  9) mage chest

    (delve=2, depth=4, experience=6, dungeon=(potion=1, dragon=1), party=(cleric=1, champion=1), treasure=(talisman=1, scroll=1, portal=1))
    (droll 10) descend

    (delve=2, depth=5, experience=6, dungeon=(goblin=1, skeleton=1, ooze=1, chest=1, potion=1, dragon=1), party=(cleric=1, champion=1), treasure=(talisman=1, scroll=1, portal=1))
    (droll 10) cleric goblin

    (delve=2, depth=5, experience=6, dungeon=(skeleton=1, ooze=1, chest=1, potion=1, dragon=1), party=(champion=1), treasure=(talisman=1, scroll=1, portal=1))
    (droll 10) champion skeleton

    (delve=2, depth=5, experience=6, dungeon=(ooze=1, chest=1, potion=1, dragon=1), party=(), treasure=(talisman=1, scroll=1, portal=1))
    (droll 10) talisman ooze

    (delve=2, depth=5, experience=6, dungeon=(chest=1, potion=1, dragon=1), party=(), treasure=(scroll=1, portal=1))
    (droll  9) retire

    (delve=3, experience=11, party=(fighter=1, mage=3, champion=3), ability=True, treasure=(scroll=1, portal=1))
    (droll 14) descend

    (delve=3, depth=1, experience=11, dungeon=(skeleton=1), party=(fighter=1, mage=3, champion=3), ability=True, treasure=(scroll=1, portal=1))
    (droll 14) mage skeleton

    (delve=3, depth=1, experience=11, dungeon=(), party=(fighter=1, mage=2, champion=3), ability=True, treasure=(scroll=1, portal=1))
    (droll 14) descend

    (delve=3, depth=2, experience=11, dungeon=(chest=2), party=(fighter=1, mage=2, champion=3), ability=True, treasure=(scroll=1, portal=1))
    (droll 14) champion chest

    (delve=3, depth=2, experience=11, dungeon=(), party=(fighter=1, mage=2, champion=2), ability=True, treasure=(scroll=1, bait=1, portal=1, scale=1))
    (droll 16) descend

    (delve=3, depth=3, experience=11, dungeon=(skeleton=2, chest=1), party=(fighter=1, mage=2, champion=2), ability=True, treasure=(scroll=1, bait=1, portal=1, scale=1))
    (droll 16) champion skeleton

    (delve=3, depth=3, experience=11, dungeon=(chest=1), party=(fighter=1, mage=2, champion=1), ability=True, treasure=(scroll=1, bait=1, portal=1, scale=1))
    (droll 16) mage chest

    (delve=3, depth=3, experience=11, dungeon=(), party=(fighter=1, mage=1, champion=1), ability=True, treasure=(scroll=1, bait=2, portal=1, scale=1))
    (droll 17) descend

    (delve=3, depth=4, experience=11, dungeon=(goblin=3, ooze=1), party=(fighter=1, mage=1, champion=1), ability=True, treasure=(scroll=1, bait=2, portal=1, scale=1))
    (droll 17) ability

    (delve=3, depth=4, experience=11, dungeon=(dragon=4), party=(fighter=1, mage=1, champion=1), treasure=(scroll=1, bait=2, portal=1, scale=1))
    (droll 17) mage dragon fighter

    (delve=3, depth=4, experience=12, dungeon=(), party=(champion=1), treasure=(scroll=1, elixir=1, bait=2, portal=1, scale=1))
    (droll 19) retire

    (delve=3, experience=16, party=(champion=1), treasure=(scroll=1, elixir=1, bait=2, portal=1, scale=1))
    (droll 23) EOF
    """
    # Drive the game according to the script in the above docstring.
    s = Shell(randrange=random.Random(4).randrange, player=Knight)
    s.preloop()
    parsed = parse_summary_command(test_knight.__doc__)
    for index, (expected_summary, following_command) in enumerate(parsed):
        assert expected_summary == s.summary(), (
            "Summary mismatch at {}".format(index))
        s.onecmd(following_command)
