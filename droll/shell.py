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

# TODO Accept constructor flag causing pdb on unexpected exception
# TODO Suggest descend() after a dungeon is completed
# TODO Tab complete heros/monsters only when sensible
# TODO Tab complete only monsters left in the current dungeon
# TODO Exit after all delves exhausted
# TODO Emit score after end of the game
# TODO Context-dependent help, in that only feasible options suggested
# TODO Context-dependent help, suggested whenever empty input received
# TODO Context-dependent help, after hitting an empty line
# TODO Permit one-dungeon of undo
# TODO Permit saving world state to file
# TODO Permit loading world state from file
# TODO Do not descend on new_delve to permit rerolling
# TODO Permit multiple players within a single shell?


# Trailing space causes tab completion to insert token separators
_NOUNS = list(i + ' ' for i in sorted(itertools.chain(
    world.Dungeon._fields,
    world.Party._fields,
    world.Treasure._fields,
)))


class Shell(cmd.Cmd):
    """"REPL permitting playing a game via tab-completion shell."""

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
        """Prepare a new game, delve, and dungeon."""
        w = world.new_game()
        w = world.new_delve(w, self._randrange)
        w = world.next_dungeon(w, self._randrange)
        self._world = w
        # Causes printing of initial world state
        self.postcmd(stop=False, line='')

    def postcmd(self, stop, line):
        """Print game state after each commmand."""
        print()
        if line != 'EOF':
            print(brief(self._world))
        self._update_prompt()
        return stop

    def _update_prompt(self):
        """Compute a prompt including the current score."""
        score = world.score(self._world) if self._world else 0
        self.prompt = '(droll {:-2d}) '.format(score)

    def do_EOF(self, line):
        """End-of-file causes shell exit."""
        return True

    def emptyline(self):
        """Empty line causes no action to occur."""
        pass

    def completenames(self, text, *ignored):
        return (super(Shell, self).completenames(text, *ignored) +
                [i for i in _NOUNS if i.startswith(text)])

    def completedefault(self, text, line, begidx, endidx):
        return [i for i in _NOUNS if i.startswith(text)]

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
        """Descend to the next dungeon (in contrast to retiring)."""
        with ShellManager():
            no_arguments(line)
            self._world = world.next_dungeon(self._world, self._randrange)

    def do_retire(self, line):
        """Retire from the dungeon after successfully completing a dungeon.

        Automatically starts a new delve, if possible."""
        with ShellManager():
            no_arguments(line)
            self._world = world.retire(self._world)
            self._world = world.new_delve(self._world, self._randrange)
            self._world = world.next_dungeon(self._world, self._randrange)

    def do_retreat(self, line):
        """Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve, if possible."""
        with ShellManager():
            no_arguments(line)
            self._world = world.new_delve(self._world, self._randrange)
            self._world = world.next_dungeon(self._world, self._randrange)


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
