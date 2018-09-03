# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Top-level entry point for playing a game via IPython shell.

Specifically, state is mutated and string representations aid tracking state."""
import random
import typing

import droll.player
import droll.world


class Interactive:
    def __init__(self, player=droll.player.DEFAULT, randrange=None):
        self._player = player
        self._randrange = (random.Random().randrange
                           if randrange is None else randrange)
        self._world = droll.world.new_game()
        self._world = droll.world.new_delve(self._world, self._randrange)
        self._world = droll.world.next_level(self._world, self._randrange)

    def score(self) -> int:
        return droll.world.score(self._world)

    def hero(self, *nouns) -> 'Droll':
        self._world = droll.player.apply(
            self._player, self._world, self._randrange, *nouns)
        return self

    def retire(self) -> 'Droll':
        self._world = droll.world.retire(self._world)
        return self

    def retreat(self) -> 'Droll':
        self._world = droll.world.new_delve(self._world, self._randrange)
        return self

    def treasure(self, *nouns) -> 'Droll':
        raise NotImplementedError("FIXME")
        return self

    def ability(self, *nouns) -> 'Droll':
        raise NotImplementedError("FIXME")
        return self

    def __str__(self) -> str:
        """Short representation eases manually observing world changes."""
        return brief(self._world)


def brief(o: typing.Any) -> str:
    """A __str__(...) variant suppressing False fields within namedtuples."""
    fields = getattr(o, '_fields', None)
    if fields is None:
        return str(o)

    keyvalues = []
    for field, value in zip(fields, o):
        if value:
            keyvalues.append('{}={}'.format(field, brief(value)))
    return '{}({})'.format(o.__class__.__name__, ', '.join(keyvalues))
