# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for droll.__main__ entry point."""
import io
import sys
import unittest

from droll.__main__ import AVAILABLE_HEROES, main


class TestImportOrigin(unittest.TestCase):
    """Game should be importable from its defining module, droll.game."""

    def test_game_import_from_game_module(self):
        """Game is defined in droll.game, not droll.shell."""
        from droll.game import Game as GameFromGame
        from droll.shell import Game as GameFromShell

        # Both resolve to the same class today, but __main__.py
        # imports from .shell which is not where Game is defined.
        # Verify the canonical location is droll.game:
        self.assertEqual(GameFromGame.__module__, "droll.game")
        # If shell ever stops re-exporting Game, __main__ breaks.
        self.assertIs(GameFromGame, GameFromShell)


class TestAvailableHeroes(unittest.TestCase):
    """AVAILABLE_HEROES should include all heroes from droll.heroes."""

    def test_all_heroes_present(self):
        from droll import heroes
        from droll.player import Default

        expected = {
            "Default",
            "Crusader",
            "Enchantress",
            "HalfGoblin",
            "Knight",
            "Minstrel",
            "Occultist",
            "Spellsword",
        }
        self.assertEqual(set(AVAILABLE_HEROES.keys()), expected)

    def test_get_vs_subscript(self):
        """AVAILABLE_HEROES.get() silently returns None for missing keys.

        __main__.py uses .get() to look up the hero, which means a
        missing key passes player=None into Game(), causing an
        AttributeError deep inside the constructor.  Using [] would
        raise a clear KeyError instead.
        """
        # .get() silently returns None
        self.assertIsNone(AVAILABLE_HEROES.get("Nonexistent"))

        # [] raises KeyError -- the safer choice
        with self.assertRaises(KeyError):
            AVAILABLE_HEROES["Nonexistent"]

    def test_none_player_crashes_game(self):
        """Passing player=None to Game crashes with AttributeError.

        This is the consequence of using .get() instead of [].
        """
        from droll.game import Game

        with self.assertRaises(AttributeError):
            Game(player=None)


class TestSeedHandling(unittest.TestCase):
    """--seed uses nargs=1, producing a list instead of a scalar."""

    def test_seed_nargs_produces_list(self):
        """argparse nargs=1 gives a list, not an int.

        __main__.py works around this with *randseed unpacking, but
        nargs=1 is unconventional.  Omitting nargs would give a plain
        int, which is the standard argparse pattern.
        """
        import argparse

        # Current behavior with nargs=1
        parser = argparse.ArgumentParser()
        parser.add_argument("--seed", type=int, nargs=1, default=None)
        args = parser.parse_args(["--seed", "42"])
        self.assertIsInstance(args.seed, list)  # It's a list!
        self.assertEqual(args.seed, [42])

        # Standard behavior without nargs
        parser2 = argparse.ArgumentParser()
        parser2.add_argument("--seed", type=int, default=None)
        args2 = parser2.parse_args(["--seed", "42"])
        self.assertIsInstance(args2.seed, int)  # It's an int.
        self.assertEqual(args2.seed, 42)


class TestMainFunction(unittest.TestCase):
    """Exercise the main() function directly."""

    def _run_main(self, args):
        """Run main() with mocked stdin (immediate EOF) to avoid blocking."""
        old_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        try:
            return main(args)
        finally:
            sys.stdin = old_stdin

    def test_main_default_hero(self):
        result = self._run_main(["Default", "--seed", "1"])
        self.assertIsNone(result)

    def test_main_every_hero(self):
        for hero_name in AVAILABLE_HEROES:
            with self.subTest(hero=hero_name):
                result = self._run_main([hero_name, "--seed", "1"])
                self.assertIsNone(result)

    def test_main_mechanical_mode(self):
        result = self._run_main(["Default", "--seed", "1", "--mechanical"])
        self.assertIsNone(result)

    def test_main_no_args_exits(self):
        """Calling main([]) should sys.exit(2) due to missing hero."""
        with self.assertRaises(SystemExit) as cm:
            self._run_main([])
        self.assertEqual(cm.exception.code, 2)

    def test_main_invalid_hero_exits(self):
        """Calling main with an invalid hero should sys.exit(2)."""
        with self.assertRaises(SystemExit) as cm:
            self._run_main(["Nonexistent"])
        self.assertEqual(cm.exception.code, 2)

    def test_main_seed_zero_works(self):
        """--seed 0 should work (seed value is falsy but [0] is truthy)."""
        result = self._run_main(["Default", "--seed", "0"])
        self.assertIsNone(result)
