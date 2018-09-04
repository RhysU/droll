# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Top-level entry point for playing a game via IPython shell.

Specifically, state is mutated and string representations aid tracking state."""
import random
import typing

import droll.error
import droll.player
import droll.world


class Interactive:
    """Tracking of state associated with a single game."""

    def __init__(self, player=droll.player.DEFAULT, randrange=None):
        self._player = player
        self._randrange = (random.Random().randrange
                           if randrange is None else randrange)
        self._world = droll.world.new_game()
        self._world = droll.world.new_delve(self._world, self._randrange)
        self._world = droll.world.next_level(self._world, self._randrange)

    def ability(self, *nouns) -> 'Droll':
        """Invoke the player's ability."""
        raise NotImplementedError("FIXME")
        return self

    def apply(self, hero, *nouns) -> 'Droll':
        """Apply some named hero or treasure to some collection of nouns."""
        self._world = droll.player.apply(
            self._player, self._world, self._randrange, hero, *nouns)
        return self

    def descend(self) -> 'Droll':
        """Descend to the next level (in contrast to retiring."""
        self._world = droll.world.next_level(self._world, self._randrange)
        return self

    def retire(self) -> 'Droll':
        """Retire from the dungeon after successfully completing a level.

        Automatically starts a new delve, if possible."""
        self._world = droll.world.retire(self._world)
        try:
            self._world = droll.world.new_delve(self._world, self._randrange)
            self._world = droll.world.next_level(self._world, self._randrange)
        except droll.error.DrollError:
            pass
        return self

    def retreat(self) -> 'Droll':
        """Retreat from the level at any time (e.g. after being defeated).

        Automatically starts a new delve, if possible."""
        try:
            self._world = droll.world.new_delve(self._world, self._randrange)
            self._world = droll.world.next_level(self._world, self._randrange)
        except droll.error.DrollError:
            pass
        return self

    def score(self) -> int:
        """Compute current game score."""
        return droll.world.score(self._world)

    def treasure(self, treasure, *nouns) -> 'Droll':
        """Apply some named treasure to some collection of nouns.."""
        raise NotImplementedError("FIXME")
        return self

    def _repr_pretty_(self, p, cycle=False):
        """Print per IPython.lib.pretty to ease observing world changes."""
        assert not cycle
        p.text(pretty(self._world))


def pretty(o: typing.Any, *, omitted: typing.Set[str] = {'reserve'}) -> str:
    """A __str__(...) variant suppressing False fields within namedtuples."""
    fields = getattr(o, '_fields', None)
    if fields is None:
        return str(o)

    keyvalues = []
    for field, value in zip(fields, o):
        if value and not field in omitted:
            keyvalues.append('{}={}'.format(field, pretty(value)))
    return '({})'.format(', '.join(keyvalues))
