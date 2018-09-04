Droll
=====
## What is it?

Droll is an implementation of some of the game mechanics underneath [Dungeon
Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll), a product of
[Tasty Minstrel Games](http://playtmg.com/).  It is in no way affiliated
with either the game or the publisher.

## What does it look like?

```
$ ipython
Python 3.5.5 | packaged by conda-forge | (default, Jul 23 2018, 23:45:43)
Type 'copyright', 'credits' or 'license' for more information
IPython 6.5.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: from droll import Interactive

In [2]: x = Interactive()

In [3]: x
Out[3]: (delve=1, depth=1, ability=True, level=(goblin=1), party=(fighter=1, cleric=1, mage=1, thief=1, scroll=3), treasure=())

In [4]: x.apply('fighter', 'goblin')
Out[4]: (delve=1, depth=1, ability=True, level=(), party=(cleric=1, mage=1, thief=1, scroll=3), treasure=())

In [5]: x.descend()
Out[5]: (delve=1, depth=2, ability=True, level=(skeleton=1, dragon=1), party=(cleric=1, mage=1, thief=1, scroll=3), treasure=())

In [6]: x.apply('mage', 'skeleton')
Out[6]: (delve=1, depth=2, ability=True, level=(dragon=1), party=(cleric=1, thief=1, scroll=3), treasure=())

In [7]: x.descend()
Out[7]: (delve=1, depth=3, ability=True, level=(skeleton=1, ooze=1, chest=1, dragon=1), party=(cleric=1, thief=1, scroll=3), treasure=())

In [8]: x.apply('scroll', 'skeleton', 'ooze')
Out[8]: (delve=1, depth=3, ability=True, level=(goblin=1, chest=2, dragon=1), party=(cleric=1, thief=1, scroll=2), treasure=())

In [9]: x.apply('scroll', 'goblin')
Out[9]: (delve=1, depth=3, ability=True, level=(ooze=1, chest=2, dragon=1), party=(cleric=1, thief=1, scroll=1), treasure=())

In [10]: x.apply('scroll', 'ooze')
Out[10]: (delve=1, depth=3, ability=True, level=(chest=3, dragon=1), party=(cleric=1, thief=1), treasure=())

In [11]: x.apply('thief', 'chest')
Out[11]: (delve=1, depth=3, ability=True, level=(dragon=1), party=(cleric=1), treasure=(sceptre=1, elixir=1, scale=1))

In [12]: x.retire()
Out[12]: (delve=2, depth=1, experience=3, ability=True, level=(goblin=1), party=(fighter=2, cleric=1, champion=3, scroll=1), treasure=(sceptre=1, elixir=1, scale=1))

```

## What is implemented?

Not much more than default player semantics and treasures (i.e. no abilities, no
promotion after experience level 5).

## Why implement it?

Seemed like a fun thing to hack on.  Possibly a fun problem to throw into
reinforcement learning algorithms as (a) the strategy isn't too complicated, (b)
the score is very straightforward, and (c) there's some probabilistic behavior
in both the basic die mechanics as well as the expected value of the treasure.

Also, I was curious how much code was required to capture a game that
small children will catch onto in the space of 20 minutes.

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
