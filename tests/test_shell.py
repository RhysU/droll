# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of the shell (at least driving with basic commands)."""

import random
import typing
import unittest

from droll.display import DisplayMode
from droll.error import DrollError
from droll.game import Game
from droll.heroes import Crusader, Enchantress, Knight, Minstrel, Spellsword
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


class TestSummaryCommand(unittest.TestCase):

    def test_summary_command(self):
        """Confirm parse_summary_command(...) helper working as required."""
        sc = parse_summary_command(parse_summary_command.__doc__)
        s, c = next(sc)
        self.assertEqual(s, "(delve=1, hello")
        self.assertEqual(c, "cleric goblin")
        s, c = next(sc)
        self.assertEqual(s, "(delve=1, world")
        self.assertEqual(c, "descend")
        try:
            s, c = next(sc)
            self.fail("StopIteration expected")
        except StopIteration:
            pass


class TestSimple(unittest.TestCase):

    def test_simple(self):
        """Runs the following scenario:

        (delve=1, party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) descend

        (delve=1, depth=1, dungeon=(goblin=1), party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) cleric goblin

        (delve=1, depth=1, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) descend

        (delve=1, depth=2, dungeon=(goblin=2), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) fighter goblin

        (delve=1, depth=2, dungeon=(), party=(cleric=1, mage=1, thief=2, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) descend

        (delve=1, depth=3, dungeon=(ooze=1, chest=1, potion=1), party=(cleric=1, mage=1, thief=2, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) thief ooze

        (delve=1, depth=3, dungeon=(chest=1, potion=1), party=(cleric=1, mage=1, thief=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) thief chest

        (delve=1, depth=3, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) scroll potion
        Require exactly 1 to revive

        (delve=1, depth=3, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) scroll potion champion

        (delve=1, depth=3, dungeon=(), party=(cleric=1, mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) descend

        (delve=1, depth=4, dungeon=(skeleton=1, ooze=1, potion=2), party=(cleric=1, mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) cleric skeleton

        (delve=1, depth=4, dungeon=(ooze=1, potion=2), party=(mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) mage ooze

        (delve=1, depth=4, dungeon=(potion=2), party=(champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) champion potion champion fighter

        (delve=1, depth=4, dungeon=(), party=(fighter=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) descend

        (delve=1, depth=5, dungeon=(goblin=1, skeleton=2, ooze=2), party=(fighter=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) champion ooze

        (delve=1, depth=5, dungeon=(goblin=1, skeleton=2), party=(fighter=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Default  1) talisman skeleton

        (delve=1, depth=5, dungeon=(goblin=1), party=(fighter=1), ability=True, regroup=(discard=()), treasure=())
        (Default  0) fighter goblin

        (delve=1, depth=5, dungeon=(), party=(), ability=True, regroup=(discard=()), treasure=())
        (Default  0) retire

        (delve=2, experience=5, party=(fighter=1, cleric=2, mage=3, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Default  5) EOF
        """
        # Drive the game according to the script in the above docstring.
        s = Shell(Game(random=random.Random(4), player=Default), display_mode=DisplayMode.MECHANICAL)
        s.preloop()
        parsed = parse_summary_command(self.test_simple.__doc__)
        for index, (expected_summary, following_command) in enumerate(parsed):
            self.assertEqual(
                expected_summary, s._game.summary(),
                "Summary mismatch at {}".format(index)
            )
            s.onecmd(following_command)

        # Confirm some non-trivial processing occurred
        self.assertEqual(index, 18)


class TestUndo(unittest.TestCase):

    def test_undo(self):
        """Based upon test_simple(...), verify undo behaving as expected."""
        s = Shell(Game(random=random.Random(4), player=Default), display_mode=DisplayMode.MECHANICAL)

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
        s = Shell(Game(random=random.Random(42), player=Default), display_mode=DisplayMode.MECHANICAL)
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


