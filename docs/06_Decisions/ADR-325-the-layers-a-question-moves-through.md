# ADR-325 — The layers a question moves through

*Splitting `ask.py`: 2,409 lines into six layers, and the guard that broke because a constant moved one file.*

**Date:** 2026-09-28
**Status:** Accepted
**Gate:** agreed before building, with the owner choosing how the leaked private names were handled
**Sibling:** ADR-324 (`service/answers.py`, split the same day by the same method)

---

## Context

`src/ask.py` was 2,409 lines — and unlike `answers.py`, only **228 of them were public**. Thirteen public
names over 61 private ones: a small, stable surface with 93% of the file behind it.

⭐ That shape decided the split. `answers.py` divides by **subject** (one handler per endpoint); `ask.py`
divides by **stage**, because a question moves through it in one direction:

```
intents   the words -> an intent and its parameters   (no store, no football)
deciders  an intent -> a decision, by calling the analytics
facts     a decision -> the numbers the answer may contain
narrate   a decision -> prose, checked back against those facts
context   what a follow-up needs to remember
defaults  the one constant every layer shares
```

⚠️ **Importing a submodule does not dodge a package's `__init__`**, so the note in
`requirements-pipeline.txt` that ADR-323 overturned would apply here too — which is why the layering was
checked for cycles *before* any code moved. It is acyclic by construction: `defaults`, `intents` and `facts`
depend on nothing local; `deciders` on those three; `context` on `deciders`; `narrate` on `context`. `ask.py`
already imported only downward, and nothing it imports imports it back, so the only cycle risk was
self-inflicted.

## Decision

**Move all 77 definitions verbatim; keep the conversation in `__init__`.**

Same method as ADR-324: AST-cut into 111 blocks, asserted byte-for-byte against the original body before
moving, then diffed against `HEAD` afterwards. The only body differences are four calls qualified as
`_deciders._dispatch(…)` — deliberate, because `_dispatch` is faked in the suite and reaching it through the
module gives it one patch point rather than one per caller.

`__init__` keeps `answer`, `converse`, `chat_transcript` and the pronoun/follow-up plumbing, and re-exports
the surface so `from src.ask import route` means what it always did.

### The five names that lost their underscore

The owner's call, taken at the gate: **promote the names read from outside the package**, rather than
preserve the surface exactly.

| was | is | read by |
|---|---|---|
| `_price_a_rebuild` | `price_a_rebuild` | `src/cli.py` |
| `_decide_gameweek` | `decide_gameweek` | the suite |
| `_match_team` | `match_team` | the suite |
| `_fixture_horizon` | `fixture_horizon` | the suite |
| `_squad_name` | `squad_name` | the suite |

⭐⭐ *A name another file imports is part of the surface whether or not it wears an underscore.* The
underscore was accurate while they were private to one 2,409-line module and became misleading the moment
anything outside read them. **No aliases were left behind** — a compatibility alias would reintroduce exactly
the ambiguity this removes.

⚠️ The helpers still underscored in the re-export list are a **recorded wart**: the suite reaches into them,
and untangling that is larger than this split.

### 🔴 The failure I did not predict

`tests/test_tiebreak_wiring.py` checks that every transfer search states the window it ranks over. It
resolves `**_TIE_BREAK` by **finding where that name is defined in the same file**. Moving the constant into
`defaults.py` turned a real guard into **four false positives**.

Its own docstring had said so, about a different move:

> *"`name` is resolved anywhere in the file, because `ask` keeps its dict as a module constant while the
> others keep theirs local. A guard that follows only the indirection you happened to write is a guard
> against yourself."*

⭐⭐⭐ **The constant now lives beside its only caller, with a comment saying why it cannot move.** Widening
the guard to resolve names across a package was the alternative and was rejected: it would make the guard
fuzzier to accommodate a placement nothing needed. ⚠️ *A guard weakened to fit a refactor stops being
evidence about the thing it guards.*

### What ADR-324 had already taught me

Seventeen patch sites across two test files inject fakes through the `ask` module — `SquadStore`,
`gameweek_plan`, `team_fdr`, `team_schedule`, `chip_advisor`, `_squad_xp`, `_dispatch` — all resolving inside
`deciders` now, so they name that module. ⚠️ My first pass matched only `setattr(ask, "…"` on one line and
fixed nine of seventeen; the multi-line `setattr(\n    ask, "…"` form slipped through until the tests failed.
⭐ *A textual sweep for a pattern with optional whitespace needs to allow the whitespace.*

And `tests/test_web.py`'s core-package list named `"src/ask.py"`. ⭐ *A list naming a file stops covering the
code the moment that file becomes a folder — and says nothing when it does.*

## Consequences

**Good:** 2,409 lines becomes 2,620 across seven modules. `intents` is now testable with strings alone — no
store, no football — which is most of the point of having it apart.

**Costs:** ~210 more lines of docstrings and headers. Three test files and `cli.py` changed.

⚠️ **`deciders.py` is still 1,343 lines.** It holds 17 deciders plus the dispatch table, and splitting it
further would separate the table from what it dispatches to. ⭐ *Stated rather than glossed: this ADR made the
biggest module smaller, it did not make it small.* The next cut, if one is wanted, is by subject inside the
layer — but nothing currently hurts.

**Open, unchanged by this:** `src/web_streamlit/views/squads.py` (1,590), `src/cli.py` (1,437) and
`src/storage.py` (1,412) are now the three largest modules in the repo; sprint records stop at Sprint270;
`docs/01_Journal/` was last written 2026-08-05.
