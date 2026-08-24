# Architectural Decision Record: A per-gameweek row is keyed by the fixture, not the gameweek

**Decision ID:** ADR-129
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved, built** (Sprint 180). Found by a deliberate audit of the
double/blank-gameweek paths, before the season's first double rather than after it. The data loss below was
reproduced, not reasoned about.
**Superseded By / Replaces:** Corrects the `player_history` primary key set by ADR-060 and widened by ADR-128.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`player_history` is keyed `PRIMARY KEY (element_code, round)` — one row per player per gameweek.

**FPL's `element-summary` does not work that way.** Its `history` array carries **one entry per fixture**, and
in a double gameweek a player has two entries with the same `round` and different `fixture` ids. The upsert
therefore collides, and the second match silently overwrites the first:

```
stored 2 fixtures → 1 row in the table
   round=19  fixture=101  pts=12  goals=2
   (the player actually scored 20 points and 3 goals that gameweek)
```

Minutes 180 become 90. Points 20 become 12. Goals 3 become 2.

**Nothing is broken today** — there has been no double gameweek this season, so every round has exactly one
fixture and the key holds. This is a bug with a start date, not a live one.

#### Why it matters more than it looks

Every consumer of per-gameweek data would be wrong, and wrong *low*, on precisely the gameweeks that decide a
season:

- **The form blend** (`form_rate`, ADR-060) — the one you are about to enable at ~GW4-6.
- **The sparklines, W-D-L dots, team form and clean-sheet rate** shipped hours ago in ADR-128.
- **`calibrate`** (ADR-101) — the walk-forward backtest pairs a gameweek's predicted xP against its actual
  points. In a double it would compare a **two-match projection against one match's return**, making the model
  look worse than it is. That is a bad way to discover a weight: the harness would be measuring our own data
  loss and reporting it as a modelling failure. This is the argument for fixing it *before* the calibration
  window, not after.

#### Decision Drivers
- **It has a deadline** — it must land before the season's first double gameweek, and before `calibrate` runs.
- **It is silent** — no error, no gap, just a smaller number. Nobody reports a player having scored too little.
- **The audit found it cheaply**; the alternative is finding it from a wrong recommendation in December.

---

### ✅ Proposed Decision

**Key a per-gameweek row by the fixture it describes: `PRIMARY KEY (element_code, fixture)`.**

That is what the row actually *is* — a player's return from one match. `round` stays as a column, because
grouping by gameweek is exactly what the analytics want; it simply stops being an identity.

Verified feasible on the live data: `fixture` is **never null** across all 609 rows, and `(element_code,
fixture)` is **already unique**, so the rebuild cannot lose a row.

#### This needs a real migration, not the existing one

`_migrate` only adds columns — `ALTER TABLE … ADD COLUMN`. SQLite cannot alter a primary key at all, so this
needs the standard four-step rebuild: create the new table, copy the rows across, drop the old, rename. That is
a different *kind* of migration than the codebase has done before, and it is the main cost of this ADR.

It should be **idempotent and self-detecting** — check the existing primary key and rebuild only when it is the
old one — so that opening any database, at any age, converges on the right schema without a flag to set or a
script to remember to run.

**No re-backfill is required.** Existing rows are one-per-round and survive the copy unchanged. A backfill would
be harmless but is not part of the fix.

#### One companion change

With the key fixed, a double gameweek legitimately produces **two rows for one round**, and
`gw_form.stat_series` currently emits a point per row — so a sparkline would plot two values at the same x.
It must **aggregate per round** (sum the counting stats, sum minutes before a per-90). `form_dots` is left
alone: two results in one gameweek is the truth, and showing both is more informative than merging them.

Reads should also order by `(round, kickoff_time)` rather than `round` alone, so the two halves of a double come
back in the order they were played rather than in whatever order SQLite returns.

---

### 🔀 Alternatives Considered

- **Key on `(element_code, round, fixture)`.** Equivalent in practice and self-documenting, but `fixture` alone
  already identifies the match, so `round` in the key is redundant. Either would work; this is a coin-flip that
  the simpler option wins.
- **Keep the key and sum the fixtures into one row at ingest.** Rejected: it destroys information we would
  immediately want back — which opponent, home or away, which match produced the haul — and it makes the
  ingest non-idempotent, since re-running would double the totals unless it first detects it had already
  summed them.
- **Keep the key and store only the "best" fixture.** Rejected as arbitrary; it is the current bug with an
  intention.
- **Wait until a double gameweek actually happens.** Rejected. The first double is when the data would be lost,
  and per-gameweek rows are only fetched once per gameweek — a late fix means re-walking 609 players to repair
  history, assuming FPL still serves it.

---

### 🧭 Consequences

**Positive** — doubles are recorded as two matches, which is what they are; the form blend and the calibration
harness measure the real return rather than half of it; the fix lands before the data it protects exists, so
nothing needs repairing.

**Negative / risks (mitigations)** — a table rebuild is a heavier migration than this project has run before
(*mitigation:* it is the documented SQLite pattern, it is idempotent and self-detecting, and it is verified
against a copy of the live database before it goes near the real one); consumers that assumed one row per round
must now group (*mitigation:* exactly one does — `stat_series` — and it is changed here, with a test);
`get_history` returning two rows for a round could surprise a future caller (*mitigation:* the docstring says
so, and the ordering makes the sequence meaningful).

---

### 🧾 Status & follow-ups

- **Accepted and built (Sprint 180).** `Storage._rekey_history` — self-detecting, idempotent, running after
  `_migrate` so the copy sees every column; `stat_series` aggregating per round; reads ordered by
  `(round, kickoff_time)`. 10 new tests. 1194 → **1204**, ruff clean.
- **Dry run first, against a copy of the live database:** 609 rows preserved, 27 columns preserved, key changed
  from `(element_code, round)` to `(element_code, fixture)`, and a second open a no-op. Only then applied to
  the real one.
- **One thing the build added beyond the plan.** `stat_series` gained an `agg` argument. Summing is right for
  counting stats (points, goals, bps, xG — a double's return *is* the sum of its matches) but wrong for
  **snapshots**: adding a player's price to itself because he played twice would read as a £6m rise. `value`
  is the column that matters and the price sparkline the widened table unblocked would have hit it. `agg="last"`
  covers it, with a test.
- **The other two findings — done the same day (Sprint 181).** Both display-only, both from the same audit.
  * The **fixture ticker** kept only the first fixture of a double (a comment said so outright), so the one
    view built for spotting doubles was the one place a double was invisible — a blank showed as an empty cell
    while a double looked like an ordinary week. Cells now carry the full `fixtures` list and render
    `CCC (H) + DDD (A)`, shaded by the **harder** of the two, since a double is only as easy as its harder half.
    `opponent`/`venue` stay as the first match so existing readers keep working.
  * The **player card's per-GW row** listed the next three *fixtures*, so a double took two of the three slots
    and each was filled with the same already-doubled `by_gameweek` value — 25 xP against a real 15, and a week
    of forward view lost. It now groups by gameweek: one cell per week, both opponents named in it, the doubled
    xP counted once.
- **Known gap, not a bug:** the chip advisor still has no DGW/BGW detection (roadmap, ADR-082).
