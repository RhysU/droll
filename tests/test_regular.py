# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for regular module helpers."""

from dataclasses import fields, replace
import random
import pytest

from droll import dice, heroes, player, regular, struct, world
from droll.dungeon import decrement_dungeon, eliminate_dungeon
from droll.struct import DrollError

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestRerollParty:
    """Tests for regular.reroll supporting party dice (issue #82)."""

    def setup_method(self):
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
        """Rerolling a single party die removes and re-rolls it."""
        # Roll value 0 => fighter
        randrange = self._canned_randrange([0])
        result = regular.reroll(self.world, randrange, "scroll", "fighter")
        # One scroll consumed for the hero cost
        assert result.party.scroll == 1
        # Fighter was removed (2-1=1) then re-rolled as fighter (+1=2)
        assert result.party.fighter == 2
        # Dungeon unchanged
        assert result.dungeon == self.world.dungeon

    def test_reroll_multiple_party_dice(self):
        """Rerolling multiple party dice removes and re-rolls each."""
        # Roll values: 0 => fighter, 1 => cleric
        randrange = self._canned_randrange([0, 1])
        result = regular.reroll(
            self.world, randrange, "scroll", "fighter", "cleric"
        )
        # One scroll consumed
        assert result.party.scroll == 1
        # fighter: 2 - 1 + 1(rolled) = 2; cleric: 1 - 1 + 1(rolled) = 1
        assert result.party.fighter == 2
        assert result.party.cleric == 1
        # Dungeon unchanged
        assert result.dungeon == self.world.dungeon

    def test_reroll_mix_dungeon_and_party(self):
        """Rerolling a mix of dungeon and party dice handles both."""
        # Dungeon roll: value 0 => goblin; Party roll: value 2 => mage
        randrange = self._canned_randrange([0, 2])
        result = regular.reroll(
            self.world, randrange, "scroll", "goblin", "fighter"
        )
        # One scroll consumed
        assert result.party.scroll == 1
        # Dungeon: goblin was 2, removed 1, re-rolled as goblin (+1) => 2
        assert result.dungeon.goblin == 2
        # Party: fighter was 2, removed 1, re-rolled as mage (+1)
        assert result.party.fighter == 1
        assert result.party.mage == 1

    def test_reroll_party_die_not_present_raises(self):
        """Rerolling a party die that is not present raises DrollError."""
        randrange = self._canned_randrange([])
        with pytest.raises(DrollError):
            regular.reroll(self.world, randrange, "scroll", "mage")

    def test_reroll_unknown_target_raises(self):
        """Rerolling an unknown target raises DrollError."""
        randrange = self._canned_randrange([])
        with pytest.raises(DrollError):
            regular.reroll(self.world, randrange, "scroll", "nonexistent")

    def test_reroll_requires_hero_before_rolling(self):
        """A rolled scroll cannot pay the cost of the reroll (issue #105)."""
        w = replace(self.world, party=replace(self.world.party, scroll=0))
        with pytest.raises(DrollError):
            regular.reroll(
                w, self._canned_randrange([5, 5, 5, 5, 5]), "scroll", "fighter"
            )


def test_all_distinct_no_options():
    """All different heroes are fully distinct."""
    assert regular.distinct_heroes(["fighter", "cleric", "mage"]) == 3


def test_duplicates_reduce_count():
    """Duplicate heroes reduce distinct count."""
    assert regular.distinct_heroes(["fighter", "fighter", "mage"]) == 2


def test_all_same():
    """All identical heroes yield 1."""
    assert regular.distinct_heroes(["fighter", "fighter", "fighter"]) == 1


def test_empty():
    """No heroes means zero distinct."""
    assert regular.distinct_heroes([]) == 0


def test_single():
    """Single hero is 1 distinct."""
    assert regular.distinct_heroes(["mage"]) == 1


