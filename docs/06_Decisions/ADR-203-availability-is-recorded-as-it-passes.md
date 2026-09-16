# Architectural Decision Record: Availability is recorded as it passes

**Decision ID:** ADR-203
**Date:** 2026-09-17
**Status:** ✅ **Accepted — built. Closes [ADR-202](./ADR-202-the-minutes-baseline.md)'s one uncloseable leak, for every future baseline.**
**1823 → 1832 tests, ruff clean.**
**Superseded By / Replaces:** The same fault as [ADR-201](./ADR-201-a-season-is-part-of-the-identity.md), in the
one other place the app was letting data expire. **No `decision_xp` change** — nothing reads the log yet.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-202 measured the minutes model and had to publish its headline number with an asterisk:

> `chance_factor` reads the player's **current** `status` / `chance` straight off the players table — today's
> injury news, applied retrospectively to round 1. That is not walk-forward and **cannot be made so**.

It cannot be made so because FPL serves availability as a **now** field. `bootstrap-static` says whether a
player is fit *today*; there is no history endpoint, no "as of", nothing to backfill from. And `players` is a
single mutable row per player, so **every refresh overwrote the previous answer**.

**195 of 659 players carry a flag today.** Against round 1 — five weeks ago — essentially all of those flags
are wrong, in both directions: players who have since been injured are scored as unavailable for matches they
started, and players who have since recovered are scored as fit for matches they missed.

⭐ **This is ADR-201 again.** Not a rollover this time, but the same shape: *a field that only ever holds the
present, quietly destroying the past on a schedule*. And the same consequence — the GW8 review would have
re-run the baseline and reproduced the identical asterisk, because nothing in between was recording.

⭐ **The observer has to be in place before the thing it observes.** Every refresh that ran while this ADR was
unwritten is an observation that does not exist.

---

### 🎯 Decision

A `player_availability` log, written on every `refresh`.

**A change log, not a poll log.** One row per *distinct* value, not per refresh. Two refreshes a day × 659
players is ~480k rows a season and carries no information a change log does not; real availability changes a
few dozen times a week league-wide. Verified on live data: a second refresh eight hours later added **0** rows.

#### ⭐ But a change log alone cannot tell "unchanged" from "not observed"

Three silent weeks and three weeks of a stable squad produce **identical tables** — and that ambiguity would
land squarely on the measurement this exists for, because *"his status was 'a'"* and *"we last looked a month
ago"* are not the same evidence.

So each row is an **interval**, not an event:

```sql
observed_at  TEXT NOT NULL,   -- when this value was first SEEN
last_seen_at TEXT NOT NULL,   -- when it was last CONFIRMED still true
```

`availability_as_of(when)` returns both alongside the value, **deliberately** — a caller that cannot see the
staleness will treat a three-week-old status like this morning's.

#### ⚠️ `observed_at`, not `changed_at` — and the distinction is the honesty of the table

ADR-201 stamps a match with its own kickoff, on the principle that *a record about a point in time takes its
timestamp from the event.* Availability has no such timestamp: FPL does not say when the flag went up, only
that it is up. The flag may have been raised hours before the refresh that first saw it.

⭐ **Naming the column `changed_at` would claim knowledge of a moment nobody recorded.** The same principle
produces the opposite column name here, because the principle is about *what is actually known*, not about
preferring one clock to another.

**`news` counts as a change.** *"Knock — 75% chance"* becoming *"Knock — expected back 20 Sep"* is new
information at an unchanged status, and it is the sentence a manager actually reads.

---

### ⚠️ What the build got wrong, and what caught it

**The recorder would have crashed the refresh.** A player FPL sends without a `code` cannot be keyed, and the
first version let the `NOT NULL` violation propagate — out of `save_availability`, out of `refresh`, taking
teams, players, fixtures and Elo down with it. ⭐ **The failure path of a side-record must not take down the
thing it observes**: `refresh` is the app's lifeline, and everything downstream degrades to stale data if it
dies. Codeless players are now skipped and the refresh completes.

**It was found by the test fixture, which is the interesting part.** The shared `bootstrap_static_sample.json`
carries eight keys and no `code` at all — so it *is* the pathological payload, and four existing ingest tests
went red the moment the writer was wired in. The fixture that was too thin to test the feature was exactly
the fixture that proved the feature unsafe.

⚠️ **And that thinness then made the wiring test vacuous.** "Every player in the payload has an observation"
against a payload where no player can be keyed asserts `0 == 0` and passes whatever the code does. ⭐ *A
fixture that cannot express the field under test turns the guard into decoration.* The wiring test now injects
codes (real payloads always carry one — 0 nulls in 659 live rows) and asserts `len(rows) == n_players > 0`;
the codeless case became its own test, asserting the refresh survives.

⭐ **Testing a component is not testing that anything uses it.** All six `save_availability` tests passed with
the call absent from `refresh` — a perfectly-tested recorder that never runs is the same as no recorder.

---

### 🧪 Mutation results — 7 mutants, 7 red

| mutant | outcome |
|---|---|
| `refresh` stops calling the recorder | 🔴 2 failed |
| every refresh writes a row (poll log, not change log) | 🔴 3 failed |
| `last_seen_at` stops advancing (staleness invisible) | 🔴 3 failed |
| `news` alone no longer counts as a change | 🔴 1 failed |
| `availability_as_of` ignores the date (sees the future) | 🔴 1 failed |
| a codeless player aborts the whole refresh | 🔴 3 failed |
| an older database never gains the table | 🔴 9 failed |

⚠️ **The first sweep reported nothing at all and looked like a pass.** The harness ran under **zsh**, which
does not word-split unquoted parameter expansions, so `$T` reached pytest as one impossible path and every
run produced no summary line. ⭐ *A mutation sweep that cannot fail is worth less than no sweep, because it
reports confidence* — the labels printed, the verdicts did not, and only the blank column gave it away.

---

### 📊 Consequences

**Good:** from the owner's next `refresh`, availability accrues with its own timeline. The GW8 review can
score the baseline on what was actually known before each deadline, and the asterisk goes with it.

**Costs / limits:**
- ⚠️ **This fixes the future, not the past.** ADR-202's numbers keep their leak permanently; there is nothing
  to backfill from. The next baseline and the one just taken are **not directly comparable** on that axis, and
  the GW8 review must say which it is quoting.
- The log starts empty. Rounds 1–4 have no observations and never will.
- Nothing reads it yet — `availability_as_of` exists for the review and has no production caller. ⭐ *A
  recorder with no reader is still worth building when the data is perishable, and only then.*
- Resolution is the refresh cadence. A flag raised and withdrawn between two refreshes is never seen — an
  honest limit of observing rather than subscribing.

---

### 🔗 Links

- [ADR-202](./ADR-202-the-minutes-baseline.md) — the leak this closes, and the review that will use it
- [ADR-201](./ADR-201-a-season-is-part-of-the-identity.md) — the same fault, the other place
- [ADR-038](./ADR-038-expected-minutes-v0.md) — `chance_factor`, the consumer this would eventually serve
- `src/storage.py` · `src/ingest.py` · `tests/test_availability_log.py` · `tests/test_ingest.py`
