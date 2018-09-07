# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""A REPL permitting playing a game via a tab-completion shell."""
import cmd
import random
import typing

import droll.error
import droll.player
import droll.world


# TODO Initialize superclass, including stdin/stdout
# TODO Initialize on starting loop
# TODO Pretty print state of world after each command
# TODO Properly handle EOF
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

    def __init__(self, player=droll.player.DEFAULT, randrange=None):
        super(Shell, self).__init__()
        self.prompt = '(droll) '
        self._player = player
        self._randrange = (random.Random().randrange
                           if randrange is None else randrange)

    def preloop(self):
        self._world = droll.world.new_game()
        self._world = droll.world.new_delve(self._world, self._randrange)
        self._world = droll.world.next_level(self._world, self._randrange)

    # FIXME Not outputting score
    def postloop(self):
        score = droll.world.score((self._world))
        print("Score: ".format(score))

    def postcmd(self, stop, line):
        print(pretty(self._world))
        return stop

    def do_EOF(self, line):
        return True


def parse(line: str) -> typing.Tuple[str]:
    """Split a line into a tuple of whitespace-delimited tokens."""
    return tuple(line.split())


def pretty(o: typing.Any, *, omitted: typing.Set[str] = {'reserve'}) -> str:
    """A __str__(...) variant suppressing False fields within namedtuples."""
    fields = getattr(o, '_fields', None)
    if fields is None:
        return str(o)

    keyvalues = []
    for field, value in zip(fields, o):
        if value and field not in omitted:
            keyvalues.append('{}={}'.format(field, pretty(value)))
    return '({})'.format(', '.join(keyvalues))
