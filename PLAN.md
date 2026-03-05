# Plan: Replace Literal Strings with Enums and Overloaded Dataclasses with Typed Dicts

## Problem Statement

Throughout the codebase, a small number of literal string values—representing
party members, dungeon faces, artifacts, and special commands—are passed as
plain `str` from the shell layer all the way into the game engine.

Compounding this, three dataclasses (`Dungeon`, `Party`, `Artifacts`) are each
used as map-like containers but with imprecise type annotations.  `Party` is
the worst offender: its field type is `Union[int, Command, str, None]` because
the same dataclass serves three completely different roles.  `Dungeon` has
`Union[int, Command]` for the same reason (two roles).  These unions make
static analysis nearly useless and hide semantic errors.

## Proposed Enums

### `DungeonDie` — the six dungeon die faces

```python
class DungeonDie(enum.Enum):
    GOBLIN = "goblin"
    SKELETON = "skeleton"
    OOZE = "ooze"
    CHEST = "chest"
    POTION = "potion"
    DRAGON = "dragon"
```

### `PartyDie` — the six party die faces

```python
class PartyDie(enum.Enum):
    FIGHTER = "fighter"
    CLERIC = "cleric"
    MAGE = "mage"
    THIEF = "thief"
    CHAMPION = "champion"
    SCROLL = "scroll"
```

### `Artifact` — the ten treasure/artifact types

```python
class Artifact(enum.Enum):
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

### `Action` — the special command verbs that aren't heroes

```python
class Action(enum.Enum):
    ABILITY = "ability"
    BAIT = "bait"
    ELIXIR = "elixir"
    REROLL = "reroll"
```

## Dataclass → Dict Type Replacement Table

The key observation is that `Party`, `Dungeon`, and `Artifacts` are each used
as map-like containers.  Today they share a single dataclass definition despite
serving fundamentally different roles with different value types.  With enums as
keys, each role becomes a distinct, precisely-typed dict:

| Current Type | Role / Context | Current Field Annotation | New Type Alias | Used In |
|---|---|---|---|---|
| `Dungeon` | Die counts on a dungeon level | `Union[int, Command]` (only `int` at runtime) | `DungeonState = dict[DungeonDie, int]` | `World.dungeon`, `dice.roll_dungeon()`, `dungeon.py` functions |
| `Dungeon` | Per-hero dispatch: what action does this hero take against each dungeon face? | `Union[int, Command]` (only `Command` at runtime) | `HeroActions = dict[DungeonDie, Command]` | Nested inside `Player.party` values (e.g. `Default.party[PartyDie.FIGHTER]`) |
| `Party` | Die counts of heroes in the current party | `Union[int, Command, str, None]` (only `int` at runtime) | `PartyState = dict[PartyDie, int]` | `World.party`, `Regroup.discard`, `dice.roll_party()`, `party.py` functions |
| `Party` | Full dispatch table: for each hero, what does it do to each dungeon face? | `Union[int, Command, str, None]` (only `HeroActions`/`Dungeon` at runtime) | `PartyActions = dict[PartyDie, HeroActions]` | `Player.party` — the two-level dispatch table |
| `Party` | Which artifact corresponds to each hero? | `Union[int, Command, str, None]` (only `Optional[str]` at runtime) | `ArtifactMapping = dict[PartyDie, Optional[Artifact]]` | `Player.artifacts` |
| `Artifacts` | Counts of each treasure type (in hand or in box) | `int` | `ArtifactCounts = dict[Artifact, int]` | `Treasure.own`, `Treasure.box`, `world.py` scoring |

### What the type aliases look like in `struct.py`

Runtime containers use `types.MappingProxyType` to preserve the frozen
semantics of the dataclasses they replace.  Type annotations use
`Mapping[K, V]` from `collections.abc` (read-only interface).

```python
from collections.abc import Mapping
from types import MappingProxyType

# State containers (runtime values are always int)
DungeonState   = Mapping[DungeonDie, int]
PartyState     = Mapping[PartyDie, int]
ArtifactCounts = Mapping[Artifact, int]

# Dispatch containers (runtime values are always Command)
HeroActions    = Mapping[DungeonDie, Command]
PartyActions   = Mapping[PartyDie, HeroActions]

