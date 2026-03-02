# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for the compact display module."""

from droll import display
from droll import struct


def test_format_items_multiple_items():
    """Test formatting party with multiple quantities uses × notation."""
    party = struct.Party(fighter=2, cleric=1, mage=3)
    assert display._format_items(party) == "fighter×2 cleric mage×3"


def test_format_items_dragon_always_shows_count():
    """Test that dragons always display with count, even when singular."""
    dungeon = struct.Dungeon(dragon=1)
    assert display._format_items(dungeon) == "dragon×1"


def test_format_treasure_multiple_items_alphabetized():
    """Test multiple treasure items are alphabetized and use × notation."""
    artifacts = struct.Artifacts(scale=4, sceptre=1, talisman=1, tools=1)
    assert (
        display._format_treasure(artifacts) == "scale×4 sceptre talisman tools"
    )


def test_format_available_alphabetized():
    """Test available commands are displayed in alphabetical order."""
    available = ["retreat", "ability", "reroll"]
    assert display._format_available(available) == "ability reroll retreat"


def test_format_available_with_deltas():
    """Test available commands show score deltas when provided."""
    available = ["retreat", "ability", "retire"]
    deltas = {"retire": 3, "retreat": 0}
    assert (
        display._format_available(available, deltas)
        == "ability retire(+3xp) retreat(+0xp)"
    )


def test_format_available_negative_delta():
    """Test retire shows negative delta when portal consumed at low depth."""
    available = ["retire", "retreat"]
    deltas = {"retire": -1, "retreat": 0}
    assert display._format_available(available, deltas) == "retire(-1xp) retreat(+0xp)"


def test_format_dungeon_empty():
    """Test formatting empty dungeon returns None (line omitted)."""
    dungeon = struct.Dungeon()
    assert display._format_dungeon(dungeon) is None


def test_format_dungeon_with_monsters():
    """Test formatting dungeon with monsters."""
    dungeon = struct.Dungeon(goblin=1, skeleton=2)
    assert display._format_dungeon(dungeon) == "goblin skeleton×2"


def test_compact_summary_in_dungeon():
    """Test compact summary while in a dungeon with monsters."""
    world = struct.World(
        delve=1,
        depth=3,
        experience=0,
        dungeon=struct.Dungeon(goblin=1, skeleton=2, ooze=2),
        party=struct.Party(fighter=1, champion=1),
        ability=True,
        treasure=struct.Treasure(own=struct.Artifacts(talisman=1)),
    )
    result = display.compact_summary(
        world, "Default", 1, ["ability", "retreat"]
    )
    lines = result.split("\n")
    assert len(lines) == 5
    assert "depth 3 in delve 1 with 0xp" in lines[0]
    assert "talisman" in lines[1]
    assert "ability retreat" in lines[2]
    assert "fighter champion" in lines[3]
    assert "goblin skeleton×2 ooze×2" in lines[4]


def test_compact_summary_long_player_name_alignment():
    """Test that long player names maintain proper column alignment."""
    world = struct.World(
        delve=2,
        depth=0,
        experience=5,
        dungeon=None,
        party=struct.Party(fighter=1, cleric=2, mage=3, champion=1),
        ability=True,
        treasure=struct.Treasure(own=struct.Artifacts(talisman=1)),
    )
    result = display.compact_summary(
        world, "DragonSlayer", 6, ["ability", "descend"]
    )
    lines = result.split("\n")
    # Check that alignment matches DragonSlayer> width (13 chars)
    for line in lines:
        colon_pos = line.index(":")
        content_start = colon_pos + 1
        while content_start < len(line) and line[content_start] == " ":
            content_start += 1
        # Content should start at same column for all lines
        assert content_start >= 13


def test_compact_summary_dungeon_omitted_when_empty():
    """Test that empty dungeons omit the Dungeon line from the summary."""
    world = struct.World(
        delve=1,
        depth=1,
        experience=0,
        dungeon=struct.Dungeon(),
        party=struct.Party(fighter=1, cleric=1),
        ability=True,
        treasure=struct.Treasure(own=struct.Artifacts()),
    )
    result = display.compact_summary(
        world, "Knight", 0, ["ability", "descend", "retire"]
    )
    lines = result.split("\n")
    assert len(lines) == 4
    assert "Dungeon:" not in result


def test_compact_summary_cleared_level_10():
    """Test compact summary after clearing dungeon level 10."""
    world = struct.World(
        delve=3,
        depth=10,
        experience=16,
        dungeon=struct.Dungeon(),
        party=struct.Party(champion=1, scroll=2),
        ability=False,
        treasure=struct.Treasure(
            own=struct.Artifacts(scale=4, sceptre=1, talisman=1, tools=1)
        ),
    )
    result = display.compact_summary(world, "Beguiler", 24, ["retire"])
    lines = result.split("\n")
    assert "depth 10 in delve 3 with 16xp" in lines[0]
    assert "scale×4 sceptre talisman tools" in lines[1]
    assert "retire" in lines[2]
    assert "champion scroll×2" in lines[3]
    assert "Dungeon:" not in result
    assert len(lines) == 4


def test_compact_summary_ending_state():
    """After final delve, Available should show 'None'."""
    world = struct.World(
        delve=3,
        experience=16,
        dungeon=None,
        party=struct.Party(champion=1),
        ability=False,
        treasure=struct.Treasure(
            own=struct.Artifacts(scroll=1, elixir=1, bait=2, portal=1, scale=1)
        ),
    )
    result = display.compact_summary(world, "DragonSlayer", 23, [])
    lines = result.split("\n")
    assert "delve 3 with 16xp" in lines[0]
    assert "Consider:" in lines[2]
    assert "None" in lines[2]
    assert len(lines) == 4  # No Dungeon line
