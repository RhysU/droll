# Coverage Analysis: test_shell.py Hero Test Classes

## Overview

Analysis of which source code lines are **exclusively** exercised by the
following 7 test classes in `tests/test_shell.py`:

- `TestKnight`
- `TestSpellsword`
- `TestMinstrel`
- `TestCrusader`
- `TestEnchantress`
- `TestHalfGoblin`
- `TestOccultist`

## Coverage Summary

| Metric | Lines |
|--------|-------|
| Total lines executed by all 142 tests | 855 |
| Total lines executed without the 7 classes (135 tests) | 847 |
| **Lines exclusively from the 7 classes** | **8** |

## Exclusively Covered Lines

### `droll/game.py` — 4 lines

**Lines 71–72** in `_next_delve()` — game-over exception handling:
```python
except error.DrollError:
    return GameState.STOP
```
Triggered by **TestKnight**: the only integration test that completes all 3
delves via retire, causing `world.delve()` to raise `DrollError` which is
caught here to end the game.

**Lines 128–129** in `retreat()` — retreat method body:
```python
self._world = world.retreat(self._world)
return self._next_delve()
```
Triggered by **TestEnchantress**: the only integration test that issues a
`retreat` command through the `Game` object.

### `droll/shell.py` — 3 lines

**Line 149** in `do_reroll()` — reroll command handler:
```python
return self._game.reroll(*_parse(line))
```
Triggered by **TestEnchantress**: the only integration test that issues a
`reroll` command through the shell.

**Lines 160–161** in `do_retreat()` — retreat command handler:
```python
_no_arguments(line)
return self._game.retreat()
```
Triggered by **TestEnchantress**: the only integration test that issues a
`retreat` command through the shell.

### `droll/world.py` — 1 line

**Line 79** in `delve()` — maximum delves exceeded:
```python
raise error.DrollError("At most three delves are permitted.")
```
Triggered by **TestKnight**: after the 3rd retire, `_next_delve()` calls
`world.delve()` which raises this error because `world.delve >= 3`.

## Key Findings

1. **Only 8 lines** (out of 855 executed) are exclusively covered by these
   7 hero integration tests.

2. **TestEnchantress** is the sole provider of coverage for `retreat` and
   `reroll` shell/game paths (5 of the 8 unique lines).

3. **TestKnight** is the sole provider of coverage for the game-termination
   path where all 3 delves are exhausted (3 of the 8 unique lines).

4. **TestSpellsword, TestMinstrel, TestCrusader, TestHalfGoblin, and
   TestOccultist** do not contribute any exclusively unique coverage beyond
   what the other tests already provide.

5. All other hero-specific logic (abilities, advancement, special rolls) is
   already covered by the dedicated unit tests in `tests/heroes/`.
