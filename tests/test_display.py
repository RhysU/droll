# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for the compact display module."""

from droll import display
from droll import struct


class TestFormatItems:

    def test_multiple_items(self):
        """Test formatting party with multiple quantities uses × notation."""
        party = struct.Party(fighter=2, cleric=1, mage=3)
        assert display._format_items(party) == "fighter×2 cleric mage×3"

    def test_dragon_always_shows_count(self):
        """Test that dragons always display with count, even when singular."""
        dungeon = struct.Dungeon(dragon=1)
        assert display._format_items(dungeon) == "dragon×1"


class TestFormatTreasure:

    def test_multiple_items_alphabetized(self):
        """Test multiple treasure items are alphabetized and use × notation."""
        treasure = struct.Treasure(scale=4, sceptre=1, talisman=1, tools=1)
        assert (
            display._format_treasure(treasure)
            == "scale×4 sceptre talisman tools"
        )


class TestFormatAvailable:

    def test_alphabetized(self):
        """Test available commands are displayed in alphabetical order."""
        available = ["retreat", "ability", "reroll"]
        assert display._format_available(available) == "ability reroll retreat"


class TestFormatDungeon:

    def test_empty_dungeon(self):
        """Test formatting empty dungeon returns 'None' string."""
        dungeon = struct.Dungeon()
        assert display._format_dungeon(dungeon) == "None"

    def test_with_monsters(self):
        """Test formatting dungeon with monsters."""
        dungeon = struct.Dungeon(goblin=1, skeleton=2)
        assert display._format_dungeon(dungeon) == "goblin skeleton×2"


class TestCompactSummary:

    def test_in_dungeon(self):
        """Test compact summary while in a dungeon with monsters."""
        world = struct.World(
            delve=1,
            depth=3,
            experience=0,
            dungeon=struct.Dungeon(goblin=1, skeleton=2, ooze=2),
            party=struct.Party(fighter=1, champion=1),
            ability=True,
            treasure=struct.Treasure(talisman=1),
        )
        result = display.compact_summary(
            world, "Default", 1, ["ability", "retreat"]
        )
        lines = result.split("\n")
        assert len(lines) == 5
        assert "depth 3 in delve 1 with experience 0" in lines[0]
        assert "talisman" in lines[1]
        assert "ability retreat" in lines[2]
        assert "fighter champion" in lines[3]
        assert "goblin skeleton×2 ooze×2" in lines[4]

    def test_long_player_name_alignment(self):
        """Test that long player names maintain proper column alignment."""
        world = struct.World(
            delve=2,
            depth=0,
            experience=5,
            dungeon=None,
            party=struct.Party(fighter=1, cleric=2, mage=3, champion=1),
            ability=True,
            treasure=struct.Treasure(talisman=1),
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

    def test_dungeon_shown_when_empty(self):
        """Test that empty dungeons display 'Dungeon: None' in the summary."""
        world = struct.World(
            delve=1,
            depth=1,
            experience=0,
            dungeon=struct.Dungeon(),
            party=struct.Party(fighter=1, cleric=1),
            ability=True,
            treasure=struct.Treasure(),
        )
        result = display.compact_summary(
            world, "Knight", 0, ["ability", "descend", "retire"]
        )
        lines = result.split("\n")
        assert len(lines) == 5
        assert "Dungeon:" in lines[4]
        assert "None" in lines[4]

    def test_cleared_level_10(self):
        """Test compact summary after clearing dungeon level 10."""
        world = struct.World(
            delve=3,
            depth=10,
            experience=16,
            dungeon=struct.Dungeon(),
            party=struct.Party(champion=1, scroll=2),
            ability=False,
            treasure=struct.Treasure(scale=4, sceptre=1, talisman=1, tools=1),
        )
        result = display.compact_summary(world, "Beguiler", 24, ["retire"])
        lines = result.split("\n")
        assert "depth 10 in delve 3 with experience 16" in lines[0]
        assert "scale×4 sceptre talisman tools" in lines[1]
        assert "retire" in lines[2]
        assert "champion scroll×2" in lines[3]
        assert "Dungeon:" in lines[4]
        assert "None" in lines[4]
        assert len(lines) == 5

    def test_ending_state(self):
        """After final delve, Available should show 'None'."""
        world = struct.World(
            delve=3,
            experience=16,
            dungeon=None,
            party=struct.Party(champion=1),
            ability=False,
            treasure=struct.Treasure(
                scroll=1, elixir=1, bait=2, portal=1, scale=1
            ),
        )
        result = display.compact_summary(world, "DragonSlayer", 23, [])
        lines = result.split("\n")
        assert "delve 3 with experience 16" in lines[0]
        assert "Available:" in lines[2]
        assert "None" in lines[2]
        assert len(lines) == 4  # No Dungeon line
