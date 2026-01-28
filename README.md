Droll
=====
[![CircleCI](https://circleci.com/gh/RhysU/droll/tree/master.svg?style=svg)](https://circleci.com/gh/RhysU/droll/tree/master)

## What is it?

Droll implements [Dungeon Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll),
a product of [Tasty Minstrel Games](http://playtmg.com/).  Droll code is
in no way affiliated with either the game or the publisher.  Go buy their
excellent game, learn [how to play](https://www.youtube.com/watch?v=PzZ8hUzXBtE)
it, and then come back here.

## What is implemented?

A REPL providing the classic game, including tab completion to speed playing.
All heroes are implement with the exception of:

 - Half-Goblin advancing to Chieftain
 - Occultist advancing to Necromancer

Additionally, a "Default" hero with no special abilities is present.

## Why implement it?

In 2018, it seemed like a fun thing to hack on.  Also, I was curious how
much code was required to capture a game that children will catch onto in
the space of 20 minutes.  In 2026, this codebase has been a self-contained
playspace for LLM-assisted coding.

This game has always seemed like a neat problem to throw into reinforcement
learning algorithms as (a) the strategy isn't too complicated, (b) the score
is very straightforward, and (c) there's probabilistic behavior in both the
basic die mechanics as well as the expected value of the treasure.  That
said, I've not done such things in either 2018 nor 2026.

## What does it look like?

NOTE: There's an `--experimental` option providing a superior experience.

```
$ droll --help
usage: droll [-h] [--seed N] {Default,Crusader,Enchantress,Knight,Minstrel,Spellsword}

Command-line version of droll.

positional arguments:
  {Default,Crusader,Knight,Minstrel,Spellsword}
                        Select the hero for this game.

optional arguments:
  -h, --help            show this help message and exit
  --seed N              An integer to seed random number generation.


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

## Without Installation

Clone this repository then run via:

```
PYTHONPATH=. python3 -m droll --help
```

## Installation

Install the package in development mode with:
```
pip install -e .
```

## Testing

When not installed, run unit tests with:
```
PYTHONPATH=. python -m pytest ./tests/
```

When installed, run unit tests with:
```
python -m pytest
```
