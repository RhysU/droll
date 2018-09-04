Droll
=====
## What is it?

Droll is an implementation of some of the game mechanics underneath [Dungeon
Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll), a product of
[Tasty Minstrel Games](http://playtmg.com/).  This code is in no way affiliated
with either the game or the publisher.  Go buy their game, learn how to play it,
and then come back here.

## What is implemented?

Not much more than default player semantics and treasures (i.e. no abilities, no
special rules like fighters/mages equivalent, no promotion after experience
level 5).

## Why implement it?

It seemed like a fun thing to hack on.  Possibly a fun problem to throw into
reinforcement learning algorithms as (a) the strategy isn't too complicated, (b)
the score is very straightforward, and (c) there's some probabilistic behavior
in both the basic die mechanics as well as the expected value of the treasure.

Also, I was curious how much code was required to capture a game that children
will catch onto in the space of 20 minutes.

## What does it look like?

```
$ ipython --no-banner

In [1]: from droll import Interactive

In [2]: x = Interactive()

In [3]: x
Out[3]: (delve=1, depth=1, ability=True, level=(goblin=1), party=(fighter=2, mage=2, champion=3), treasure=())

In [4]: x.apply('fighter', 'goblin')
Out[4]: (delve=1, depth=1, ability=True, level=(), party=(fighter=1, mage=2, champion=3), treasure=())

In [5]: x.descend()
Out[5]: (delve=1, depth=2, ability=True, level=(skeleton=2), party=(fighter=1, mage=2, champion=3), treasure=())

In [6]: x.apply('champion', 'skeleton')
Out[6]: (delve=1, depth=2, ability=True, level=(), party=(fighter=1, mage=2, champion=2), treasure=())

In [7]: x.descend()
Out[7]: (delve=1, depth=3, ability=True, level=(goblin=1, chest=1, dragon=1), party=(fighter=1, mage=2, champion=2), treasure=())

In [8]: x.apply('mage', 'goblin')
Out[8]: (delve=1, depth=3, ability=True, level=(chest=1, dragon=1), party=(fighter=1, mage=1, champion=2), treasure=())

In [9]: x.apply('champion', 'chest')
Out[9]: (delve=1, depth=3, ability=True, level=(dragon=1), party=(fighter=1, mage=1, champion=1), treasure=(talisman=1))

In [10]: x.descend()
Out[10]: (delve=1, depth=4, ability=True, level=(goblin=1, skeleton=1, potion=1, dragon=2), party=(fighter=1, mage=1, champion=1), treasure=(talisman=1))

In [11]: x.apply('mage', 'skeleton')
Out[11]: (delve=1, depth=4, ability=True, level=(goblin=1, potion=1, dragon=2), party=(fighter=1, champion=1), treasure=(talisman=1))

In [12]: x.apply('fighter', 'goblin')
Out[12]: (delve=1, depth=4, ability=True, level=(potion=1, dragon=2), party=(champion=1), treasure=(talisman=1))

In [13]: x.retire()  # Retiring to the tavern immediately starts the next delve
Out[13]: (delve=2, depth=1, experience=4, ability=True, level=(chest=1), party=(cleric=2, thief=1, champion=4), treasure=(talisman=1))

In [14]: x.apply('cleric', 'chest')
Out[14]: (delve=2, depth=1, experience=4, ability=True, level=(), party=(cleric=1, thief=1, champion=4), treasure=(talisman=1, scale=1))

In [15]: x.descend()
Out[15]: (delve=2, depth=2, experience=4, ability=True, level=(goblin=1, skeleton=1), party=(cleric=1, thief=1, champion=4), treasure=(talisman=1, scale=1))

In [16]: x.apply('champion', 'goblin')
Out[16]: (delve=2, depth=2, experience=4, ability=True, level=(skeleton=1), party=(cleric=1, thief=1, champion=3), treasure=(talisman=1, scale=1))

In [17]: x.apply('champion', 'skeleton')
Out[17]: (delve=2, depth=2, experience=4, ability=True, level=(), party=(cleric=1, thief=1, champion=2), treasure=(talisman=1, scale=1))

In [18]: x.descend()
Out[18]: (delve=2, depth=3, experience=4, ability=True, level=(skeleton=1, potion=1, dragon=1), party=(cleric=1, thief=1, champion=2), treasure=(talisman=1, scale=1))

In [19]: x.apply('champion', 'skeleton')
Out[19]: (delve=2, depth=3, experience=4, ability=True, level=(potion=1, dragon=1), party=(cleric=1, thief=1, champion=1), treasure=(talisman=1, scale=1))

In [20]: x.descend()
Out[20]: (delve=2, depth=4, experience=4, ability=True, level=(ooze=1, chest=1, dragon=3), party=(cleric=1, thief=1, champion=1), treasure=(talisman=1, scale=1))

In [21]: x.apply('mage', 'ooze')
---------------------------------------------------------------------------
DrollError                                Traceback (most recent call last)
<ipython-input-21-447da923a2d0> in <module>()
----> 1 x.apply('mage', 'ooze')

~/Build/droll/droll/interactive.py in apply(self, hero, *nouns)
     32         """Apply some named hero or treasure to some collection of nouns."""
     33         self._world = droll.player.apply(
---> 34             self._player, self._world, self._randrange, hero, *nouns)
     35         return self
     36 

~/Build/droll/droll/player.py in apply(player, world, randrange, noun, target, *additional)
     51         else:
     52             raise DrollError("Neither hero {} nor artifact {} available"
---> 53                              .format(noun, artifact))
     54 
     55     # Apply a hero (or hero-like artifact) to some collection of targets.

DrollError: Neither hero mage nor artifact sceptre available

In [22]: x.apply('cleric', 'ooze')
Out[22]: (delve=2, depth=4, experience=4, ability=True, level=(chest=1, dragon=3), party=(thief=1, champion=1), treasure=(talisman=1, scale=1))

In [23]: x.apply('cleric', 'dragon', 'thief', 'champion')  # Three heroes required for a dragon
Out[23]: (delve=2, depth=4, experience=5, ability=True, level=(chest=1), party=(), treasure=(bait=1, scale=1))

In [24]: x.retire()
Out[24]: (delve=3, depth=1, experience=9, ability=True, level=(chest=1), party=(fighter=3, thief=1, champion=2, scroll=1), treasure=(bait=1, scale=1))

In [25]: x.apply('fighter', 'chest')
Out[25]: (delve=3, depth=1, experience=9, ability=True, level=(), party=(fighter=2, thief=1, champion=2, scroll=1), treasure=(bait=1, portal=1, scale=1))

In [26]: x.descend()
Out[26]: (delve=3, depth=2, experience=9, ability=True, level=(ooze=1, chest=1), party=(fighter=2, thief=1, champion=2, scroll=1), treasure=(bait=1, portal=1, scale=1))

In [27]: x.apply('fighter', 'ooze')
Out[27]: (delve=3, depth=2, experience=9, ability=True, level=(chest=1), party=(fighter=1, thief=1, champion=2, scroll=1), treasure=(bait=1, portal=1, scale=1))

In [28]: x.apply('champion', 'chest')
Out[28]: (delve=3, depth=2, experience=9, ability=True, level=(), party=(fighter=1, thief=1, champion=1, scroll=1), treasure=(talisman=1, bait=1, portal=1, scale=1))

In [29]: x.descend()
Out[29]: (delve=3, depth=3, experience=9, ability=True, level=(goblin=2, dragon=1), party=(fighter=1, thief=1, champion=1, scroll=1), treasure=(talisman=1, bait=1, portal=1, scale=1))

In [30]: x.apply('fighter', 'goblin')
Out[30]: (delve=3, depth=3, experience=9, ability=True, level=(dragon=1), party=(thief=1, champion=1, scroll=1), treasure=(talisman=1, bait=1, portal=1, scale=1))

In [31]: x.descend()
Out[31]: (delve=3, depth=4, experience=9, ability=True, level=(goblin=1, skeleton=1, potion=1, dragon=2), party=(thief=1, champion=1, scroll=1), treasure=(talisman=1, bait=1, portal=1, scale=1))

In [32]: x.apply('scroll', 'goblin', 'skeleton')
Out[32]: (delve=3, depth=4, experience=9, ability=True, level=(goblin=1, chest=1, potion=1, dragon=2), party=(thief=1, champion=1), treasure=(talisman=1, bait=1, portal=1, scale=1))

In [33]: x.apply('thief', 'goblin')
Out[33]: (delve=3, depth=4, experience=9, ability=True, level=(chest=1, potion=1, dragon=2), party=(champion=1), treasure=(talisman=1, bait=1, portal=1, scale=1))

In [34]: x.apply('champion', 'chest')
Out[34]: (delve=3, depth=4, experience=9, ability=True, level=(potion=1, dragon=2), party=(), treasure=(talisman=2, bait=1, portal=1, scale=1))

In [35]: x.descend()
Out[35]: (delve=3, depth=5, experience=9, ability=True, level=(skeleton=2, potion=1, dragon=4), party=(), treasure=(talisman=2, bait=1, portal=1, scale=1))

In [36]: x.retire()  # Consumes the town portal and escapes.  No new delve as we had three.
Out[36]: (delve=3, experience=14, ability=True, party=(), treasure=(talisman=2, bait=1, scale=1))

In [37]: x.score()
Out[37]: 18
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
