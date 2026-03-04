# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from using treasure."""

from dataclasses import fields, replace
import random
import pytest

from droll import player, struct, world
from droll.treasure import replace_treasure


class TestTreasure:

    def setup_method(self):
        """Fixture with a game containing dungeon items but no party."""
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(*([2] * len(fields(struct.Dungeon)))),
            party=struct.Party(),
        )
        self.randrange = random.Random(4).randrange

    def test_elixir(self):
        """Test elixir treasure used to revive a party member."""
        game = replace(
            self.game,
            treasure=replace(
                self.game.treasure,
                own=replace(self.game.treasure.own, elixir=1),
            ),
        )
        game = player.apply(
            player.Default, game, self.randrange, "elixir", "cleric"
        )
        assert game.party.cleric == 1
        assert game.treasure.own.elixir == 0

        with pytest.raises(struct.DrollError):
            player.apply(
                player.Default, game, self.randrange, "elixir", "mage"
            )

    def test_bait(self):
        """Test bait treasure used to convert monsters to dragons."""
        game = replace(
            self.game,
            treasure=replace(
                self.game.treasure, own=replace(self.game.treasure.own, bait=2)
            ),
        )
        game = player.apply(
            player.Default, game, self.randrange, "bait", "dragon"
        )
        assert game.treasure.own.bait == 1
        assert game.dungeon.goblin == 0
        assert game.dungeon.skeleton == 0
        assert game.dungeon.ooze == 0
        assert game.dungeon.dragon == 8

        with pytest.raises(struct.DrollError):
            player.apply(player.Default, game, self.randrange, "bait")

    def _helper_artifact(self, artifact, hero, specialty, other):
        """Artifact defeats its specialty and one of another type."""
        game = replace(
            self.game,
            treasure=replace(
                self.game.treasure,
                own=replace(self.game.treasure.own, **{artifact: 2}),
            ),
        )
        game = player.apply(player.Default, game, None, artifact, specialty)
        assert getattr(game.treasure.own, artifact) == 1
        assert getattr(game.party, hero) == 0
        assert getattr(game.dungeon, specialty) == 0

        game = player.apply(player.Default, game, None, artifact, other)
        assert getattr(game.treasure.own, artifact) == 0
        assert getattr(game.party, hero) == 0
        assert getattr(game.dungeon, other) == 1

        with pytest.raises(struct.DrollError):
            player.apply(player.Default, game, None, artifact, other)

    def test_sword_via_fighter(self):
        """Test sword treasure referred to as 'fighter'."""
        self._helper_artifact("sword", "fighter", "goblin", "ooze")

    def test_talisman(self):
        """Test talisman treasure behaves as cleric."""
        self._helper_artifact("talisman", "cleric", "skeleton", "ooze")

    def test_sceptre(self):
        """Test sceptre treasure behaves as mage."""
        self._helper_artifact("sceptre", "mage", "ooze", "goblin")

    def test_tools(self):
        """Test tools treasure behaves as thief (defeats one monster)."""
        game = replace(
            self.game,
            treasure=replace(
                self.game.treasure,
                own=replace(self.game.treasure.own, tools=1),
            ),
        )
        game = player.apply(player.Default, game, None, "tools", "goblin")
        assert game.treasure.own.tools == 0
        assert game.party.thief == 0
        assert game.dungeon.goblin == 1


class TestPhantomTreasure:
    """Bug 3: artifact commands must not work without owning the treasure."""

    def setup_method(self):
        """Fixture with party members but no treasures owned."""
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(*([2] * len(fields(struct.Dungeon)))),
            party=struct.Party(*([2] * len(fields(struct.Party)))),
        )

    def test_sword_without_treasure(self):
        """Using sword without owning one is rejected."""
        with pytest.raises(struct.DrollError, match="not in player's treasure"):
            player.apply(player.Default, self.game, None, "sword", "goblin")

    def test_talisman_without_treasure(self):
        """Using talisman without owning one is rejected."""
        with pytest.raises(struct.DrollError, match="not in player's treasure"):
            player.apply(player.Default, self.game, None, "talisman", "skeleton")

    def test_sceptre_without_treasure(self):
        """Using sceptre without owning one is rejected."""
        with pytest.raises(struct.DrollError, match="not in player's treasure"):
            player.apply(player.Default, self.game, None, "sceptre", "ooze")

    def test_tools_without_treasure(self):
        """Using tools without owning one is rejected."""
        with pytest.raises(struct.DrollError, match="not in player's treasure"):
            player.apply(player.Default, self.game, None, "tools", "goblin")


class TestTreasureAsRecoveryType:
    """Bug 5: treasure names must not be accepted as potion recovery types."""

    def setup_method(self):
        """Fixture with monsters cleared and potions available."""
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(potion=2),
            party=struct.Party(fighter=2, champion=2),
        )

    def test_sword_rejected_as_recovery(self):
        """Drinking a potion to recover 'sword' is rejected."""
        with pytest.raises(struct.DrollError):
            player.apply(
                player.Default, self.game, None,
                "champion", "potion", "sword", "sword",
            )

    def test_talisman_rejected_as_recovery(self):
        """Drinking a potion to recover 'talisman' is rejected."""
        with pytest.raises(struct.DrollError):
            player.apply(
                player.Default, self.game, None,
                "champion", "potion", "talisman", "talisman",
            )

    def test_valid_recovery_still_works(self):
        """Drinking a potion with valid party die names still works."""
        game = player.apply(
            player.Default, self.game, None,
            "champion", "potion", "fighter", "mage",
        )
        assert game.party.fighter == 3
        assert game.party.mage == 1
        assert game.dungeon.potion == 0


def test_replace_treasure_invalid_type():
    """replace_treasure raises DrollError for non-treasure names."""
    treasure = struct.Treasure(own=struct.Artifacts(sword=1))
    with pytest.raises(struct.DrollError, match="not a valid treasure type"):
        replace_treasure(treasure, "cleric")
