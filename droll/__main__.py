# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command-line version of droll."""
import argparse
import collections
import random
import sys

from .shell import Game
from .heroes import Knight, Minstrel, Spellsword
from .player import Default
from .shell import Shell

AVAILABLE_HEROES = collections.OrderedDict([
    ('Default', Default),
    ('Knight', Knight),
    ('Minstrel', Minstrel),
    ('Spellsword', Spellsword),
])


def main(args=None) -> None:
    parser = argparse.ArgumentParser(prog='droll', description=__doc__)
    parser.add_argument('hero', choices=AVAILABLE_HEROES.keys(),
                        help='Select the hero for this game.')
    parser.add_argument('--seed', metavar='N', type=int, nargs=1, default=None,
                        help='An integer to seed random number generation.')
    arguments = parser.parse_args(args)
    randseed = arguments.seed if arguments.seed else ()
    g = Game(player=AVAILABLE_HEROES.get(arguments.hero),
             random=random.Random(*randseed))
    s = Shell(g)
    return s.cmdloop()


if __name__ == '__main__':
    main(sys.argv[1:])
