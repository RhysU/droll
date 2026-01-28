Droll
=====
[![CircleCI](https://circleci.com/gh/RhysU/droll/tree/master.svg?style=svg)](https://circleci.com/gh/RhysU/droll/tree/master)

## What is it?

Droll implements [Dungeon Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll),
a product of [Tasty Minstrel Games](http://playtmg.com/).  Droll is
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

```
$ droll --help
usage: droll [-h] [--seed N]
             {Default,Crusader,Enchantress,Knight,Minstrel,Spellsword}

Command-line version of droll.

positional arguments:
  {Default,Crusader,Enchantress,Knight,Minstrel,Spellsword}
                        Select the hero for this game.

options:
  -h, --help            show this help message and exit
  --seed N              An integer to seed random number generation.


$ droll --seed 7 Knight

Score 0:   delve 1 with experience 0
Treasure:  none
Available: ability descend
Party:     fighter×2 cleric mage thief champion×2
Knight> help

Feasible commands (help <command>):
===================================
ability  descend


Score 0:   delve 1 with experience 0
Treasure:  none
Available: ability descend
Party:     fighter×2 cleric mage thief champion×2
Knight> descend

Score 0:   depth 1 in delve 1 with experience 0
Treasure:  none
Available: ability retreat
Party:     fighter×2 cleric mage thief champion×2
Dungeon:   goblin
Knight> help fighter
Attack monsters, quaff potions, and open chests with a fighter like so:

        champion skeleton            # Attack skeleton(s)
        thief chest                  # Open chest(s)
        fighter potion mage thief    # Drink 2 potions obtaining mage, thief
        mage dragon champion cleric  # Attack dragon with party of 3


Score 0:   depth 1 in delve 1 with experience 0
Treasure:  none
Available: ability retreat
Party:     fighter×2 cleric mage thief champion×2
Dungeon:   goblin
Knight> fighter goblin

Score 0:   depth 1 in delve 1 with experience 0
Treasure:  none
Available: ability descend retire undo
Party:     fighter cleric mage thief champion×2
Knight> descend

Score 0:   depth 2 in delve 1 with experience 0
Treasure:  none
Available: ability retreat
Party:     fighter cleric mage thief champion×2
Dungeon:   ooze potion
Knight> mage ooze

Score 0:   depth 2 in delve 1 with experience 0
Treasure:  none
Available: ability descend retire undo
Party:     fighter cleric thief champion×2
Dungeon:   potion
Knight> champion potion mage

Score 0:   depth 2 in delve 1 with experience 0
Treasure:  none
Available: ability descend retire undo
Party:     fighter cleric mage thief champion
Knight> descend

Score 0:   depth 3 in delve 1 with experience 0
Treasure:  none
Available: ability retreat
Party:     fighter cleric mage thief champion
Dungeon:   goblin skeleton potion
Knight> help ability
Invoke the player's ability.

    Convert all monster faces into dragon dice.

Score 0:   depth 3 in delve 1 with experience 0
Treasure:  none
Available: ability retreat
Party:     fighter cleric mage thief champion
Dungeon:   goblin skeleton potion
Knight> ability

Score 0:   depth 3 in delve 1 with experience 0
Treasure:  none
Available: descend retire undo
Party:     fighter cleric mage thief champion
Dungeon:   potion dragon×2
Knight> descend

Score 0:   depth 4 in delve 1 with experience 0
Treasure:  none
Available: retreat
Party:     fighter cleric mage thief champion
Dungeon:   goblin×2 chest×2 dragon×2
Knight> fighter goblin

Score 0:   depth 4 in delve 1 with experience 0
Treasure:  none
Available: descend retire undo
Party:     cleric mage thief champion
Dungeon:   chest×2 dragon×2
Knight> thief chest

Score 2:   depth 4 in delve 1 with experience 0
Treasure:  elixir talisman
Available: descend retire
Party:     cleric mage champion
Dungeon:   dragon×2
Knight> descend

Score 2:   depth 5 in delve 1 with experience 0
Treasure:  elixir talisman
Available: retreat
Party:     cleric mage champion
Dungeon:   goblin×2 chest potion×2 dragon×2
Knight> champion goblin

Score 2:   depth 5 in delve 1 with experience 0
Treasure:  elixir talisman
Available: descend retire undo
Party:     cleric mage
Dungeon:   chest potion×2 dragon×2
Knight> mage potion champion thief

Score 2:   depth 5 in delve 1 with experience 0
Treasure:  elixir talisman
Available: descend retire undo
Party:     cleric thief champion
Dungeon:   chest dragon×2
Knight> thief chest

Score 3:   depth 5 in delve 1 with experience 0
Treasure:  elixir sceptre talisman
Available: descend retire
Party:     cleric champion
Dungeon:   dragon×2
Knight> help retreat
Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve or ends game, as suitable.

Score 3:   depth 5 in delve 1 with experience 0
Treasure:  elixir sceptre talisman
Available: descend retire
Party:     cleric champion
Dungeon:   dragon×2
Knight> retire

Score 8:      delve 2 with experience 5
Treasure:     elixir sceptre talisman
Available:    ability descend
Party:        fighter cleric champion×5
DragonSlayer> descend

Score 8:      depth 1 in delve 2 with experience 5
Treasure:     elixir sceptre talisman
Available:    ability descend retire
Party:        fighter cleric champion×5
Dungeon:      chest
DragonSlayer> champion chest

Score 9:      depth 1 in delve 2 with experience 5
Treasure:     elixir sceptre talisman×2
Available:    ability descend retire
Party:        fighter cleric champion×4
DragonSlayer> descend

Score 9:      depth 2 in delve 2 with experience 5
Treasure:     elixir sceptre talisman×2
Available:    ability retreat
Party:        fighter cleric champion×4
Dungeon:      goblin skeleton
DragonSlayer> talisman goblin

Score 9:      depth 2 in delve 2 with experience 5
Treasure:     elixir sceptre talisman×2
Available:    ability retreat undo
Party:        fighter champion×4
Dungeon:      skeleton
DragonSlayer> sceptre skeleton

Score 8:      depth 2 in delve 2 with experience 5
Treasure:     elixir talisman×2
Available:    ability descend retire undo
Party:        fighter champion×4
DragonSlayer> elixir mage

Score 7:      depth 2 in delve 2 with experience 5
Treasure:     talisman×2
Available:    ability descend retire
Party:        fighter mage champion×4
DragonSlayer> ^D
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
