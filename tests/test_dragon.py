# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from attacking dragons."""

from dataclasses import fields, replace
import random
import unittest

import droll.action as action
import droll.error as error
import droll.heroes as heroes
import droll.player as player
import droll.struct as struct
import droll.world as world


class TestDragon(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with a game containing dragons and party members."""
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=1, potion=2, dragon=3
            ),
            party=struct.Party(*([2] * len(fields(struct.Party)))),
        )
        self.randrange = random.Random(4).randrange

    def test_successful(self):
        """Test successfully defeating a dragon with three distinct heroes."""
        game = player.apply(
            player.Default,
            self.game,
            self.randrange,
            "fighter",
            "dragon",
            "cleric",
            "mage",
        )
        assert game.party.fighter == 1
        assert game.party.cleric == 1
        assert game.party.mage == 1
        assert game.dungeon.dragon == 0
        assert game.experience == 1
        assert sum(struct.field_values(game.treasure)) == 1

    def test_treasure_slot1(self):
        """Test that sword treasure can substitute for fighter in dragon combat."""
        game = replace(
            self.game, treasure=replace(self.game.treasure, sword=7)
        )
        game = replace(game, party=replace(game.party, fighter=0))
        game = player.apply(
            player.Default,
            game,
            self.randrange,  # Notice sword!
            "fighter",
            "dragon",
            "cleric",
            "mage",
        )
        assert game.treasure.sword == 6
        assert game.party.fighter == 0
        assert game.party.cleric == 1
        assert game.party.mage == 1
        assert game.dungeon.dragon == 0
        assert game.experience == 1
        assert sum(struct.field_values(game.treasure)) == 7

    def test_treasure_slot3(self):
        """Test that talisman treasure can substitute for cleric in dragon combat."""
        game = replace(
            self.game, treasure=replace(self.game.treasure, talisman=7)
        )
        game = replace(game, party=replace(game.party, cleric=0))
        game = player.apply(
            player.Default,
            game,
            self.randrange,  # Notice talisman!
            "fighter",
            "dragon",
            "cleric",
            "mage",
        )
        assert game.treasure.talisman == 6
        assert game.party.fighter == 1
        assert game.party.cleric == 0
        assert game.party.mage == 1
        assert game.dungeon.dragon == 0
        assert game.experience == 1
        assert sum(struct.field_values(game.treasure)) == 7

    def test_treasure_slot2(self):
        """Test that sceptre treasure can substitute for mage in dragon combat."""
        game = replace(
            self.game, treasure=replace(self.game.treasure, sceptre=7)
        )
        game = replace(game, party=replace(game.party, mage=0))
        game = player.apply(
            player.Default,
            game,
            self.randrange,  # Notice talisman!
            "fighter",
            "dragon",
            "cleric",
            "mage",
        )
        assert game.treasure.sceptre == 6
        assert game.party.fighter == 1
        assert game.party.cleric == 1
        assert game.party.mage == 0
        assert game.dungeon.dragon == 0
        assert game.experience == 1
        assert sum(struct.field_values(game.treasure)) == 7

    def test_monsters_remain(self):
        """Test that dragon cannot be attacked while monsters remain in dungeon."""
        game = replace(self.game, dungeon=replace(self.game.dungeon, goblin=1))
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "mage",
            )

    def test_too_few_specified(self):
        """Test that attacking dragon with too few heroes raises an error."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
            )

        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default, self.game, self.randrange, "fighter", "dragon"
            )

        # Dragon Slayer requires only two
        with self.assertRaises(error.DrollError):
            player.apply(
                heroes.DragonSlayer,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
            )

    def test_too_many_specified(self):
        """Test that attacking dragon with too many heroes raises an error."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "mage",
                "thief",
            )

        # Dragon Slayer requires only two
        with self.assertRaises(error.DrollError):
            player.apply(
                heroes.DragonSlayer,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "mage",
            )

    def test_only_heroes_accepted(self):
        """Test that only valid heroes can be used against dragons."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "foo",
            )

    def test_one_scroll(self):
        """Test that a single scroll cannot be used as a hero substitute."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "scroll",
            )

        # Dragon Slayer requires only two
        with self.assertRaises(error.DrollError):
            player.apply(
                heroes.DragonSlayer,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "scroll",
            )

    def test_not_enough_distinct(self):
        """Test that duplicate heroes cannot defeat a dragon."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "mage",
                "mage",
            )