def test_wildcard_adds_one_each():
    """Each wildcard counts as a distinct hero."""
    assert (
        regular.distinct_heroes(
            ["cleric", "thief", "scroll"],
            wildcard=frozenset({"scroll"}),
        )
        == 3
    )


def test_multiple_wildcards():
    """Multiple wildcards each contribute 1."""
    assert (
        regular.distinct_heroes(
            ["fighter", "scroll", "scroll"],
            wildcard=frozenset({"scroll"}),
        )
        == 3
    )


def test_all_wildcards():
    """All wildcards still count as distinct."""
    assert (
        regular.distinct_heroes(
            ["scroll", "scroll", "scroll"],
            wildcard=frozenset({"scroll"}),
        )
        == 3
    )


def test_wildcard_does_not_help_duplicates():
    """Wildcards don't fix duplicate non-wildcards."""
    assert (
        regular.distinct_heroes(
            ["mage", "mage", "scroll"],
            wildcard=frozenset({"scroll"}),
        )
        == 2
    )


def test_interchangeable_two_from_pool():
    """Two interchangeable heroes contribute 2 distinct."""
    assert (
        regular.distinct_heroes(
            ["fighter", "cleric", "mage"],
            interchangeable=frozenset({"fighter", "cleric"}),
        )
        == 3
    )


def test_interchangeable_capped_by_pool_size():
    """Interchangeable contribution capped at pool size."""
    assert (
        regular.distinct_heroes(
            ["mage", "mage", "mage"],
            interchangeable=frozenset({"mage", "fighter"}),
        )
        == 2
    )


def test_interchangeable_all_same_type():
    """All same type from a 2-member pool still capped at 2."""
    assert (
        regular.distinct_heroes(
            ["fighter", "fighter", "fighter"],
            interchangeable=frozenset({"mage", "fighter"}),
        )
        == 2
    )


def test_interchangeable_mixed_overflow():
    """Mixed interchangeable heroes exceeding pool size."""
    assert (
        regular.distinct_heroes(
            ["fighter", "mage", "mage"],
            interchangeable=frozenset({"mage", "fighter"}),
        )
        == 2
    )


def test_interchangeable_with_regular():
    """Interchangeable heroes + distinct regular hero."""
    assert (
        regular.distinct_heroes(
            ["fighter", "cleric", "thief"],
            interchangeable=frozenset({"fighter", "cleric"}),
        )
        == 3
    )


def test_interchangeable_single_member_present():
    """One hero from interchangeable set contributes 1."""
    assert (
        regular.distinct_heroes(
            ["cleric", "thief", "fighter"],
            interchangeable=frozenset({"fighter"}),
        )
        == 3
    )


def test_interchangeable_single_member_absent():
    """No heroes from interchangeable set contribute 0 from pool."""
    assert (
        regular.distinct_heroes(
            ["cleric", "thief", "mage"],
            interchangeable=frozenset({"fighter"}),
        )
        == 3
    )


def test_dragon_wildcard_less_interesting_successful_cases():
    """Test valid dragon defeats with wildcard heroes."""
    assert regular.defeat_dragon_heroes(
        "cleric",
        "thief",
        "mage",
        disallowed_heroes=frozenset(),
        wildcard=frozenset({"scroll"}),
    )
    assert regular.defeat_dragon_heroes(
        "cleric",
        "thief",
        "fighter",
        disallowed_heroes=frozenset(),
        wildcard=frozenset({"scroll"}),
    )


