Droll
=====
## What is it?

Droll is an implementation of some of the game mechanics underneath [Dungeon
Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll), a product of
[Tasty Minstrel Games](http://playtmg.com/).  This code is in no way affiliated
with either the game or the publisher.  Go buy their game, learn how to play it,
and then come back here.

## What is implemented?

Default player semantics (i.e. no special abilities).  Special semantics for the
Knight with advancement to DragonSlayer after 5 experience points.  Also,
semantics for Spellsword with advancement to Battlemage.  Other characters
remain to be done.  Known shortcomings are flagged with TODOs.

## Why implement it?

It seemed like a fun thing to hack on.  Possibly a fun problem to throw into
reinforcement learning algorithms as (a) the strategy isn't too complicated, (b)
the score is very straightforward, and (c) there's some probabilistic behavior
in both the basic die mechanics as well as the expected value of the treasure.

Also, I was curious how much code was required to capture a game that children
will catch onto in the space of 20 minutes.  And, I wanted to stick to
collections.namedtuple and free functions instead of OOPing all-the-things.

## What does it look like?

```
$ droll --seed 7 Knight

(delve=1, party=(fighter=2, cleric=1, mage=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) help

Feasible commands (help <command>):
===================================
descend


(delve=1, party=(fighter=2, cleric=1, mage=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) descend

(delve=1, depth=1, dungeon=(goblin=1), party=(fighter=2, cleric=1, mage=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) help

Feasible commands (help <command>):
===================================
ability  champion   cleric   fighter   mage   retreat  thief


(delve=1, depth=1, dungeon=(goblin=1), party=(fighter=2, cleric=1, mage=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) help fighter
Attack monsters, quaff potions, and open chests with a fighter like so:

        champion skeleton            # Attack skeleton(s)
        thief chest                  # Open chest(s)
        fighter potion mage thief    # Drink 2 potions obtaining mage, thief
        mage dragon champion cleric  # Attack dragon with party of 3


(delve=1, depth=1, dungeon=(goblin=1), party=(fighter=2, cleric=1, mage=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) fighter goblin

(delve=1, depth=1, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) descend

(delve=1, depth=2, dungeon=(ooze=1, potion=1), party=(fighter=1, cleric=1, mage=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) mage ooze

(delve=1, depth=2, dungeon=(potion=1), party=(fighter=1, cleric=1, thief=1, champion=2), ability=True, treasure=())
(Knight  0) champion potion mage

(delve=1, depth=2, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1), ability=True, treasure=())
(Knight  0) descend

(delve=1, depth=3, dungeon=(goblin=1, skeleton=1, potion=1), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1), ability=True, treasure=())
(Knight  0) help ability
Invoke the player's ability.

    Convert all monster faces into dragon dice.

(delve=1, depth=3, dungeon=(goblin=1, skeleton=1, potion=1), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1), ability=True, treasure=())
(Knight  0) ability

(delve=1, depth=3, dungeon=(potion=1, dragon=2), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1), treasure=())
(Knight  0) help

Feasible commands (help <command>):
===================================
champion   cleric   descend  fighter   mage   retire  thief


(delve=1, depth=3, dungeon=(potion=1, dragon=2), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1), treasure=())
(Knight  0) descend

(delve=1, depth=4, dungeon=(goblin=2, chest=2, dragon=2), party=(fighter=1, cleric=1, mage=1, thief=1, champion=1), treasure=())
(Knight  0) fighter goblin

(delve=1, depth=4, dungeon=(chest=2, dragon=2), party=(cleric=1, mage=1, thief=1, champion=1), treasure=())
(Knight  0) thief chest

(delve=1, depth=4, dungeon=(dragon=2), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1, elixir=1))
(Knight  2) descend

(delve=1, depth=5, dungeon=(goblin=2, chest=1, potion=2, dragon=2), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1, elixir=1))
(Knight  2) champion goblin

(delve=1, depth=5, dungeon=(chest=1, potion=2, dragon=2), party=(cleric=1, mage=1), treasure=(talisman=1, elixir=1))
(Knight  2) mage potion champion thief

(delve=1, depth=5, dungeon=(chest=1, dragon=2), party=(cleric=1, thief=1, champion=1), treasure=(talisman=1, elixir=1))
(Knight  2) thief chest

(delve=1, depth=5, dungeon=(dragon=2), party=(cleric=1, champion=1), treasure=(talisman=1, sceptre=1, elixir=1))
(Knight  3) help retreat
Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve or ends game, as suitable.

(delve=1, depth=5, dungeon=(dragon=2), party=(cleric=1, champion=1), treasure=(talisman=1, sceptre=1, elixir=1))
(Knight  3) retreat
Why retreat when you could instead retire?

(delve=1, depth=5, dungeon=(dragon=2), party=(cleric=1, champion=1), treasure=(talisman=1, sceptre=1, elixir=1))
(Knight  3) retire

(delve=2, experience=5, party=(fighter=1, cleric=1, champion=5), ability=True, treasure=(talisman=1, sceptre=1, elixir=1))
(DragonSlayer  8) descend

(delve=2, depth=1, experience=5, dungeon=(chest=1), party=(fighter=1, cleric=1, champion=5), ability=True, treasure=(talisman=1, sceptre=1, elixir=1))
(DragonSlayer  8) champion chest

(delve=2, depth=1, experience=5, dungeon=(), party=(fighter=1, cleric=1, champion=4), ability=True, treasure=(talisman=2, sceptre=1, elixir=1))
(DragonSlayer  9) descend

(delve=2, depth=2, experience=5, dungeon=(goblin=1, skeleton=1), party=(fighter=1, cleric=1, champion=4), ability=True, treasure=(talisman=2, sceptre=1, elixir=1))
(DragonSlayer  9) talisman goblin

(delve=2, depth=2, experience=5, dungeon=(skeleton=1), party=(fighter=1, champion=4), ability=True, treasure=(talisman=2, sceptre=1, elixir=1))
(DragonSlayer  9) sceptre skeleton

(delve=2, depth=2, experience=5, dungeon=(), party=(fighter=1, champion=4), ability=True, treasure=(talisman=2, elixir=1))
(DragonSlayer  8) elixir mage

(delve=2, depth=2, experience=5, dungeon=(), party=(fighter=1, mage=1, champion=4), ability=True, treasure=(talisman=2))
(DragonSlayer  7) ^D
```

## Testing

You can run unit tests through setup.py with:

```
python setup.py test
```

## Documentation

To generate Sphinx documentation, run:

```
python setup.py doc
```

The generated documentation will be available in `docs/_build`
