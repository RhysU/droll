# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of Game (at least driving with basic commands)."""

from dataclasses import replace
import random
import pytest

from droll import struct
from droll.struct import DrollError
from droll.game import Game, GameState
from droll.player import Default


def test_game_repr():
    """Game has a meaningful repr showing player, score, delve, and depth."""
    g = Game(random=random.Random(4), player=Default)
    r = repr(g)
    assert r.startswith("Game(")
    assert "player=Default" in r
    assert "score=" in r
    assert "delve=" in r
    assert "depth=" in r


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
        treasure=replace(
            g._world.treasure, own=replace(g._world.treasure.own, portal=1)
        ),
    )
    with pytest.raises(DrollError):
        g.apply("portal")


def test_apply_ring_directly_fails():
    """Test that using ring directly gives helpful error."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(
        g._world,
        treasure=replace(
            g._world.treasure, own=replace(g._world.treasure.own, ring=1)
        ),
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
    """completenames returns contextual completions."""
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


def test_score_deltas_retire_cleared():
    """score_deltas returns +depth for retire with cleared dungeon."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(g._world, dungeon=struct.Dungeon())
    deltas = g.score_deltas()
    assert "retire" in deltas
    assert deltas["retire"] == g._world.depth


def test_score_deltas_retreat_with_monsters():
    """score_deltas returns 0 for retreat with monsters present."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(g._world, dungeon=struct.Dungeon(goblin=1))
    deltas = g.score_deltas()
    assert "retreat" in deltas
    assert deltas["retreat"] == 0


def test_score_deltas_retire_consumes_portal():
    """score_deltas accounts for portal consumption when monsters remain."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(
        g._world,
        depth=1,
        dungeon=struct.Dungeon(goblin=1),
        treasure=replace(
            g._world.treasure, own=replace(g._world.treasure.own, portal=1)
        ),
    )
    deltas = g.score_deltas()
    assert "retire" in deltas
    # depth 1 XP gained, but portal worth 2 is consumed: net -1
    assert deltas["retire"] == -1


def test_score_deltas_retire_nonzero():
    """Retire at depth 5 with cleared dungeon earns +5."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(g._world, depth=5, dungeon=struct.Dungeon())
    deltas = g.score_deltas()
    assert deltas["retire"] == 5


def test_score_deltas_retreat_nonzero():
    """Retreat with a portal earns depth XP minus portal cost."""
    g = Game(random=random.Random(4), player=Default)
    g.descend()
    g._world = replace(
        g._world,
        depth=5,
        dungeon=struct.Dungeon(goblin=1),
        treasure=replace(
            g._world.treasure, own=replace(g._world.treasure.own, portal=1)
        ),
    )
    deltas = g.score_deltas()
    # depth 5 XP gained, portal worth 2 consumed: net +3
    assert deltas["retreat"] == 3


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
