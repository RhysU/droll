# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of the shell (at least driving with basic commands)."""

import io
import random
import typing
import unittest
from dataclasses import replace
from unittest.mock import patch

from droll import struct
from droll.display import DisplayMode
from droll.error import DrollError
from droll.game import Game
from droll.player import Default
from droll.shell import Shell, _RESET


def _mechanical_shell(game: Game) -> Shell:
    return Shell(game, display_mode=DisplayMode.MECHANICAL)


class TestPrecmd(unittest.TestCase):

    def test_precmd_emits_reset_when_color_enabled(self):
        with patch("sys.stdout.isatty", return_value=True):
            s = Shell(Game(), display_mode=DisplayMode.CURRENT)
        s.preloop()
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            result = s.precmd("fighter goblin")
        self.assertEqual(result, "fighter goblin")
        self.assertEqual(fake_out.getvalue(), _RESET)

    def test_precmd_emits_nothing_when_color_disabled(self):
        s = _mechanical_shell(Game())
        s.preloop()
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            result = s.precmd("fighter goblin")
        self.assertEqual(result, "fighter goblin")
        self.assertEqual(fake_out.getvalue(), "")


class TestShell(unittest.TestCase):

    def test_EOF(self):
        """Confirm providing EOF exits cmdloop(...)."""
        s = _mechanical_shell(Game())
        self.assertFalse(s.cmdqueue)
        s.cmdqueue.append("EOF")
        s.cmdloop()
        self.assertEqual(s.prompt, "(Default  0) ")
        self.assertEqual(s.lastcmd, "")

    def test_reroll(self):
        """Confirm reroll command forwards to game."""
        s = _mechanical_shell(Game(random=random.Random(4), player=Default))
        s.preloop()
        s.onecmd("descend")
        # Depth 1 with seed 4 has a single goblin; reroll it
        s.onecmd("reroll goblin")

    def test_retreat(self):
        """Confirm retreat command forwards to game."""
        s = _mechanical_shell(Game(random=random.Random(4), player=Default))
        s.preloop()
        s.onecmd("descend")
        # Need a monster present so retreat is valid
        s._game._world = replace(
            s._game._world, dungeon=struct.Dungeon(goblin=1)
        )
        s.onecmd("retreat")

    def test_help(self):
        """Confirm help invocations do not throw exceptions."""
        s = _mechanical_shell(Game())
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
        s = _mechanical_shell(Game(random=random.Random(4), player=Default))

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
        s = _mechanical_shell(Game(random=random.Random(42), player=Default))
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


class TestRetireAndQuaffError(unittest.TestCase):

    def test_retire(self):
        """Shell.do_retire exercises the retire command path."""
        s = _mechanical_shell(Game(random=random.Random(4), player=Default))
        s.preloop()
        s.onecmd("descend")
        # Seed 4 at depth 1 produces goblin=1; defeat it
        s.onecmd("fighter goblin")
        # Dungeon cleared: retire covers shell.py do_retire
        s.onecmd("retire")

    def test_quaff_wrong_revive_count_prints_error(self):
        """Quaffing with wrong revive count prints DrollError via onecmd."""
        s = _mechanical_shell(Game(random=random.Random(4), player=Default))
        s.preloop()
        s.onecmd("descend")
        # Replace dungeon with a single potion and no monsters
        s._game._world = replace(
            s._game._world,
            dungeon=struct.Dungeon(potion=1),
        )
        # Quaff 1 potion providing 0 revive targets:
        # - action.py quaff raises "Exactly 1 heroes to revive required."
        # - onecmd catches and prints the DrollError
        s.onecmd("fighter potion")
