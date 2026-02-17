# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for action module helpers."""

from dataclasses import replace
import random
import unittest

from droll import action, dice, struct, world
from droll.error import DrollError

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestDefeatAllPlusAdditional(unittest.TestCase):

    def test_defeats_all_plus_one_additional(self):
        """Defeats all of one type plus one additional."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=2, skeleton=1),
            party=struct.Party(champion=1),
        )
        result = action.defeat_all_plus_additional(
            w, _UNUSED, "champion", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.champion, 0)

    def test_no_additional_when_cleared(self):
        """No additional needed when monsters cleared."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=2),
            party=struct.Party(champion=1),
        )
        result = action.defeat_all_plus_additional(
            w, _UNUSED, "champion", "goblin"
        )
        self.assertEqual(result.dungeon.goblin, 0)

    def test_rejects_extra_additional(self):
        """Rejects more than one additional target."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1, skeleton=2),
            party=struct.Party(champion=1),
        )
        with self.assertRaises(DrollError):
            action.defeat_all_plus_additional(
                w,
                _UNUSED,
                "champion",
                "goblin",
                "skeleton",
                "skeleton",
            )

    def test_requires_additional_when_monsters_remain(self):
        """Requires additional target when monsters remain."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1, skeleton=1),
            party=struct.Party(champion=1),
        )
        with self.assertRaises(DrollError):
            action.defeat_all_plus_additional(
                w,
                _UNUSED,
                "champion",
                "goblin",
            )


class TestDefeatOnePlusAdditional(unittest.TestCase):

    def test_defeats_one_plus_one_additional(self):
        """Defeats one of primary target plus one additional."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=2, skeleton=1),
            party=struct.Party(champion=1),
        )
        result = action.defeat_one_plus_additional(
            w, _UNUSED, "champion", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.champion, 0)

    def test_no_additional_when_cleared(self):
        """No additional needed when all monsters cleared after defeating one."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1),
            party=struct.Party(fighter=1),
        )
        result = action.defeat_one_plus_additional(
            w, _UNUSED, "fighter", "goblin"
        )
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertEqual(result.party.fighter, 0)

    def test_rejects_additional_when_cleared(self):
        """Rejects additional target when all monsters already cleared."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1),
            party=struct.Party(fighter=1),
        )
        with self.assertRaises(DrollError):
            action.defeat_one_plus_additional(
                w, _UNUSED, "fighter", "goblin", "skeleton"
            )

    def test_requires_additional_when_monsters_remain(self):
        """Requires additional target when monsters remain after defeating one."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1, skeleton=1),
            party=struct.Party(fighter=1),
        )
        with self.assertRaises(DrollError):
            action.defeat_one_plus_additional(
                w, _UNUSED, "fighter", "goblin"
            )

    def test_rejects_extra_additional(self):
        """Rejects more than one additional target."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1, skeleton=1, ooze=1),
            party=struct.Party(champion=1),
        )
        with self.assertRaises(DrollError):
            action.defeat_one_plus_additional(
                w,
                _UNUSED,
                "champion",
                "goblin",
                "skeleton",
                "ooze",
            )

    def test_only_decrements_one_of_primary(self):
        """Defeats only one of the primary target, not all."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=3, skeleton=1),
            party=struct.Party(champion=1),
        )
        result = action.defeat_one_plus_additional(
            w, _UNUSED, "champion", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 2)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.champion, 0)


