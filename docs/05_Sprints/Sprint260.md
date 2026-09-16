# Sprint 260: The gameweek you failed to store

**Dates:** 2026-09-16
**Status:** ✅ Complete — **1819 → 1823 tests, ruff clean.** ADR-201 written, live cache migrated.
**Phase 0a of the ML roadmap.**

---

## Why a schema change came before a model

The ML conversation ended with *"can we not use the data now, why gated?"*, so the first job was to look at
what the cache actually holds. It holds less than it should, and it was about to hold less still.

`player_history` was keyed `(element_code, fixture)`. ADR-129 set that key to fix double gameweeks — two
matches in one `round` — and it is right about that. It is wrong about the year boundary, because
**FPL restarts fixture ids at 1 every August.** Today: 2,547 rows, 40 distinct fixture ids, numbered 1–40.
Next August the API serves a different set of matches numbered 1–38, and the upsert would have overwritten
this season's rows with next season's, one for one.

⭐⭐ **THE COLLISION WOULD NOT HAVE LOOKED LIKE DATA LOSS — IT WOULD HAVE LOOKED LIKE A REFRESH.**

---

## The number that set the priority

`player_history_past` is what FPL will sell back: **2,097 rows covering twenty seasons, back to 2006/07 —
one row per player per season.** Four gameweeks of the current season are **2,547 rows**.

The per-match record exists for the current season only. Overwrite it and *"12 points, 88 minutes, away to
Newcastle"* becomes *"212 points, 2026/27"*, permanently.

⭐ **A model can be built next winter. The gameweek you failed to store cannot.**

---

## Built

`season` joins the primary key — `(element_code, season, fixture)` — and is taken from the row's own
`kickoff_time`, never from the clock. A refresh run in late July, or a fixture that gets delayed across
the boundary, is exactly the case the change exists for, and "today's season" gets it wrong.
⭐ *A record about a point in time takes its timestamp from the event, not from the process that stored it.*

`_rekey_history` backfills the column before the rebuild. Live migration: **2,547 rows → `2026/27`,
rounds 1–4, none lost**, no scaffolding left, second open a no-op.

---

## ⚠️ What mutation testing found, twice

**The migration re-ran on every open.** The idempotency check compared the current key against an ordered
list — but `PRAGMA table_info` returns columns in **table** order, and `season` was appended, so it always
read last however the key was declared. The list never matched. Drop, copy, rename, every connection,
forever — and invisible, because the data it leaves is correct.

⭐⭐ **A MIGRATION THAT CANNOT TELL IT HAS ALREADY RUN IS NOT A MIGRATION, IT IS A REBUILD.**
A key is a **set** of columns and was being tested as a sequence.

**Then the guard for it passed while the bug was in place — twice.**

1. It asserted the rows survived and no `*_rekeyed` table was left. A rebuild does both. ⭐⭐ **WHEN THE
   BROKEN AND THE WORKING VERSIONS PRODUCE THE SAME END STATE, ASSERT THE WORK AND NOT THE RESULT.**
2. Rebuilt to trace the SQL — and still passed, because it attached the trace to `storage.conn`, by which
   time `__init__` had already run the migration it was watching. ⭐ *The observer has to be in place
   before the thing it observes.* `sqlite3.connect` is patched so the connection is traced from the moment
   it opens.

Only then did the mutant go red. Same family as ADR-189 and ADR-191 §1, one turn worse: a fixture where
**both outcomes are the lucky case.**

| mutant | outcome |
|---|---|
| `season` dropped from the key | 🔴 2 failed |
| season boundary moved to January | 🔴 1 failed |
| idempotency check compares a list again | 🔴 1 failed (after two rebuilds of the guard) |
| early `if not kickoff_time` return removed | ⚪ **equivalent** — `int("None")` raises and the `except` returns `None` anyway; recorded, not papered over |

---

## 💡 The lesson

⭐⭐ **A GUARD AGAINST SILENT CORRUPTION CANNOT BE WRITTEN BY LOOKING AT THE DATA AFTERWARDS** — the whole
defining property of this class of bug is that the after-state looks fine. Both failed versions of the test
were reasonable, careful, and checked the only thing visible from the outside.

---

## Definition of Done

- ✅ **Tests** — 4 new (`tests/test_history_retention.py`), `test_double_gameweek.py` updated to the
  3-column key; full suite **1823 passed**; 4 mutants, 3 red and 1 recorded as equivalent
- ✅ **Manual smoke** — live `data/fpl.db` migrated and inspected: 2,547 rows, all `2026/27`, rounds 1–4,
  no leftover tables, second open 0.000s
- ✅ **Docs** — ADR-201 + index row, PROJECT_STATUS, this sprint doc

**Next:** Phase 0b — the minutes baseline, so anything learned later has a number to beat.
