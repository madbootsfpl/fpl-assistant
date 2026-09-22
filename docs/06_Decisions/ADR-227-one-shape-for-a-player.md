# ADR-227 — One shape for a player

**Date:** 2026-09-22
**Status:** Accepted
**Closes:** `Flutter_Start_Checklist.md` item 1b
**Builds on:** ADR-221 (the models), ADR-226 (where it bit)

---

## Context

The API described a player **five different ways**, and I had parked the decision on the owner three times
before he asked what I actually needed from him.

⭐⭐ **The honest answer was "nothing".** Every consumer was code written this week, the payload only gets
smaller, and nothing user-visible changes. There was no trade-off for him to weigh — *I had been treating a
refactor as a product decision, which is its own way of not doing the work.*

| where | keys |
|---|---|
| `analysis` — xi · bench · issues · weakest · top_pick · `my-team` | **11**, curated |
| `transfers.moves[].in` / `.out` | **5** |
| `route.target` | **6** |
| `captain.picks[]` | **~20** — the xP model's working |
| `build.selected[]`, `route.blocked[].out` | **45 raw database columns** |

## Why it was not merely untidy

* **It cost bytes.** `build` was 12.2 KB where 3.4 will do, on the client whose whole architecture was
  justified by measuring payload (spike 017: 2.41 MB → 0.81 MB).
* **It made the database schema part of the API contract.** Rename a column and the mobile response
  changes, with nothing in between to notice.
* **It shipped the model's internals.** `captain.picks` carried `rate`, `rate_source`, `ep_next`,
  `defcon_xp`, `by_gameweek_exact` — ⭐ *the working, not the answer*. A change to how xP is computed
  would have changed what a phone receives.
* ⭐⭐ **And it bit.** The five-key shape carries no `status`, so ADR-226's manual-transfer list **could not
  flag a doubtful player** — *a doubt hidden is a doubt priced at certainty* (ADR-206).

## Decision

**One `player_summary()`, used everywhere.** Eleven keys: who he is, what he costs, what he is projected to
score, and the three separate facts about whether he will play — `status`, `chance`, `leaving`.

Its three optional maps let every caller use it with what it has. ⭐ **Absent is not wrong**: no per-gameweek
map means `{}`, no weights means `1.0` — exactly the values those callers were already producing by
omission.

An endpoint may add keys that are **answers rather than raw data**: `bench` and `forced` (the solver decided
one, the caller asked for the other), `affordable` and `over_by` (a price against *your* budget), and
`opponent` · `venue` · `difficulty` · `penalty_taker` (facts about the fixture, not the player).

⚠️ **`doubtful` was dropped from captain picks.** It is `status == "d"` said twice, and two representations
of one fact are two things that can disagree.

### The guard sweeps rather than checking known places

`tests/test_player_shape.py` walks **every** endpoint's response, finds anything with `id` + `web_name`, and
requires exactly the shared shape. ⭐ Identified by content rather than by a list of paths, because a new
endpoint nesting a player somewhere unexpected is precisely what a hand-written list would miss (ADR-184).

⚠️ **Exactly these keys, not "at least".** A superset is how the database row crept in last time: every
assertion about the curated fields passed while 34 extra columns rode along.

---

## What doing it found

### ⭐⭐ A redundant override is a blind spot wearing the costume of safety

ADR-226 had added `position`, `status` and `chance` explicitly inside `replacements_for`, because the
summary it used carried none of them. After the merge those lines were redundant — and **they masked the
shared function**: a mutation falsifying `status` inside `player_summary` could not reach that list, so no
test caught it anywhere in the suite.

Removing the redundancy made the guard real.

### ⚠️ A fifth shape I had not counted

The sweep found `captain.picks`, which I had never listed among the four. ⭐ *A sweep finds what an
inventory does not* — which is the argument for writing one.

### ⚠️ Another hedge of mine, found by a legitimate change

`test_a_sample_carries_no_integer_keys` read
`assert '"by_gameweek"' not in text or '": {\n' in text` — which asserts essentially nothing. It went red
only because an empty `by_gameweek` appeared, and the fix was to walk the decoded structure and check the
keys themselves. ⭐ *A hedge is not a weaker assertion, it is the absence of one* (ADR-180) — the second
one of mine found this week.

---

## Verification

* **5/5 mutations killed** on the shape sweep, including *transfers get their own five-key shape again*,
  *route.blocked ships the raw row again*, *build ships the raw solver rows again* and *captain ships the
  xP working again*.
* All **44 pre-existing transfer tests** and the full **2,242-test** suite pass unchanged.
* Payloads: `build` **16.3 → 4.7 KB**, `route` **5.9 → 1.9 KB**, `captain` **1.9 → 1.1 KB**.
* The Dart client lost a whole class: `PlayerRef` existed only to cope with the smallest shape. ⭐ *A model
  that needed two classes was telling us the contract had two answers to one question.*

## Consequences

**Good:** one class and one widget serve every screen; a new endpoint inherits availability, price and
projection without deciding anything; the database schema is out of the contract.

**Costs:** a caller that genuinely wants a raw column must now ask for it deliberately. That is the point,
but it will feel like friction the first time.

**Open:** ⚠️ `gameweek-plan` is now **22 KB** — by far the largest response, and the screen most likely to
be opened on mobile data. Most of it is the explanation (ADR-224), which is the reason to open it.