class TestDefeatDragonHeroesInterchangeable(unittest.TestCase):

    def test_less_interesting_successful_cases(self):
        """Test valid dragon defeats with interchangeable heroes."""
        assert action.defeat_dragon_heroes_interchangeable(
            "cleric", "thief", "mage", _interchangeable={"fighter"}
        )
        assert action.defeat_dragon_heroes_interchangeable(
            "cleric", "thief", "fighter", _interchangeable={"fighter"}
        )

    def test_less_interesting_failure_cases(self):
        """Test invalid dragon defeats with interchangeable heroes."""
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric", "thief", _interchangeable={"fighter"}
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric", "fighter", _interchangeable={"fighter"}
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric",
                "thief",
                "champion",
                "mage",
                _interchangeable={"fighter"},
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric",
                "thief",
                "champion",
                "fighter",
                _interchangeable={"fighter"},
            )

    def test_more_interesting_successful_cases(self):
        """Test valid dragon defeats with multiple interchangeable hero types."""
        # More than two could be interchangeable, but does not appear in the game.
        # Therefore, only two interchangeable case is checked below.
        assert action.defeat_dragon_heroes_interchangeable(
            "cleric", "thief", "mage", _interchangeable={"mage", "fighter"}
        )
        assert action.defeat_dragon_heroes_interchangeable(
            "cleric", "fighter", "mage", _interchangeable={"mage", "fighter"}
        )
        assert action.defeat_dragon_heroes_interchangeable(
            "cleric",
            "fighter",
            "fighter",
            _interchangeable={"mage", "fighter"},
        )
        assert action.defeat_dragon_heroes_interchangeable(
            "cleric", "mage", "mage", _interchangeable={"mage", "fighter"}
        )

    def test_more_interesting_failure_cases(self):
        """Test invalid dragon defeats with multiple interchangeable hero types."""
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "mage", "mage", "mage", _interchangeable={"mage", "fighter"}
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "fighter",
                "fighter",
                "fighter",
                _interchangeable={"mage", "fighter"},
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "fighter", "mage", "mage", _interchangeable={"mage", "fighter"}
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "mage",
                "fighter",
                "fighter",
                _interchangeable={"mage", "fighter"},
            )


class TestDefeatDragonHeroesWildcard(unittest.TestCase):

    def test_less_interesting_successful_cases(self):
        """Test valid dragon defeats with wildcard heroes."""
        assert action.defeat_dragon_heroes_wildcard(
            "cleric",
            "thief",
            "mage",
        )
        assert action.defeat_dragon_heroes_wildcard(
            "cleric", "thief", "fighter", _wildcard={"scroll"}
        )

    def test_less_interesting_failure_cases(self):
        """Test invalid dragon defeats with wildcard heroes."""
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric", "thief", _wildcard={"scroll"}
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric", "fighter", _wildcard={"fighter"}
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric", "thief", "champion", "mage", _wildcard={"fighter"}
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric",
                "thief",
                "champion",
                "fighter",
                _wildcard={"fighter"},
            )

    def test_more_interesting_successful_cases(self):
        """Test valid dragon defeats with multiple wildcard heroes."""
        # More than one could be wildcard, but does not appear in the game.
        # Therefore, only one wildcard case is checked below.
        assert action.defeat_dragon_heroes_wildcard(
            "cleric",
            "thief",
            "scroll",
        )
        assert action.defeat_dragon_heroes_wildcard(
            "cleric",
            "scroll",
            "scroll",
        )
        assert action.defeat_dragon_heroes_wildcard(
            "scroll",
            "scroll",
            "scroll",
        )

    def test_more_interesting_failure_cases(self):
        """Test invalid dragon defeats with multiple wildcard heroes."""
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_wildcard(
                "mage",
                "mage",
                "scroll",
            )
        with self.assertRaises(error.DrollError):
            action.defeat_dragon_heroes_wildcard(
                "fighter",
                "fighter",
                "fighter",
                _wildcard={"mage"},
            )
