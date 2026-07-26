Droll
=====
[![CircleCI](https://circleci.com/gh/RhysU/droll/tree/master.svg?style=svg)](https://circleci.com/gh/RhysU/droll/tree/master)

## What is it?

Droll implements [Dungeon Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll),
a product of [Tasty Minstrel Games](https://boardgamegeek.com/boardgamepublisher/9499/tasty-minstrel-games).
Droll is not affiliated with the game or its publisher.  Buy
their excellent game, learn [how to play](https://www.youtube.com/watch?v=PzZ8hUzXBtE)
it, and then come back here.

## Why implement it?

In 2018, it seemed like a fun project.  I was also curious how
much code was required to fully implement a game that children can
learn in 20 minutes.  In 2026, this codebase has been a self-contained
playspace for LLM-assisted coding.

This game has always seemed like a good candidate for reinforcement
learning as the strategy isn't too complicated, the scoring
rules are very straightforward, and there's probabilistic behavior in both
the basic die mechanics and the expected value of the treasure.
That said, I haven't pursued that in either 2018 or 2026.

## What does it look like?

Droll is an interactive command-line interface for playing the base game without
expansions.  All base game heroes are implemented.  Tab completion is available
for commands and arguments, adapting to the current game state.  The rules are
explained in the below section "How to play".  Here is a taste of the gameplay
as a Knight:

```
$ droll --help
usage: droll [-h] [--seed N]
             {Crusader,Enchantress,HalfGoblin,Knight,Mercenary,Minstrel,Occultist,Spellsword}

Command-line version of droll.

positional arguments:
  {Crusader,Enchantress,HalfGoblin,Knight,Mercenary,Minstrel,Occultist,Spellsword}
                        Select the hero for this game.

options:
  -h, --help            show this help message and exit
  --seed N              An integer to seed random number generation.


$ droll --seed 7 Knight
── Knight ────────────────────────────────────────
Convert all monster faces into dragon dice.
Try: ability

Score 0:  delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: descend
Party:    fighter×2 cleric mage thief champion×2
Dungeon:  (empty)
00 Knight> descend

Score 0:  depth 1 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: ability retreat(+0 score)
Party:    fighter×2 cleric mage thief champion×2
Dungeon:  goblin
01 Knight> help fighter
Fighters defeat ALL goblins but only ONE skeleton or ooze:

        fighter goblin                # Defeat all goblins
        fighter skeleton              # Defeat one skeleton
        fighter ooze                  # Defeat one ooze
        fighter chest                 # Open one chest
        fighter potion mage thief       # Drink 2 potions obtaining mage, thief
        fighter dragon cleric mage      # Attack dragon with party of 3


Score 0:  depth 1 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: ability retreat(+0 score)
Party:    fighter×2 cleric mage thief champion×2
Dungeon:  goblin
01 Knight> fighter goblin

Score 0:  depth 1 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: descend retire(+1 score) undo
Party:    fighter cleric mage thief champion×2
Dungeon:  (empty)
02 Knight> descend

Score 0:  depth 2 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: ability retreat(+0 score)
Party:    fighter cleric mage thief champion×2
Dungeon:  ooze potion
03 Knight> mage ooze

Score 0:  depth 2 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: descend retire(+2 score) undo
Party:    fighter cleric thief champion×2
Dungeon:  potion
04 Knight> champion potion mage

Score 0:  depth 2 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: descend retire(+2 score) undo
Party:    fighter cleric mage thief champion
Dungeon:  (empty)
05 Knight> descend

Score 0:  depth 3 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: ability retreat(+0 score)
Party:    fighter cleric mage thief champion
Dungeon:  goblin skeleton potion
06 Knight> help ability
Invoke the player's ability.

    Convert all monster faces into dragon dice.

    Example: ability

Score 0:  depth 3 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: ability retreat(+0 score)
Party:    fighter cleric mage thief champion
Dungeon:  goblin skeleton potion
06 Knight> ability

Score 0:  depth 3 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: descend retire(+3 score) undo
Party:    fighter cleric mage thief champion
Dungeon:  potion dragon×2
07 Knight> descend

Score 0:  depth 4 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: retreat(+0 score)
Party:    fighter cleric mage thief champion
Dungeon:  goblin×2 chest×2 dragon×2
08 Knight> fighter goblin

Score 0:  depth 4 in delve 1 with 0 XP plus 0 treasure
Treasure: (empty)
Consider: descend retire(+4 score) undo
Party:    cleric mage thief champion
Dungeon:  chest×2 dragon×2
09 Knight> thief chest

Score 2:  depth 4 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: descend retire(+4 score)
Party:    cleric mage champion
Dungeon:  dragon×2
10 Knight> descend

Score 2:  depth 5 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: retreat(+0 score)
Party:    cleric mage champion
Dungeon:  goblin×2 chest potion×2 dragon×2
11 Knight> champion goblin

Score 2:  depth 5 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: descend retire(+5 score) undo
Party:    cleric mage
Dungeon:  chest potion×2 dragon×2
12 Knight> mage potion champion thief

Score 2:  depth 5 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: descend retire(+5 score) undo
Party:    cleric thief champion
Dungeon:  chest dragon×2
13 Knight> thief chest

Score 3:  depth 5 in delve 1 with 0 XP plus 3 treasure
Treasure: elixir sceptre talisman
Consider: descend retire(+5 score)
Party:    cleric champion
Dungeon:  dragon×2
14 Knight> retire
```

In addition to the commands shown on the "Consider:" line,
party members and treasures in your possession are valid
commands.  Type "help" to see the full list.

The default display uses color when writing to a terminal.
Press Ctrl+D to exit at any time.

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
4. After clearing all monsters, "retire" from the delve to earn
   experience equal to your depth.  You must descend at least once
   before retiring.  If monsters remain and you cannot defeat them,
   you must instead "retreat" and earn nothing.  However, if you
   hold a town portal, retreating consumes it automatically to
   escape, earning experience equal to your depth.  When you have
   no way to defeat the remaining monsters, retreat is your only
   option.

Undo: you can `undo` any command that did not involve rolling dice or drawing treasure.

Combat: each party die you spend can target any monster type.
Against a favored type it defeats all at once; otherwise it
defeats one:

| Hero     | Defeats all | Defeats one            | Special          |
|----------|-------------|------------------------|------------------|
| fighter  | goblin      | skeleton, ooze         | opens one chest  |
| cleric   | skeleton    | goblin, ooze           | opens one chest  |
| mage     | ooze        | goblin, skeleton       | opens one chest  |
| thief    | —           | goblin, skeleton, ooze | opens all chests |
| champion | goblin, skeleton, ooze | —             | opens all chests |
| scroll   | —           | —                      | quaffs potions, rerolls dice |

Potions: any party member can quaff potions.  The syntax is
`<drinker> potion <type1> <type2> ...` where you specify one
die type per potion to recover.  For example,
`fighter potion mage thief` spends the fighter to drink 2
potions, adding a mage and thief to your party.  The number
of die types you specify must equal the number of potion dice
in the dungeon.

Scrolls cannot target monsters directly.  The `reroll` command
consumes one scroll and re-rolls any number of dungeon or party
dice, for example `reroll goblin skeleton` re-rolls those two
dice.  A scroll can also quaff potions: `scroll potion fighter`
adds a fighter to your party.

Scroll behavior varies by hero (see
[Hero abilities](#hero-abilities) below): Enchantress/Beguiler can
use a scroll as any companion, Knight converts scrolls
to champions during party roll, and Mercenary/Commander receives one
bonus scroll, discarded on regroup.

Dragon dice accumulate across depths.  At 3 or more, dragons
block progress and must be fought by 3 party members of
different types.  Defeating a dragon earns 1 experience and
draws 1 treasure.

Two treasures affect dungeon progress:
a ring lets you ignore a blocking dragon without removing the
dragon dice, and a portal immediately ends the delve, earning
experience equal to your current depth.  When monsters or
dragons block, retiring or retreating consumes a portal
automatically if one is available; a ring is preferred over a
portal when only a dragon blocks.

Display notation:

- `name×N` means N dice of that type, for example `champion×3`.
- Dragon dice always show their count (e.g. `dragon×1`,
  `dragon×2`) because at 3 or more they block progress.
- `name~D` or `name×N~D` in the party line means `D` of those
  dice are temporary and will be discarded at the next regroup.
  Regroup is the cleanup phase when descending, retiring, or
  retreating — temporary dice are allies converted from monsters
  by hero abilities.  For example, `thief×2~1` means 2 thieves,
  1 of which is temporary.
- The prompt shows the move number and current hero name,
  for example `00 Knight>`.

### Hero abilities

| Hero        | Ability                          | Syntax example                    | Requires                |
|-------------|----------------------------------|-----------------------------------|-------------------------|
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
upgraded ability and a party change.  "Interchangeable" means
those party types can substitute for each other in any command;
other entries describe different mechanical bonuses:

| Base        | Advanced      | New ability                          | Party change                            |
|-------------|---------------|--------------------------------------|-----------------------------------------|
| Crusader    | Paladin       | Consume treasure to clear dungeon    | Heroes fighter and cleric are interchangeable           |
| Enchantress | Beguiler      | Transform up to 2 monsters to potion | *(unchanged)*                                      |
| HalfGoblin  | Chieftain     | Transform up to 2 goblins to thieves | Open chests/quaff potions before clearing monsters |
| Knight      | DragonSlayer  | *(unchanged)*                        | Dragon requires only 2 party members of different types |
| Mercenary   | Commander     | Reroll any number of dice            | Each fighter defeats one additional monster         |
| Minstrel    | Bard          | *(unchanged)*                        | Each champion defeats one additional monster        |
| Occultist   | Necromancer   | Transform up to 2 skeletons to fighters | Heroes cleric and mage are interchangeable            |
| Spellsword  | Battlemage    | Discard all monsters, chests, potions | Heroes fighter and mage are interchangeable              |

## How does scoring work?

Your score has two components: experience earned by retiring
and treasure.  Experience accumulates across delves.  For
example, retiring at depth 5 earns 5 experience; if you then
retire at depth 3 in the next delve, you have 8 experience total.

Treasure is drawn randomly from a shared box whenever you open
chests.  Each piece of treasure scores 1 point, except portal (2)
and scale (1 each, but 4 per pair).

| Treasure   | Points | Notes                                  |
|------------|--------|----------------------------------------|
| sword      | 1      | Usable as a fighter                    |
| talisman   | 1      | Usable as a cleric                     |
| sceptre    | 1      | Usable as a mage                       |
| tools      | 1      | Usable as a thief                      |
| scroll     | 1      | Usable as a scroll                     |
| elixir     | 1      | Add a party member of any type         |
| bait       | 1      | Lure the dragon                        |
| portal     | 2      | Town portal to escape the dungeon      |
| ring       | 1      | Sneak past a dragon                    |
| scale      | 1      | Each pair scores 4 (not 2)             |

Treasures are used by typing them as commands.  `sword goblin`
acts as a fighter, `talisman skeleton` acts as a cleric,
`tools chest` acts as a thief, `elixir mage` adds a mage,
and `bait` converts all monsters to dragons.
Using a treasure during a delve removes it from your collection
and reduces your score accordingly.

Total score = experience + treasure points.

## Quick Start

Requires Python 3.9+.  Clone this repository, install (which
provides the `droll` command), and run:

```
pip install -e .
droll --help
```

Or, without installing, run directly:
```
PYTHONPATH=. python3 -m droll --help
```

## Testing

Run unit tests with:
```
pytest
```
