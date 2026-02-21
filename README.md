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
All base game heroes are implemented.
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
said, I've done such things in neither 2018 nor 2026.

## What does it look like?

```
$ droll --help
usage: droll [-h] [--seed N] [--mechanical]
             {Default,Crusader,Enchantress,HalfGoblin,Knight,Mercenary,Minstrel,Occultist,Spellsword}

Command-line version of droll.

positional arguments:
  {Default,Crusader,Enchantress,HalfGoblin,Knight,Mercenary,Minstrel,Occultist,Spellsword}
                        Select the hero for this game.

options:
  -h, --help            show this help message and exit
  --seed N              An integer to seed random number generation.
  --mechanical          Use mechanical display format.


$ droll --seed 7 Knight

Score 0:   delve 1 with experience 0
Treasure:  None
Available: ability descend
Party:     fighter×2 cleric mage thief champion×2
00 Knight> help

Feasible commands (help <command>):
===================================
ability  descend

Miscellaneous help topics:
==========================
score  treasure


Score 0:   delve 1 with experience 0
Treasure:  None
Available: ability descend
Party:     fighter×2 cleric mage thief champion×2
00 Knight> descend

Score 0:   depth 1 in delve 1 with experience 0
Treasure:  None
Available: ability retreat
Party:     fighter×2 cleric mage thief champion×2
Dungeon:   goblin
01 Knight> help fighter
Fighters defeat ALL goblins but only ONE skeleton or ooze:

        fighter goblin                # Defeat all goblins
        fighter skeleton              # Defeat one skeleton
        fighter ooze                  # Defeat one ooze
        fighter chest                 # Open one chest
        fighter potion mage thief     # Drink 2 potions obtaining mage, thief
        fighter dragon cleric mage    # Attack dragon with party of 3


Score 0:   depth 1 in delve 1 with experience 0
Treasure:  None
Available: ability retreat
Party:     fighter×2 cleric mage thief champion×2
Dungeon:   goblin
01 Knight> fighter goblin

Score 0:   depth 1 in delve 1 with experience 0
Treasure:  None
Available: ability descend retire undo
Party:     fighter cleric mage thief champion×2
Dungeon:   None
02 Knight> descend

Score 0:   depth 2 in delve 1 with experience 0
Treasure:  None
Available: ability retreat
Party:     fighter cleric mage thief champion×2
Dungeon:   ooze potion
03 Knight> mage ooze

Score 0:   depth 2 in delve 1 with experience 0
Treasure:  None
Available: ability descend retire undo
Party:     fighter cleric thief champion×2
Dungeon:   potion
04 Knight> champion potion mage

Score 0:   depth 2 in delve 1 with experience 0
Treasure:  None
Available: ability descend retire undo
Party:     fighter cleric mage thief champion
Dungeon:   None
05 Knight> descend

Score 0:   depth 3 in delve 1 with experience 0
Treasure:  None
Available: ability retreat
Party:     fighter cleric mage thief champion
Dungeon:   goblin skeleton potion
06 Knight> help ability
Invoke the player's ability.

    Convert all monster faces into dragon dice.

Score 0:   depth 3 in delve 1 with experience 0
Treasure:  None
Available: ability retreat
Party:     fighter cleric mage thief champion
Dungeon:   goblin skeleton potion
06 Knight> ability

Score 0:   depth 3 in delve 1 with experience 0
Treasure:  None
Available: descend retire undo
Party:     fighter cleric mage thief champion
Dungeon:   potion dragon×2
07 Knight> descend

Score 0:   depth 4 in delve 1 with experience 0
Treasure:  None
Available: retreat
Party:     fighter cleric mage thief champion
Dungeon:   goblin×2 chest×2 dragon×2
08 Knight> fighter goblin

Score 0:   depth 4 in delve 1 with experience 0
Treasure:  None
Available: descend retire undo
Party:     cleric mage thief champion
Dungeon:   chest×2 dragon×2
09 Knight> thief chest

Score 2:   depth 4 in delve 1 with experience 0
Treasure:  elixir talisman
Available: descend retire
Party:     cleric mage champion
Dungeon:   dragon×2
10 Knight> descend

Score 2:   depth 5 in delve 1 with experience 0
Treasure:  elixir talisman
Available: retreat
Party:     cleric mage champion
Dungeon:   goblin×2 chest potion×2 dragon×2
11 Knight> champion goblin

Score 2:   depth 5 in delve 1 with experience 0
Treasure:  elixir talisman
Available: descend retire undo
Party:     cleric mage
Dungeon:   chest potion×2 dragon×2
12 Knight> mage potion champion thief

Score 2:   depth 5 in delve 1 with experience 0
Treasure:  elixir talisman
Available: descend retire undo
Party:     cleric thief champion
Dungeon:   chest dragon×2
13 Knight> thief chest

Score 3:   depth 5 in delve 1 with experience 0
Treasure:  elixir sceptre talisman
Available: descend retire
Party:     cleric champion
Dungeon:   dragon×2
14 Knight> help retreat
Retreat from the dungeon while monsters remain.

        Automatically starts a new delve or ends game, as suitable.

Score 3:   depth 5 in delve 1 with experience 0
Treasure:  elixir sceptre talisman
Available: descend retire
Party:     cleric champion
Dungeon:   dragon×2
14 Knight> retire

Score 8:      delve 2 with experience 5
Treasure:     elixir sceptre talisman
Available:    ability descend
Party:        fighter cleric champion×5
15 DragonSlayer> descend

Score 8:      depth 1 in delve 2 with experience 5
Treasure:     elixir sceptre talisman
Available:    ability descend retire
Party:        fighter cleric champion×5
Dungeon:      chest
16 DragonSlayer> champion chest

Score 9:      depth 1 in delve 2 with experience 5
Treasure:     elixir sceptre talisman×2
Available:    ability descend retire
Party:        fighter cleric champion×4
Dungeon:      None
17 DragonSlayer> descend

Score 9:      depth 2 in delve 2 with experience 5
Treasure:     elixir sceptre talisman×2
Available:    ability retreat
Party:        fighter cleric champion×4
Dungeon:      goblin skeleton
18 DragonSlayer> talisman goblin

Score 9:      depth 2 in delve 2 with experience 5
Treasure:     elixir sceptre talisman×2
Available:    ability retreat undo
Party:        fighter champion×4
Dungeon:      skeleton
19 DragonSlayer> sceptre skeleton

Score 8:      depth 2 in delve 2 with experience 5
Treasure:     elixir talisman×2
Available:    ability descend retire undo
Party:        fighter champion×4
Dungeon:      None
20 DragonSlayer> elixir mage

Score 7:      depth 2 in delve 2 with experience 5
Treasure:     talisman×2
Available:    ability descend retire undo
Party:        fighter mage champion×4
Dungeon:      None
21 DragonSlayer> ^D
```

