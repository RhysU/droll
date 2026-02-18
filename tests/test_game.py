# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of Game (at least driving with basic commands)."""

from dataclasses import replace
import random
import pytest

from droll import struct
from droll.error import DrollError
from droll.game import Game, GameState
from droll.player import Default


def test_game_construction():
    """Game can be constructed with various parameter combinations."""
    Game()
    Game(player=Default)
    Game(random=random.Random(4))


def test_gamestate_truthiness():
    """GameState values coerce to boolean correctly for control flow."""
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
        dungeon=struct.Dungeon(goblin=2),
    )
    pre_scroll = g._world.party.scroll
    g.reroll("goblin")
    # Scroll consumed, dungeon rerolled
    assert g._world.party.scroll == pre_scroll - 1


def test_reroll_portion():
    """Test rerolling potion using a scroll."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()  # Start delve
    # Set up dungeon with goblin and party with scroll
    g._world = replace(
        g._world,
        depth=1,
        party=replace(g._world.party, scroll=1),
        dungeon=struct.Dungeon(potion=2),
    )
    pre_scroll = g._world.party.scroll
    g.reroll("potion")
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
        dungeon=struct.Dungeon(goblin=1, skeleton=1),
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


def test_retreat():
    """Game.retreat() retreats from dungeon and starts next delve."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    # Place a monster so retreat is valid (can't retreat from cleared dungeon)
    g._world = replace(g._world, dungeon=struct.Dungeon(goblin=1))
    result = g.retreat()
    assert result == GameState.PLAY
    # After retreat, a new delve should have started
    assert g._world.depth == 0
    assert g._world.party is not None


def test_completenames():
    """completenames returns contextual completions including retire/retreat."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()

    # With monsters: retreat is possible, retire is not
    g._world = replace(g._world, dungeon=struct.Dungeon(goblin=1))
    names = g.completenames(text="", head=[], tail=[])
    assert "ability" in names
    assert "retreat" in names
    assert "retire" not in names
    # Hero-related completions appear (dungeon not exhausted)
    assert any(
        n not in ("ability", "descend", "retire", "retreat") for n in names
    )

    # With cleared dungeon: retire is possible
    g._world = replace(g._world, dungeon=struct.Dungeon())
    names = g.completenames(text="", head=[], tail=[])
    assert "retire" in names


def test_completedefault():
    """completedefault delegates to player.complete."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(
        g._world,
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(fighter=1),
    )
    results = g.completedefault(text="fi", head=[], tail=[])
    assert "fighter" in results


def test_next_delve_returns_stop_after_three():
    """Game returns STOP when no more delves remain."""
    g = Game(random=random.Random(4), player=Default)
    # Play through 3 delves by retiring from each
    for _ in range(2):
        g.descend()
        g._world = replace(g._world, dungeon=struct.Dungeon())
        result = g.retire()
        assert result == GameState.PLAY
    # Third delve: retire should trigger STOP
    g.descend()
    g._world = replace(g._world, dungeon=struct.Dungeon())
    result = g.retire()
    assert result == GameState.STOP
