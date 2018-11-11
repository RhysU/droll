Droll
=====
## What is it?

Droll is an implementation of some of the game mechanics underneath [Dungeon
Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll), a product of
[Tasty Minstrel Games](http://playtmg.com/).  This code is in no way affiliated
with either the game or the publisher.  Go buy their game, learn how to play it,
and then come back here.

## What is implemented?

Default player semantics (i.e. no special abilities).  Special semantics for
the Knight with advancement to DragonSlayer after 5 experience points.  Other
characters remain to be done.

## Why implement it?

It seemed like a fun thing to hack on.  Possibly a fun problem to throw into
reinforcement learning algorithms as (a) the strategy isn't too complicated, (b)
the score is very straightforward, and (c) there's some probabilistic behavior
in both the basic die mechanics as well as the expected value of the treasure.

Also, I was curious how much code was required to capture a game that children
will catch onto in the space of 20 minutes.

## What does it look like?

```
$ droll Default --seed 4
(delve=1, depth=1, ability=True, dungeon=(goblin=1), party=(fighter=1, cleric=2, mage=1, thief=2, scroll=1), treasure=())
(droll  0) cleric goblin

(delve=1, depth=1, ability=True, dungeon=(), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), treasure=())
(droll  0) descend

(delve=1, depth=2, ability=True, dungeon=(goblin=2), party=(fighter=1, cleric=1, mage=1, thief=2, scroll=1), treasure=())
(droll  0) fighter goblin

(delve=1, depth=2, ability=True, dungeon=(), party=(cleric=1, mage=1, thief=2, scroll=1), treasure=())
(droll  0) descend

(delve=1, depth=3, ability=True, dungeon=(ooze=1, chest=1, potion=1), party=(cleric=1, mage=1, thief=2, scroll=1), treasure=())
(droll  0) thief ooze

(delve=1, depth=3, ability=True, dungeon=(chest=1, potion=1), party=(cleric=1, mage=1, thief=1, scroll=1), treasure=())
(droll  0) thief chest

(delve=1, depth=3, ability=True, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), treasure=(talisman=1))
(droll  1) scroll potion
Require exactly 1 to revive

(delve=1, depth=3, ability=True, dungeon=(potion=1), party=(cleric=1, mage=1, scroll=1), treasure=(talisman=1))
(droll  1) scroll potion champion

(delve=1, depth=3, ability=True, dungeon=(), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1))
(droll  1) descend

(delve=1, depth=4, ability=True, dungeon=(skeleton=1, ooze=1, potion=2), party=(cleric=1, mage=1, champion=1), treasure=(talisman=1))
(droll  1) cleric skeleton

(delve=1, depth=4, ability=True, dungeon=(ooze=1, potion=2), party=(mage=1, champion=1), treasure=(talisman=1))
(droll  1) mage ooze

(delve=1, depth=4, ability=True, dungeon=(potion=2), party=(champion=1), treasure=(talisman=1))
(droll  1) champion potion champion fighter

(delve=1, depth=4, ability=True, dungeon=(), party=(fighter=1, champion=1), treasure=(talisman=1))
(droll  1) descend

(delve=1, depth=5, ability=True, dungeon=(goblin=1, skeleton=2, ooze=2), party=(fighter=1, champion=1), treasure=(talisman=1))
(droll  1) champion ooze

(delve=1, depth=5, ability=True, dungeon=(goblin=1, skeleton=2), party=(fighter=1), treasure=(talisman=1))
(droll  1) talisman skeleton

(delve=1, depth=5, ability=True, dungeon=(goblin=1), party=(fighter=1), treasure=())
(droll  0) fighter goblin

(delve=1, depth=5, ability=True, dungeon=(), party=(), treasure=())
(droll  0) retire

(delve=2, depth=1, experience=5, ability=True, dungeon=(ooze=1), party=(fighter=1, cleric=2, mage=3, scroll=1), treasure=())
(droll  5) ^D
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
