# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command-line version of droll."""
import argparse
import random
import sys

from .heroes import KNOWN
from .shell import Shell


def main(args=None):
    parser = argparse.ArgumentParser(prog='droll', description=__doc__)
    parser.add_argument('hero', choices=KNOWN.keys(),
                        help='Select the hero for this game.')
    parser.add_argument('--seed', metavar='N', type=int, nargs=1, default=None,
                        help='An integer to seed random number generation.')
    arguments = parser.parse_args(args)
    randseed = arguments.seed if arguments.seed else ()
    randrange = random.Random(*randseed).randrange
    s = Shell(randrange=randrange, player=KNOWN.get(arguments.hero))
    s.cmdloop()


if __name__ == '__main__':
    main(sys.argv[1:])