class TestConvertDungeonToParty(unittest.TestCase):

    def test_converts_up_to_max_count(self):
        """Converts min(available, max_count) dungeon dice to party dice."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=3),
            party=struct.Party(fighter=1),
        )
        result = action.convert_dungeon_to_party(
            w, source="goblin", destination="thief", max_count=2
        )
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.party.thief, 2)
        self.assertEqual(result.regroup.discard.thief, 2)

    def test_converts_fewer_when_limited(self):
        """Converts only available count when fewer than max_count."""
        w = struct.World(
            dungeon=struct.Dungeon(skeleton=1),
            party=struct.Party(),
        )
        result = action.convert_dungeon_to_party(
            w, source="skeleton", destination="fighter", max_count=2
        )
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.fighter, 1)
        self.assertEqual(result.regroup.discard.fighter, 1)


class TestDefeatDragonHeroesInterchangeable(unittest.TestCase):

    def test_less_interesting_successful_cases(self):
        """Test valid dragon defeats with interchangeable heroes."""
        self.assertTrue(
            action.defeat_dragon_heroes_interchangeable(
                "cleric", "thief", "mage", _interchangeable={"fighter"}
            )
        )
        self.assertTrue(
            action.defeat_dragon_heroes_interchangeable(
                "cleric", "thief", "fighter", _interchangeable={"fighter"}
            )
        )

    def test_less_interesting_failure_cases(self):
        """Test invalid dragon defeats with interchangeable heroes."""
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric", "thief", _interchangeable={"fighter"}
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric", "fighter", _interchangeable={"fighter"}
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric",
                "thief",
                "champion",
                "mage",
                _interchangeable={"fighter"},
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "cleric",
                "thief",
                "champion",
                "fighter",
                _interchangeable={"fighter"},
            )

    def test_more_interesting_failure_cases(self):
        """Invalid dragon defeats with multiple interchangeable hero types."""
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "mage", "mage", "mage", _interchangeable={"mage", "fighter"}
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "fighter",
                "fighter",
                "fighter",
                _interchangeable={"mage", "fighter"},
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "fighter", "mage", "mage", _interchangeable={"mage", "fighter"}
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "mage",
                "fighter",
                "fighter",
                _interchangeable={"mage", "fighter"},
            )


class TestDefeatDragonHeroesWildcard(unittest.TestCase):

    def test_less_interesting_successful_cases(self):
        """Test valid dragon defeats with wildcard heroes."""
        self.assertTrue(
            action.defeat_dragon_heroes_wildcard(
                "cleric",
                "thief",
                "mage",
            )
        )
        self.assertTrue(
            action.defeat_dragon_heroes_wildcard(
                "cleric", "thief", "fighter", _wildcard={"scroll"}
            )
        )

    def test_less_interesting_failure_cases(self):
        """Test invalid dragon defeats with wildcard heroes."""
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric", "thief", _wildcard={"scroll"}
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric", "fighter", _wildcard={"fighter"}
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric", "thief", "champion", "mage", _wildcard={"fighter"}
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_wildcard(
                "cleric",
                "thief",
                "champion",
                "fighter",
                _wildcard={"fighter"},
            )

    def test_more_interesting_failure_cases(self):
        """Test invalid dragon defeats with multiple wildcard heroes."""
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_wildcard(
                "mage",
                "mage",
                "scroll",
            )
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_wildcard(
                "fighter",
                "fighter",
                "fighter",
                _wildcard={"mage"},
            )


class TestRerollParty(unittest.TestCase):
    """Tests for action.reroll supporting party dice (issue #82)."""

    def setUp(self):
        """Fixture with a world containing known dungeon and party dice."""
        self.world = replace(
            world.new_world(),
            dungeon=struct.Dungeon(goblin=2, skeleton=1),
            party=struct.Party(fighter=2, cleric=1, scroll=2),
        )

    def _canned_randrange(self, sequence):
        """Return a randrange function that yields predetermined values."""
        seq = list(sequence)

        def randrange(start, stop):
            return start + seq.pop(0)

        return randrange

    def test_reroll_single_party_die(self):
        """Rerolling a single party die removes it and re-rolls one party die."""
        # Roll value 0 => fighter
        randrange = self._canned_randrange([0])
        result = action.reroll(
            self.world, randrange, "scroll", "fighter"
        )
        # One scroll consumed for the hero cost
        self.assertEqual(result.party.scroll, 1)
        # Fighter was removed (2-1=1) then re-rolled as fighter (+1=2)
        self.assertEqual(result.party.fighter, 2)
        # Dungeon unchanged
        self.assertEqual(result.dungeon, self.world.dungeon)

    def test_reroll_multiple_party_dice(self):
        """Rerolling multiple party dice removes and re-rolls each."""
        # Roll values: 0 => fighter, 1 => cleric
        randrange = self._canned_randrange([0, 1])
        result = action.reroll(
            self.world, randrange, "scroll", "fighter", "cleric"
        )
        # One scroll consumed
        self.assertEqual(result.party.scroll, 1)
        # fighter: 2 - 1 + 1(rolled) = 2; cleric: 1 - 1 + 1(rolled) = 1
        self.assertEqual(result.party.fighter, 2)
        self.assertEqual(result.party.cleric, 1)
        # Dungeon unchanged
        self.assertEqual(result.dungeon, self.world.dungeon)

    def test_reroll_mix_dungeon_and_party(self):
        """Rerolling a mix of dungeon and party dice handles both."""
        # Dungeon roll: value 0 => goblin; Party roll: value 2 => mage
        randrange = self._canned_randrange([0, 2])
        result = action.reroll(
            self.world, randrange, "scroll", "goblin", "fighter"
        )
        # One scroll consumed
        self.assertEqual(result.party.scroll, 1)
        # Dungeon: goblin was 2, removed 1, re-rolled as goblin (+1) => 2
        self.assertEqual(result.dungeon.goblin, 2)
        # Party: fighter was 2, removed 1, re-rolled as mage (+1)
        self.assertEqual(result.party.fighter, 1)
        self.assertEqual(result.party.mage, 1)

    def test_reroll_party_die_not_present_raises(self):
        """Rerolling a party die that is not present raises DrollError."""
        randrange = self._canned_randrange([])
        with self.assertRaises(DrollError):
            action.reroll(
                self.world, randrange, "scroll", "mage"
            )

    def test_reroll_unknown_target_raises(self):
        """Rerolling a target that is neither dungeon nor party raises DrollError."""
        randrange = self._canned_randrange([])
        with self.assertRaises(DrollError):
            action.reroll(
                self.world, randrange, "scroll", "nonexistent"
            )


class TestActionErrorPaths(unittest.TestCase):
    """Tests for game-rule error paths in the action module."""

    def test_decrement_dungeon_zero_target(self):
        """Cannot decrement a dungeon target that is already zero."""
        dungeon = struct.Dungeon(goblin=0, skeleton=1)
        with self.assertRaises(DrollError):
            action.decrement_dungeon(dungeon, "goblin")

    def test_eliminate_dungeon_zero_target(self):
        """Cannot eliminate a dungeon target that is already zero."""
        dungeon = struct.Dungeon(goblin=0, skeleton=1)
        with self.assertRaises(DrollError):
            action.eliminate_dungeon(dungeon, "goblin")

    def test_open_one_before_monsters_defeated(self):
        """Cannot open chests while monsters remain."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1, chest=1),
            party=struct.Party(thief=1),
        )
        with self.assertRaises(DrollError):
            action.open_one(w, _UNUSED, "thief", "chest")

    def test_open_all_before_monsters_defeated(self):
        """Cannot open all chests while monsters remain."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1, chest=2),
            party=struct.Party(thief=1),
        )
        with self.assertRaises(DrollError):
            action.open_all(w, _UNUSED, "thief", "chest")

    def test_quaff_no_potions(self):
        """Cannot quaff when no potions are available."""
        w = struct.World(
            dungeon=struct.Dungeon(potion=0),
            party=struct.Party(fighter=1),
        )
        with self.assertRaises(DrollError):
            action.quaff(w, _UNUSED, "fighter", "potion")

    def test_reroll_no_targets(self):
        """Reroll requires at least one target."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1),
            party=struct.Party(scroll=1),
        )
        with self.assertRaises(DrollError):
            action.reroll(w, _UNUSED, "scroll")

    def test_reroll_dragon_disallowed(self):
        """Cannot reroll dragon dice by default."""
        w = struct.World(
            dungeon=struct.Dungeon(dragon=3),
            party=struct.Party(scroll=1),
        )
        with self.assertRaises(DrollError):
            action.reroll(w, _UNUSED, "scroll", "dragon")

    def test_interchangeable_disallowed_hero(self):
        """Scrolls cannot defeat a dragon via interchangeable heroes."""
        with self.assertRaises(DrollError):
            action.defeat_dragon_heroes_interchangeable(
                "scroll", "fighter", "thief",
                _interchangeable={"fighter", "mage"},
            )

    def test_bait_non_dragon_target(self):
        """Bait can only target dragons."""
        w = struct.World(
            dungeon=struct.Dungeon(goblin=1),
            party=struct.Party(fighter=1),
            treasure=struct.Treasure(bait=1),
        )
        with self.assertRaises(DrollError):
            action.bait_dragon(w, _UNUSED, "bait", "goblin")

    def test_consume_ability_when_unavailable(self):
        """Cannot consume ability that is already used."""
        w = struct.World(ability=False)
        with self.assertRaises(DrollError):
            action.consume_ability(w)

    def test_nop_ability_rejects_target(self):
        """Default nop ability rejects any target."""
        w = struct.World(ability=True)
        with self.assertRaises(DrollError):
            action.nop_ability(w, _UNUSED, "ability", "fighter")


class TestRegroupDiscard(unittest.TestCase):

    def test_regroup_discard_after_quaff(self):
        """
        Quaffing a new thief with a force-discard thief clears discarding.

        A thief gained via Half-Goblin ability (marked for discard) quaffs a
        potion to revive another thief.  The revived thief survives regroup.
        """
        # Setup: thief from ability (marked for discard), 1 potion available
        pre = struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=False,
            dungeon=struct.Dungeon(potion=1),
            party=struct.Party(thief=1),
            regroup=struct.Regroup(discard=struct.Party(thief=1)),
        )
        # Thief quaffs potion, reviving another thief
        post = action.quaff(pre, None, "thief", "potion", "thief")
        # The marked thief was consumed so the discard counter must drop
        self.assertEqual(post.regroup.discard.thief, 0)
        self.assertEqual(post.party.thief, 1)

        # After descending the revived thief must survive regroup
        descended = world.descend(
            post,
            dice.roll_dungeon,
            random.Random(4).randrange,
        )
        self.assertEqual(descended.party.thief, 1)

    def test_regroup_discard_after_elixir1(self):
        """Accounting of revived vs force-discard thieves via elixirs."""
        # Setup: thief from ability (marked for discard), 1 ooze present
        pre = struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=False,
            dungeon=struct.Dungeon(ooze=1),
            party=struct.Party(thief=1),
            regroup=struct.Regroup(discard=struct.Party(thief=1)),
            treasure=struct.Treasure(elixir=1),
        )

        # Force-discard thief kills the ooze
        post1 = action.defeat_one(pre, None, "thief", "ooze")
        self.assertEqual(post1.regroup.discard.thief, 0)
        self.assertEqual(post1.party.thief, 0)

        # Elixir revives a new thief
        post2 = action.elixir(post1, None, "elixir", "thief")
        self.assertEqual(post2.regroup.discard.thief, 0)
        self.assertEqual(post2.party.thief, 1)

        # After descending the revived thief must survive regroup
        descended = world.descend(
            post2,
            dice.roll_dungeon,
            random.Random(4).randrange,
        )
        self.assertEqual(descended.party.thief, 1)

    def test_regroup_discard_after_elixir2(self):
        """Accounting of revived vs force-discard thieves via elixirs."""
        # Setup: thief from ability (marked for discard), 1 ooze present
        pre = struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=False,
            dungeon=struct.Dungeon(ooze=1),
            party=struct.Party(thief=1),
            regroup=struct.Regroup(discard=struct.Party(thief=1)),
            treasure=struct.Treasure(elixir=1),
        )

        # Elixir revives a new thief
        post1 = action.elixir(pre, None, "elixir", "thief")
        self.assertEqual(post1.regroup.discard.thief, 1)
        self.assertEqual(post1.party.thief, 2)

        # Force-discard thief kills the ooze
        post2 = action.defeat_one(post1, None, "thief", "ooze")
        self.assertEqual(post2.regroup.discard.thief, 0)
        self.assertEqual(post2.party.thief, 1)

        # After descending the revived thief must survive regroup
        descended = world.descend(
            post2,
            dice.roll_dungeon,
            random.Random(4).randrange,
        )
        self.assertEqual(descended.party.thief, 1)
