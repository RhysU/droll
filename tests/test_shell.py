# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of the shell (at least driving with basic commands)."""

import random
import typing
import unittest
from dataclasses import replace

from droll import struct
from droll.display import DisplayMode
from droll.error import DrollError
from droll.game import Game
from droll.heroes import HalfGoblin
from droll.player import Default
from droll.shell import Shell


class TestShell(unittest.TestCase):

    def test_EOF(self):
        """Confirm providing EOF exits cmdloop(...)."""
        s = Shell(Game(), display_mode=DisplayMode.MECHANICAL)
        self.assertFalse(s.cmdqueue)
        s.cmdqueue.append("EOF")
        s.cmdloop()
        self.assertEqual(s.prompt, "(Default  0) ")
        self.assertEqual(s.lastcmd, "")

    def test_reroll(self):
        """Confirm reroll command forwards to game."""
        s = Shell(
            Game(random=random.Random(4), player=Default),
            display_mode=DisplayMode.MECHANICAL,
        )
        s.preloop()
        s.onecmd("descend")
        # Depth 1 with seed 4 has a single goblin; reroll it
        s.onecmd("reroll goblin")

    def test_retreat(self):
        """Confirm retreat command forwards to game."""
        s = Shell(
            Game(random=random.Random(4), player=Default),
            display_mode=DisplayMode.MECHANICAL,
        )
        s.preloop()
        s.onecmd("descend")
        # Need a monster present so retreat is valid
        s._game._world = replace(
            s._game._world, dungeon=struct.Dungeon(goblin=1)
        )
        s.onecmd("retreat")

    def test_help(self):
        """Confirm help invocations do not throw exceptions."""
        s = Shell(Game(), display_mode=DisplayMode.MECHANICAL)
        s.help_ability()
        s.help_bait()
        s.help_champion()
        s.help_cleric()
        s.help_elixir()
        s.help_fighter()
        s.help_mage()
        s.help_ring()
        s.help_sceptre()
        s.help_scroll()
        s.help_sword()
        s.help_talisman()
        s.help_thief()
        s.help_tools()


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
        if line.startswith("(delve="):
            summaries.append(line)
        elif line.startswith("("):  # For example, "(Bard  6) descend"
            command = line[line.index(") ") + 2 :]
            commands.append(command)
    return zip(summaries, commands)


class TestUndo(unittest.TestCase):

    def test_undo(self):
        """Based upon test_simple(...), verify undo behaving as expected."""
        s = Shell(
            Game(random=random.Random(4), player=Default),
            display_mode=DisplayMode.MECHANICAL,
        )

        # Supplies a private flag so that DrollErrors percolate to this level
        def onecmd(line):
            """Execute shell command with errors raised instead of printed."""
            s.onecmd(line, _raises=True)

        s.preloop()

        # (delve=1, party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), ...)
        with self.assertRaises(DrollError):
            onecmd("undo")
        with self.assertRaises(DrollError):
            onecmd("undo")
        onecmd("descend")

        # (delve=1, depth=1, dungeon=(goblin=1),
        #  party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), ...)
        with self.assertRaises(DrollError):
            onecmd("undo")
        onecmd("fighter goblin")
        onecmd("undo")
        with self.assertRaises(DrollError):
            onecmd("undo")
        onecmd("cleric goblin")
        onecmd("undo")
        with self.assertRaises(DrollError):
            onecmd("undo")
        onecmd("mage goblin")
        onecmd("descend")

        # (delve=1, depth=2, dungeon=(goblin=2), ...)
        self.assertEqual(s._game._world.dungeon.goblin, 2)
        with self.assertRaises(DrollError):
            onecmd("undo")
        onecmd("thief goblin")
        onecmd("fighter goblin")
        onecmd("undo")
        onecmd("undo")
        onecmd("fighter goblin")
        onecmd("descend")

        # (delve=1, depth=3, dungeon=(ooze=1, chest=1, potion=1), ...)
        self.assertEqual(s._game._world.dungeon.ooze, 1)
        self.assertEqual(s._game._world.dungeon.chest, 1)
        self.assertEqual(s._game._world.dungeon.potion, 1)
        with self.assertRaises(DrollError):
            onecmd("undo")
        onecmd("cleric ooze")
        onecmd("undo")
        onecmd("cleric ooze")
        onecmd("thief chest")
        with self.assertRaises(DrollError):
            onecmd("undo")
        onecmd("scroll potion champion")
        onecmd("undo")
        onecmd("scroll potion thief")
        onecmd("descend")

    def test_undo_in_available_commands(self):
        """Verify undo appears in available commands only when undo stack is not empty."""
        s = Shell(
            Game(random=random.Random(42), player=Default),
            display_mode=DisplayMode.MECHANICAL,
        )
        s.preloop()

        # Initially, undo stack is empty, so "undo" should not be available
        available = s._available_commands()
        self.assertNotIn("undo", available)

        # Execute a command that can be undone (ability doesn't change random state)
        s.onecmd("ability")

        # Now undo stack has one item, so "undo" should be available
        available = s._available_commands()
        self.assertIn("undo", available)

        # Execute undo to restore previous state
        s.onecmd("undo")

        # Undo stack is empty again, so "undo" should not be available
        available = s._available_commands()
        self.assertNotIn("undo", available)