class TestKnight(unittest.TestCase):

    def test_knight(self):
        """Runs the following scenario involving unique Knight/Dragonslayer details:

        (delve=1, party=(fighter=1, cleric=2, mage=1, thief=2, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Knight  0) descend

        (delve=1, depth=1, dungeon=(goblin=1), party=(fighter=1, cleric=2, mage=1, thief=2, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Knight  0) cleric goblin

        (delve=1, depth=1, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=2, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Knight  0) descend

        (delve=1, depth=2, dungeon=(goblin=2), party=(fighter=1, cleric=1, mage=1, thief=2, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Knight  0) fighter goblin

        (delve=1, depth=2, dungeon=(), party=(cleric=1, mage=1, thief=2, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Knight  0) descend

        (delve=1, depth=3, dungeon=(ooze=1, chest=1, potion=1), party=(cleric=1, mage=1, thief=2, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Knight  0) thief ooze

        (delve=1, depth=3, dungeon=(chest=1, potion=1), party=(cleric=1, mage=1, thief=1, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Knight  0) thief chest

        (delve=1, depth=3, dungeon=(potion=1), party=(cleric=1, mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) descend

        (delve=1, depth=4, dungeon=(skeleton=1, ooze=1, potion=2), party=(cleric=1, mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) ability

        (delve=1, depth=4, dungeon=(potion=2, dragon=2), party=(cleric=1, mage=1, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) mage potion mage fighter

        (delve=1, depth=4, dungeon=(dragon=2), party=(fighter=1, cleric=1, mage=1, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) descend

        (delve=1, depth=5, dungeon=(goblin=1, skeleton=2, ooze=2, dragon=2), party=(fighter=1, cleric=1, mage=1, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) cleric skeleton

        (delve=1, depth=5, dungeon=(goblin=1, ooze=2, dragon=2), party=(fighter=1, mage=1, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) mage ooze

        (delve=1, depth=5, dungeon=(goblin=1, dragon=2), party=(fighter=1, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) fighter goblin

        (delve=1, depth=5, dungeon=(dragon=2), party=(champion=1), regroup=(discard=()), treasure=(talisman=1))
        (Knight  1) retire

        (delve=2, experience=5, party=(fighter=1, cleric=2, mage=3, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (DragonSlayer  6) descend

        (delve=2, depth=1, experience=5, dungeon=(ooze=1), party=(fighter=1, cleric=2, mage=3, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (DragonSlayer  6) mage ooze

        (delve=2, depth=1, experience=5, dungeon=(), party=(fighter=1, cleric=2, mage=2, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (DragonSlayer  6) descend

        (delve=2, depth=2, experience=5, dungeon=(dragon=2), party=(fighter=1, cleric=2, mage=2, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (DragonSlayer  6) descend

        (delve=2, depth=3, experience=5, dungeon=(goblin=1, ooze=1, potion=1, dragon=2), party=(fighter=1, cleric=2, mage=2, champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (DragonSlayer  6) ability

        (delve=2, depth=3, experience=5, dungeon=(potion=1, dragon=4), party=(fighter=1, cleric=2, mage=2, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (DragonSlayer  6) mage potion thief

        (delve=2, depth=3, experience=5, dungeon=(dragon=4), party=(fighter=1, cleric=2, mage=1, thief=1, champion=1), regroup=(discard=()), treasure=(talisman=1))
        (DragonSlayer  6) cleric dragon thief

        (delve=2, depth=3, experience=6, dungeon=(), party=(fighter=1, cleric=1, mage=1, champion=1), regroup=(discard=()), treasure=(talisman=1, portal=1))
        (DragonSlayer  9) descend

        (delve=2, depth=4, experience=6, dungeon=(skeleton=1, chest=1, potion=1, dragon=1), party=(fighter=1, cleric=1, mage=1, champion=1), regroup=(discard=()), treasure=(talisman=1, portal=1))
        (DragonSlayer  9) fighter skeleton

        (delve=2, depth=4, experience=6, dungeon=(chest=1, potion=1, dragon=1), party=(cleric=1, mage=1, champion=1), regroup=(discard=()), treasure=(talisman=1, portal=1))
        (DragonSlayer  9) mage chest

        (delve=2, depth=4, experience=6, dungeon=(potion=1, dragon=1), party=(cleric=1, champion=1), regroup=(discard=()), treasure=(talisman=1, scroll=1, portal=1))
        (DragonSlayer 10) descend

        (delve=2, depth=5, experience=6, dungeon=(goblin=1, skeleton=1, ooze=1, chest=1, potion=1, dragon=1), party=(cleric=1, champion=1), regroup=(discard=()), treasure=(talisman=1, scroll=1, portal=1))
        (DragonSlayer 10) cleric goblin

        (delve=2, depth=5, experience=6, dungeon=(skeleton=1, ooze=1, chest=1, potion=1, dragon=1), party=(champion=1), regroup=(discard=()), treasure=(talisman=1, scroll=1, portal=1))
        (DragonSlayer 10) champion skeleton

        (delve=2, depth=5, experience=6, dungeon=(ooze=1, chest=1, potion=1, dragon=1), party=(), regroup=(discard=()), treasure=(talisman=1, scroll=1, portal=1))
        (DragonSlayer 10) talisman ooze

        (delve=2, depth=5, experience=6, dungeon=(chest=1, potion=1, dragon=1), party=(), regroup=(discard=()), treasure=(scroll=1, portal=1))
        (DragonSlayer  9) retire

        (delve=3, experience=11, party=(fighter=1, mage=3, champion=3), ability=True, regroup=(discard=()), treasure=(scroll=1, portal=1))
        (DragonSlayer 14) descend

        (delve=3, depth=1, experience=11, dungeon=(skeleton=1), party=(fighter=1, mage=3, champion=3), ability=True, regroup=(discard=()), treasure=(scroll=1, portal=1))
        (DragonSlayer 14) mage skeleton

        (delve=3, depth=1, experience=11, dungeon=(), party=(fighter=1, mage=2, champion=3), ability=True, regroup=(discard=()), treasure=(scroll=1, portal=1))
        (DragonSlayer 14) descend

        (delve=3, depth=2, experience=11, dungeon=(chest=2), party=(fighter=1, mage=2, champion=3), ability=True, regroup=(discard=()), treasure=(scroll=1, portal=1))
        (DragonSlayer 14) champion chest

        (delve=3, depth=2, experience=11, dungeon=(), party=(fighter=1, mage=2, champion=2), ability=True, regroup=(discard=()), treasure=(scroll=1, bait=1, portal=1, scale=1))
        (DragonSlayer 16) descend

        (delve=3, depth=3, experience=11, dungeon=(skeleton=2, chest=1), party=(fighter=1, mage=2, champion=2), ability=True, regroup=(discard=()), treasure=(scroll=1, bait=1, portal=1, scale=1))
        (DragonSlayer 16) champion skeleton

        (delve=3, depth=3, experience=11, dungeon=(chest=1), party=(fighter=1, mage=2, champion=1), ability=True, regroup=(discard=()), treasure=(scroll=1, bait=1, portal=1, scale=1))
        (DragonSlayer 16) mage chest

        (delve=3, depth=3, experience=11, dungeon=(), party=(fighter=1, mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(scroll=1, bait=2, portal=1, scale=1))
        (DragonSlayer 17) descend

        (delve=3, depth=4, experience=11, dungeon=(goblin=3, ooze=1), party=(fighter=1, mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(scroll=1, bait=2, portal=1, scale=1))
        (DragonSlayer 17) ability

        (delve=3, depth=4, experience=11, dungeon=(dragon=4), party=(fighter=1, mage=1, champion=1), regroup=(discard=()), treasure=(scroll=1, bait=2, portal=1, scale=1))
        (DragonSlayer 17) mage dragon fighter

        (delve=3, depth=4, experience=12, dungeon=(), party=(champion=1), regroup=(discard=()), treasure=(scroll=1, elixir=1, bait=2, portal=1, scale=1))
        (DragonSlayer 19) retire

        (delve=3, experience=16, party=(champion=1), regroup=(discard=()), treasure=(scroll=1, elixir=1, bait=2, portal=1, scale=1))
        (DragonSlayer 23) EOF
        """
        # Drive the game according to the script in the above docstring.
        s = Shell(Game(random=random.Random(4), player=Knight), display_mode=DisplayMode.MECHANICAL)
        s.preloop()
        parsed = parse_summary_command(self.test_knight.__doc__)
        for index, (expected_summary, following_command) in enumerate(parsed):
            self.assertEqual(
                expected_summary, s._game.summary(),
                "Summary mismatch at {}".format(index)
            )
            s.onecmd(following_command)

        # Confirm some non-trivial processing occurred
        self.assertEqual(index, 41)