# Mapping container
ArtifactMapping = Mapping[PartyDie, Optional[Artifact]]
```

Annotations say `Mapping` (read-only contract); factories return
`MappingProxyType` (enforced at runtime).  A thin `frozen()` helper
wraps construction:

```python
def frozen(d: dict) -> MappingProxyType:
    """Wrap a dict as an immutable MappingProxyType."""
    return MappingProxyType(d)
```

### Updated `Player`, `World`, `Treasure`, `Regroup`

Note: `frozen=True` on the dataclasses prevents reassignment of the fields
themselves (e.g. `world.party = ...` raises `FrozenInstanceError`).
`MappingProxyType` on the mapping values prevents mutation of the
containers (e.g. `world.party[PartyDie.FIGHTER] = 99` raises `TypeError`).
Together they provide the same depth of immutability as the old frozen
dataclasses.

```python
@dataclass(frozen=True)
class Treasure:
    own: ArtifactCounts    # was Artifacts; runtime: MappingProxyType
    box: ArtifactCounts    # was Artifacts; runtime: MappingProxyType

@dataclass(frozen=True)
class Regroup:
    discard: PartyState    # was Party; runtime: MappingProxyType

@dataclass(frozen=True)
class World:
    delve: int = 0
    depth: int = 0
    experience: int = 0
    dungeon: Optional[DungeonState] = None   # runtime: MappingProxyType | None
    party: PartyState = ...                   # runtime: MappingProxyType
    ability: bool = False
    regroup: Regroup = ...
    treasure: Treasure = ...

@dataclass(frozen=True)
class Player:
    name: str
    ability: Command
    advance: Advance
    bait: Command
    elixir: Command
    roll: Roll
    artifacts: ArtifactMapping    # runtime: MappingProxyType
    party: PartyActions           # runtime: MappingProxyType of MappingProxyType
```

### Updated `Command` Signature

```python
# Before
Command = Callable[[World, RandRange, str, tuple[str, ...]], World]

# After
Command = Callable[[World, RandRange, PartyDie, tuple[DungeonDie | PartyDie, ...]], World]
```

The `str` that was `hero` becomes `PartyDie`.  The `tuple[str, ...]` that was
`targets` becomes `tuple[DungeonDie | PartyDie, ...]` (targets can be
dungeon faces to attack, or party die names for reroll/quaff).

## What Changes in the Access Patterns

### `getattr`/`replace` → dict `[]`/`{**d, k: v}`

Every `getattr(obj, name)` / `replace(obj, **{name: val})` on these six types
becomes a plain dict lookup / dict spread:

```python
# Before (dungeon.py)
def decrement_dungeon(dungeon: Dungeon, target: str) -> Dungeon:
    _check_dungeon_target(target)
    prior = getattr(dungeon, target)
    return replace(dungeon, **{target: prior - 1})

# After
def decrement_dungeon(dungeon: DungeonState, target: DungeonDie) -> DungeonState:
    prior = dungeon[target]
    if not prior:
        raise DrollError(f"At least 1 {target.value} required in dungeon.")
    return frozen({**dungeon, target: prior - 1})
```

```python
# Before (party.py)
def increment_party(party: Party, hero: str) -> Party:
    _check_party_member(hero)
    return replace(party, **{hero: getattr(party, hero) + 1})

# After
def increment_party(party: PartyState, hero: PartyDie) -> PartyState:
    return frozen({**party, hero: party[hero] + 1})
```

### `field_names`/`field_values`/`field_items` → dict methods

```python
# Before
for name, count in field_items(dungeon): ...
sum(field_values(dungeon))

# After
for face, count in dungeon.items(): ...
sum(dungeon.values())
```

### `_check_*` validation functions → deleted

`_check_dungeon_target`, `_check_party_member`, `_DUNGEON_FIELDS`,
`_PARTY_FIELDS` all become unnecessary — the enum type enforces membership.

### Hero definitions use dict literals instead of `replace()`

```python
# Before (knight.py)
DragonSlayer = replace(Default, ...,
    party=struct.Party(
        fighter=replace(Default.party.fighter, dragon=_dragonslayer_defeat_dragon),
        ...
    ))

# After
DragonSlayer = replace(Default, ...,
    party=frozen({
        PartyDie.FIGHTER: frozen({**Default.party[PartyDie.FIGHTER],
                                  DungeonDie.DRAGON: _dragonslayer_defeat_dragon}),
        ...
    }))
