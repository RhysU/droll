# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tracks details associated with a playable game."""
import copy
import enum
import typing
from random import Random

from . import error
from . import player
from . import struct
from . import world


class GameState(enum.IntEnum):
    DONE = 0
    PLAY = 1


class Game:
    """Tracks all state associated with a programmatically driven game."""

    def __init__(
            self,
            player: struct.Player = player.Default,
            random: Random = None
    ) -> None:
        self._player = player
        self._random = Random() if random is None else copy.copy(random)
        self._world = world.new_world()
        if self._next_delve() != GameState.PLAY:
            raise RuntimeError('Unexpected GameState during constructor()')

    def _next_delve(self) -> GameState:
        """Either start next delve or complete this game."""
        try:
            # Record any world updates
            self._world = world.next_delve(self._world,
                                           self._player.roll.party,
                                           self._random.randrange)
            # Permit the player to advance to higher abilities
            self._player = self._player.advance(self._world)
            return GameState.PLAY
        except error.DrollError:
            return GameState.DONE

    def summary(self) -> str:
        """Brief, string description of the world."""
        return struct.brief(self._world)

    def score(self) -> int:
        """The current score for the world."""
        return world.score(self._world)

    def prompt(self) -> int:
        """A prompt-like string including the player name and score."""
        return '({} {:-2d})'.format(self._player.name, self.score())

    def ability(self, *args: str) -> GameState.PLAY:
        """Invoke the player's ability."""
        self._world = player.apply(self._player, self._world,
                                   self._random.randrange, 'ability',
                                   *args)
        return GameState.PLAY

    def apply(self, *args: str) -> GameState.PLAY:
        """Apply some named hero or treasure to some collection of nouns."""
        self._world = player.apply(self._player, self._world,
                                   self._random.randrange, *args)
        return GameState.PLAY

    def descend(self) -> GameState:
        """Descend to the next depth (in contrast to retiring/retreating)."""
        self._world = world.next_dungeon(self._world,
                                         self._player.roll.dungeon,
                                         self._random.randrange)
        return GameState.PLAY

    def retire(self) -> GameState:
        """Retire to the tavern after successfully clearing a dungeon depth..

        Automatically uses a 'ring' or 'portal' treasure if so required.
        Automatically starts a new delve or ends game, as suitable."""
        self._world = world.retire(self._world)
        return self._next_delve()

    def retreat(self) -> GameState:
        """Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve or ends game, as suitable."""
        self._world = world.retreat(self._world)
        return self._next_delve()

    def completenames(
            self,
            text: str,
            head: typing.Sequence[str],
            tail: typing.Sequence[str]
    ) -> typing.Sequence[str]:
        """Complete possible command names based upon context."""
        # Which world actions might be taken successfully given game state?
        possible = []
        if self._world.ability:
            possible.append('ability')
        try:
            world.next_dungeon(self._world,
                               self._player.roll.dungeon,
                               dummy_randrange)
            possible.append('descend')
        except error.DrollError:
            pass
        try:
            world.retire(self._world)
            possible.append('retire')
        except error.DrollError:
            pass
        try:
            world.retreat(self._world)
            possible.append('retreat')
        except error.DrollError:
            pass

        results = [x for x in possible if x.startswith(text)]

        # Add any hero-related possibilities
        if not world.exhausted_dungeon(self._world.dungeon):
            results += self.completedefault(text, head, tail)

        return results

    def completedefault(
            self,
            text: str,
            head: typing.Sequence[str],
            tail: typing.Sequence[str]
    ) -> typing.Sequence[str]:
        """Complete loosely based upon available heroes/treasures/dungeon."""
        return player.complete(game=self._world,
                               tokens=head + tail,
                               text=text,
                               position=len(head))


def dummy_randrange(start, stop=None):
    """Non-random psuedorandom generator so that completion is stateless."""
    return start