class TestSpellsword(unittest.TestCase):

    def test_spellsword(self):
        """Runs the following scenario involving unique Spellsword/Battlemage details:

        (delve=1, party=(cleric=1, mage=3, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Spellsword  0) ability fighter

        (delve=1, party=(fighter=1, cleric=1, mage=3, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (Spellsword  0) descend

        (delve=1, depth=1, dungeon=(dragon=1), party=(fighter=1, cleric=1, mage=3, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (Spellsword  0) descend

        (delve=1, depth=2, dungeon=(potion=1, dragon=2), party=(fighter=1, cleric=1, mage=3, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (Spellsword  0) scroll potion champion

        (delve=1, depth=2, dungeon=(dragon=2), party=(fighter=1, cleric=1, mage=3, thief=1, champion=2), regroup=(discard=()), treasure=())
        (Spellsword  0) descend

        (delve=1, depth=3, dungeon=(goblin=2, ooze=1, dragon=2), party=(fighter=1, cleric=1, mage=3, thief=1, champion=2), regroup=(discard=()), treasure=())
        (Spellsword  0) mage goblin

        (delve=1, depth=3, dungeon=(ooze=1, dragon=2), party=(fighter=1, cleric=1, mage=2, thief=1, champion=2), regroup=(discard=()), treasure=())
        (Spellsword  0) fighter ooze

        (delve=1, depth=3, dungeon=(dragon=2), party=(cleric=1, mage=2, thief=1, champion=2), regroup=(discard=()), treasure=())
        (Spellsword  0) descend

        (delve=1, depth=4, dungeon=(skeleton=1, chest=2, dragon=3), party=(cleric=1, mage=2, thief=1, champion=2), regroup=(discard=()), treasure=())
        (Spellsword  0) cleric skeleton

        (delve=1, depth=4, dungeon=(chest=2, dragon=3), party=(mage=2, thief=1, champion=2), regroup=(discard=()), treasure=())
        (Spellsword  0) thief chest

        (delve=1, depth=4, dungeon=(dragon=3), party=(mage=2, champion=2), regroup=(discard=()), treasure=(elixir=1, scale=1))
        (Spellsword  2) champion dragon mage mage

        (delve=1, depth=4, experience=1, dungeon=(), party=(champion=1), regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Spellsword  4) retire

        (delve=2, experience=5, party=(fighter=1, cleric=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) descend

        (delve=2, depth=1, experience=5, dungeon=(skeleton=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) cleric skeleton

        (delve=2, depth=1, experience=5, dungeon=(), party=(fighter=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) descend

        (delve=2, depth=2, experience=5, dungeon=(skeleton=2), party=(fighter=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) champion skeleton

        (delve=2, depth=2, experience=5, dungeon=(), party=(fighter=1, thief=1, scroll=3), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) descend

        (delve=2, depth=3, experience=5, dungeon=(potion=2, dragon=1), party=(fighter=1, thief=1, scroll=3), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) scroll potion fighter mage

        (delve=2, depth=3, experience=5, dungeon=(dragon=1), party=(fighter=2, mage=1, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) descend

        (delve=2, depth=4, experience=5, dungeon=(skeleton=1, ooze=1, potion=1, dragon=2), party=(fighter=2, mage=1, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) ability

        (delve=2, depth=4, experience=5, dungeon=(), party=(fighter=2, mage=1, thief=1, scroll=2), regroup=(discard=()), treasure=(elixir=1, bait=1, scale=1))
        (Battlemage  8) EOF
        """
        # Drive the game according to the script in the above docstring.
        s = Shell(Game(random=random.Random(17), player=Spellsword), display_mode=DisplayMode.MECHANICAL)
        s.preloop()
        parsed = parse_summary_command(self.test_spellsword.__doc__)
        for index, (expected_summary, following_command) in enumerate(parsed):
            self.assertEqual(
                expected_summary, s._game.summary(),
                "Summary mismatch at {}".format(index)
            )
            s.onecmd(following_command)

        # Confirm some non-trivial processing occurred
        self.assertEqual(index, 20)