```

### `Dungeon()` as empty → factory helper

```python
# Before
struct.Dungeon()  # all zeros

# After
empty_dungeon()   # returns frozen({face: 0 for face in DungeonDie})
```

### Constructor patterns with `*list` unpacking

```python
# Before (dice.py)
Dungeon(*_roll(dice, 0, 6, randrange))

# After
frozen(dict(zip(DungeonDie, _roll(dice, 0, 6, randrange))))
```

## Detailed Per-File Impact

### `struct.py`
- Add `from types import MappingProxyType` and `from collections.abc import Mapping`
- Add `frozen()` helper wrapping `MappingProxyType`
- Add four enums and six type aliases (using `Mapping[K, V]`)
- Remove `Dungeon`, `Party`, `Artifacts` dataclasses
- Add factory helpers: `empty_dungeon() -> DungeonState`,
  `empty_party() -> PartyState`, `empty_artifacts() -> ArtifactCounts`
  (each returns `frozen({...})`)
- Update `Treasure` fields: `own: ArtifactCounts`, `box: ArtifactCounts`
- Update `Regroup.discard: PartyState`
- Update `World.dungeon: Optional[DungeonState]`, `World.party: PartyState`
- Update `Player.artifacts: ArtifactMapping`, `Player.party: PartyActions`
- Update `Command` signature
- Replace `field_names`/`field_values`/`field_items` usages on the removed
  types with dict `.keys()`/`.values()`/`.items()` (callers migrate too)
- Keep `brief()` working via duck typing on dict `.items()`

### `dungeon.py`
- Param `target: str` → `target: DungeonDie` in all functions
- Return `Dungeon` → `DungeonState` (i.e. `dict[DungeonDie, int]`)
- Delete `_DUNGEON_FIELDS`, `_check_dungeon_target`
- `getattr(dungeon, target)` → `dungeon[target]`
- `replace(dungeon, **{target: v})` → `frozen({**dungeon, target: v})`
- Direct access `dungeon.goblin` → `dungeon[DungeonDie.GOBLIN]`
- `field_values(dungeon)` → `dungeon.values()`

### `party.py`
- Param `hero: str` → `hero: PartyDie` in all functions
- Return `Party` → `PartyState`
- Delete `_PARTY_FIELDS`, `_check_party_member`
- Same `getattr`→`[]` and `replace`→`frozen({**d})` migration as `dungeon.py`

### `treasure.py`
- `_draw` returns `Artifact` instead of `str`
- `replace_treasure` param `item: str` → `item: Artifact`
- `field_items(box)` → `box.items()`
- `field_values(box)` → `box.values()`
- `getattr(treasure.own, drawn)` → `treasure.own[drawn]`
- `replace(treasure.own, **{drawn: v})` → `frozen({**treasure.own, drawn: v})`
  (but `Treasure` itself stays a dataclass, so its `replace` stays)

### `regular.py`
- All `Command`-signature functions: `hero: str` → `hero: PartyDie`,
  `targets: tuple[str, ...]` → `tuple[DungeonDie | PartyDie, ...]`
- `_DUNGEON_NAMES`, `_PARTY_NAMES` frozensets → deleted (use `isinstance`
  checks or enum type)
- `_classify_reroll_targets`: check `isinstance(t, DungeonDie)` vs
  `isinstance(t, PartyDie)`
- `bait_dragon`: `_enemies` becomes `tuple[DungeonDie, ...]`
- `defeat_dragon_heroes`: `disallowed_heroes` becomes `frozenset[PartyDie]`
- `elixir`: `targets[0]` is already `PartyDie`
- String literals like `"potion"` → `DungeonDie.POTION`, `"scroll"` →
  `PartyDie.SCROLL`, etc.

### `special.py`
- Same `Command` signature updates as `regular.py`
- `convert_dungeon_to_party`: `source: str` → `source: DungeonDie`,
  `destination: str` → `destination: PartyDie`
- `getattr(world.dungeon, source)` → `world.dungeon[source]`

### `ability.py`
- All ability functions: `command: str` → `command: Action`,
  `targets: tuple[str, ...]` → typed tuple
- `_choose_and_add_hero`: `acceptable: frozenset[str]` →
  `frozenset[PartyDie]`
- `_convert_one`/`_convert_two`: `source: str` → `DungeonDie`,
  `destination: str` → `PartyDie`
- Literal strings like `increment_dungeon(dungeon, "potion")` →
  `increment_dungeon(dungeon, DungeonDie.POTION)`
- `increment_party(world.party, "scroll")` →
  `increment_party(world.party, PartyDie.SCROLL)`

### `player.py`
- `Default.artifacts` becomes `ArtifactMapping`:
  `{PartyDie.FIGHTER: Artifact.SWORD, ..., PartyDie.CHAMPION: None, ...}`
- `Default.party` becomes `PartyActions`:
  `{PartyDie.FIGHTER: {DungeonDie.GOBLIN: defeat_all, ...}, ...}`
- `apply()`: `command: str` becomes a union or is pre-parsed into the
  appropriate enum type by the caller; dispatch uses enum comparisons
- `_partify_command`: `Artifact` → `PartyDie` reverse lookup
- `_ARTIFACT_COMMANDS`: `frozenset[Artifact]`
- `_TREASURE_NO_COMMAND`: `frozenset[Artifact]`
- `complete()`: returns `Sequence[str]` (for the shell), but internally
  works with enum `.value` strings
- `_available_nouns`/`_available_targets`: iterate `.items()` on dicts
  instead of `field_items()`
- `_adjust_phantom_treasures`: iterates `artifacts.items()` instead of
  `field_items(artifacts)`

### `world.py`
- `new_world()`: `Artifacts(sword=3, ...)` →
  `{Artifact.SWORD: 3, ...}`
- `_regroup()`: `Party(**{name: max(...)})` →
  `{die: max(0, world.party[die] - world.regroup.discard[die]) for die in PartyDie}`
- `descend()`: `replace(rolled, dragon=...)` → `{**rolled, DungeonDie.DRAGON: ...}`
- `_apply_ring`/`_apply_portal`: `noun: str = "ring"` →
  `noun: Artifact = Artifact.RING`
- `score()`: `field_values(world.treasure.own)` → `world.treasure.own.values()`
- `world.treasure.own.portal` → `world.treasure.own[Artifact.PORTAL]`
- `world.treasure.own.scale` → `world.treasure.own[Artifact.SCALE]`

### `display.py`
- `_format_items`: `field_items(counts)` → `counts.items()`
- `_format_treasure`: `field_items(artifacts)` → `artifacts.items()`
- `field_values(party)` → `party.values()`
- Item names in output use `face.value` / `die.value` for display strings
- `_ALWAYS_COUNT = frozenset({DungeonDie.DRAGON})`

### `dice.py`
- `roll_dungeon` returns `DungeonState` instead of `Dungeon`
- `roll_party` returns `PartyState` instead of `Party`
- `Dungeon(*_roll(...))` → `dict(zip(DungeonDie, _roll(...)))`
- `Party(*_roll(...))` → `dict(zip(PartyDie, _roll(...)))`
- `len(fields(Dungeon))` → `len(DungeonDie)` (enum length)
- `len(fields(Party))` → `len(PartyDie)`

### `game.py`
- `Game.ability()`: passes `Action.ABILITY` instead of `"ability"`
- `Game.reroll()`: passes `Action.REROLL` instead of `"reroll"`
- `Game.apply()`: tokenized strings arrive from shell; parsing happens
  in `player.apply()` or the caller converts first
- `_possible_world_actions()`: `"ability"` → `Action.ABILITY` etc.
- `score_deltas()`: no enum changes (returns `dict[str, int]` for display)

### `shell.py`
- `_tokenize` stays string-based (it's the raw user input boundary)
- `do_ability`, `default`, `do_reroll` pass raw strings into `Game`
  methods, which forward to `player.apply()` where conversion happens
- Alternatively: conversion at the shell boundary via a `_parse_token`
  function
- Tab completion operates on `.value` strings throughout
- `_AVAILABLE_COMMANDS` stays as `frozenset[str]` (UI concern)

### Hero files (`droll/heroes/*.py`)
- All `struct.Party(fighter=struct.Dungeon(...), ...)` constructions →
  `{PartyDie.FIGHTER: {DungeonDie.GOBLIN: defeat_all, ...}, ...}`
- `replace(Default.party.fighter, dragon=...)` →
  `frozen({**Default.party[PartyDie.FIGHTER], DungeonDie.DRAGON: ...})`
- `replace(Default.party, fighter=..., cleric=...)` →
  `frozen({**Default.party, PartyDie.FIGHTER: ..., PartyDie.CLERIC: ...})`
- `Default.party.cleric.skeleton` → `Default.party[PartyDie.CLERIC][DungeonDie.SKELETON]`
- `frozenset({"fighter", "cleric"})` → `frozenset({PartyDie.FIGHTER, PartyDie.CLERIC})`

### Test files
- Every `struct.Dungeon(goblin=1, ...)` → `{DungeonDie.GOBLIN: 1, ...}`
  (or use `{**empty_dungeon(), DungeonDie.GOBLIN: 1}`)
- Every `struct.Party(fighter=2, ...)` → same pattern with `PartyDie`
- Every `struct.Artifacts(sword=1, ...)` → same pattern with `Artifact`
- Direct field access `game.dungeon.goblin` → `game.dungeon[DungeonDie.GOBLIN]`
- Direct field access `game.party.fighter` → `game.party[PartyDie.FIGHTER]`

## Implementation Steps

### Step 1: Define enums and type aliases in `struct.py`

Add `DungeonDie`, `PartyDie`, `Artifact`, `Action` plus all six
type aliases.  Add `empty_dungeon()`, `empty_party()`, `empty_artifacts()`
factory helpers.  Keep the old dataclasses temporarily.  Tests still pass.

### Step 2: Migrate `Artifacts` → `ArtifactCounts`

This is the simplest migration — `Artifacts` has only one role (`int` fields).
- Replace `Artifacts` dataclass with `ArtifactCounts = dict[Artifact, int]`
- Update `Treasure.own` and `Treasure.box` field types
- Update `treasure.py`: `field_items` → `.items()`, `getattr` → `[]`,
  `replace(own, **{k: v})` → `{**own, k: v}`
- Update `world.py`: `new_world()` construction, `score()` access
- Update `display.py`: `_format_treasure`
- Update `player.py`: `_ARTIFACT_COMMANDS`, `_TREASURE_NO_COMMAND`,
  `_available_nouns` treasure iteration
- Update tests
- Run tests

### Step 3: Migrate `Dungeon` state → `DungeonState`

Replace the `Dungeon` dataclass's state role (counting die faces) with
`DungeonState = dict[DungeonDie, int]`.
- Update `dungeon.py`: all functions take/return `DungeonState`, delete
  `_check_dungeon_target` and `_DUNGEON_FIELDS`
- Update `World.dungeon: Optional[DungeonState]`
- Update `dice.py`: `roll_dungeon` returns `DungeonState`
- Update `regular.py`, `special.py`, `ability.py`: all dungeon state access
- Update `world.py`: `descend()`, `_regroup()`, `new_world()`
- Update tests
- Run tests

### Step 4: Migrate `Party` state → `PartyState`

Replace the `Party` dataclass's counting role with
`PartyState = dict[PartyDie, int]`.
- Update `party.py`: all functions take/return `PartyState`, delete
  `_check_party_member` and `_PARTY_FIELDS`
- Update `World.party: PartyState`, `Regroup.discard: PartyState`
- Update `dice.py`: `roll_party` returns `PartyState`
- Update `regular.py`, `special.py`, `ability.py`: all party state access
- Update `player.py`: `_adjust_phantom_treasures`, `apply()` party iteration
- Update `world.py`: `_regroup()`
- Update tests
- Run tests

### Step 5: Migrate `Dungeon` dispatch → `HeroActions`, and `Party` dispatch → `PartyActions`

These two are tightly coupled (a `PartyActions` is a dict of `HeroActions`).
- Define `HeroActions = dict[DungeonDie, Command]`
- Define `PartyActions = dict[PartyDie, HeroActions]`
- Remove the `Dungeon` and `Party` dataclasses entirely
- Update `Player.party: PartyActions`
- Update `player.py:apply()`: `getattr(player.party, command)` →
  `player.party[command]`, `getattr(action_, targets[0])` →
  `action_[targets[0]]`
- Update all hero files: `struct.Party(fighter=struct.Dungeon(...), ...)` →
  dict literals; `replace(Default.party.fighter, ...)` → dict spread
- Update tests
- Run tests

### Step 6: Migrate `Party` artifact mapping → `ArtifactMapping`

- Define `ArtifactMapping = dict[PartyDie, Optional[Artifact]]`
- Update `Player.artifacts: ArtifactMapping`
- Update `player.py`: `Default.artifacts` construction,
  `_partify_command`, `_adjust_phantom_treasures`, `_ARTIFACT_COMMANDS`
- Update tests
- Run tests

### Step 7: Update `Command` signature and action functions

- Update `Command = Callable[[World, RandRange, PartyDie, tuple[...]], World]`
- Update every function that matches the `Command` signature (`defeat_one`,
  `defeat_all`, `open_one`, `open_all`, `quaff`, `reroll`, `defeat_dragon`,
  `bait_dragon`, `elixir`, all ability functions, all special functions)
- Update `player.py:apply()` to pass typed values
- Update tests
- Run tests

### Step 8: Port `game.py`, `shell.py`, and the boundary layer

- `game.py`: pass `Action.ABILITY` / `Action.REROLL` instead of
  string literals
- `shell.py`: add `_parse_token` to convert user input strings → enum at
  the boundary; or let `player.apply` handle the conversion
- Tab completion returns `.value` strings
- Update tests
- Run tests

### Step 9: Clean up

- Remove any remaining `field_names`/`field_values`/`field_items` usage
  that operated on the now-deleted dataclasses
- Remove helper functions in `struct.py` if no longer needed
- Verify `brief()` works on the remaining dataclasses (`World`, `Treasure`,
  `Regroup`, `Player`, `Roll`)
- Run full test suite
- Verify shell interaction and tab completion unchanged

## Cross-Cutting Concerns

### `brief()` must handle both dicts and surviving dataclasses

`brief()` in `struct.py` recursively formats nested structures using
`field_names()` / `field_values()`, which call `dataclasses.fields()`.
After migration, `World.dungeon` will be a `dict` (or `None`), and
`World.party` will be a `dict`.  When `brief()` recurses into these, it
must detect dicts and use `.items()` instead of `fields()`.

```python
from collections.abc import Mapping

def brief(o: Any) -> str:
    if isinstance(o, Mapping):
        keyvalues = [f"{k.value if hasattr(k, 'value') else k}={brief(v)}"
                     for k, v in o.items() if v]
        return f"({', '.join(keyvalues)})"
    try:
        names = field_names(o)
        values = field_values(o)
    except TypeError:
        return str(o)
    keyvalues = [f"{f}={brief(v)}" for f, v in zip(names, values) if v]
    return f"({', '.join(keyvalues)})"
```

Note: `isinstance(o, Mapping)` catches both plain `dict` and
`MappingProxyType`, since `MappingProxyType` implements `Mapping`.

### `field_names` / `field_values` / `field_items` helpers survive but shrink in scope

These helpers remain useful for the surviving dataclasses (`World`,
`Treasure`, `Regroup`, `Player`, `Roll`).  But they are no longer called
on `Dungeon`, `Party`, or `Artifacts` — those callers migrate to dict
`.keys()` / `.values()` / `.items()`.  The helpers themselves don't change;
only their call sites do.

Callers that used them on the removed types:

| Caller | Was | Becomes |
|---|---|---|
| `dice.py`: `len(fields(Dungeon))` | dataclass field count | `len(DungeonDie)` |
| `dice.py`: `len(fields(Party))` | dataclass field count | `len(PartyDie)` |
| `dungeon.py`: `field_names(Dungeon)` | frozenset of names | deleted (enum membership) |
| `dungeon.py`: `field_values(dungeon)` | sum of values | `dungeon.values()` |
| `party.py`: `field_names(Party)` | frozenset of names | deleted (enum membership) |
| `regular.py`: `field_names(Dungeon)` / `field_names(Party)` | frozensets | deleted |
| `regular.py`: `field_values(dungeon)` / `field_values(party)` | for map/add | `.values()` |
| `treasure.py`: `field_items(box)` / `field_values(box)` | iteration | `.items()` / `.values()` |
| `player.py`: `field_items(artifacts)` | iteration | `.items()` |
| `player.py`: `field_items(action_)` | iteration | `.items()` |
| `player.py`: `field_names(player.party)` | membership check | `in player.party` |
| `player.py`: `field_names(action_)` | membership check | `in action_` |
| `player.py`: `field_names(struct.Party)` / `field_names(struct.Dungeon)` | completion | `PartyDie` / `DungeonDie` members |
| `display.py`: `field_items(counts)` / `field_values(party)` | formatting | `.items()` / `.values()` |
| `world.py`: `field_values(world.treasure.own)` | scoring | `.values()` |
| `world.py`: `field_items(world.regroup.discard)` | regroup | `.items()` |
| Tests: `len(fields(struct.Dungeon))` / `len(fields(struct.Party))` | construction | `len(DungeonDie)` / `len(PartyDie)` |

### `RollDungeon` and `RollParty` type aliases need updating

```python
# Before
RollDungeon = Callable[[int, RandRange], Dungeon]
RollParty = Callable[[int, RandRange], tuple[Party, Regroup]]

# After
RollDungeon = Callable[[int, RandRange], DungeonState]
RollParty = Callable[[int, RandRange], tuple[PartyState, Regroup]]
```

### `hasattr()` in `treasure.py` → `in` operator

Line 49: `if not hasattr(treasure.own, item):` becomes
`if item not in treasure.own:` — a natural dict idiom.

### Frozen dict semantics — `MappingProxyType`

`Dungeon` and `Party` are frozen dataclasses today.  To preserve the same
runtime immutability, all six mapping types use `types.MappingProxyType`
from the stdlib.  This is a zero-dependency read-only view over a `dict`:

```python
from types import MappingProxyType

proxy = MappingProxyType({DungeonDie.GOBLIN: 2})
proxy[DungeonDie.GOBLIN]          # 2 — reads work
proxy[DungeonDie.GOBLIN] = 99     # TypeError — mutation blocked
```

The "update" idiom builds a new plain `dict` via spread, then re-wraps:

```python
frozen({**proxy, DungeonDie.GOBLIN: 0})
# → MappingProxyType({DungeonDie.GOBLIN: 0, ...})
```

This pairs with frozen dataclasses: `World(frozen=True)` prevents field
reassignment, and `MappingProxyType` prevents mutation of the mapping
values.  Together they provide the same depth of immutability as the
original nested frozen dataclasses.

Type annotations use `Mapping[K, V]` (the abstract read-only interface
from `collections.abc`), so function signatures express the read-only
contract without mentioning `MappingProxyType` directly.

### All 8 hero files need migration

The plan's Step 5 must cover all hero files:
- `enchantress.py` (Enchantress/Beguiler)
- `crusader.py` (Crusader/Paladin)
- `halfgoblin.py` (HalfGoblin/Chieftain)
- `knight.py` (Knight/DragonSlayer)
- `mercenary.py` (Mercenary/Commander)
- `minstrel.py` (Minstrel/Bard)
- `occultist.py` (Occultist/Necromancer)
- `spellsword.py` (Spellsword/Battlemage)

Each uses `replace(Default.party.X, ...)` and/or `struct.Party(X=struct.Dungeon(...))`
patterns that must become dict literals / dict spreads.

## Risk Assessment

- **Low risk:** `Artifacts` → `ArtifactCounts` (Step 2) is purely mechanical
  — one role, one type, every field is `int`.
- **Medium risk:** `Dungeon`/`Party` state migrations (Steps 3–4) touch many
  files but each `getattr`→`[]` change is mechanical.
- **Higher risk:** Dispatch table migration (Step 5) changes how hero files
  build their action tables.  The `replace(Default.party.fighter, dragon=...)`
  pattern becomes `{**Default.party[PartyDie.FIGHTER], DungeonDie.DRAGON: ...}`.
  This is more verbose but precisely typed.  Must test all 8 hero variants.
- **Medium risk:** `Command` signature (Step 7) touches every action function.
  Doing it late means intermediate steps have a mixed `str`/`enum` period.
- **`brief()` breakage:** If not handled in Step 1, `brief(world)` will
  produce ugly `str(dict)` output for dungeon/party sub-objects.  Must be
  addressed early (Step 1 or 2).
- **Frozen semantics:** `MappingProxyType` preserves the same runtime
  immutability as frozen dataclasses.  The `frozen()` helper adds one
  function call per construction, which is negligible.
- **Boundary clarity:** The shell is the only place raw user strings enter.
  Converting there (Step 8) means the engine interior speaks enums throughout.