## How to play

You get 3 delves into the dungeon per game.  Each delve proceeds
as follows:

1. Roll 7 party dice producing random fighters, clerics, mages,
   thieves, champions, and scrolls.
2. Descend one depth at a time.  At each depth, new dungeon dice
   appear: goblins, skeletons, ooze, chests, potions, and dragons.
3. Use party members to defeat monsters, open chests, and quaff
   potions.  Monsters must be cleared before opening chests, quaffing
   potions, or descending further.
4. After defeating any monsters, "retire" from the delve to earn
   experience equal to your depth.  If monsters remain and you cannot
   defeat them, instead "retreat" but earn nothing.

Combat: each party member can target any monster, but specialists
defeat all of their favored type while non-specialists defeat one:

| Hero     | Defeats all | Defeats one each       | Special          |
|----------|-------------|------------------------|------------------|
| fighter  | goblin      | skeleton, ooze         | opens one chest  |
| cleric   | skeleton    | goblin, ooze           | opens one chest  |
| mage     | ooze        | goblin, skeleton       | opens one chest  |
| thief    | —           | goblin, skeleton, ooze | opens all chests |
| champion | all three   | —                      | opens all chests |
| scroll   | —           | —                      | quaffs potions, rerolls dice |

Scrolls cannot target monsters directly.  Instead, spend a scroll
via `reroll <targets>` to re-roll any dungeon or party dice,
for example `reroll goblin skeleton` re-rolls those two dice.