class TestMinstrel(unittest.TestCase):

    def test_minstrel(self):
        """Runs the following scenario involving unique Minstrel/Bard details:

        (delve=1, party=(fighter=1, cleric=1, mage=2, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) descend

        (delve=1, depth=1, dungeon=(goblin=1), party=(fighter=1, cleric=1, mage=2, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) mage goblin

        (delve=1, depth=1, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) descend

        (delve=1, depth=2, dungeon=(ooze=1, potion=1), party=(fighter=1, cleric=1, mage=1, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) thief ooze

        (delve=1, depth=2, dungeon=(potion=1), party=(fighter=1, cleric=1, mage=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) scroll potion thief

        (delve=1, depth=2, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) descend

        (delve=1, depth=3, dungeon=(ooze=3), party=(fighter=1, cleric=1, mage=1, thief=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) thief ooze

        (delve=1, depth=3, dungeon=(), party=(fighter=1, cleric=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) descend

        (delve=1, depth=4, dungeon=(skeleton=3, chest=1), party=(fighter=1, cleric=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) cleric skeleton

        (delve=1, depth=4, dungeon=(chest=1), party=(fighter=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) descend

        (delve=1, depth=5, dungeon=(goblin=1, chest=1, potion=1, dragon=2), party=(fighter=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) fighter goblin

        (delve=1, depth=5, dungeon=(chest=1, potion=1, dragon=2), party=(mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Minstrel  0) mage chest

        (delve=1, depth=5, dungeon=(potion=1, dragon=2), party=(scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Minstrel  1) scroll potion champion

        (delve=1, depth=5, dungeon=(dragon=2), party=(champion=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Minstrel  1) ability

        (delve=1, depth=5, dungeon=(), party=(champion=1), regroup=(discard=()), treasure=(talisman=1))
        (Minstrel  1) retire

        (delve=2, experience=5, party=(fighter=1, thief=3, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) descend

        (delve=2, depth=1, experience=5, dungeon=(ooze=1), party=(fighter=1, thief=3, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) thief ooze

        (delve=2, depth=1, experience=5, dungeon=(), party=(fighter=1, thief=2, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) descend

        (delve=2, depth=2, experience=5, dungeon=(goblin=1, dragon=1), party=(fighter=1, thief=2, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) thief goblin

        (delve=2, depth=2, experience=5, dungeon=(dragon=1), party=(fighter=1, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) descend

        (delve=2, depth=3, experience=5, dungeon=(skeleton=1, ooze=1, chest=1, dragon=1), party=(fighter=1, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) champion skeleton ooze

        (delve=2, depth=3, experience=5, dungeon=(chest=1, dragon=1), party=(fighter=1, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) descend

        (delve=2, depth=4, experience=5, dungeon=(ooze=1, potion=2, dragon=2), party=(fighter=1, thief=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) thief ooze

        (delve=2, depth=4, experience=5, dungeon=(potion=2, dragon=2), party=(fighter=1, scroll=2), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) scroll potion mage cleric

        (delve=2, depth=4, experience=5, dungeon=(dragon=2), party=(fighter=1, cleric=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) descend

        (delve=2, depth=5, experience=5, dungeon=(goblin=1, skeleton=2, potion=1, dragon=3), party=(fighter=1, cleric=1, mage=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) scroll goblin skeleton skeleton

        (delve=2, depth=5, experience=5, dungeon=(ooze=1, chest=1, potion=1, dragon=4), party=(fighter=1, cleric=1, mage=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) mage ooze

        (delve=2, depth=5, experience=5, dungeon=(chest=1, potion=1, dragon=4), party=(fighter=1, cleric=1), ability=True, regroup=(discard=()), treasure=(talisman=1))
        (Bard  6) fighter chest

        (delve=2, depth=5, experience=5, dungeon=(potion=1, dragon=4), party=(cleric=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard  7) ability

        (delve=2, depth=5, experience=5, dungeon=(potion=1), party=(cleric=1), regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard  7) retire

        (delve=3, experience=10, party=(fighter=1, cleric=2, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) descend

        (delve=3, depth=1, experience=10, dungeon=(ooze=1), party=(fighter=1, cleric=2, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) cleric ooze

        (delve=3, depth=1, experience=10, dungeon=(), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) descend

        (delve=3, depth=2, experience=10, dungeon=(goblin=1, potion=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) fighter goblin

        (delve=3, depth=2, experience=10, dungeon=(potion=1), party=(cleric=1, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) scroll potion fighter

        (delve=3, depth=2, experience=10, dungeon=(), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) descend

        (delve=3, depth=3, experience=10, dungeon=(goblin=1, skeleton=1, dragon=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) cleric goblin

        (delve=3, depth=3, experience=10, dungeon=(skeleton=1, dragon=1), party=(fighter=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) champion skeleton

        (delve=3, depth=3, experience=10, dungeon=(dragon=1), party=(fighter=1, thief=1, scroll=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) descend

        (delve=3, depth=4, experience=10, dungeon=(skeleton=1, ooze=1, chest=1, potion=1, dragon=1), party=(fighter=1, thief=1, scroll=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) fighter skeleton

        (delve=3, depth=4, experience=10, dungeon=(ooze=1, chest=1, potion=1, dragon=1), party=(thief=1, scroll=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) thief ooze

        (delve=3, depth=4, experience=10, dungeon=(chest=1, potion=1, dragon=1), party=(scroll=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) scroll potion thief

        (delve=3, depth=4, experience=10, dungeon=(chest=1, dragon=1), party=(thief=1), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1))
        (Bard 12) thief chest

        (delve=3, depth=4, experience=10, dungeon=(dragon=1), party=(), ability=True, regroup=(discard=()), treasure=(sword=1, talisman=1, ring=1))
        (Bard 13) ability

        (delve=3, depth=4, experience=10, dungeon=(), party=(), regroup=(discard=()), treasure=(sword=1, talisman=1, ring=1))
        (Bard 13) EOF
        """
        # Drive the game according to the script in the above docstring.
        s = Shell(Game(random=random.Random(27), player=Minstrel), display_mode=DisplayMode.MECHANICAL)
        s.preloop()
        parsed = parse_summary_command(self.test_minstrel.__doc__)
        for index, (expected_summary, following_command) in enumerate(parsed):
            self.assertEqual(
                expected_summary, s._game.summary(),
                "Summary mismatch at {}".format(index)
            )
            s.onecmd(following_command)

        # Confirm some non-trivial processing occurred
        self.assertEqual(index, 44)


