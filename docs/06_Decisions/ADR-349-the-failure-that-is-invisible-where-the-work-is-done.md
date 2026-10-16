# ADR-349 — The failure that is invisible where the work is done

**Date:** 2026-10-16
**Status:** Accepted
**Found by:** the same CI failure, twice in four hours
**Builds on:** ADR-346 (which recorded it the first time and did not prevent the second)

---

## Context

Twice today CI went red with **every test passing**:

> *🔴 The test suite modified `data/seed.db`, which is committed to git.*

Both times the cause was identical. Adding a column means `Storage._migrate` runs
`ALTER TABLE … ADD COLUMN` on any database lacking it, and the committed snapshot is such a database — so
the first test to open it **writes to a file that is in git**. First `team_h_score` and friends
(ADR-346), then `highlights_url` (ADR-347), four hours apart.

### ⭐⭐ Why recording it was not enough

ADR-346 wrote the lesson down in detail. It happened again anyway, and the reason is structural rather
than careless:

⚠️⚠️ **It cannot fail on a developer machine.** A machine that has ever run the app has `data/fpl.db` —
**gitignored** — so the migration lands there, invisibly. CI has no such file, so the same code reaches
the snapshot instead.

⭐ *The failure is invisible exactly where the work is done and visible only where nobody is watching.* A
note in an ADR does not help, because nothing on the machine making the change ever disagrees with you.

## Decision

**A test that compares the committed snapshot against the schema the code declares** —
`tests/test_the_snapshot_matches_the_schema.py`, one case per table.

It reads `SCHEMA_DDL` **and** `_MIGRATIONS`, and reads the snapshot **read-only through `sqlite3`** rather
than through `Storage`, which would migrate the very file it is inspecting.

⭐ The point is the *location*, not the assertion: it fails on the machine where the column was added, in
the same `pytest` run that would otherwise be green, with the fix in its own failure message.

## ⭐ What it does not do

It does not stop a column being added. ⚠️ *The snapshot is a fixture and fixtures follow the schema* —
the work is one command, and the value here is being told to do it before pushing rather than afterwards
by a machine in another country.

📌 It also says nothing about the *other* half of this problem, recorded and still open in ADR-346: a
developer running `ingest.refresh` locally turns ten unrelated tests red, because on SQLite any test
opening the default store reads `data/fpl.db`. ⭐ **Both faults are the same root** — a gitignored file
that tests read — and this ADR only closes the direction that reaches CI.

## Consequences

✅ Both snapshots migrated deliberately, verified schema-only: eleven tables, **no row-count change**, and
the fifty backfilled scores intact.

⏳ The deeper fix — tests not reading a gitignored database at all — stays open.
