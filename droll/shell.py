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


# TODO Populate all help topics
# TODO Populate intro


class Shell(cmd.Cmd):
    """"REPL permitting playing a game via tab-completion shell."""

    ######################
    # LIFECYCLE BELOW HERE
    ######################

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
        """Print game state after each commmand and final details on exit."""
        self._update_prompt()
        print()
        if line != 'EOF':
            print(self.summary())
            if stop:
                print(self.prompt)
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
        return self.onecmd('help')

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
        """Descend to the next depth (in contrast to retiring/retreating)."""
        with ShellManager():
            no_arguments(line)
            self._world = world.next_dungeon(self._world, self._randrange)

    def do_retire(self, line):
        """Retire to the tavern after successfully clearing a dungeon depth..

        Automatically uses a 'ring' or 'portal' treasure if so required.
        Automatically starts a new delve or ends game, as suitable."""
        with ShellManager():
            no_arguments(line)
            self._world = world.retire(self._world)
            return self._next_delve_or_exit()

    def do_retreat(self, line):
        """Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve or ends game, as suitable."""
        with ShellManager():
            no_arguments(line)
            self._world = world.retreat(self._world)
            return self._next_delve_or_exit()

    def _next_delve_or_exit(self) -> bool:
        """Either start next delve or exit the game, printing final score."""
        try:
            self._world = world.next_delve(self._world, self._randrange)
            return False
        except error.DrollError:
            return True

    #######################
    # COMPLETION BELOW HERE
    #######################

    def completenames(self, text, line, begidx, endidx):
        """Complete possible command names based upon context."""
        # Are any dungeon dice still active?  Distinct from defeating dungeon!
        # Distinct from exhausting dungeon-- could convert potions to dragon!
        dungeon_dice = sum(self._world.dungeon) if self._world.dungeon else 0

        # Which world actions might be taken successfully given game state?
        possible = []
        if self._world.ability and dungeon_dice:
            possible.append('ability')
        with ShellManager(verbose=False):
            world.next_dungeon(self._world, dummy_randrange)
            possible.append('descend')
        with ShellManager(verbose=False):
            world.retire(self._world)
            possible.append('retire')
        with ShellManager(verbose=False):
            world.retreat(self._world)
            possible.append('retreat')
        results = [x for x in possible if x.startswith(text)]

        # Add any hero-related possibilities
        if not world.exhausted_dungeon(self._world.dungeon):
            results += self.completedefault(text, line, begidx, endidx)

        return results

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

    #################
    # HELP BELOW HERE
    #################

    doc_header = "Feasible commands (help <command>):"

    # Overrides superclass behavior relying purely on do_XXX(...) methods.
    # Also, lies that help_XXX(...) present for completedefault(...) methods.
    def get_names(self):
        """Compute potential help topics from contextual completions."""
        names = self.completenames(text='', line='', begidx=0, endidx=0)
        return (['do_' + x for x in names] +
                ['help_' + x for x in names
                 if not getattr(self, 'do_' + x, None)])


class ShellManager:
    """Print DrollErrors (if verbose) while propagating other exceptions."""

    def __init__(self, verbose=True):
        self._verbose = verbose

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, error.DrollError):
            if self._verbose:
                print(exc_val)
            return True


def parse(line: str) -> typing.Tuple[str]:
    """Split a line into a tuple of whitespace-delimited tokens."""
    return tuple(line.split())


def no_arguments(line):
    """Raise DrollError if line is non-empty."""
    if line:
        raise error.DrollError('Command accepts no arguments.')


def dummy_randrange(start, stop=None):
    """Non-random psuedorandom generator so that completion is stateless."""
    return start
