# ADR-324 — The seam a module already has

*Splitting `service/answers.py`: 2,368 lines into seven families, and the three things the barrel could not hide.*

**Date:** 2026-09-28
**Status:** Accepted
**Gate:** agreed before building — scope, layering and the private-name question settled with the owner first
**Sibling:** ADR-325 (`ask.py`, the same job on a module shaped differently)
**From:** the health check's *"keep modules small"* finding

---

## Context

`src/service/answers.py` was 2,368 lines: 25 public handlers (1,663 lines) and 18 private helpers. Against
the project's own *"keep modules small"*, it and `src/ask.py` were the two worst offenders in the repo.

⭐ **The split was not designed; it was measured.** Every handler is one endpoint, and a dependency map
showed each private helper was used by exactly one family of them — except three. So the boundaries were
already in the file, and the only real question was where those three go.

| | used by |
|---|---|
| `plain` | market + language |
| `_chip_status` | squad + language |
| `_entry_history` | squad + mini_leagues |

Everything else fell out: **squad** (9 handlers), **mini_leagues** (4), **profiles** (5), **market** (3),
**language** (2), **meta** (1), **common** (those three).

⚠️ `src/service/__init__.py` was already the contract layer (ADR-219) and already re-exported all 24
handlers, so `app.py` and Streamlit could not tell the difference. That is what made this the cheaper of the
two splits, and why it went first.

## Decision

**Move the functions verbatim into a package; change nothing else.**

⭐⭐ *The proof is the method.* The file was cut into 50 blocks by AST — each top-level statement plus the
comments above it — and the blocks were asserted to reproduce the original body **byte for byte** before any
were moved. Afterwards, all 43 definitions were diffed against `HEAD`: the only differences are the ten call
sites now qualified through `common`. A refactor that cannot show it changed nothing is a rewrite.

### 🔴 What the barrel could not hide

The plan said the split would be invisible to callers. **It was not**, and the reason is worth recording:

**1. The flat module's whole import namespace was a test seam.** Nine names are faked through it —
`suggest_transfers`, `captain_picks`, `select_squad`, `route_to_player`, `fetch_manager_team`, `team_dna_all`,
`_chip_status`, `_entry_history`, `backfill_due`. A package re-export forwards attribute *reads*; it cannot
forward *writes*. So `monkeypatch.setattr(answers, "suggest_transfers", …)` rebinds a name nothing looks up
and the fake silently does nothing.

⭐⭐ *A fake that reaches one caller but not the next is worse than no fake, because the test still passes —
for the wrong reason.*

Two fixes, chosen by whether the name is shared:

* the three helpers in `common` are called **module-qualified** (`common.plain(…)`), giving each **one**
  patch point instead of one per importer — ⚠️ this is the one deliberate deviation from the verbatim move;
* the rest name the family that resolves them (`answers.squad`, `answers.profiles`).

**2. 🔴 Two handlers shadowed their own modules.** `league()` and `player()` are re-exported, so
`answers.league` and `answers.player` resolved to the *functions*, and `answers.player.team_dna_all` raised
`AttributeError`. Renamed to **`mini_leagues`** and **`profiles`**. ⭐⭐ *A name that resolves to two
different objects depending on import order is a trap, not a convenience.*

**3. 🔴🔴 The miss that mattered: I scanned `tests/`, and the offender was in `spikes/`.**
`spikes/018-flutter-read-slice/regenerate_samples.py` stubs the FPL network call the same way, to build the
committed `my-team` sample. With the stub inert, the sample would have been regenerated from a **real network
call**. Caught by `test_api_contract`, and confirmed as mine by running that test against `HEAD` in a
throwaway worktree rather than assuming.

⭐⭐⭐ *A stub that fails open is worse than one that raises: the output still looks like a sample.* And the
process lesson is plainer — **a repo-wide pattern needs a repo-wide scan**; `tests/` was where I expected the
callers, not where they all were.

### Guarded

`tests/test_answers_package.py`: no handler may shadow a family · every family must be listed (⭐ *a
parametrised guard is only as wide as its list, and the list is the part that goes stale*) · the contract
layer must resolve every name it publishes · the shared helpers must be reached through the module. Verified
by reintroducing the `profiles` → `player` rename and watching two of them fail.

## Consequences

**Good:** 2,368 lines in one file becomes 2,634 across eight, largest **868**. The contract layer is
untouched. Patch targets now say which module they are faking.

**Costs:** ~260 more lines, all docstrings and per-module import headers — ⭐ *the price of a module knowing
what it is for*. Eight test files and one spike changed, which the gate did not predict; the barrel hides
reads, not writes, and that should have been obvious before I claimed otherwise.

**Open:** the suite still imports nine private helpers from this package. Recorded in `__all__` with a
comment rather than preserved silently — a name another file imports is not private, and fixing that is a
bigger job than this split.
