# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command-line version of droll."""
import argparse
import random
import sys

from .shell import Shell


def main(args=None):
    parser = argparse.ArgumentParser(prog='droll', description=__doc__)
    parser.add_argument('--seed', metavar='N', type=int, nargs=1, default=None,
                        help='an integer to seed random number generation')
    arguments = parser.parse_args(args)
    randseed = arguments.seed if arguments.seed else ()
    randrange = random.Random(*randseed).randrange
    s = Shell(randrange=randrange)
    s.cmdloop()


# TODO Permit specifying different players
# TODO Picking up the random seed could be much simpler
if __name__ == '__main__':
    main(sys.argv[1:])
