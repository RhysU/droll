# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""A REPL permitting playing a game via a tab-completion shell."""
import cmd
import random
import typing

from . import brief
from . import player
from . import world


# TODO Disable empty line repeating prior command
# TODO Suggest descend() after a level is completed
# TODO Display DrollErrors in a non-fatal manner
# TODO Tab complete all possibilities
# TODO Tab complete heros/monsters only when sensible
# TODO Tab complete only monsters left in the current level
# TODO Exit after all delves exhausted
# TODO Emit score after end of the game
# TODO Context-dependent help, in that only feasible options suggested
# TODO Context-dependent help, suggested whenever empty input received
# TODO Permit one-level of undo
# TODO Permit saving world state to file
# TODO Permit loading world state from file
# TODO Do not descend on new_delve to permit rerolling
# TODO Permit multiple players within a single shell?

# TODO ability
# TODO apply
# TODO descend
# TODO retire
# TODO retreat
# TODO score
# TODO treasure


class Shell(cmd.Cmd):
    """"FIXME"""

    def __init__(self, player=player.DEFAULT, randrange=None):
        super(Shell, self).__init__()
        self._player = player
        self._randrange = (random.Random().randrange
                           if randrange is None else randrange)
        self._world = None

    def preloop(self):
        w = world.new_game()
        w = world.new_delve(w, self._randrange)
        w = world.next_level(w, self._randrange)
        self._world = w
        self.__update_prompt()

    def postcmd(self, stop, line):
        print(brief(self._world))
        self.__update_prompt()
        return stop

    def __update_prompt(self):
        score = world.score(self._world) if self._world else 0
        self.prompt = '(droll {:-2d}) '.format(score)

    def do_EOF(self, line):
        print()
        return True


def parse(line: str) -> typing.Tuple[str]:
    """Split a line into a tuple of whitespace-delimited tokens."""
    return tuple(line.split())