class TestCrusader(unittest.TestCase):

    def test_crusader(self):
        """
        Runs the following scenario involving unique Crusader/Paladin details:

        (delve=1, party=(cleric=2, mage=3, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Crusader  0) descend

        (delve=1, depth=1, dungeon=(chest=1), party=(cleric=2, mage=3, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Crusader  0) mage chest

        (delve=1, depth=1, dungeon=(), party=(cleric=2, mage=2, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) descend

        (delve=1, depth=2, dungeon=(goblin=1, potion=1), party=(cleric=2, mage=2, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) scroll goblin

        (delve=1, depth=2, dungeon=(potion=1, dragon=1), party=(cleric=2, mage=2, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) descend

        (delve=1, depth=3, dungeon=(ooze=1, potion=1, dragon=2), party=(cleric=2, mage=2, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) mage ooze

        (delve=1, depth=3, dungeon=(potion=1, dragon=2), party=(cleric=2, mage=1, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) mage potion fighter

        (delve=1, depth=3, dungeon=(dragon=2), party=(fighter=1, cleric=2, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) descend

        (delve=1, depth=4, dungeon=(goblin=1, ooze=1, potion=1, dragon=3), party=(fighter=1, cleric=2, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) fighter goblin

        (delve=1, depth=4, dungeon=(ooze=1, potion=1, dragon=3), party=(cleric=2, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) cleric ooze

        (delve=1, depth=4, dungeon=(potion=1, dragon=3), party=(cleric=1, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Crusader  1) elixir cleric

        (delve=1, depth=4, dungeon=(potion=1, dragon=3), party=(cleric=2, champion=1), ability=True, regroup=(discard=()), treasure=())
        (Crusader  0) cleric dragon cleric champion

        (delve=1, depth=4, experience=1, dungeon=(potion=1), party=(), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Crusader  3) ability fighter

        (delve=1, depth=4, experience=1, dungeon=(potion=1), party=(fighter=1), regroup=(discard=()), treasure=(portal=1))
        (Crusader  3) retire

        (delve=2, experience=5, party=(fighter=3, mage=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) descend

        (delve=2, depth=1, experience=5, dungeon=(dragon=1), party=(fighter=3, mage=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) descend

        (delve=2, depth=2, experience=5, dungeon=(goblin=1, ooze=1, dragon=1), party=(fighter=3, mage=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) fighter goblin

        (delve=2, depth=2, experience=5, dungeon=(ooze=1, dragon=1), party=(fighter=2, mage=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) fighter ooze

        (delve=2, depth=2, experience=5, dungeon=(dragon=1), party=(fighter=1, mage=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) descend

        (delve=2, depth=3, experience=5, dungeon=(goblin=1, chest=1, dragon=2), party=(fighter=1, mage=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) mage goblin

        (delve=2, depth=3, experience=5, dungeon=(chest=1, dragon=2), party=(fighter=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) undo

        (delve=2, depth=3, experience=5, dungeon=(goblin=1, chest=1, dragon=2), party=(fighter=1, mage=1, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) scroll goblin

        (delve=2, depth=3, experience=5, dungeon=(goblin=1, chest=1, dragon=2), party=(fighter=1, mage=1, thief=1, champion=1), ability=True, regroup=(discard=()), treasure=(portal=1))
        (Paladin  7) ability portal

        (delve=2, depth=3, experience=5, dungeon=(), party=(fighter=1, mage=1, thief=1, champion=1), regroup=(discard=()), treasure=(elixir=1))
        (Paladin  6) descend

        (delve=2, depth=4, experience=5, dungeon=(goblin=1, skeleton=1, ooze=2), party=(fighter=1, mage=1, thief=1, champion=1), regroup=(discard=()), treasure=(elixir=1))
        (Paladin  6) mage ooze

        (delve=2, depth=4, experience=5, dungeon=(goblin=1, skeleton=1), party=(fighter=1, thief=1, champion=1), regroup=(discard=()), treasure=(elixir=1))
        (Paladin  6) fighter goblin

        (delve=2, depth=4, experience=5, dungeon=(skeleton=1), party=(thief=1, champion=1), regroup=(discard=()), treasure=(elixir=1))
        (Paladin  6) thief skeleton

        (delve=2, depth=4, experience=5, dungeon=(), party=(champion=1), regroup=(discard=()), treasure=(elixir=1))
        (Paladin  6) retire

        (delve=3, experience=9, party=(fighter=2, cleric=1, mage=2, thief=1, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Paladin 10) descend

        (delve=3, depth=1, experience=9, dungeon=(skeleton=1), party=(fighter=2, cleric=1, mage=2, thief=1, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Paladin 10) fighter skeleton

        (delve=3, depth=1, experience=9, dungeon=(), party=(fighter=1, cleric=1, mage=2, thief=1, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Paladin 10) descend

        (delve=3, depth=2, experience=9, dungeon=(goblin=1, potion=1), party=(fighter=1, cleric=1, mage=2, thief=1, champion=1), ability=True, regroup=(discard=()), treasure=(elixir=1))
        (Paladin 10) ability elixir mage

        (delve=3, depth=2, experience=9, dungeon=(), party=(fighter=1, cleric=1, mage=3, thief=1, champion=1), regroup=(discard=()), treasure=())
        (Paladin  9) EOF
        """
        # Drive the game according to the script in the above docstring.
        s = Shell(Game(random=random.Random(35), player=Crusader), display_mode=DisplayMode.MECHANICAL)
        s.preloop()
        parsed = parse_summary_command(self.test_crusader.__doc__)
        for index, (expected_summary, following_command) in enumerate(parsed):
            self.assertEqual(
                expected_summary, s._game.summary(),
                "Summary mismatch at {}".format(index)
            )
            s.onecmd(following_command)

        # Confirm some non-trivial processing occurred
        self.assertEqual(index, 32)


