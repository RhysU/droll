# Plan: Replace Literal Strings with Enums

## Problem Statement

Throughout the codebase, a small number of literal string values—representing
party members, dungeon faces, artifacts, and special commands—are passed as
plain `str` from the shell layer all the way into the game engine.  These
strings are the game's vocabulary: `"fighter"`, `"goblin"`, `"sword"`,
`"reroll"`, `"ability"`, etc.  They are never arbitrary user text; they always
belong to one of a few closed sets.  Using bare strings means:

- No static checking that a value belongs to its intended set.
- `getattr(obj, name)` / `replace(obj, **{name: ...})` patterns where `name`
  is a raw string, bypassing type-checker visibility.
- Validation scattered across ad-hoc `frozenset` lookups and runtime `if`
  checks (`_DUNGEON_FIELDS`, `_PARTY_FIELDS`, `_check_dungeon_target`, etc.).
- Easy to accidentally pass a dungeon name where a party name is expected (or
  vice versa) with no tool-time feedback.

## Proposed Enums

### 1. `DungeonFace` — the six dungeon die faces

```python
class DungeonFace(enum.Enum):
    GOBLIN = "goblin"
    SKELETON = "skeleton"
    OOZE = "ooze"
    CHEST = "chest"
    POTION = "potion"
    DRAGON = "dragon"
```

**Where it replaces strings today:**
- `dungeon.py`: `decrement_dungeon(dungeon, target: str)` → `target: DungeonFace`
- `dungeon.py`: `increment_dungeon(dungeon, target: str)` → `target: DungeonFace`
- `dungeon.py`: `eliminate_dungeon(dungeon, target: str)` → `target: DungeonFace`
- `regular.py`: `_classify_reroll_targets` membership checks against `_DUNGEON_NAMES`
- `regular.py`: `bait_dragon` iterating `_enemies: Sequence[str]`
- `ability.py`: calls like `increment_dungeon(dungeon, "potion")`
- `special.py`: `convert_dungeon_to_party(world, source="goblin", ...)`

### 2. `PartyDie` — the six party die faces

```python
class PartyDie(enum.Enum):
    FIGHTER = "fighter"
    CLERIC = "cleric"
    MAGE = "mage"
    THIEF = "thief"
    CHAMPION = "champion"
    SCROLL = "scroll"
```

**Where it replaces strings today:**
- `party.py`: `decrement_party(party, hero: str)` → `hero: PartyDie`
- `party.py`: `increment_party(party, hero: str)` → `hero: PartyDie`
- `party.py`: `decrement_regroup(regroup, hero: str)` → `hero: PartyDie`
- `regular.py`: `_classify_reroll_targets` membership checks against `_PARTY_NAMES`
- `regular.py`: `defeat_dragon_heroes` disallowed set `{"scroll"}`
- `ability.py`: calls like `increment_party(world.party, "scroll")`
- `special.py`: `convert_dungeon_to_party(world, ..., destination="thief")`
- `player.py`: artifact mapping values, `_partify_command` return values

### 3. `ArtifactKind` — the ten treasure/artifact types

```python
class ArtifactKind(enum.Enum):
    SWORD = "sword"
    TALISMAN = "talisman"
    SCEPTRE = "sceptre"
    TOOLS = "tools"
    SCROLL = "scroll"
    ELIXIR = "elixir"
    BAIT = "bait"
    PORTAL = "portal"
    RING = "ring"
    SCALE = "scale"
```

**Where it replaces strings today:**
- `treasure.py`: `_draw` returns `str` → `ArtifactKind`
- `treasure.py`: `replace_treasure(treasure, item: str)` → `item: ArtifactKind`
- `player.py`: `_ARTIFACT_COMMANDS` frozenset
- `player.py`: `artifacts=struct.Party(fighter="sword", ...)` mappings
- `world.py`: `_apply_ring(world, *, noun: str = "ring")`
- `world.py`: `_apply_portal(world, *, noun: str = "portal")`
- `regular.py`: `bait_dragon` calling `replace_treasure(world.treasure, command)`
- `regular.py`: `elixir` calling `replace_treasure(world.treasure, command)`

### 4. `ActionVerb` — the special command verbs that aren't heroes

```python
class ActionVerb(enum.Enum):
    ABILITY = "ability"
    BAIT = "bait"
    ELIXIR = "elixir"
    REROLL = "reroll"
```

**Where it replaces strings today:**
- `player.py:apply()`: `if command == "portal"`, `if command == "ring"`,
  `if command in {"ability", "bait", "elixir"}`, `if command == "reroll"`
- `game.py`: passing `"ability"` and `"reroll"` into `player.apply()`

This enum is small but eliminates the riskiest string comparisons—the ones
that dispatch to fundamentally different code paths.

## Dataclass Field Access Pattern

The core challenge is that `Dungeon`, `Party`, and `Artifacts` are frozen
dataclasses whose fields are named after enum values.  Today the code uses
`getattr(dungeon, target)` and `replace(dungeon, **{target: new_val})` where
`target` is a bare string matching a field name.

With enums, the accessor pattern becomes:

```python
# Before
getattr(dungeon, target)                  # target = "goblin"
replace(dungeon, **{target: new_val})

# After
getattr(dungeon, target.value)            # target = DungeonFace.GOBLIN
replace(dungeon, **{target.value: new_val})
```

