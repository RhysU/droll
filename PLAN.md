# Plan: Strings → Enums, Overloaded Dataclasses → Typed Frozen Mappings

## Problem

Literal strings (`"fighter"`, `"goblin"`, `"sword"`, …) flow from the shell
into the engine with no static checking.  Three dataclasses (`Dungeon`,
`Party`, `Artifacts`) serve as map-like containers with imprecise unions
(`Party` fields are `Union[int, Command, str, None]` to cover three unrelated
roles).

## Enums

```python
class Dungeon(enum.Enum):                    # replaces Dungeon dataclass name
    GOBLIN = "goblin";  SKELETON = "skeleton";  OOZE = "ooze"
    CHEST = "chest";    POTION = "potion";      DRAGON = "dragon"

class Party(enum.Enum):                      # replaces Party dataclass name
    FIGHTER = "fighter"; CLERIC = "cleric"; MAGE = "mage"
    THIEF = "thief";     CHAMPION = "champion"; SCROLL = "scroll"

class Artifact(enum.Enum):
    SWORD = "sword";   TALISMAN = "talisman"; SCEPTRE = "sceptre"
    TOOLS = "tools";   SCROLL = "scroll";     ELIXIR = "elixir"
    BAIT = "bait";     PORTAL = "portal";     RING = "ring";  SCALE = "scale"

class Action(enum.Enum):
    ABILITY = "ability"; BAIT = "bait"; ELIXIR = "elixir"; REROLL = "reroll"
```

## Type Aliases (annotations use `Mapping`; runtime is `MappingProxyType`)

```python
from collections.abc import Mapping
from types import MappingProxyType

def frozen(d: dict) -> MappingProxyType:
    return MappingProxyType(d)

DungeonState    = Mapping[Dungeon, int]                 # was Dungeon dataclass (int fields)
PartyState      = Mapping[Party, int]                   # was Party dataclass (int fields)
ArtifactCounts  = Mapping[Artifact, int]                # was Artifacts dataclass
HeroActions     = Mapping[Dungeon, Command]             # was Dungeon dataclass (Command fields)
PartyActions    = Mapping[Party, HeroActions]            # was Party dataclass (Dungeon-of-Command fields)
ArtifactMapping = Mapping[Party, Optional[Artifact]]    # was Party dataclass (str|None fields)

Command = Callable[[World, RandRange, Party, tuple[Dungeon | Party, ...]], World]
RollDungeon = Callable[[int, RandRange], DungeonState]
RollParty   = Callable[[int, RandRange], tuple[PartyState, Regroup]]
```

`frozen=True` on surviving dataclasses prevents field reassignment;
`MappingProxyType` prevents mutation of mapping contents — together matching
the old frozen-dataclass depth of immutability.

## Dataclass Replacement Table

| Old Type | Role | Old Field Type | New Alias | Primary Sites |
|---|---|---|---|---|
| `Dungeon` dc | die counts | `Union[int,Command]` → `int` | `DungeonState` | `World.dungeon`, `dungeon.py`, `dice.py` |
| `Dungeon` dc | hero dispatch | `Union[int,Command]` → `Command` | `HeroActions` | nested in `Player.party` values |
| `Party` dc | die counts | `Union[int,Command,str,None]` → `int` | `PartyState` | `World.party`, `Regroup.discard`, `party.py` |
| `Party` dc | full dispatch | → `HeroActions` | `PartyActions` | `Player.party` |
| `Party` dc | artifact map | → `Optional[str]` | `ArtifactMapping` | `Player.artifacts` |
| `Artifacts` dc | treasure counts | `int` | `ArtifactCounts` | `Treasure.own`, `Treasure.box` |

## Access Pattern Migration

| Before | After |
|---|---|
| `getattr(dungeon, target)` | `dungeon[target]` |
| `replace(dungeon, **{target: v})` | `frozen({**dungeon, target: v})` |
| `field_items(dungeon)` / `field_values(d)` | `dungeon.items()` / `d.values()` |
| `len(fields(Dungeon))` | `len(Dungeon)` |
| `_check_dungeon_target(t)` | _(deleted — enum type enforces)_ |
| `dungeon.goblin` | `dungeon[Dungeon.GOBLIN]` |
| `Dungeon(*_roll(...))` | `frozen(dict(zip(Dungeon, _roll(...))))` |
| `struct.Dungeon()` | `empty_dungeon()` |
| `replace(Default.party.fighter, dragon=fn)` | `frozen({**Default.party[Party.FIGHTER], Dungeon.DRAGON: fn})` |
| `Default.party.cleric.skeleton` | `Default.party[Party.CLERIC][Dungeon.SKELETON]` |
| `hasattr(treasure.own, item)` | `item in treasure.own` |

## Updated Surviving Dataclasses

```python
@dataclass(frozen=True)
class Treasure:
    own: ArtifactCounts;  box: ArtifactCounts

@dataclass(frozen=True)
class Regroup:
    discard: PartyState

@dataclass(frozen=True)
class World:
    delve: int = 0;  depth: int = 0;  experience: int = 0
    dungeon: Optional[DungeonState] = None;  party: PartyState = ...
    ability: bool = False;  regroup: Regroup = ...;  treasure: Treasure = ...

@dataclass(frozen=True)
class Player:
    name: str;  ability: Command;  advance: Advance
    bait: Command;  elixir: Command;  roll: Roll
    artifacts: ArtifactMapping;  party: PartyActions
```

## `brief()` Update

```python
def brief(o: Any) -> str:
    if isinstance(o, Mapping):                             # catches MappingProxyType
        kv = [f"{k.value}={brief(v)}" for k, v in o.items() if v]
        return f"({', '.join(kv)})"
    try:
        names, values = field_names(o), field_values(o)
    except TypeError:
        return str(o)
    return f"({', '.join(f'{f}={brief(v)}' for f, v in zip(names, values) if v)})"
```

