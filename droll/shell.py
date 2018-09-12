# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""A REPL permitting playing a game via a tab-completion shell."""
import cmd
import random
import typing

from . import brief
from . import error
from . import player
from . import world


# TODO "(droll  0) fighter" input is fatal
# TODO Accept constructor flag causing pdb on unexpected exception
# TODO Suggest descend() after a dungeon is completed
# TODO Exit after all delves exhausted
# TODO Emit score after end of the game
# TODO Context-dependent help, in that only feasible options suggested
# TODO Context-dependent help, suggested whenever empty input received
# TODO Context-dependent help, after hitting an empty line
# TODO Permit one-dungeon of undo
# TODO Exit after all delves completed


class Shell(cmd.Cmd):
    """"REPL permitting playing a game via tab-completion shell."""

    ##################
    # SETUP BELOW HERE
    ##################

    def __init__(self, *, player=player.DEFAULT, randrange=None):
        super(Shell, self).__init__()
        self._player = player
        self._randrange = (random.Random().randrange
                           if randrange is None else randrange)
        self._world = None

    def summary(self) -> str:
        """Brief, string description of the present game state."""
        return '(None)' if self._world is None else brief(self._world)

    def preloop(self):
        """Prepare a new game and start the first delve."""
        w = world.new_game()
        w = world.next_delve(w, self._randrange)
        self._world = w
        # Causes printing of initial world state
        self.postcmd(stop=False, line='')

    def postcmd(self, stop, line):
        """Print game state after each commmand."""
        print()
        if line != 'EOF':
            print(self.summary())
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

    def completenames(self, text, line, begidx, endidx):
        return (super(Shell, self).completenames(text, line, begidx, endidx) +
                self.completedefault(text, line, begidx, endidx))

    def completedefault(self, text, line, begidx, endidx):
        """Complete loosely based upon available heroes/treasures/dungeon."""
        # Break line into tokens until and starting from present text
        head = parse(line[:begidx])
        tail = parse(line[begidx:])

        # Bulk of processing elsewhere to simplify unit testing, and because
        # many exceptions silently suppress tab completion in readline.
        raw = player.complete(game=self._world,
                              tokens=head + tail,
                              text=text,
                              position=len(head))

        # Trailing space causes tab completion to insert token separators.
        return [x + ' ' for x in raw]


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
            self._world = world.next_delve(self._world, self._randrange)

    def do_retreat(self, line):
        """Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve, if possible."""
        with ShellManager():
            no_arguments(line)
            self._world = world.next_delve(self._world, self._randrange)


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