This is the minimally invasive approach.  An alternative would be to replace
the dataclasses with dict-like containers keyed by enum, but that would be a
much larger change with less benefit from the frozen-dataclass guarantees.

## What the Finished Result Looks Like

1. **`struct.py`** gains four `enum.Enum` classes (`DungeonFace`, `PartyDie`,
   `ArtifactKind`, `ActionVerb`) alongside the existing dataclasses.

2. **`Dungeon`, `Party`, `Artifacts` dataclasses** keep their field names
   unchanged (so `Dungeon.goblin`, `Party.fighter`, etc. remain valid Python
   identifiers).  The enum `.value` serves as the bridge between the typed
   token and the field name.

3. **Module-internal validation** (`_check_dungeon_target`,
   `_check_party_member`, `_DUNGEON_FIELDS`, `_PARTY_FIELDS`) **is deleted**
   because the enum type annotation enforces membership at the call site.

4. **`shell.py`** gains a thin `_parse_token(text: str) -> Enum` function at
   the boundary where user input becomes typed.  `_tokenize` returns
   `tuple[str, ...]` today; the new version would return typed tokens that the
   rest of the engine consumes.

5. **All intermediate functions** (`decrement_dungeon`, `increment_party`,
   `replace_treasure`, `bait_dragon`, `quaff`, etc.) accept enum parameters
   instead of `str`, gaining static type safety.

6. **Error messages** use `target.value` to produce the same human-readable
   strings as today—no user-facing change.

7. **Tab completion** continues to work with string values; conversion happens
   at the boundary.

## Implementation Steps

### Step 1: Define the enums in `struct.py`

Add `DungeonFace`, `PartyDie`, `ArtifactKind`, and `ActionVerb` to `struct.py`.
Export them from `__all__`.  No other file changes yet.  Tests still pass.

### Step 2: Port `dungeon.py` to use `DungeonFace`

- Change `decrement_dungeon`, `increment_dungeon`, `eliminate_dungeon` to
  accept `target: DungeonFace` and use `target.value` for `getattr`/`replace`.
- Remove `_check_dungeon_target` and `_DUNGEON_FIELDS`.
- Update all callers in `regular.py`, `special.py`, and `ability.py` to pass
  `DungeonFace.GOBLIN` instead of `"goblin"`, etc.
- Update tests.

### Step 3: Port `party.py` to use `PartyDie`

- Change `decrement_party`, `increment_party`, `decrement_regroup` to accept
  `hero: PartyDie` and use `hero.value`.
- Remove `_check_party_member` and `_PARTY_FIELDS`.
- Update all callers in `regular.py`, `special.py`, `ability.py`, and
  `player.py`.
- Update tests.

### Step 4: Port `treasure.py` to use `ArtifactKind`

- Change `_draw` to return `ArtifactKind`.
- Change `replace_treasure` to accept `item: ArtifactKind`.
- Update callers in `world.py`, `regular.py`, `ability.py`, and `player.py`.
- Update tests.

### Step 5: Port `player.py` to use `ActionVerb` and integrate all enums

- Replace the string comparisons in `apply()` with `ActionVerb` checks.
- Update `_partify_command` to work with `ArtifactKind` → `PartyDie` mapping.
- Update `_ARTIFACT_COMMANDS` to use `ArtifactKind`.
- Update `_available_nouns`, `_available_targets`, `_all_dice_names`, and
  `complete` to return/compare enum values, converting to strings only for
  display.
- Update tests.

### Step 6: Port `game.py` and `shell.py` — the boundary layer

- In `game.py`, pass enum values instead of string literals to `player.apply`.
- In `shell.py`, add `_parse_token` to convert user input strings into the
  appropriate enum type.  `_tokenize` stays string-based; parsing happens
  inside `do_ability`, `default`, `do_reroll`, and completion methods.
- Tab completion operates on `.value` strings but the typed boundary ensures
  invalid tokens are caught early.
- Update tests.

### Step 7: Port the `Command` type signature

- Update `struct.Command` from
  `Callable[[World, RandRange, str, tuple[str, ...]], World]`
  to use the appropriate enum types for the `hero` and `targets` parameters.
- This is the signature used by `defeat_one`, `defeat_all`, `quaff`,
  `defeat_dragon`, `bait_dragon`, `elixir`, and every hero ability.
- Update all implementations and their callers.
- Update tests.

### Step 8: Clean up and final verification

- Remove any remaining `frozenset` lookups that the enums made redundant.
- Run the full test suite.
- Verify tab completion and shell interaction still work correctly.
- Verify `brief()` display output is unchanged.

## Risk Assessment

- **Low risk:** Each step is independently testable.  The enum `.value`
  property means all `getattr`/`replace` patterns work with a mechanical
  `.value` suffix addition.
- **Medium risk:** The `Command` type signature change (Step 7) touches
  every action function.  Doing it last means the intermediate steps carry
  a mixed `str`/`enum` signature, but this is manageable and each step's
  tests confirm correctness.
- **Boundary clarity:** The shell is the only place where raw user strings
  enter the system.  Converting there means the entire engine interior
  speaks enums, which is the ideal end state.