Dragons accumulate across depths.  At 3 or more, the dragon
blocks progress and must be fought by 3 distinct party members.
Defeating a dragon earns 1 experience and draws 1 treasure.
A ring or portal can bypass a blocking dragon automatically.

Display notation: `name×N` means N dice of that type (e.g.
`champion×3`).  In the party line, `name~D` or `name×N~D` means
D of those dice will be discarded at the next regroup—these are
temporary allies converted from monsters by hero abilities.
For example, `thief×2~1` means 2 thieves, 1 temporary.

Level up: at 5+ experience your hero gains a new name and
upgraded abilities, for example Knight becomes DragonSlayer.

Abilities: each hero has a once-per-delve special ability.
Type `help ability` in-game to see what your hero can do.

### Hero abilities

| Hero        | Ability                          | Syntax example                    | Requires                |
|-------------|----------------------------------|-----------------------------------|-------------------------|
| Default     | No special ability               | `ability`                         | —                       |
| Crusader    | Add 1 fighter or cleric          | `ability` or `ability cleric`     | —                       |
| Enchantress | Transform 1 monster into potion  | `ability goblin`                  | 1 monster target        |
| HalfGoblin  | Transform 1 goblin into thief    | `ability` or `ability goblin`     | goblin present          |
| Knight      | Convert all monsters to dragons  | `ability`                         | —                       |
| Mercenary   | Defeat any 2 monsters            | `ability goblin skeleton`         | 1–2 monster targets     |
| Minstrel    | Discard all dragon dice          | `ability`                         | —                       |
| Occultist   | Transform 1 skeleton into fighter| `ability` or `ability skeleton`   | skeleton present        |
| Spellsword  | Add 1 fighter or mage            | `ability` or `ability mage`       | —                       |

### Level-up progression

At 5+ experience, each hero advances to a stronger form with an
upgraded ability and enhanced party interactions:

| Base        | Advanced      | New ability                          | Party change                            |
|-------------|---------------|--------------------------------------|-----------------------------------------|
| Crusader    | Paladin       | Consume treasure to clear dungeon    | Fighter/Cleric interchangeable          |
| Enchantress | Beguiler      | Transform up to 2 monsters to potion | Scrolls become offensive combatants     |
| HalfGoblin  | Chieftain     | Transform up to 2 goblins to thieves | Chests/potions accessible during combat |
| Knight      | DragonSlayer  | Convert monsters to dragons          | Dragon needs only 2 distinct heroes     |
| Mercenary   | Commander     | Reroll any number of dice            | Fighter defeats extra monster per use   |
| Minstrel    | Bard          | Discard all dragon dice              | Champion defeats extra monster per use  |
| Occultist   | Necromancer   | Transform up to 2 skeletons to fighters | Cleric/Mage interchangeable          |
| Spellsword  | Battlemage    | Discard all monsters, chests, potions | Fighter/Mage interchangeable           |

## How does scoring work?

Your score has two components: experience and treasure.

Experience is earned by retiring from a delve.  When you retire,
you gain experience equal to the depth you reached in the dungeon.
For example, retiring at depth 5 earns 5 experience points.
Retreating earns no experience.

Treasure is drawn randomly from a shared box whenever you open
chests.  Each piece of treasure scores 1 point, with two exceptions:

| Treasure   | Points | Notes                                  |
|------------|--------|----------------------------------------|
| sword      | 1      | Usable as a fighter                    |
| talisman   | 1      | Usable as a cleric                     |
| sceptre    | 1      | Usable as a mage                       |
| tools      | 1      | Usable as a thief                      |
| scroll     | 1      | Usable as a scroll                     |
| elixir     | 1      | Revive party members                   |
| bait       | 1      | Lure the dragon                        |
| portal     | 2      | Town portal to escape the dungeon      |
| ring       | 1      | Sneak past a dragon                    |
| scale      | 1      | But a pair of scales scores 4          |

Town portals are worth 2 points each.  Scales score 1 point each,
but every pair of scales scores 4 rather than 2, a +2 bonus per pair.
Using a treasure during a delve removes it from your collection and
reduces your score accordingly.

Total score = experience + treasure points.

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

Run unit tests with:
```
pytest
```
