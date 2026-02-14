# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for HalfGoblin/Chieftain hero abilities."""

import random
import unittest

import droll.error
import droll.struct
from droll.heroes.halfgoblin import (
    Chieftain,
    HalfGoblin,
    _chieftain_ability,
    _halfgoblin_ability,
)


class TestHalfGoblin(unittest.TestCase):

    def test_halfgoblin_transforms_goblin_to_thief(self):
        """HalfGoblin transforms 1 goblin into 1 thief."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _halfgoblin_ability(
            world, state.randrange, "ability", "goblin"
        )
        # Discard during subsequent regroup phase tested elsewhere
        assert result.dungeon.goblin == 1
        assert result.party.thief == 1
        assert result.ability is False

    def test_chieftain_transforms_two_monsters(self):
        """Chieftain transforms 2 goblins into 2 thieves when available."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _chieftain_ability(
            world, state.randrange, "ability", "goblin", "goblin"
        )
        # Discard during subsequent regroup phase tested elsewhere
        assert result.dungeon.goblin == 0
        assert result.dungeon.skeleton == 1
        assert result.party.thief == 2

    def test_chieftain_transforms_two_monsters(self):
        """Chieftain transforms 1 goblin into 1 thieves when 1 available."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _chieftain_ability(
            world, state.randrange, "ability", "goblin",
        )
        # Discard during subsequent regroup phase tested elsewhere
        assert result.dungeon.goblin == 0
        assert result.dungeon.skeleton == 1
        assert result.party.thief == 1

    def test_halfgoblin_advances_to_chieftain(self):
        """HalfGoblin advances to Chieftain at 5+ experience."""
        low_xp = droll.struct.World(
            delve=1,
            depth=0,
            experience=4,
            ability=True,
            dungeon=None,
            party=None,
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        high_xp = droll.struct.World(
            delve=1,
            depth=0,
            experience=5,
            ability=True,
            dungeon=None,
            party=None,
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        assert HalfGoblin.advance(low_xp) == HalfGoblin
        assert HalfGoblin.advance(high_xp) == Chieftain
