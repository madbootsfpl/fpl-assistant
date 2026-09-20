# ADR-216 — Hardening what exists says nothing about what arrives

**Date:** 2026-09-20
**Status:** Accepted — **SQL not yet applied to production**
**Follows:** ADR-212 (the manual described the hole the code had closed) · ADR-211 (the pipeline)

---

## Context

Found while preparing to run the pipeline on production after ADR-213/214 added two new tables.

ADR-212 hardened **seven tables** — the ones holding emails and saved squads — by hand, and closed them to
the publishable key. It did not consider the tables that did not exist yet.

The data pipeline creates its tables with a plain `CREATE TABLE`, so they inherit the project's **default
privileges**. A stock Supabase project ships with:

```sql
alter default privileges in schema public grant all on tables to postgres, anon, authenticated, service_role;
```

Reproduced on a production-shaped Postgres — Supabase's roles, Supabase's defaults, then a real pipeline
tick. Every one of the eleven tables it created came out as:

```
DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE   →  anon
```

⭐⭐ **So the hardening closed the front door while the pipeline kept building side doors.** Each new table —
`players`, `fixtures`, `player_transfer_flow`, and now `xp_board` and `team_dna_board` — arrives writable by
the publishable key, and nothing anywhere says so.

⚠️ **This is vandalism, not disclosure.** The data is public: anyone can pull the same numbers from the FPL
API, so there is nothing to leak. What it permits is `truncate players` from a key that, per the mobile
audit, *"is compiled into the binary and can be extracted from the IPA in minutes"* — which takes the app
down for every tester.

⭐ **The shape is ADR-212's, one level down.** That ADR was about documentation describing a system that had
changed underneath it. This is a *permission model* describing a database that keeps growing underneath it.
Both are the same error: **a fix scoped to the things you could see at the time.**

---

## Decision

`sql/lock_data_tables.sql`, in two parts — and the second is the one that matters.

**1. The pipeline's tables become SELECT-only.** They must stay readable: the mobile client reads them
directly (audit §4.1), and that is the whole point of publishing them. No caller anywhere writes them with
the publishable key — the pipeline authenticates as the database owner.

**2. New tables arrive closed.**

```sql
alter default privileges in schema public revoke all on tables from anon, authenticated;
```

⭐ Revoking eleven tables fixes today. This is what stops the twelfth from repeating the whole problem, and
it is also now part of `sql/setup.sql`, so a fresh project never has it.

⚠️ **Failing closed is deliberate.** A new table the app cannot read is a visible bug on the first page
load. A new table the world can delete is invisible until someone does.

---

## Verified before proposing it

On a production-shaped database, after a real pipeline run had created the tables **already open**:

| | |
|---|---|
| `anon` reads `players` / `xp_board` | ✅ 667 rows each — mobile unaffected |
| `anon` delete · truncate · update · insert | 🔒 all four refused |
| **a real pipeline tick afterwards** | ✅ published normally |
| **a table created afterwards** | ✅ arrives with no grants at all |

That fourth row is the claim the whole ADR rests on, so it is the one with a test.

## Two wrong turns, both caught

⚠️ **I read staging's grants and nearly reported them as production's.** The owner caught it. Staging shows
`squads` open and `beta_users` closed — because staging has Stage A/B and never had B3 — which is exactly
the pattern that would look alarming on production. The diagnostic query now **names the database in its
first row**, because a result you cannot attribute is not a result. ⭐ *The same mistake as the `git log` vs
deployed-code incident: an expectation read as an observation.*

⚠️ **The first guard could not catch a missing revoke.** It created the tables *after* `setup.sql` had
already closed the defaults, so they arrived shut, the revoke was redundant, and deleting it changed nothing
— the mutation passed green. Production's situation is a table that has been writable for weeks, so the test
now opens them first. ⭐ *A fixture that models less than reality will confirm a broken mechanism* — the
ninth time this month.

## Consequences

**Good:** the pipeline's tables can be published for mobile without also being deletable by it. The default
privilege change means this class of hole closes once rather than per table.

**Cost:** one more SQL file a new project must run. ⚠️ Mitigated by putting the default-privileges line in
`setup.sql` itself — `lock_data_tables.sql` is a **migration for projects that already have open tables**,
not part of a fresh install, and 📅 it can be deleted once no such project remains.

**Not done:** `events` was deferred at the original cutover and still is. It needs `INSERT` only; whether it
currently has more is part of the same audit.

⏳ **Not yet applied to production.** The diagnostic runs first, because a fix applied without reading the
answer is how the 2026-09-19 incident happened.
