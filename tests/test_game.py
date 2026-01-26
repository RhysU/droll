# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of Game (at least driving with basic commands)."""

import random
from dataclasses import replace

import pytest

from droll.error import DrollError
from droll.game import Game, GameState
from droll.player import Default
import droll.struct


def test_game_construction():
    Game()
    Game(player=Default)
    Game(random=random.Random(4))


def test_gamestate_truthiness():
    assert GameState.STOP, "STOP must coerce to True."
    assert not GameState.PLAY, "PLAY must coerce to False."


def test_reroll_dungeon_dice():
    """Test rerolling dungeon dice using a scroll."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()  # Start delve
    # Set up dungeon with goblin and party with scroll
    g._world = replace(
        g._world,
        depth=1,
        party=replace(g._world.party, scroll=1),
        dungeon=droll.struct.Dungeon(goblin=2),
    )
    pre_scroll = g._world.party.scroll
    g.reroll("goblin")
    # Scroll consumed, dungeon rerolled
    assert g._world.party.scroll == pre_scroll - 1


def test_reroll_multiple_targets():
    """Test rerolling multiple dungeon dice."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(
        g._world,
        depth=1,
        party=replace(g._world.party, scroll=1),
        dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
    )
    g.reroll("goblin", "skeleton")
    assert g._world.party.scroll == 0


def test_apply_portal_directly_fails():
    """Test that using portal directly gives helpful error."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(
        g._world,
        treasure=replace(g._world.treasure, portal=1),
    )
    with pytest.raises(DrollError):
        g.apply("portal")


def test_apply_ring_directly_fails():
    """Test that using ring directly gives helpful error."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(
        g._world,
        treasure=replace(g._world.treasure, ring=1),
    )
    with pytest.raises(DrollError):
        g.apply("ring")