class TestEnchantress(unittest.TestCase):

    def test_enchantress(self):
        """
        Runs the following scenario involving unique Enchantress/Beguiler details:

        (delve=1, party=(cleric=1, mage=2, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (Enchantress  0) descend

        (delve=1, depth=1, dungeon=(chest=1), party=(cleric=1, mage=2, thief=1, champion=1, scroll=2), ability=True, regroup=(discard=()), treasure=())
        (Enchantress  0) reroll chest

        (delve=1, depth=1, dungeon=(goblin=1), party=(cleric=1, mage=2, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Enchantress  0) cleric goblin

        (delve=1, depth=1, dungeon=(), party=(mage=2, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Enchantress  0) descend

        (delve=1, depth=2, dungeon=(ooze=1, chest=1), party=(mage=2, thief=1, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=())
        (Enchantress  0) ability ooze

        (delve=1, depth=2, dungeon=(chest=1, potion=1), party=(mage=2, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=())
        (Enchantress  0) mage chest

        (delve=1, depth=2, dungeon=(potion=1), party=(mage=1, thief=1, champion=1, scroll=1), regroup=(discard=()), treasure=(elixir=1))
        (Enchantress  1) elixir scroll

        (delve=1, depth=2, dungeon=(potion=1), party=(mage=1, thief=1, champion=1, scroll=2), regroup=(discard=()), treasure=())
        (Enchantress  0) descend

        (delve=1, depth=3, dungeon=(chest=1, dragon=2), party=(mage=1, thief=1, champion=1, scroll=2), regroup=(discard=()), treasure=())
        (Enchantress  0) descend

        (delve=1, depth=4, dungeon=(goblin=1, skeleton=1, potion=2, dragon=2), party=(mage=1, thief=1, champion=1, scroll=2), regroup=(discard=()), treasure=())
        (Enchantress  0) mage goblin

        (delve=1, depth=4, dungeon=(skeleton=1, potion=2, dragon=2), party=(thief=1, champion=1, scroll=2), regroup=(discard=()), treasure=())
        (Enchantress  0) thief skeleton

        (delve=1, depth=4, dungeon=(potion=2, dragon=2), party=(champion=1, scroll=2), regroup=(discard=()), treasure=())
        (Enchantress  0) champion potion scroll scroll

        (delve=1, depth=4, dungeon=(dragon=2), party=(scroll=4), regroup=(discard=()), treasure=())
        (Enchantress  0) descend

        (delve=1, depth=5, dungeon=(skeleton=1, ooze=1, chest=1, potion=1, dragon=3), party=(scroll=4), regroup=(discard=()), treasure=())
        (Enchantress  0) scroll skeleton

        (delve=1, depth=5, dungeon=(ooze=1, chest=1, potion=1, dragon=3), party=(scroll=3), regroup=(discard=()), treasure=())
        (Enchantress  0) scroll ooze

        (delve=1, depth=5, dungeon=(chest=1, potion=1, dragon=3), party=(scroll=2), regroup=(discard=()), treasure=())
        (Enchantress  0) scroll chest

        (delve=1, depth=5, dungeon=(potion=1, dragon=3), party=(scroll=1), regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) scroll potion champion

        (delve=1, depth=5, dungeon=(dragon=3), party=(champion=1), regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) retreat

        (delve=2, party=(fighter=2, cleric=2, mage=1, champion=2), ability=True, regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) descend

        (delve=2, depth=1, dungeon=(dragon=1), party=(fighter=2, cleric=2, mage=1, champion=2), ability=True, regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) descend

        (delve=2, depth=2, dungeon=(ooze=1, dragon=2), party=(fighter=2, cleric=2, mage=1, champion=2), ability=True, regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) fighter ooze

        (delve=2, depth=2, dungeon=(dragon=2), party=(fighter=1, cleric=2, mage=1, champion=2), ability=True, regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) descend

        (delve=2, depth=3, dungeon=(goblin=2, chest=1, dragon=2), party=(fighter=1, cleric=2, mage=1, champion=2), ability=True, regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) fighter goblin

        (delve=2, depth=3, dungeon=(chest=1, dragon=2), party=(cleric=2, mage=1, champion=2), ability=True, regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) descend

        (delve=2, depth=4, dungeon=(goblin=1, skeleton=1, potion=1, dragon=3), party=(cleric=2, mage=1, champion=2), ability=True, regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) ability skeleton

        (delve=2, depth=4, dungeon=(goblin=1, potion=2, dragon=3), party=(cleric=2, mage=1, champion=2), regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) cleric goblin

        (delve=2, depth=4, dungeon=(potion=2, dragon=3), party=(cleric=1, mage=1, champion=2), regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) champion potion scroll scroll

        (delve=2, depth=4, dungeon=(dragon=3), party=(cleric=1, mage=1, champion=1, scroll=2), regroup=(discard=()), treasure=(tools=1))
        (Enchantress  1) cleric dragon mage champion

        (delve=2, depth=4, experience=1, dungeon=(), party=(scroll=2), regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Enchantress  3) retire

        (delve=3, experience=5, party=(fighter=1, cleric=1, thief=3, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) descend

        (delve=3, depth=1, experience=5, dungeon=(ooze=1), party=(fighter=1, cleric=1, thief=3, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) thief ooze

        (delve=3, depth=1, experience=5, dungeon=(), party=(fighter=1, cleric=1, thief=2, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) descend

        (delve=3, depth=2, experience=5, dungeon=(potion=2), party=(fighter=1, cleric=1, thief=2, champion=1, scroll=1), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) thief potion scroll scroll

        (delve=3, depth=2, experience=5, dungeon=(), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) descend

        (delve=3, depth=3, experience=5, dungeon=(goblin=1, skeleton=1, dragon=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) fighter goblin

        (delve=3, depth=3, experience=5, dungeon=(skeleton=1, dragon=1), party=(cleric=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) undo

        (delve=3, depth=3, experience=5, dungeon=(goblin=1, skeleton=1, dragon=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=3), ability=True, regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) ability goblin skeleton

        (delve=3, depth=3, experience=5, dungeon=(potion=1, dragon=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=3), regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) descend

        (delve=3, depth=4, experience=5, dungeon=(goblin=1, skeleton=1, potion=2, dragon=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=3), regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) scroll goblin

        (delve=3, depth=4, experience=5, dungeon=(skeleton=1, potion=2, dragon=1), party=(fighter=1, cleric=1, thief=1, champion=1, scroll=2), regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) cleric skeleton

        (delve=3, depth=4, experience=5, dungeon=(potion=2, dragon=1), party=(fighter=1, thief=1, champion=1, scroll=2), regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) thief potion scroll scroll

        (delve=3, depth=4, experience=5, dungeon=(dragon=1), party=(fighter=1, champion=1, scroll=4), regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) descend

        (delve=3, depth=5, experience=5, dungeon=(chest=2, potion=2, dragon=2), party=(fighter=1, champion=1, scroll=4), regroup=(discard=()), treasure=(talisman=1, tools=1))
        (Beguiler  7) scroll chest

        (delve=3, depth=5, experience=5, dungeon=(potion=2, dragon=2), party=(fighter=1, champion=1, scroll=3), regroup=(discard=()), treasure=(talisman=1, tools=1, scale=2))
        (Beguiler 11) scroll potion scroll scroll

        (delve=3, depth=5, experience=5, dungeon=(dragon=2), party=(fighter=1, champion=1, scroll=4), regroup=(discard=()), treasure=(talisman=1, tools=1, scale=2))
        (Beguiler 11) descend

        (delve=3, depth=6, experience=5, dungeon=(goblin=1, chest=1, potion=2, dragon=3), party=(fighter=1, champion=1, scroll=4), regroup=(discard=()), treasure=(talisman=1, tools=1, scale=2))
        (Beguiler 11) fighter goblin

        (delve=3, depth=6, experience=5, dungeon=(chest=1, potion=2, dragon=3), party=(champion=1, scroll=4), regroup=(discard=()), treasure=(talisman=1, tools=1, scale=2))
        (Beguiler 11) scroll potion scroll scroll

        (delve=3, depth=6, experience=5, dungeon=(chest=1, dragon=3), party=(champion=1, scroll=5), regroup=(discard=()), treasure=(talisman=1, tools=1, scale=2))
        (Beguiler 11) champion chest

        (delve=3, depth=6, experience=5, dungeon=(dragon=3), party=(scroll=5), regroup=(discard=()), treasure=(talisman=1, sceptre=1, tools=1, scale=2))
        (Beguiler 12) scroll dragon scroll scroll

        (delve=3, depth=6, experience=6, dungeon=(), party=(scroll=2), regroup=(discard=()), treasure=(talisman=1, sceptre=1, tools=1, scale=3))
        (Beguiler 14) EOF
        """
        # Drive the game according to the script in the above docstring.
        s = Shell(Game(random=random.Random(12), player=Enchantress), display_mode=DisplayMode.MECHANICAL)
        s.preloop()
        parsed = parse_summary_command(self.test_enchantress.__doc__)
        for index, (expected_summary, following_command) in enumerate(parsed):
            self.assertEqual(
                expected_summary, s._game.summary(),
                "Summary mismatch at {}".format(index)
            )
            s.onecmd(following_command)

        # Confirm some non-trivial processing occurred
        self.assertEqual(index, 49)
