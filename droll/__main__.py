# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command-line version of droll."""
import argparse
import collections
import random
import sys

from .game import Game
from .display import DisplayMode
from .heroes import (
    Crusader,
    Enchantress,
    HalfGoblin,
    Knight,
    Minstrel,
    Occultist,
    Spellsword,
)
from .player import Default
from .shell import Shell

AVAILABLE_HEROES = collections.OrderedDict(
    [
        ("Default", Default),
        ("Crusader", Crusader),
        ("Enchantress", Enchantress),
        ("HalfGoblin", HalfGoblin),
        ("Knight", Knight),
        ("Minstrel", Minstrel),
        ("Occultist", Occultist),
        ("Spellsword", Spellsword),
    ]
)


def main(args=None) -> None:
    """Run the droll command-line game with the specified hero and options."""
    parser = argparse.ArgumentParser(prog="droll", description=__doc__)
    parser.add_argument(
        "hero",
        choices=AVAILABLE_HEROES.keys(),
        help="Select the hero for this game.",
    )
    parser.add_argument(
        "--seed",
        metavar="N",
        type=int,
        default=None,
        help="An integer to seed random number generation.",
    )
    parser.add_argument(
        "--mechanical",
        action="store_true",
        help="Use mechanical verbose display format.",
    )
    arguments = parser.parse_args(args)
    rng = random.Random() if arguments.seed is None else random.Random(arguments.seed)
    g = Game(
        player=AVAILABLE_HEROES[arguments.hero],
        random=rng,
    )
    display_mode = (
        DisplayMode.MECHANICAL if arguments.mechanical else DisplayMode.CURRENT
    )
    s = Shell(g, display_mode=display_mode)
    return s.cmdloop()


if __name__ == "__main__":
    main(sys.argv[1:])