class TestHalfGoblin(unittest.TestCase):

    def test_halfgoblin(self):
        """
        Runs following scenario involving unique HalfGoblin/Chieftain details:

        (delve=1, party=(fighter=1, cleric=1, mage=2, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (HalfGoblin  0) descend

        (delve=1, depth=1, dungeon=(goblin=1), party=(fighter=1, cleric=1, mage=2, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (HalfGoblin  0) ability

        (delve=1, depth=1, dungeon=(), party=(fighter=1, cleric=1, mage=2, thief=2, scroll=2), regroup=(discard=(thief=1)), treasure=())
        (HalfGoblin  0) descend

        (delve=1, depth=2, dungeon=(ooze=1, potion=1), party=(fighter=1, cleric=1, mage=2, thief=1, scroll=2), regroup=(discard=()), treasure=())
        (HalfGoblin  0) scroll potion champion

        (delve=1, depth=2, dungeon=(ooze=1), party=(fighter=1, cleric=1, mage=2, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) mage ooze

        (delve=1, depth=2, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) descend

        (delve=1, depth=3, dungeon=(ooze=3), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) mage ooze

        (delve=1, depth=3, dungeon=(), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) descend

        (delve=1, depth=4, dungeon=(skeleton=3, chest=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) cleric skeleton

        (delve=1, depth=4, dungeon=(chest=1), party=(fighter=1, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) descend

        (delve=1, depth=5, dungeon=(goblin=1, chest=1, potion=1, dragon=2), party=(fighter=1, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) scroll potion cleric

        (delve=1, depth=5, dungeon=(goblin=1, chest=1, dragon=2), party=(fighter=1, cleric=1, thief=1, champion=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) cleric goblin

        (delve=1, depth=5, dungeon=(chest=1, dragon=2), party=(fighter=1, thief=1, champion=1), regroup=(discard=()), treasure=())
        (HalfGoblin  0) fighter chest

        (delve=1, depth=5, dungeon=(dragon=2), party=(thief=1, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (HalfGoblin  1) retire

        (delve=2, experience=5, party=(fighter=1, thief=3, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Chieftain  6) descend

        (delve=2, depth=1, experience=5, dungeon=(ooze=1), party=(fighter=1, thief=3, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Chieftain  6) thief ooze

        (delve=2, depth=1, experience=5, dungeon=(), party=(fighter=1, thief=2, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Chieftain  6) descend

        (delve=2, depth=2, experience=5, dungeon=(goblin=1, dragon=1), party=(fighter=1, thief=2, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Chieftain  6) scroll goblin

        (delve=2, depth=2, experience=5, dungeon=(chest=1, dragon=1), party=(fighter=1, thief=2, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Chieftain  6) thief chest

        (delve=2, depth=2, experience=5, dungeon=(dragon=1), party=(fighter=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain  7) descend

        (delve=2, depth=3, experience=5, dungeon=(skeleton=1, ooze=1, potion=1, dragon=1), party=(fighter=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain  7) champion skeleton

        (delve=2, depth=3, experience=5, dungeon=(ooze=1, potion=1, dragon=1), party=(fighter=1, thief=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain  7) thief ooze

        (delve=2, depth=3, experience=5, dungeon=(potion=1, dragon=1), party=(fighter=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain  7) scroll potion champion

        (delve=2, depth=3, experience=5, dungeon=(dragon=1), party=(fighter=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain  7) retire

        (delve=3, experience=8, party=(fighter=1, cleric=2, champion=2, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain 10) descend

        (delve=3, depth=1, experience=8, dungeon=(chest=1), party=(fighter=1, cleric=2, champion=2, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain 10) descend

        (delve=3, depth=2, experience=8, dungeon=(ooze=1, dragon=1), party=(fighter=1, cleric=2, champion=2, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain 10) cleric ooze

        (delve=3, depth=2, experience=8, dungeon=(dragon=1), party=(fighter=1, cleric=1, champion=2, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain 10) descend

        (delve=3, depth=3, experience=8, dungeon=(goblin=1, potion=1, dragon=2), party=(fighter=1, cleric=1, champion=2, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain 10) ability

        (delve=3, depth=3, experience=8, dungeon=(potion=1, dragon=2), party=(fighter=1, cleric=1, thief=1, champion=2, scroll=2), regroup=(discard=(thief=1)), treasure=(talisman=1, elixir=1))
        (Chieftain 10) thief potion
        Require exactly 1 to revive.

        (delve=3, depth=3, experience=8, dungeon=(potion=1, dragon=2), party=(fighter=1, cleric=1, thief=1, champion=2, scroll=2), regroup=(discard=(thief=1)), treasure=(talisman=1, elixir=1))
        (Chieftain 10) thief potion cleric

        (delve=3, depth=3, experience=8, dungeon=(dragon=2), party=(fighter=1, cleric=2, champion=2, scroll=2), regroup=(discard=()), treasure=(talisman=1, elixir=1))
        (Chieftain 10) EOF
        """
        # Drive the game according to the script in the above docstring.
        s = Shell(
            Game(random=random.Random(27), player=HalfGoblin),
            display_mode=DisplayMode.MECHANICAL,
        )
        s.preloop()
        parsed = parse_summary_command(self.test_halfgoblin.__doc__)
        for index, (expected_summary, following_command) in enumerate(parsed):
            self.assertEqual(
                expected_summary,
                s._game.summary(),
                "Summary mismatch at {}".format(index),
            )
            s.onecmd(following_command)

        # Confirm some non-trivial processing occurred
        self.assertEqual(index, 31)
