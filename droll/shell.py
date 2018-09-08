# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""A REPL permitting playing a game via a tab-completion shell."""
import cmd
import itertools
import random
import typing

from . import brief
from . import error
from . import player
from . import world

# TODO Suggest descend() after a level is completed
# TODO Display DrollErrors in a non-fatal manner
# TODO Tab complete all possibilities
# TODO Tab complete heros/monsters only when sensible
# TODO Tab complete only monsters left in the current level
# TODO Exit after all delves exhausted
# TODO Emit score after end of the game
# TODO Context-dependent help, in that only feasible options suggested
# TODO Context-dependent help, suggested whenever empty input received
# TODO Context-dependent help, after hitting an empty line
# TODO Permit one-level of undo
# TODO Permit saving world state to file
# TODO Permit loading world state from file
# TODO Do not descend on new_delve to permit rerolling
# TODO Permit multiple players within a single shell?


_NOUNS = list(sorted(itertools.chain(
    world.Level._fields,
    world.Party._fields,
    world.Treasure._fields,
)))


class Shell(cmd.Cmd):
    """"FIXME"""

    ##################
    # SETUP BELOW HERE
    ##################

    def __init__(self, player=player.DEFAULT, randrange=None):
        super(Shell, self).__init__()
        self._player = player
        self._randrange = (random.Random().randrange
                           if randrange is None else randrange)
        self._world = None

    def preloop(self):
        """Prepare a new game, delve, and level."""
        w = world.new_game()
        w = world.new_delve(w, self._randrange)
        w = world.next_level(w, self._randrange)
        self._world = w
        # Causes printing of initial world state
        self.postcmd(stop=False, line='')

    def postcmd(self, stop, line):
        """Print game state after each commmand."""
        print(brief(self._world))
        self._update_prompt()
        return stop

    def _update_prompt(self):
        """Compute a prompt including the current score."""
        score = world.score(self._world) if self._world else 0
        self.prompt = '(droll {:-2d}) '.format(score)

    def do_EOF(self, line):
        """End-of-file causes shell exit."""
        print()
        return True

    def emptyline(self):
        """Empty line causes no action to occur."""
        pass

    def _completenouns(self, text):
        return [i for i in _NOUNS if i.startswith(text)]

    def completenames(self, text, *ignored):
        return (super(Shell, self).completenames(text, *ignored) +
                self._completenouns(text))

    ####################
    # ACTIONS BELOW HERE
    ####################

    def do_ability(self, line):
        """Invoke the player's ability."""
        with ShellManager():
            raise error.DrollError("NotYetImplemented")

    def default(self, line):
        """Apply some named hero or treasure to some collection of nouns."""
        with ShellManager():
            self._world = player.apply(
                self._player, self._world, self._randrange, *parse(line))

    def do_descend(self, line):
        """Descend to the next level (in contrast to retiring)."""
        with ShellManager():
            no_arguments(line)
            self._world = world.next_level(self._world, self._randrange)

    def do_retire(self, line):
        """Retire from the dungeon after successfully completing a level.

        Automatically starts a new delve, if possible."""
        with ShellManager():
            no_arguments(line)
        try:
            self._world = world.new_delve(self._world, self._randrange)
            self._world = world.next_level(self._world, self._randrange)
        except error.DrollError:
            pass

    def do_retreat(self, line):
        """Retreat from the level at any time (e.g. after being defeated).

        Automatically starts a new delve, if possible."""
        with ShellManager():
            no_arguments(line)
        try:
            self._world = world.new_delve(self._world, self._randrange)
            self._world = world.next_level(self._world, self._randrange)
        except error.DrollError:
            pass


class ShellManager:
    """Print DrollErrors while propagating other exceptions."""

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, error.DrollError):
            print(exc_val)
            return True


def parse(line: str) -> typing.Tuple[str]:
    """Split a line into a tuple of whitespace-delimited tokens."""
    return tuple(line.split())


def no_arguments(line):
    """Raise DrollError if line is non-empty."""
    if line:
        raise error.DrollError('Command accepts no arguments.')
