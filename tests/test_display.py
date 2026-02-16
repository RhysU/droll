# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for the compact display module."""
import unittest

from droll import display
from droll import struct


class TestFormatItems(unittest.TestCase):

    def test_empty_party(self):
        """Test formatting an empty party returns 'none'."""
        party = struct.Party()
        self.assertEqual(display._format_items(party), "None")

    def test_single_items(self):
        """Test formatting party with single quantities of each item."""
        party = struct.Party(fighter=1, cleric=1, mage=1)
        self.assertEqual(display._format_items(party), "fighter cleric mage")

    def test_multiple_items(self):
        """Test formatting party with multiple quantities uses × notation."""
        party = struct.Party(fighter=2, cleric=1, mage=3)
        self.assertEqual(
            display._format_items(party), "fighter×2 cleric mage×3"
        )

    def test_dragon_always_shows_count(self):
        """Test that dragons always display with count, even when singular."""
        dungeon = struct.Dungeon(dragon=1)
        self.assertEqual(display._format_items(dungeon), "dragon×1")

    def test_dragon_multiple(self):
        """Test formatting dungeon with multiple dragons."""
        dungeon = struct.Dungeon(goblin=1, dragon=2)
        self.assertEqual(display._format_items(dungeon), "goblin dragon×2")


class TestFormatTreasure(unittest.TestCase):

    def test_empty_treasure(self):
        """Test formatting empty treasure returns 'none'."""
        treasure = struct.Treasure()
        self.assertEqual(display._format_treasure(treasure), "None")

    def test_single_items_alphabetized(self):
        """Test treasure items are displayed in alphabetical order."""
        treasure = struct.Treasure(talisman=1, elixir=1)
        self.assertEqual(display._format_treasure(treasure), "elixir talisman")

    def test_multiple_items_alphabetized(self):
        """Test multiple treasure items are alphabetized and use × notation."""
        treasure = struct.Treasure(scale=4, sceptre=1, talisman=1, tools=1)
        self.assertEqual(
            display._format_treasure(treasure),
            "scale×4 sceptre talisman tools",
        )


class TestFormatAvailable(unittest.TestCase):

    def test_alphabetized(self):
        """Test available commands are displayed in alphabetical order."""
        available = ["retreat", "ability", "reroll"]
        self.assertEqual(
            display._format_available(available), "ability reroll retreat"
        )

    def test_empty(self):
        """Test empty available commands list displays 'None'."""
        self.assertEqual(display._format_available([]), "None")


class TestFormatDungeon(unittest.TestCase):

    def test_none_dungeon(self):
        """Test formatting None dungeon returns None."""
        self.assertIsNone(display._format_dungeon(None))

    def test_empty_dungeon(self):
        """Test formatting empty dungeon returns 'None' string."""
        dungeon = struct.Dungeon()
        self.assertEqual(display._format_dungeon(dungeon), "None")

    def test_with_monsters(self):
        """Test formatting dungeon with monsters."""
        dungeon = struct.Dungeon(goblin=1, skeleton=2)
        self.assertEqual(display._format_dungeon(dungeon), "goblin skeleton×2")

    def test_with_dragon(self):
        """Test formatting dungeon with only dragons."""
        dungeon = struct.Dungeon(dragon=2)
        self.assertEqual(display._format_dungeon(dungeon), "dragon×2")


class TestCompactSummary(unittest.TestCase):

    def test_start_of_game(self):
        """Test compact summary at the start of a new game."""
        world = struct.World(
            delve=1,
            depth=0,
            experience=0,
            dungeon=None,
            party=struct.Party(
                fighter=2, cleric=1, mage=1, thief=1, champion=2
            ),
            ability=True,
            treasure=struct.Treasure(),
        )
        result = display.compact_summary(
            world, "Knight", 0, ["ability", "descend"]
        )
        lines = result.split("\n")
        self.assertEqual(len(lines), 4)
        self.assertIn("delve 1 with experience 0", lines[0])
        self.assertIn("Treasure:", lines[1])
        self.assertIn("None", lines[1])
        self.assertIn("Available:", lines[2])
        self.assertIn("ability descend", lines[2])
        self.assertIn("Party:", lines[3])
        self.assertIn("fighter×2", lines[3])

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
        self.assertEqual(len(lines), 5)
        self.assertIn("depth 3 in delve 1 with experience 0", lines[0])
        self.assertIn("talisman", lines[1])
        self.assertIn("ability retreat", lines[2])
        self.assertIn("fighter champion", lines[3])
        self.assertIn("goblin skeleton×2 ooze×2", lines[4])

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
            self.assertGreaterEqual(content_start, 13)

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
        self.assertEqual(len(lines), 5)
        self.assertIn("Dungeon:", lines[4])
        self.assertIn("None", lines[4])

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
        self.assertIn("depth 10 in delve 3 with experience 16", lines[0])
        self.assertIn("scale×4 sceptre talisman tools", lines[1])
        self.assertIn("retire", lines[2])
        self.assertIn("champion scroll×2", lines[3])
        self.assertIn("Dungeon:", lines[4])
        self.assertIn("None", lines[4])
        self.assertEqual(len(lines), 5)

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
        self.assertIn("delve 3 with experience 16", lines[0])
        self.assertIn("Available:", lines[2])
        self.assertIn("None", lines[2])
        self.assertEqual(len(lines), 4)  # No Dungeon line
