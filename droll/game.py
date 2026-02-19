# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tracks details associated with a playable game."""
from __future__ import annotations

import collections.abc
import copy
import enum
from random import Random

from .error import DrollError
from . import player
from . import struct
from . import world

__all__ = (
    "Game",
    "GameState",
)


class GameState(enum.Enum):
    """Game should STOP or one can still PLAY?"""

    STOP = 0
    PLAY = 1

    def __bool__(self):
        """All non-STOP states coerce to False.

        Inverted so STOP is truthy and PLAY is falsy because cmd.Cmd.cmdloop
        stops its loop when postcmd returns a truthy value.  Shell.postcmd
        passes through the GameState returned by each do_XXX handler, so
        STOP must be truthy to signal loop termination."""
        return self.value == self.STOP.value


class Game:
    """Tracks all state associated with a programmatically driven game."""

    def __init__(
        self,
        player: struct.Player = player.Default,
        random: Random | None = None,
    ) -> None:
        """Initialize a new game with the specified player and random number generator."""
        self._player = player
        self._random = Random() if random is None else copy.copy(random)
        self._world = world.new_world()
        if self._next_delve() != GameState.PLAY:
            raise RuntimeError("Unexpected GameState during constructor()")

    def __eq__(self, other) -> bool:
        """Is other equivalent to self?"""
        return (
            isinstance(other, Game)
            and self._player == other._player
            and self._world == other._world
            and self.randhash() == other.randhash()
        )

    def __copy__(self):
        """Shallow copy sharing frozen dataclass fields, copying random state."""
        new = object.__new__(type(self))
        new._player = self._player  # Frozen dataclass, safe to share
        new._world = self._world  # Frozen dataclass, safe to share
        new._random = copy.copy(self._random)  # Mutable, needs state copy
        return new

    def randhash(self) -> int:
        """Hash of the current random state."""
        return hash(self._random.getstate())

    def _next_delve(self) -> GameState:
        """Either start next delve or complete this game."""
        try:
            # Record any world updates
            self._world = world.delve(
                self._world, self._player.roll.party, self._random.randrange
            )
            # Permit the player to advance to higher abilities
            self._player = self._player.advance(self._world)
            return GameState.PLAY
        except DrollError:
            return GameState.STOP

    @property
    def player_name(self) -> str:
        """The name of the current player/hero."""
        return self._player.name

    @property
    def ability_doc(self) -> str:
        """The docstring of the current player's ability."""
        return self._player.ability.__doc__

    @property
    def current_world(self) -> struct.World:
        """The current world state (read-only frozen dataclass)."""
        return self._world

    def summary(self) -> str:
        """Brief, string description of the world."""
        return struct.brief(self._world)

    def score(self) -> int:
        """The current score for the world."""
        return world.score(self._world)

    def prompt(self) -> str:
        """A prompt-like string including the player name and score."""
        return f"({self._player.name} {self.score():-2d})"

    def ability(self, *args: str) -> GameState:
        """Invoke the player's ability."""
        self._world = player.apply(
            self._player, self._world, self._random.randrange, "ability", *args
        )
        return GameState.PLAY

    def apply(self, *args: str) -> GameState:
        """Apply some named hero or treasure to some collection of nouns."""
        self._world = player.apply(
            self._player, self._world, self._random.randrange, *args
        )
        return GameState.PLAY

    def descend(self) -> GameState:
        """Descend to the next depth (in contrast to retiring/retreating)."""
        self._world = world.descend(
            self._world, self._player.roll.dungeon, self._random.randrange
        )
        return GameState.PLAY

    def reroll(self, *args: str) -> GameState:
        """Reroll any number of party or dungeon dice by consuming a scroll."""
        # Reroll implemented in player.apply(...) because close to apply(...)
        # except for fact that it does not name a hero die as initial token.
        self._world = player.apply(
            self._player, self._world, self._random.randrange, "reroll", *args
        )
        return GameState.PLAY

    def retire(self) -> GameState:
        """Retire to the tavern after successfully clearing a dungeon depth.

        Automatically uses a 'ring' or 'portal' treasure if so required.
        Automatically starts a new delve or ends game, as suitable."""
        self._world = world.retire(self._world)
        return self._next_delve()

    def retreat(self) -> GameState:
        """Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve or ends game, as suitable."""
        self._world = world.retreat(self._world)
        return self._next_delve()

    def _possible_world_actions(self) -> list[str]:
        """Determine which world-level actions can currently succeed."""
        possible = []
        if self._world.ability:
            possible.append("ability")
        for name, action in (
            (
                "descend",
                lambda: world.descend(
                    self._world, self._player.roll.dungeon, _dummy_randrange
                ),
            ),
            ("retire", lambda: world.retire(self._world)),
            ("retreat", lambda: world.retreat(self._world)),
        ):
            try:
                action()
                possible.append(name)
            except DrollError:
                pass
        return possible

    def completenames(
        self,
        text: str,
        head: collections.abc.Sequence[str],
        tail: collections.abc.Sequence[str],
    ) -> collections.abc.Sequence[str]:
        """Complete possible command names based upon context."""
        results = [
            x for x in self._possible_world_actions() if x.startswith(text)
        ]
        if not world.exhausted_dungeon(self._world.dungeon):
            results += self.completedefault(text, head, tail)
        return results

    def completedefault(
        self,
        text: str,
        head: collections.abc.Sequence[str],
        tail: collections.abc.Sequence[str],
    ) -> collections.abc.Sequence[str]:
        """Complete loosely based upon available heroes/treasures/dungeon."""
        return player.complete(
            world=self._world,
            tokens=head + tail,
            text=text,
            position=len(head),
        )


def _dummy_randrange(start, stop=None):
    """Non-random pseudorandom generator so that completion is stateless."""
    return start
