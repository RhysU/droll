# Droll Input Validation Report

## Methodology

Played the sample game from the README (`droll --seed 7 Knight`) to confirm all
outputs match exactly, then systematically injected malformed input to find bugs.

## Sample Game Verification

The full sample game from the README (moves 00–21, including the Knight →
DragonSlayer level-up) reproduces **exactly** — every line of output matches.

## Findings

### BUG 1 (Critical): Crash via dunder attribute injection in ability targets

Passing Python dunder attribute names as ability targets causes **unhandled
exceptions** that crash the game with a full stack trace.

**Reproduction:**

```
printf 'descend\nability __class__\n' | droll --seed 7 Enchantress
printf 'descend\nability __class__\n' | droll --seed 7 Mercenary
```

**Result:** Process terminates with exit code 1 and a `TypeError` traceback:

```
TypeError: unsupported operand type(s) for -: 'type' and 'int'
```

The root cause is `decrement_dungeon()` in `droll/dungeon.py` at line 60 — it
calls `getattr(dungeon, target)` where `target` is unsanitized user input.
When `target` is `__class__`, `getattr` returns the class object itself, and
the subsequent `prior_targets - 1` arithmetic fails.

**Affected heroes:** Enchantress and Mercenary (their abilities pass targets
directly to `decrement_dungeon` without validating the target is a known
dungeon face).  HalfGoblin and Occultist are not affected because their
abilities validate the target name earlier.

### BUG 2 (Critical): Crash via dunder attribute injection in combat targets

Passing dunder names as combat targets also crashes the game:

```
printf 'descend\nfighter __class__\n' | droll --seed 7 Knight
printf 'descend\nchampion __class__\n' | droll --seed 7 Knight
```

**Result:** Process terminates with `AttributeError`:

```
AttributeError: 'Dungeon' object has no attribute 'party'
```

### BUG 3 (High): Phantom treasure — sword/talisman/sceptre/tools work without inventory

The treasure commands `sword`, `talisman`, `sceptre`, and `tools` can be used
even when the player **does not possess** that treasure.  Instead of checking
the treasure inventory, the game silently consumes the corresponding party
member (fighter, cleric, mage, thief respectively).

**Reproduction:**

```
printf 'descend\nsword goblin\n' | droll --seed 7 Knight
```

**Result:** The goblin is defeated and a **fighter** is consumed from the
party, even though `Treasure: None`.  No sword is deducted (there is none
to deduct).  Observed for all four weapon-type treasures:

| Command          | Party member consumed | Treasure deducted |
|------------------|-----------------------|-------------------|
| `sword goblin`   | fighter               | None (bug)        |
| `talisman goblin`| cleric                | None (bug)        |
| `sceptre goblin` | mage                  | None (bug)        |
| `tools goblin`   | thief                 | None (bug)        |

Other treasures (`elixir`, `bait`, `ring`, `portal`) correctly validate
inventory with the message `'<name>' not in player's treasure.`

### BUG 4 (Medium): Internal error messages leaked to user via potion recovery

Requesting invalid types when drinking potions leaks raw Python exception
messages instead of user-friendly errors:

```
printf 'descend\nfighter goblin\ndescend\nmage ooze\nchampion potion dragon\n' \
  | droll --seed 7 Knight
```

**Result (non-crashing but exposes internals):**

```
'Party' object has no attribute 'dragon'
'Party' object has no attribute 'goblin'
'Party' object has no attribute 'potion'
'Party' object has no attribute 'chest'
```

And with dunder attributes:

```
champion potion __class__  →  unsupported operand type(s) for +: 'type' and 'int'
champion potion __dict__   →  unsupported operand type(s) for +: 'dict' and 'int'
champion potion __module__ →  can only concatenate str (not "int") to str
```

These are caught by a broad `except` and displayed as error text (the game
does not crash), but they reveal internal implementation details.

### BUG 5 (Low): Treasure names accepted as potion recovery types

```
printf 'descend\nfighter goblin\ndescend\nmage ooze\nchampion potion sword\n' \
  | droll --seed 7 Knight
```

**Result:** Succeeds silently — a **fighter** is added to the party (the
`sword` → `fighter` alias applies here too).  This is conceptually wrong:
potion recovery should only accept party die types (fighter, cleric, mage,
thief, champion, scroll), not treasure names.

### BUG 6 (Low): Grammar error in validation message

```
printf 'descend\nfighter goblin\ndescend\nmage ooze\nfighter potion mage thief cleric\n' \
  | droll --seed 7 Knight
```

**Result:** `Exactly 1 heroes to revive required.` — should read "Exactly 1
hero to revive required" (singular).

## What Works Well

The game handles many malformed inputs gracefully:

- **Empty input:** Shows the help/command list
- **Nonsense words:** `Unknown command "asdfghjkl".`
- **Shell injection:** `$(echo pwned)`, `; ls /` — treated as unknown commands
- **Python injection:** `__import__("os").system("id")` — treated as unknown command
- **Very long input (10,000 chars):** Handled without crash
- **Extra whitespace:** Correctly parsed
- **Tab characters:** Treated as whitespace separator (works fine)
- **Unicode characters:** Rejected as unknown commands
- **Case sensitivity:** `Fighter`, `FIGHTER` correctly rejected (game is lowercase-only)
- **Double undo:** `Cannot undo any prior command(s).`
- **Retire before descend:** `Descend at least once prior to retiring.`
- **Retire with monsters:** `Monsters remain. Defeat them or 'retreat'.`
- **Descend with monsters:** `Monsters must be defeated before descending.`
- **Repeated targets:** `Exactly 1 target required but 3 given.`
- **Missing target:** `"fighter" requires a target. Available: goblin.`
- **Using absent party member:** `At least 1 fighter required in party.`
- **Fighting dragon < 3:** `At least 3 dragon dice required to fight.`
- **Reroll without scroll:** `At least 1 scroll required in party.`
- **Reroll invalid die:** `__class__ cannot be re-rolled.` / `dragon cannot be re-rolled.`
- **Game over:** Clean termination after 3 delves

## Summary

| # | Severity | Description                                      |
|---|----------|--------------------------------------------------|
| 1 | Critical | Crash: dunder names in ability targets            |
| 2 | Critical | Crash: dunder names in combat targets             |
| 3 | High     | Phantom treasures used without inventory check    |
| 4 | Medium   | Internal Python errors leaked to user via potions |
| 5 | Low      | Treasure names accepted as potion recovery types  |
| 6 | Low      | Grammar: "1 heroes" instead of "1 hero"           |
