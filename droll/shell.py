# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""A REPL permitting playing a Game via a tab-completion shell."""
import cmd
import copy
import functools
import textwrap
import typing

from . import action
from .error import DrollError
from .game import Game, GameState


class Shell(cmd.Cmd):
    """"REPL permitting playing a Game via tab-completion shell."""

    def __init__(self, game: Game) -> None:
        super(Shell, self).__init__()
        assert game is not None
        self._game = game
        self._undo = None

    def preloop(self) -> None:
        """Prepare a new game and start the first delve."""
        assert self._undo is None, "Cannot call preloop(...) multiple times."
        self._undo = []
        self.postcmd(stop=False, line='')  # Prints initial world state

    def postcmd(self, stop, line) -> bool:
        """Print game state after each command and final details on exit."""
        self.prompt = self._game.prompt() + ' '
        print()
        if line != 'EOF':
            print(self._game.summary())
            if stop:
                print(self.prompt)
        return stop

    def onecmd(self, line, *, _raises=False) -> GameState:
        """Performs undo tracking whenever undo won't cause re-roll/re-draw."""
        # Track observable state before and after command processing.
        before = copy.deepcopy(self._game)  # TODO Simplify from deepcopy?
        try:
            result = GameState.PLAY
            result = super(Shell, self).onecmd(line)
        except DrollError as e:
            if _raises:
                raise
            print(*e.args)
            return result

        # Retain only undo candidates that disallow cheating.
        # Okay would be 'Oh! I should have used a fighter on the goblin!'
        # Not okay would be undoing a 'descend' to roll a different dungeon.
        if line == 'undo':
            pass  # Retaining undo operations would break multiple undos
        elif self._game == before:
            pass  # No change in state (e.g. help) so nothing to track
        elif self._game.randhash() == before.randhash():
            self._undo.append(before)  # Same random state so undo permitted
        else:
            self._undo.clear()  # Random state mutated so no under permitted

        return result

    def do_undo(self, line) -> GameState:
        """Undo prior commands.  Only permitted when nothing rolled/drawn."""
        no_arguments(line)
        if self._undo:
            # Assertion confirms onecmd(...) processing matches expectations
            assert self._game.randhash() == self._undo[-1].randhash()
            self._game = self._undo.pop()
        else:
            raise DrollError("Cannot undo any prior command(s).")
        return GameState.PLAY

    def do_EOF(self, line) -> GameState:
        """End-of-file causes shell exit."""
        return GameState.STOP

    def emptyline(self) -> GameState:
        """Empty line causes no action to occur."""
        return self.onecmd('help')

    ####################
    # ACTIONS BELOW HERE
    ####################

    @functools.wraps(Game.ability)
    def do_ability(self, line) -> GameState:
        return self._game.ability(*parse(line))

    @functools.wraps(Game.apply)
    def default(self, line) -> GameState:
        return self._game.apply(*parse(line))

    @functools.wraps(Game.descend)
    def do_descend(self, line) -> GameState:
        no_arguments(line)
        return self._game.descend()

    @functools.wraps(Game.retire)
    def do_retire(self, line) -> GameState:
        no_arguments(line)
        return self._game.retire()

    @functools.wraps(Game.retreat)
    def do_retreat(self, line) -> GameState:
        no_arguments(line)
        return self._game.retreat()

    #######################
    # COMPLETION BELOW HERE
    #######################

    def completedefault(self, text, line, begidx, endidx):
        # Break line into tokens until and starting from present text
        names = self._game.completenames(text=text,
                                         head=parse(line[:begidx]),
                                         tail=parse(line[begidx:]))
        if self._undo and 'undo'.startswith(text):
            names.append('undo')
        # Trailing space causes tab completion to insert token separators
        return [x + ' ' for x in names]

    def completenames(self, text, line, begidx, endidx):
        return self.completedefault(text, line, begidx, endidx)

    # Overrides superclass behavior relying purely on do_XXX(...) methods.
    # Also, lies that help_XXX(...) present for completedefault(...) methods.
    def get_names(self):
        """Compute potential help topics from contextual completions."""
        names = self._game.completenames(text='', head=[], tail=[])
        if self._undo:
            names.append('undo')
        return (['do_' + x for x in names] +
                ['help_' + x for x in names
                 if not getattr(self, 'do_' + x, None)])

    #################
    # HELP BELOW HERE
    #################

    doc_header = "Feasible commands (help <command>):"
    doc_hero_template = ("Attack monsters, quaff potions, and open chests"
                         " with a {} like so:")
    doc_hero_example = """
        champion skeleton            # Attack skeleton(s)
        thief chest                  # Open chest(s)
        fighter potion mage thief    # Drink 2 potions obtaining mage, thief
        mage dragon champion cleric  # Attack dragon with party of 3
    """

    def help_ability(self):
        print(self.do_ability.__doc__)
        print()
        print(textwrap.indent(self._player.ability.__doc__, '    '))

    def help_bait(self):
        print(action.bait_dragon.__doc__)

    def help_champion(self):
        print(self.doc_hero_template.format('champion'))
        print(self.doc_hero_example)

    def help_cleric(self):
        print(self.doc_hero_template.format('cleric'))
        print(self.doc_hero_example)

    def help_elixir(self):
        print(action.elixir.__doc__)

    def help_fighter(self):
        print(self.doc_hero_template.format('fighter'))
        print(self.doc_hero_example)

    def help_mage(self):
        print(self.doc_hero_template.format('mage'))
        print(self.doc_hero_example)

    def help_sceptre(self):
        print("""Sceptres behave identically to a mage.""")

    def help_scroll(self):
        print("Scrolls may quaff potions and re-roll dungeon dice like so:")
        print("""
            scroll potion mage thief    # Drink 2 potions obtaining mage, thief
            scroll skeleton goblin      # Re-roll all skeletons and goblins
        """)

    def help_sword(self):
        print("""Swords behave identically to a fighter.""")

    def help_talisman(self):
        print("""Talismans behave identically to a cleric.""")

    def help_thief(self):
        print(self.doc_hero_template.format('thief'))
        print(self.doc_hero_example)

    def help_tools(self):
        print("""Tools behave identically to a thief.""")


def parse(line: str) -> typing.Tuple[str]:
    """Split a line into a tuple of whitespace-delimited tokens."""
    return tuple(line.split())


def no_arguments(line):
    """Raise DrollError if line is non-empty."""
    if line:
        raise DrollError('Command accepts no arguments.')
