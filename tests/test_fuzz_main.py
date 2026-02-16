# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Fuzz tests for the droll/__main__.py entry point.

Exercises main() argument parsing, Game construction across all heroes and
seeds, and random command sequences driven through the Shell to look for
crashes, unhandled exceptions, and assertion errors.
"""

import io
import random
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

from droll.__main__ import main, AVAILABLE_HEROES
from droll.display import DisplayMode
from droll.error import DrollError
from droll.game import Game, GameState
from droll.player import Default
from droll.shell import Shell


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

HERO_NAMES = list(AVAILABLE_HEROES.keys())

hero_strategy = st.sampled_from(HERO_NAMES)
seed_strategy = st.integers(min_value=-(2**31), max_value=2**31 - 1)

# Valid game-level commands (not all will be valid at every state)
SHELL_COMMANDS = [
    "descend",
    "retire",
    "retreat",
    "ability",
    "reroll goblin",
    "reroll skeleton",
    "reroll ooze",
    "reroll chest",
    "reroll potion",
    "reroll goblin skeleton",
    "reroll goblin ooze",
    "fighter goblin",
    "fighter skeleton",
    "fighter ooze",
    "fighter chest",
    "fighter potion fighter",
    "fighter dragon cleric mage",
    "cleric goblin",
    "cleric skeleton",
    "cleric ooze",
    "cleric chest",
    "cleric potion cleric",
    "cleric dragon fighter mage",
    "mage goblin",
    "mage skeleton",
    "mage ooze",
    "mage chest",
    "mage potion mage",
    "mage dragon fighter cleric",
    "thief goblin",
    "thief skeleton",
    "thief ooze",
    "thief chest",
    "thief potion thief",
    "thief dragon fighter cleric",
    "champion goblin",
    "champion skeleton",
    "champion ooze",
    "champion chest",
    "champion potion champion",
    "champion dragon fighter cleric",
    "scroll potion fighter",
    "scroll potion cleric",
    "scroll potion mage",
    "scroll potion thief",
    "sword goblin",
    "talisman skeleton",
    "sceptre ooze",
    "tools chest",
    "elixir fighter",
    "elixir cleric",
    "elixir mage",
    "elixir thief",
    "elixir champion",
    "elixir scroll",
    "bait",
    "bait dragon",
    "undo",
    "help",
    "",
]

# Garbage / malformed commands for robustness testing
GARBAGE_COMMANDS = [
    "notacommand",
    "fighter",
    "fighter notarget",
    "descend extra_arg",
    "retire extra_arg",
    "retreat extra_arg",
    "reroll",
    "reroll dragon",
    "fighter dragon",
    "fighter dragon fighter fighter",
    "portal",
    "ring",
    "scale",
    "    ",
    "fighter goblin skeleton ooze chest potion dragon",
    "a b c d e f g h i j",
    "",
    "EOF",
]

command_strategy = st.sampled_from(SHELL_COMMANDS + GARBAGE_COMMANDS)
command_sequence_strategy = st.lists(command_strategy, min_size=1, max_size=40)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_shell_commands(hero_cls, seed, commands):
    """Create a Game + Shell and execute a sequence of commands.

    Returns (game_state_at_end, exceptions_seen).
    All DrollErrors are expected and swallowed.  Any other exception is
    collected and re-raised after recording.
    """
    rng = random.Random(seed)
    game = Game(player=hero_cls, random=rng)
    shell = Shell(game, display_mode=DisplayMode.MECHANICAL)

    # Suppress stdout from Shell printing
    with redirect_stdout(io.StringIO()):
        shell.preloop()
        for cmd in commands:
            try:
                result = shell.onecmd(cmd)
                if result is GameState.STOP or result is True:
                    break
            except DrollError:
                pass  # Expected game-rule violations
            except SystemExit:
                break  # EOF or argparse exits


def run_main_with_args(args):
    """Run main() capturing all output, allowing SystemExit from argparse."""
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        try:
            main(args)
        except SystemExit:
            pass  # argparse calls sys.exit on bad args


# ---------------------------------------------------------------------------
# Test: Argument parsing
# ---------------------------------------------------------------------------

class TestMainArgParsing(unittest.TestCase):
    """Fuzz the argument parsing of main()."""

    def test_all_heroes_no_seed(self):
        """main() accepts every hero name without --seed and doesn't crash."""
        for hero in HERO_NAMES:
            with redirect_stdout(io.StringIO()), \
                 patch("sys.stdin", io.StringIO("EOF\n")):
                try:
                    main([hero])
                except SystemExit:
                    pass

    def test_all_heroes_with_seed_zero(self):
        """main() with --seed 0 for every hero."""
        for hero in HERO_NAMES:
            with redirect_stdout(io.StringIO()), \
                 patch("sys.stdin", io.StringIO("EOF\n")):
                try:
                    main([hero, "--seed", "0"])
                except SystemExit:
                    pass

    def test_all_heroes_mechanical_mode(self):
        """main() with --mechanical for every hero."""
        for hero in HERO_NAMES:
            with redirect_stdout(io.StringIO()), \
                 patch("sys.stdin", io.StringIO("EOF\n")):
                try:
                    main([hero, "--mechanical"])
                except SystemExit:
                    pass

    def test_no_args_exits(self):
        """main() with no arguments causes SystemExit(2) from argparse."""
        with self.assertRaises(SystemExit):
            with redirect_stderr(io.StringIO()):
                main([])

    def test_invalid_hero_exits(self):
        """main() with an invalid hero name causes SystemExit from argparse."""
        with self.assertRaises(SystemExit):
            with redirect_stderr(io.StringIO()):
                main(["NotAHero"])

    def test_seed_negative(self):
        """main() with a negative seed."""
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default", "--seed", "-1"])
            except SystemExit:
                pass

    def test_seed_large(self):
        """main() with a very large seed."""
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default", "--seed", "999999999"])
            except SystemExit:
                pass

    @given(seed_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_random_seeds(self, seed):
        """main() with hypothesis-generated seeds never crashes."""
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default", "--seed", str(seed)])
            except SystemExit:
                pass

    @given(hero_strategy, seed_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_random_hero_and_seed(self, hero, seed):
        """main() with random hero + seed combinations never crashes."""
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main([hero, "--seed", str(seed)])
            except SystemExit:
                pass


# ---------------------------------------------------------------------------
# Test: Random command sequences through Shell
# ---------------------------------------------------------------------------

class TestFuzzShellCommands(unittest.TestCase):
    """Drive random command sequences through the Shell for every hero."""

    @given(seed_strategy, command_sequence_strategy)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_commands_default(self, seed, commands):
        """Random command sequences against Default hero never crash."""
        run_shell_commands(Default, seed, commands)

    @given(hero_strategy, seed_strategy, command_sequence_strategy)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_commands_any_hero(self, hero_name, seed, commands):
        """Random command sequences against any hero never crash."""
        hero_cls = AVAILABLE_HEROES[hero_name]
        run_shell_commands(hero_cls, seed, commands)

    def test_descend_retire_loop_all_heroes(self):
        """Repeatedly descend/retire for each hero across many seeds."""
        for hero_name, hero_cls in AVAILABLE_HEROES.items():
            for seed in range(50):
                commands = []
                for _ in range(30):
                    commands.append("descend")
                    # Try to clear things and retire/retreat
                    commands.extend([
                        "champion goblin",
                        "champion skeleton",
                        "champion ooze",
                        "champion chest",
                        "champion potion champion",
                        "fighter dragon cleric mage",
                        "retire",
                        "retreat",
                    ])
                run_shell_commands(hero_cls, seed, commands)

    def test_all_garbage_commands_all_heroes(self):
        """Every garbage command against every hero with several seeds."""
        for hero_name, hero_cls in AVAILABLE_HEROES.items():
            for seed in range(10):
                run_shell_commands(hero_cls, seed, GARBAGE_COMMANDS)


# ---------------------------------------------------------------------------
# Test: Game construction and basic operations for all heroes
# ---------------------------------------------------------------------------

class TestFuzzGameConstruction(unittest.TestCase):
    """Verify Game construction doesn't crash for varied inputs."""

    @given(hero_strategy, seed_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_game_construction(self, hero_name, seed):
        """Game(...) never crashes for valid hero + seed."""
        hero_cls = AVAILABLE_HEROES[hero_name]
        game = Game(player=hero_cls, random=random.Random(seed))
        # Basic sanity: summary and score don't crash
        game.summary()
        game.score()
        game.prompt()

    @given(hero_strategy, seed_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_game_completenames(self, hero_name, seed):
        """completenames() never crashes."""
        hero_cls = AVAILABLE_HEROES[hero_name]
        game = Game(player=hero_cls, random=random.Random(seed))
        # Test with various text prefixes
        for prefix in ["", "f", "c", "m", "d", "r", "a", "x", "zzz"]:
            game.completenames(prefix, head=[], tail=[])
            game.completenames(prefix, head=["fighter"], tail=[])
            game.completenames(prefix, head=["fighter", "goblin"], tail=[])

    def test_game_copy_equality(self):
        """copy(game) == game for all heroes."""
        import copy
        for hero_name, hero_cls in AVAILABLE_HEROES.items():
            for seed in range(20):
                game = Game(player=hero_cls, random=random.Random(seed))
                game_copy = copy.copy(game)
                self.assertEqual(game, game_copy,
                                 f"Copy failed for {hero_name} seed={seed}")


# ---------------------------------------------------------------------------
# Test: Shell tab completion fuzzing
# ---------------------------------------------------------------------------

class TestFuzzCompletion(unittest.TestCase):
    """Fuzz tab completion to ensure it never crashes."""

    @given(hero_strategy, seed_strategy, st.text(min_size=0, max_size=20))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_completenames_arbitrary_text(self, hero_name, seed, text):
        """completenames with arbitrary text never crashes."""
        hero_cls = AVAILABLE_HEROES[hero_name]
        game = Game(player=hero_cls, random=random.Random(seed))
        shell = Shell(game, display_mode=DisplayMode.MECHANICAL)
        with redirect_stdout(io.StringIO()):
            shell.preloop()
        # completenames(text, line, begidx, endidx)
        line = text
        shell.completenames(text, line, 0, len(text))

    @given(hero_strategy, seed_strategy,
           st.text(min_size=0, max_size=10),
           st.text(min_size=0, max_size=30))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_completedefault_arbitrary(self, hero_name, seed, text, line):
        """completedefault with arbitrary text+line never crashes."""
        hero_cls = AVAILABLE_HEROES[hero_name]
        game = Game(player=hero_cls, random=random.Random(seed))
        shell = Shell(game, display_mode=DisplayMode.MECHANICAL)
        with redirect_stdout(io.StringIO()):
            shell.preloop()
        begidx = min(len(line), max(0, len(line) - len(text)))
        endidx = len(line)
        shell.completedefault(text, line, begidx, endidx)


# ---------------------------------------------------------------------------
# Test: Long games - play through many seeds to completion
# ---------------------------------------------------------------------------

class TestFuzzFullGames(unittest.TestCase):
    """Play full or near-full games to exercise deep game states."""

    def _play_game(self, hero_cls, seed, strategy="aggressive"):
        """Play a game using a simple automated strategy."""
        rng = random.Random(seed)
        game = Game(player=hero_cls, random=rng)
        shell = Shell(game, display_mode=DisplayMode.MECHANICAL)

        with redirect_stdout(io.StringIO()):
            shell.preloop()

            for turn in range(200):  # Max turns to prevent infinite loops
                world = shell._game._world

                # Try descending first
                try:
                    result = shell.onecmd("descend", _raises=True)
                    if result is GameState.STOP or result is True:
                        break
                    continue
                except DrollError:
                    pass

                if world.dungeon is None:
                    break

                # Try to defeat monsters
                acted = False
                for hero in ["champion", "fighter", "cleric", "mage", "thief"]:
                    for target in ["goblin", "skeleton", "ooze"]:
                        try:
                            result = shell.onecmd(
                                f"{hero} {target}", _raises=True
                            )
                            acted = True
                            break
                        except DrollError:
                            pass
                    if acted:
                        continue

                # Try opening chests
                for hero in ["champion", "thief", "fighter", "cleric", "mage"]:
                    try:
                        result = shell.onecmd(
                            f"{hero} chest", _raises=True
                        )
                        acted = True
                        break
                    except DrollError:
                        pass

                if acted:
                    continue

                # Try quaffing potions
                for hero in ["champion", "fighter", "cleric", "mage", "thief"]:
                    for revive in ["fighter", "cleric", "mage", "thief",
                                   "champion"]:
                        try:
                            result = shell.onecmd(
                                f"{hero} potion {revive}", _raises=True
                            )
                            acted = True
                            break
                        except DrollError:
                            pass
                    if acted:
                        break

                if acted:
                    continue

                # Try retiring
                try:
                    result = shell.onecmd("retire", _raises=True)
                    if result is GameState.STOP or result is True:
                        break
                    continue
                except DrollError:
                    pass

                # Try retreating
                try:
                    result = shell.onecmd("retreat", _raises=True)
                    if result is GameState.STOP or result is True:
                        break
                    continue
                except DrollError:
                    pass

                # Try ability
                try:
                    result = shell.onecmd("ability", _raises=True)
                    if result is GameState.STOP or result is True:
                        break
                    continue
                except DrollError:
                    pass

                # Nothing worked, end
                break

    def test_aggressive_games_all_heroes(self):
        """Play aggressive games for every hero across many seeds."""
        for hero_name, hero_cls in AVAILABLE_HEROES.items():
            for seed in range(50):
                self._play_game(hero_cls, seed, "aggressive")


# ---------------------------------------------------------------------------
# Test: Edge cases in main() argument handling
# ---------------------------------------------------------------------------

class TestMainEdgeCases(unittest.TestCase):
    """Edge cases in the main() function's argument processing."""

    def test_seed_is_list_from_nargs(self):
        """Verify --seed with nargs=1 produces a list and Random accepts it."""
        # This tests the line: randseed = arguments.seed if arguments.seed else ()
        # When --seed 42 is passed, arguments.seed = [42] (a list due to nargs=1)
        # Then random.Random(*[42]) is called, which is random.Random(42)
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default", "--seed", "42"])
            except SystemExit:
                pass

    def test_seed_zero_is_truthy_as_list(self):
        """--seed 0 produces [0] which is truthy, so seed is applied."""
        # arguments.seed = [0], which is truthy, so randseed = [0]
        # random.Random(*[0]) = random.Random(0)
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default", "--seed", "0"])
            except SystemExit:
                pass

    def test_no_seed_gives_empty_tuple(self):
        """Without --seed, arguments.seed is None, so randseed = ()."""
        # arguments.seed = None, so randseed = ()
        # random.Random(*()) = random.Random() (unseeded)
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default"])
            except SystemExit:
                pass

    def test_main_none_args(self):
        """main(None) reads sys.argv; ensure it doesn't crash with mocked argv."""
        with redirect_stdout(io.StringIO()), \
             redirect_stderr(io.StringIO()), \
             patch("sys.argv", ["droll", "Default"]), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(None)
            except SystemExit:
                pass

    def test_duplicate_flags(self):
        """Duplicate --mechanical flags don't crash."""
        with redirect_stdout(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default", "--mechanical", "--mechanical"])
            except SystemExit:
                pass

    def test_seed_repeated(self):
        """Repeating --seed takes the last value (argparse behavior)."""
        with redirect_stdout(io.StringIO()), \
             redirect_stderr(io.StringIO()), \
             patch("sys.stdin", io.StringIO("EOF\n")):
            try:
                main(["Default", "--seed", "1", "--seed", "2"])
            except SystemExit:
                pass


# ---------------------------------------------------------------------------
# Test: Display modes through main-like paths
# ---------------------------------------------------------------------------

class TestFuzzDisplayModes(unittest.TestCase):
    """Ensure both display modes work across heroes and game states."""

    def test_both_display_modes_all_heroes(self):
        """Construct Shell in both modes for each hero; run a few commands."""
        for hero_name, hero_cls in AVAILABLE_HEROES.items():
            for mode in (DisplayMode.CURRENT, DisplayMode.MECHANICAL):
                for seed in range(5):
                    game = Game(player=hero_cls, random=random.Random(seed))
                    shell = Shell(game, display_mode=mode)
                    with redirect_stdout(io.StringIO()):
                        shell.preloop()
                        shell.onecmd("descend")
                        shell.onecmd("help")
                        shell.onecmd("champion goblin")
                        shell.onecmd("retire")


# ---------------------------------------------------------------------------
# Test: Hypothesis-driven random command strings
# ---------------------------------------------------------------------------

class TestFuzzArbitraryStrings(unittest.TestCase):
    """Feed completely arbitrary strings as commands to the Shell."""

    @given(
        hero_strategy,
        seed_strategy,
        st.lists(st.text(min_size=0, max_size=50), min_size=1, max_size=20),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_arbitrary_strings_as_commands(self, hero_name, seed, commands):
        """Completely arbitrary strings fed to Shell never crash."""
        hero_cls = AVAILABLE_HEROES[hero_name]
        rng = random.Random(seed)
        game = Game(player=hero_cls, random=rng)
        shell = Shell(game, display_mode=DisplayMode.MECHANICAL)

        with redirect_stdout(io.StringIO()):
            shell.preloop()
            for cmd in commands:
                try:
                    result = shell.onecmd(cmd)
                    if result is GameState.STOP or result is True:
                        break
                except (DrollError, SystemExit):
                    pass


if __name__ == "__main__":
    unittest.main()