def test_dragon_wildcard_less_interesting_failure_cases():
    """Test invalid dragon defeats with wildcard heroes."""
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "thief",
            disallowed_heroes=frozenset(),
            wildcard=frozenset({"scroll"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "fighter",
            disallowed_heroes=frozenset(),
            wildcard=frozenset({"fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "thief",
            "champion",
            "mage",
            disallowed_heroes=frozenset(),
            wildcard=frozenset({"fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "thief",
            "champion",
            "fighter",
            disallowed_heroes=frozenset(),
            wildcard=frozenset({"fighter"}),
        )


def test_dragon_wildcard_more_interesting_failure_cases():
    """Test invalid dragon defeats with multiple wildcard heroes."""
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "mage",
            "mage",
            "scroll",
            disallowed_heroes=frozenset(),
            wildcard=frozenset({"scroll"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "fighter",
            "fighter",
            "fighter",
            disallowed_heroes=frozenset(),
            wildcard=frozenset({"mage"}),
        )


def test_dragon_interchangeable_less_interesting_successful_cases():
    """Test valid dragon defeats with interchangeable heroes."""
    assert regular.defeat_dragon_heroes(
        "cleric",
        "thief",
        "mage",
        interchangeable=frozenset({"fighter"}),
    )
    assert regular.defeat_dragon_heroes(
        "cleric",
        "thief",
        "fighter",
        interchangeable=frozenset({"fighter"}),
    )


def test_dragon_interchangeable_less_interesting_failure_cases():
    """Test invalid dragon defeats with interchangeable heroes."""
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "thief",
            interchangeable=frozenset({"fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "fighter",
            interchangeable=frozenset({"fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "thief",
            "champion",
            "mage",
            interchangeable=frozenset({"fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "cleric",
            "thief",
            "champion",
            "fighter",
            interchangeable=frozenset({"fighter"}),
        )


def test_dragon_interchangeable_more_interesting_failure_cases():
    """Invalid dragon defeats with multiple interchangeable hero types."""
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "mage",
            "mage",
            "mage",
            interchangeable=frozenset({"mage", "fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "fighter",
            "fighter",
            "fighter",
            interchangeable=frozenset({"mage", "fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "fighter",
            "mage",
            "mage",
            interchangeable=frozenset({"mage", "fighter"}),
        )
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "mage",
            "fighter",
            "fighter",
            interchangeable=frozenset({"mage", "fighter"}),
        )


class TestDragon:

    def setup_method(self):
        """Set up fixture for a game containing dragons and party members."""
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
        assert sum(struct.field_values(game.treasure.own)) == 1

    def test_treasure_slot1(self):
        """Sword treasure can substitute for fighter in dragon combat."""
        game = replace(
            self.game,
            treasure=replace(
                self.game.treasure,
                own=replace(self.game.treasure.own, sword=7),
            ),
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
        assert game.treasure.own.sword == 6
        assert game.party.fighter == 0
        assert game.party.cleric == 1
        assert game.party.mage == 1
        assert game.dungeon.dragon == 0
        assert game.experience == 1
        assert sum(struct.field_values(game.treasure.own)) == 7

    def test_monsters_remain(self):
        """Dragon cannot be attacked while monsters remain in dungeon."""
        game = replace(self.game, dungeon=replace(self.game.dungeon, goblin=1))
        with pytest.raises(DrollError):
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
        """Attacking dragon with too few heroes raises an error."""
        with pytest.raises(DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
            )

        with pytest.raises(DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
            )

        # Dragon Slayer requires only two
        with pytest.raises(DrollError):
            player.apply(
                heroes.DragonSlayer,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
            )

    def test_only_heroes_accepted(self):
        """Only valid heroes can be used against dragons."""
        with pytest.raises(DrollError):
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
        """A single scroll cannot be used as a hero substitute."""
        with pytest.raises(DrollError):
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
        with pytest.raises(DrollError):
            player.apply(
                heroes.DragonSlayer,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "scroll",
            )

    def test_not_enough_distinct(self):
        """Duplicate heroes cannot defeat a dragon."""
        with pytest.raises(DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "mage",
                "mage",
            )


def test_decrement_dungeon_zero_target():
    """Cannot decrement a dungeon target that is already zero."""
    dungeon = struct.Dungeon(goblin=0, skeleton=1)
    with pytest.raises(DrollError):
        decrement_dungeon(dungeon, "goblin")


def test_eliminate_dungeon_zero_target():
    """Cannot eliminate a dungeon target that is already zero."""
    dungeon = struct.Dungeon(goblin=0, skeleton=1)
    with pytest.raises(DrollError):
        eliminate_dungeon(dungeon, "goblin")


def test_open_one_before_monsters_defeated():
    """Cannot open chests while monsters remain."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1, chest=1),
        party=struct.Party(thief=1),
    )
    with pytest.raises(DrollError):
        regular.open_one(w, _UNUSED, "thief", "chest")


def test_open_all_before_monsters_defeated():
    """Cannot open all chests while monsters remain."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1, chest=2),
        party=struct.Party(thief=1),
    )
    with pytest.raises(DrollError):
        regular.open_all(w, _UNUSED, "thief", "chest")


def test_quaff_no_potions():
    """Cannot quaff when no potions are available."""
    w = struct.World(
        dungeon=struct.Dungeon(potion=0),
        party=struct.Party(fighter=1),
    )
    with pytest.raises(DrollError):
        regular.quaff(w, _UNUSED, "fighter", "potion")


def test_reroll_no_targets():
    """Reroll requires at least one target."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(scroll=1),
    )
    with pytest.raises(DrollError):
        regular.reroll(w, _UNUSED, "scroll")


def test_reroll_dragon_disallowed():
    """Cannot reroll dragon dice by default."""
    w = struct.World(
        dungeon=struct.Dungeon(dragon=3),
        party=struct.Party(scroll=1),
    )
    with pytest.raises(DrollError):
        regular.reroll(w, _UNUSED, "scroll", "dragon")


def test_interchangeable_disallowed_hero():
    """Scrolls cannot defeat a dragon via interchangeable heroes."""
    with pytest.raises(DrollError):
        regular.defeat_dragon_heroes(
            "scroll",
            "fighter",
            "thief",
            interchangeable=frozenset({"fighter", "mage"}),
        )


def test_bait_non_dragon_target():
    """Bait can only target dragons."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(fighter=1),
        treasure=struct.Treasure(own=struct.Artifacts(bait=1)),
    )
    with pytest.raises(DrollError):
        regular.bait_dragon(w, _UNUSED, "bait", "goblin")


def test_regroup_discard_after_quaff():
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
    post = regular.quaff(pre, None, "thief", "potion", "thief")
    # The marked thief was consumed so the discard counter must drop
    assert post.regroup.discard.thief == 0
    assert post.party.thief == 1

    # After descending the revived thief must survive regroup
    descended = world.descend(
        post,
        dice.roll_dungeon,
        random.Random(4).randrange,
    )
    assert descended.party.thief == 1


def test_regroup_discard_after_elixir1():
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
        treasure=struct.Treasure(own=struct.Artifacts(elixir=1)),
    )

    # Force-discard thief kills the ooze
    post1 = regular.defeat_one(pre, None, "thief", "ooze")
    assert post1.regroup.discard.thief == 0
    assert post1.party.thief == 0

    # Elixir revives a new thief
    post2 = regular.elixir(post1, None, "elixir", "thief")
    assert post2.regroup.discard.thief == 0
    assert post2.party.thief == 1

    # After descending the revived thief must survive regroup
    descended = world.descend(
        post2,
        dice.roll_dungeon,
        random.Random(4).randrange,
    )
    assert descended.party.thief == 1


def test_regroup_discard_after_elixir2():
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
        treasure=struct.Treasure(own=struct.Artifacts(elixir=1)),
    )

    # Elixir revives a new thief
    post1 = regular.elixir(pre, None, "elixir", "thief")
    assert post1.regroup.discard.thief == 1
    assert post1.party.thief == 2

    # Force-discard thief kills the ooze
    post2 = regular.defeat_one(post1, None, "thief", "ooze")
    assert post2.regroup.discard.thief == 0
    assert post2.party.thief == 1

    # After descending the revived thief must survive regroup
    descended = world.descend(
        post2,
        dice.roll_dungeon,
        random.Random(4).randrange,
    )
    assert descended.party.thief == 1