## Per-File Impact

- **`struct.py`** — add enums, type aliases, `frozen()`, `empty_*()` factories;
  remove `Dungeon`/`Party`/`Artifacts` dataclasses; update `Command`,
  `RollDungeon`, `RollParty`, `Treasure`, `Regroup`, `World`, `Player`; update `brief()`
- **`dungeon.py`** — `target: str` → `Dungeon`; return `DungeonState`;
  delete `_check_dungeon_target`/`_DUNGEON_FIELDS`; `getattr`→`[]`, `replace`→`frozen({**d})`
- **`party.py`** — `hero: str` → `Party`; return `PartyState`;
  delete `_check_party_member`/`_PARTY_FIELDS`; same accessor migration
- **`treasure.py`** — `_draw` returns `Artifact`; `replace_treasure` takes `Artifact`;
  `field_items`→`.items()`, `hasattr`→`in`, `getattr`→`[]`
- **`regular.py`** — `hero: str`→`Party`, `targets: tuple[str,...]`→`tuple[Dungeon|Party,...]`;
  delete `_DUNGEON_NAMES`/`_PARTY_NAMES`; `_classify_reroll_targets` uses `isinstance`;
  `"potion"`→`Dungeon.POTION`, `"scroll"`→`Party.SCROLL`, etc.
- **`special.py`** — `source: str`→`Dungeon`, `destination: str`→`Party`;
  `getattr`→`[]`
- **`ability.py`** — `command: str`→`Action`; `acceptable: frozenset[str]`→`frozenset[Party]`;
  `"potion"`→`Dungeon.POTION`, `"scroll"`→`Party.SCROLL`
- **`player.py`** — `Default.artifacts`/`Default.party` become dict literals;
  `apply()` dispatches on enums; `_partify_command`: `Artifact`→`Party` lookup;
  `_ARTIFACT_COMMANDS`/`_TREASURE_NO_COMMAND`: `frozenset[Artifact]`;
  `complete()` returns `.value` strings
- **`world.py`** — `Artifacts(sword=3,...)`→`frozen({Artifact.SWORD: 3,...})`;
  `.portal`→`[Artifact.PORTAL]`; `_apply_ring`/`_apply_portal` take `Artifact`;
  `field_values`→`.values()`
- **`display.py`** — `field_items`→`.items()`, `field_values`→`.values()`;
  names via `.value`; `_ALWAYS_COUNT = frozenset({Dungeon.DRAGON})`
- **`dice.py`** — returns `DungeonState`/`PartyState`;
  `frozen(dict(zip(Dungeon, _roll(...))))`;
  `len(fields(X))`→`len(X)`
- **`game.py`** — `"ability"`→`Action.ABILITY`, `"reroll"`→`Action.REROLL`
- **`shell.py`** — `_tokenize` stays string-based; add `_parse_token` str→enum
  at the boundary; tab completion uses `.value`
- **`heroes/*.py`** (all 8) — `struct.Party(fighter=struct.Dungeon(...),...)`→
  `frozen({Party.FIGHTER: frozen({Dungeon.GOBLIN: defeat_all,...}),...})`;
  `replace(Default.party.X, Y=fn)`→`frozen({**Default.party[X], Y: fn})`;
  `frozenset({"fighter","cleric"})`→`frozenset({Party.FIGHTER, Party.CLERIC})`
- **Tests** — `struct.Dungeon(goblin=1)`→`{**empty_dungeon(), Dungeon.GOBLIN: 1}`;
  `.goblin`→`[Dungeon.GOBLIN]`; same for `Party`/`Artifacts`

## `field_names`/`field_values`/`field_items`

Survive for remaining dataclasses (`World`, `Treasure`, `Regroup`, `Player`,
`Roll`).  All calls on removed types migrate to `.keys()`/`.values()`/`.items()`.

## Steps

1. **Define enums + aliases** in `struct.py`. Add `frozen()`, `empty_*()`.
   Keep old dataclasses temporarily. Tests pass.
2. **`Artifacts` → `ArtifactCounts`** — `treasure.py`, `world.py`, `display.py`,
   `player.py`, tests.
3. **`Dungeon` state → `DungeonState`** — `dungeon.py`, `dice.py`, `World.dungeon`,
   `regular.py`, `special.py`, `ability.py`, `world.py`, tests.
4. **`Party` state → `PartyState`** — `party.py`, `dice.py`, `World.party`,
   `Regroup.discard`, `regular.py`, `special.py`, `ability.py`, `player.py`,
   `world.py`, tests.
5. **Dispatch → `HeroActions`/`PartyActions`** — remove old `Dungeon`/`Party`
   dataclasses; update `Player.party`, `player.py:apply()`, all 8 hero files, tests.
6. **`ArtifactMapping`** — `Player.artifacts`, `player.py`, tests.
7. **`Command` signature** — all action functions, ability functions, `player.py:apply()`, tests.
8. **Boundary layer** — `game.py` (enum literals), `shell.py` (`_parse_token`), tests.
9. **Clean up** — remove stale helpers, verify `brief()`, full test suite, shell smoke test.

## Risk

- **Low:** Step 2 (`Artifacts`) — single role, mechanical.
- **Medium:** Steps 3–4 (state dicts) — many files, but each change is `getattr`→`[]`.
- **Higher:** Step 5 (dispatch) — all 8 hero files change construction patterns.
- **Medium:** Step 7 (`Command` sig) — touches every action function.
- **`brief()`** — must handle `Mapping` early (Step 1) to avoid ugly output.
- **Frozen semantics** — `MappingProxyType` preserves immutability; `frozen()` cost negligible.
