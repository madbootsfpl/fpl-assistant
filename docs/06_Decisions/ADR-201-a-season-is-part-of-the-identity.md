# Architectural Decision Record: A season is part of the identity

**Decision ID:** ADR-201
**Date:** 2026-09-16
**Status:** ✅ **Accepted — built and migrated. Phase 0a of the ML roadmap.**
**1823 tests, ruff clean.**
**Superseded By / Replaces:** Extends [ADR-129](./ADR-129-per-gameweek-key-is-the-fixture.md)'s key
(`element_code, fixture` → `element_code, season, fixture`). **No `decision_xp` change** — nothing that
scores a player reads a second season yet; this is about what will still be there when something does.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The ML roadmap's first question was *"can we not use the data now, why gated?"* and the honest answer was
that there wasn't much data to gate. Checking what the cache actually holds turned up something worse than
a small training set.

`player_history` was keyed on `(element_code, fixture)` — correct as far as ADR-129 went, which was about
**double gameweeks within a season**: FPL's `element-summary` sends one entry per match, so keying on
`round` made a player's second match silently overwrite their first.

**But FPL restarts `fixture` ids at 1 every August.** Today's cache holds 2,547 rows across 40 distinct
fixture ids, numbered 1–40. Next August it will serve a completely different set of matches numbered 1–38
again, and `INSERT … ON CONFLICT(element_code, fixture) DO UPDATE` would have **overwritten this season's
GW1 with next season's GW1, row for row, with no error, no warning and no way to tell afterwards.**

⭐⭐ **THE COLLISION WOULD NOT HAVE LOOKED LIKE DATA LOSS — IT WOULD HAVE LOOKED LIKE A REFRESH.** Row
counts stay roughly the same. Every value is individually plausible. Nothing raises.

#### ⚠️ And it is unrecoverable, which is what set the priority

FPL will sell the aggregate back and not the detail. `player_history_past` proves it: **2,097 rows covering
twenty seasons back to 2006/07 — one row per player per season.** Against that, four gameweeks of *this*
season are **2,547 rows**. The per-match record exists for the current season only; once the rollover
overwrites it, *"Salah scored 12 in GW7 away to Newcastle having played 88 minutes the previous week"*
becomes *"Salah, 2026/27, 212 points"* forever.

⭐ **A model can be built next winter. The gameweek you failed to store cannot.** That is the whole reason
this landed before any model did, ahead of every more interesting item on the roadmap.

---

### 🎯 Decision

**`season` joins the primary key**, so `(element_code, season, fixture)` identifies a match:

```sql
season         TEXT NOT NULL DEFAULT '',
PRIMARY KEY (element_code, season, fixture)
```

**The season comes from the match, not from the clock.** `season_from_kickoff()` reads the row's own
`kickoff_time` — month ≥ 7 → that year starts the season, otherwise the previous year. Stamping rows with
*"whatever season it is today"* would be right for 51 weeks and wrong for the one that matters: a refresh
run in late July or on a delayed fixture would file the match under the wrong season, and that is precisely
the boundary the whole change exists to handle. ⭐ **A record about a point in time should take its
timestamp from the event, never from the process that stored it.**

`_rekey_history` backfills `season` on existing rows *before* rebuilding the table under the new key —
2,547 live rows migrated to `2026/27`, rounds 1–4, none lost.

---

### ⚠️ Two things this got wrong first, both caught by mutation testing

**1. The migration re-ran on every single open.** The idempotency check compared the current primary key
against `["element_code", "season", "fixture"]` — but `PRAGMA table_info` lists columns in **table** order,
and `season` was appended to the table, so it always reads *last* regardless of how the key was declared.
The list never matched, and the table was dropped, copied and renamed on **every connection, forever**.

⭐⭐ **A MIGRATION THAT CANNOT TELL IT HAS ALREADY RUN IS NOT A MIGRATION, IT IS A REBUILD** — and this one
was invisible, because the data it leaves behind is correct. Fixed by comparing **sets**: the key is a set
of columns, and it was being tested as a sequence.

**2. The test that was supposed to catch it couldn't.** It asserted that a re-open preserved every row and
left no `*_rekeyed` scaffolding behind — and **passed with the check reverted**, because a rebuild also
preserves every row and drops its own temp table. ⭐⭐ **WHEN THE BROKEN AND THE WORKING VERSIONS PRODUCE
THE SAME END STATE, ASSERT THE WORK AND NOT THE RESULT.** The guard now traces the SQL and asserts no
rebuild ran.

⚠️ **And the second version still passed**, because it attached the trace to `storage.conn` — by which
time `__init__` had already run the migration it was meant to be watching. ⭐ *The observer has to be in
place before the thing it observes*: `sqlite3.connect` is patched so the connection is traced from the
moment it opens. Only then did the mutant go red.

Same family as ADR-189 and ADR-191 §1: ⭐ *a fixture that only exercises the lucky case will confirm a
broken mechanism* — here, a fixture where **both outcomes are the lucky case.**

---

### 🧪 Mutation results

| mutant | outcome |
|---|---|
| `season` dropped from the primary key | 🔴 2 failed — the two seasons collide |
| season boundary moved to January | 🔴 1 failed — an August match files under the wrong season |
| idempotency check compares a list again | 🔴 1 failed — *after* the guard was rebuilt twice |
| the early `if not kickoff_time` return removed | ⚪ survives — **equivalent**: `int("None")` raises and the existing `except` returns `None` anyway. Recorded rather than papered over with a test that would only assert the fast path exists |

---

### 📊 Consequences

**Good:** the rollover is safe, and per-match history now accumulates season on season — which is the
training set Phase 1 needs. Existing caches migrate on next open with no manual step.

**Costs / limits:**
- ⚠️ **This preserves the future, not the past.** Whatever earlier seasons were overwritten before today
  are gone; the only per-match data that exists is from GW1 2026/27 forward.
- The archive import (11 seasons of community-collected per-match data) is still **gated on licensing** —
  `vaastav/Fantasy-Premier-League` reads **NOASSERTION**, which is not a grant of rights, and that matters
  more now the project is AGPL with a donations question open.
- One season of stored history is not a training set. Phase 0b (the minutes baseline) is next, and it
  measures the model we already have so that anything learned later has a number to beat.

---

### 🔗 Links

- [ADR-129](./ADR-129-per-gameweek-key-is-the-fixture.md) — the key this extends
- [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) — the minutes default 0b will measure
- `src/storage.py` · `src/analytics/last_season.py` · `tests/test_history_retention.py`
