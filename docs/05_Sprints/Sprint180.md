# Sprint 180: A per-gameweek row is keyed by the fixture, not the gameweek (ADR-129)

**Dates:** 2026-08-24
**Status:** ✅ Complete — ADR-129. 1194 → 1204 tests, ruff clean.

> **Owner:** asked for a deliberate DGW/BGW pass, then gated and approved the fix it found.

---

### 🔍 Why this sprint exists

GW1 produced six bugs of one species: code that had shipped correct-looking and had **never executed under
real conditions**. The obvious next instance was the first double or blank gameweek. So rather than wait to be
surprised, we audited those paths on purpose — and found three more, before the event.

### 🐛 The one that mattered

`player_history` was keyed `PRIMARY KEY (element_code, round)`. **FPL's `element-summary` sends one entry per
fixture**, so in a double gameweek a player has two entries sharing a `round`. The upsert collided:

```
stored 2 fixtures → 1 row
   round=19  fixture=101  pts=12  goals=2
   (he actually scored 20 points and 3 goals, over 180 minutes)
```

Nothing was broken yet — there has been no double this season, so every round has one fixture. **A bug with a
start date.**

The blast radius would have been the form blend (about to be enabled at GW4-6), every surface shipped in
ADR-128, and — worst — **`calibrate`**. Its walk-forward pairs a gameweek's predicted xP against its actual
points; in a double it would compare a two-match projection against one match's return, making the model look
worse than it is. The harness would have measured our own data loss and reported it as a modelling failure.

---

### 🔧 What shipped

**The key is now `(element_code, fixture)`** — what the row actually is, a player's return from one match.
`round` stays a column, because grouping by gameweek is what the analytics want; it just stops being an
identity. Verified feasible first: `fixture` is never null and was already unique across all 609 rows.

**A different kind of migration.** `_migrate` only adds columns, and SQLite cannot alter a primary key at all,
so `_rekey_history` does the standard rebuild — create, copy, drop, rename — and is **self-detecting and
idempotent**: it inspects the current key and does nothing once the table is right. It runs *after* `_migrate`,
so the copy sees every column the old table just gained.

**Dry run on a copy of the live database before touching the real one:** 609 rows preserved, 27 columns
preserved, key changed, second open a no-op.

**`stat_series` now aggregates per round** — a double is one point on a sparkline, not two at the same x — and
gained an `agg` argument. `form_dots` deliberately still shows **both** results: two matches, two results, and
merging them would hide half the gameweek.

---

### ✅ Definition of Done

- **Automated:** 1194 → **1204 tests**, green, ruff clean. 10 new: both halves of a double surviving, ingest
  still idempotent, a single-fixture round unchanged, the rekey preserving rows and the widened columns, the
  rekey being idempotent, a sparkline showing one point per gameweek, a per-90 dividing by summed minutes, a
  snapshot stat not being summed, and the dots showing both results.
- **Manual smoke:** the dry run above, then the live database and `seed.db` rekeyed and verified.
- **Docs:** ADR-129, this sprint doc, PROJECT_STATUS, Roadmap (the standing-risk note now records that auditing
  ahead of a first occurrence works).

---

### 📝 Lessons

**Audit before the first occurrence, not after it.** Six bugs arrived with GW1 because nobody could run those
branches beforehand. These three were found by deliberately constructing the conditions — a synthetic double
and blank — and it cost an hour. The same is worth doing before the first blank gameweek and the first chip
deadline.

**A primary key is a claim about the domain.** `(element_code, round)` asserts "a player has one row per
gameweek", which is *false in FPL* and had been false the whole time. It held only because the season hadn't
reached a double. Worth asking of any composite key: is this uniqueness a rule of the domain, or just of the
data we happen to have seen?

**Check your test data before believing your finding.** The first run of this audit reported that xP itself
was broken in a double. It wasn't — the synthetic fixtures had `team_id`s that didn't match their names, so
`team_schedule` (which keys on names) saw two matches while `player_xp` (which keys on ids) saw one. A wrong
finding reported confidently would have sent a whole sprint after nothing.

---

### 🔭 Still open from the same audit

Both display-only, both cheaper than this one:

- **The fixture ticker shows only one fixture of a double.** Its cells hold one fixture per team-gameweek, so
  a team playing twice shows one opponent. This is the one tool built for spotting doubles.
- **The player card's per-GW row double-counts a double.** `team_schedule(...)[:3]` yields two slots for the
  same gameweek and fills each with the already-doubled `by_gameweek` value — 25 xP against a real 15 — while
  spending two of its three slots on one week.

**Confirmed correct and left alone:** `player_xp` doubles a DGW and zeroes a BGW exactly as ADR-007/032 claim;
`_card_horizon` and the per-GW xP toggle both handle it.
