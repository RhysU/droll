# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""A REPL permitting playing a Game via a tab-completion shell."""

import cmd
import copy
import functools
import sys
import textwrap

from . import display
from .game import Game, GameState
from .struct import DrollError

__all__ = ("Shell",)

_ABSENT = "\033[90m"
_COMMAND = "\033[96m"
_DRAGON = "\033[31m"
_ERROR = "\033[91m"
_HELP = "\033[93m"
_LOOT = "\033[33m"
_MONSTER = "\033[91m"
_PROMPT = "\033[92m"
_RESET = "\033[0m"


class Shell(cmd.Cmd):
    """REPL permitting playing a Game via tab-completion shell."""

    def __init__(
        self,
        game: Game,
        *,
        display_mode: display.DisplayMode = display.DisplayMode.CURRENT,
    ) -> None:
        """Initialize the shell with a game instance and display mode."""
        super().__init__()
        assert game is not None
        self._game = game
        self._undo = None
        self._command_count = 0
        self._display_mode = display_mode
        self._color = (
            display_mode == display.DisplayMode.CURRENT and sys.stdout.isatty()
        )

    def precmd(self, line: str) -> str:
        """Reset terminal color after user input."""
        if self._color:
            print(_RESET, end="")
        return line

    def preloop(self) -> None:
        """Prepare a new game and start the first delve."""
        assert self._undo is None, "Cannot call preloop(...) multiple times."
        self._undo = []
        self.postcmd(stop=False, line="")  # Prints initial world state

    _BANNER_WIDTH = 50

    def _print_delve_banner(self) -> None:
        """Print hero name and ability at the start of each delve."""
        name = self._game.player_name
        ability_doc = self._game.ability_doc

        # Separate description lines from example lines
        desc_parts = []
        examples = []
        for line in ability_doc.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("example:"):
                examples.append(stripped.split(":", 1)[1].strip())
            elif stripped:
                desc_parts.append(stripped)

        # Header rule with embedded name: ── Knight ─────────────...
        prefix = f"\u2500\u2500 {name} "
        rule = prefix + "\u2500" * max(0, self._BANNER_WIDTH - len(prefix))
        if self._color:
            print(_HELP + rule + _RESET)
        else:
            print(rule)

        # Description
        for part in desc_parts:
            print(part)

        # Compact examples on one line
        if examples:
            example_str = " \u00b7 ".join(examples)
            if self._color:
                print(f"Try: {_COMMAND}{example_str}{_RESET}")
            else:
                print(f"Try: {example_str}")

        print()

    def _postcmd_current(self, stop, line) -> None:
        """Display state using the compact summary format."""
        self.prompt = f"{self._command_count:02d} {self._game.player_name}> "
        if self._color:
            self.prompt = _PROMPT + self.prompt + _RESET
        print()
        if line != "EOF" and not stop and self._game.world.depth == 0:
            self._print_delve_banner()
        if line != "EOF":
            feasible = [] if stop else [
                name[3:]
                for name in self.get_names()
                if name.startswith("do_")
            ]
            available = [
                cmd for cmd in feasible
                if cmd in self._AVAILABLE_COMMANDS
            ]
            deltas = self._game.score_deltas()
            summary = display.compact_summary(
                self._game.world,
                self._game.player_name,
                self._game.score,
                available,
                deltas,
            )
            if self._color:
                for cmd in feasible:
                    summary = summary.replace(
                        cmd, _COMMAND + cmd + _RESET
                    )
                summary = summary.replace(
                    "dragon", _DRAGON + "dragon" + _RESET
                ).replace(
                    "goblin", _MONSTER + "goblin" + _RESET
                ).replace(
                    "ooze", _MONSTER + "ooze" + _RESET
                ).replace(
                    "skeleton", _MONSTER + "skeleton" + _RESET
                ).replace(
                    "chest", _LOOT + "chest" + _RESET
                ).replace(
                    "potion", _LOOT + "potion" + _RESET
                ).replace("None", _ABSENT + "None" + _RESET)
            print(summary)
            if stop:
                print(f"\nGame over!  Final score: {self._game.score}")

    def _postcmd_legacy(self, stop, line) -> None:
        """Display state using the brief summary format."""
        self.prompt = f"{self._game.player_name}  {self._game.score}> "
        print()
        if line != "EOF":
            print(self._game.summary)
            if stop:
                print(f"\nGame over!  Final score: {self._game.score}")

    def postcmd(self, stop, line) -> bool:
        """Print game state after each command and final details on exit."""
        # cmd.Cmd.cmdloop stops when postcmd returns truthy
        should_stop = stop is GameState.STOP
        if self._display_mode == display.DisplayMode.CURRENT:
            self._postcmd_current(should_stop, line)
        else:
            self._postcmd_legacy(should_stop, line)
        print("", end="", flush=True)
        return should_stop

    _AVAILABLE_COMMANDS = frozenset(
        {"ability", "descend", "retire", "retreat", "reroll", "undo"}
    )

    def _available_commands(self) -> list[str]:
        """Get available non-hero/non-treasure commands from help system."""
        return [
            name[3:]
            for name in self.get_names()
            if name.startswith("do_") and name[3:] in self._AVAILABLE_COMMANDS
        ]

    def onecmd(self, line, *, raises=False) -> GameState:
        """Performs undo tracking whenever undo won't cause re-roll/re-draw."""
        # Track observable state before and after command processing.
        before = copy.copy(self._game)
        try:
            result = GameState.PLAY
            result = super().onecmd(line)
        except DrollError as e:
            if raises:
                raise
            if self._color:
                print(_ERROR, " ".join(e.args), _RESET, sep="")
            else:
                print(*e.args)
            return result

        # Retain only undo candidates that disallow cheating.
        # Okay would be 'Oh! I should have used a fighter on the goblin!'
        # Not okay would be undoing a 'descend' to roll a different dungeon.
        if line == "undo":
            pass  # Retaining undo operations would break multiple undos
        elif self._game == before:
            pass  # No change in state (e.g. help) so nothing to track
        elif self._game.randstate() == before.randstate():
            self._undo.append(before)  # Same random state so undo permitted
        else:
            self._undo.clear()  # Random state mutated so no undo permitted

        if self._game != before:
            self._command_count += -1 if line == "undo" else 1

        return result

    def do_undo(self, line) -> GameState:
        """Undo prior commands.  Only permitted when nothing rolled/drawn."""
        _no_arguments(line)
        if self._undo:
            # Assertion confirms onecmd(...) processing matches expectations
            assert self._game.randstate() == self._undo[-1].randstate()
            self._game = self._undo.pop()
        else:
            raise DrollError("Cannot undo any prior command(s).")
        return GameState.PLAY

    def do_EOF(self, line) -> GameState:
        """End-of-file causes shell exit."""
        return GameState.STOP

    def emptyline(self) -> GameState:
        """Empty line displays help."""
        return self.onecmd("help")

    ####################
    # ACTIONS BELOW HERE
    ####################

    @functools.wraps(Game.ability)
    def do_ability(self, line) -> GameState:
        """Execute the player's special ability with the given arguments."""
        return self._game.ability(*_tokenize(line))

    @functools.wraps(Game.apply)
    def default(self, line) -> GameState:
        """Handle unknown commands as game actions."""
        return self._game.apply(*_tokenize(line))

    @functools.wraps(Game.descend)
    def do_descend(self, line) -> GameState:
        """Descend to the next dungeon level."""
        _no_arguments(line)
        return self._game.descend()

    @functools.wraps(Game.reroll)
    def do_reroll(self, line) -> GameState:
        """Reroll the specified party or dungeon dice."""
        return self._game.reroll(*_tokenize(line))

    @functools.wraps(Game.retire)
    def do_retire(self, line) -> GameState:
        """Retire to the tavern after clearing a dungeon depth."""
        _no_arguments(line)
        return self._game.retire()

    @functools.wraps(Game.retreat)
    def do_retreat(self, line) -> GameState:
        """Retreat to the tavern without completing the dungeon."""
        _no_arguments(line)
        return self._game.retreat()

    #######################
    # COMPLETION BELOW HERE
    #######################

    def completedefault(self, text, line, begidx, endidx):
        """Provide tab completion suggestions for default commands."""
        # Break line into tokens until and starting from present text
        names = self._game.completenames(
            text=text, head=_tokenize(line[:begidx]), tail=_tokenize(line[begidx:])
        )
        if self._undo and "undo".startswith(text):
            names.append("undo")
        # Trailing space causes tab completion to insert token separators
        return [x + " " for x in names]

    def completenames(self, text, line, begidx, endidx):
        """Provide tab completion suggestions for command names."""
        return self.completedefault(text, line, begidx, endidx)

    # Overrides superclass behavior relying purely on do_XXX(...) methods.
    # Also, lies that help_XXX(...) present for completedefault(...) methods.
    _HELP_TOPICS = ("score", "treasure")

    def get_names(self):
        """Compute potential help topics from contextual completions."""
        names = self._game.completenames(text="", head=[], tail=[])
        if self._undo:
            names.append("undo")
        return (
            ["do_" + x for x in names]
            + [
                "help_" + x
                for x in names
                if not getattr(self, "do_" + x, None)
            ]
            + ["help_" + x for x in self._HELP_TOPICS]
        )

    #################
    # HELP BELOW HERE
    #################

    def do_help(self, arg):
        """List available commands or show help for a specific command."""
        if self._color:
            print(_HELP, end="")
        try:
            super().do_help(arg)
        finally:
            if self._color:
                print(_RESET, end="")

    doc_header = "Feasible commands (help <command>):"
    doc_dragon_example = (
        "        {0} dragon cleric mage      # Attack dragon with party of 3"
    )
    doc_potion_example = (
        "        {0} potion mage thief       # Drink 2 potions obtaining mage, thief"
    )

    def help_ability(self):
        """Display help for the ability command."""
        print(self.do_ability.__doc__)
        print()
        print(textwrap.indent(self._game.ability_doc, "    "))

    def help_bait(self):
        """Display help for using bait against dragons."""
        print(self._game.bait_doc)

    def help_champion(self):
        """Display help for using the champion hero."""
        print(textwrap.dedent(f"""\
            Champions defeat ALL of any monster type and open ALL chests:

                    champion goblin              # Defeat all goblins
                    champion skeleton             # Defeat all skeletons
                    champion ooze                 # Defeat all ooze
                    champion chest                # Open all chests
            {self.doc_potion_example.format("champion")}
            {self.doc_dragon_example.format("champion")}"""))

    def help_cleric(self):
        """Display help for using the cleric hero."""
        print(textwrap.dedent(f"""\
            Clerics defeat ALL skeletons but only ONE goblin or ooze:

                    cleric skeleton               # Defeat all skeletons
                    cleric goblin                 # Defeat one goblin
                    cleric ooze                   # Defeat one ooze
                    cleric chest                  # Open one chest
            {self.doc_potion_example.format("cleric")}
            {self.doc_dragon_example.format("cleric")}"""))

    def help_elixir(self):
        """Display help for using elixir treasures."""
        print(self._game.elixir_doc)

    def help_fighter(self):
        """Display help for using the fighter hero."""
        print(textwrap.dedent(f"""\
            Fighters defeat ALL goblins but only ONE skeleton or ooze:

                    fighter goblin                # Defeat all goblins
                    fighter skeleton              # Defeat one skeleton
                    fighter ooze                  # Defeat one ooze
                    fighter chest                 # Open one chest
            {self.doc_potion_example.format("fighter")}
            {self.doc_dragon_example.format("fighter")}"""))

    def help_mage(self):
        """Display help for using the mage hero."""
        print(textwrap.dedent(f"""\
            Mages defeat ALL ooze but only ONE goblin or skeleton:

                    mage ooze                     # Defeat all ooze
                    mage goblin                   # Defeat one goblin
                    mage skeleton                 # Defeat one skeleton
                    mage chest                    # Open one chest
            {self.doc_potion_example.format("mage")}
            {self.doc_dragon_example.format("mage")}"""))

    def help_portal(self):
        """Display help for portal treasures."""
        print(textwrap.dedent("""\
            Town portals escape the dungeon, worth 2 points each.
            Retiring consumes a portal automatically."""))

    def help_ring(self):
        """Display help for using rings of invisibility."""
        print(textwrap.dedent("""\
            Rings of invisibility sneak past a blocking dragon.
            They are used automatically when descending or retiring."""))

    def help_sceptre(self):
        """Display help for using sceptre treasures."""
        print("""Sceptres behave identically to a mage.""")

    def help_scroll(self):
        """Display help for using scroll treasures."""
        print(textwrap.dedent("""\
            Consume a scroll to quaff potions or re-roll dice:

                    scroll potion mage thief    # Drink 2 potions obtaining mage, thief
                    reroll skeleton goblin      # Re-roll a skeleton and a goblin

            Scroll behavior varies by hero:

                    scroll skeleton             # Enchantress/Beguiler: kill all skeletons
                    Knight: scrolls become champions during party roll
                    Mercenary/Commander: one bonus scroll, discarded on regroup"""))

    def help_reroll(self):
        """Display help for the reroll command."""
        print(self.do_reroll.__doc__)
        print(textwrap.dedent("""
            Targets can be any dungeon die (goblin, skeleton, ooze,
            chest, potion) or party die (fighter, cleric, mage, etc.):

                    reroll goblin skeleton      # Re-roll a goblin and a skeleton
                    reroll fighter              # Re-roll one fighter"""))

    def help_scale(self):
        """Display help for scale treasures."""
        print("""Scales are treasures that score 2 points per pair.""")

    def help_sword(self):
        """Display help for using sword treasures."""
        print("""Swords behave identically to a fighter.""")

    def help_talisman(self):
        """Display help for using talisman treasures."""
        print("""Talismans behave identically to a cleric.""")

    def help_thief(self):
        """Display help for using the thief hero."""
        print(textwrap.dedent(f"""\
            Thieves open ALL chests but only defeat ONE monster at a time:

                    thief chest                   # Open all chests
                    thief goblin                  # Defeat one goblin
                    thief skeleton                # Defeat one skeleton
                    thief ooze                    # Defeat one ooze
            {self.doc_potion_example.format("thief")}
            {self.doc_dragon_example.format("thief")}"""))

    def help_tools(self):
        """Display help for using tools treasures."""
        print("""Tools behave identically to a thief.""")

    def help_score(self):
        """Display help for the scoring system."""
        print(textwrap.dedent("""\
            Your score has two components: experience and treasure.

            Experience is earned by retiring from a delve.  When you retire,
            you gain experience equal to the depth you reached in the dungeon.
            For example, retiring at depth 5 earns 5 experience points.
            Retreating earns no experience.

            Town portals are worth 2 points each.  Scales score 1 point each,
            but every pair of scales scores 4 rather than 2, a +2 bonus per pair.
            Using a treasure during a delve removes it from your collection and
            reduces your score accordingly.

            Total score = experience + treasure points.
            See 'help treasure' for the full treasure list."""))

    def help_treasure(self):
        """Display help for the treasure system."""
        print(textwrap.dedent("""\
            Treasure is drawn randomly from a shared box whenever you open
            chests.  Each piece of treasure scores 1 point, with two exceptions:

                    sword       1   Usable as a fighter
                    talisman    1   Usable as a cleric
                    sceptre     1   Usable as a mage
                    tools       1   Usable as a thief
                    scroll      1   Usable as a scroll
                    elixir      1   Revive party members
                    bait        1   Lure the dragon
                    portal      2   Town portal to escape the dungeon
                    ring        1   Sneak past a dragon
                    scale       1   But a pair of scales scores 4"""))


def _tokenize(line: str) -> tuple[str, ...]:
    """Split a line into a tuple of whitespace-delimited tokens."""
    return tuple(line.split())


def _no_arguments(line: str) -> None:
    """Raise DrollError if line is non-empty.

    Strictness here prevents typos like 'retire goblin' from silently
    ignoring the extra argument, which would confuse the player."""
    if line:
        raise DrollError("Command accepts no arguments.")
