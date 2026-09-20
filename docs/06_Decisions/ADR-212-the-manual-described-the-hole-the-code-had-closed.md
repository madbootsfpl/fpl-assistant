# ADR-212 — The manual described the hole the code had closed

**Date:** 2026-09-20
**Status:** Accepted
**Supersedes the setup SQL in:** `docs/BETA.md`, `docs/CLOUD_SQUADS.md`, `docs/ANALYTICS.md`

---

## Context

Stages A, B and B3 closed the Supabase store: the tables holding email addresses and saved squads were
revoked from the publishable key, and the app's access was replaced by twelve `security definer` functions
(ADR-211 era work, `docs/SUPABASE_RLS.md`). Production was cut over on 2026-09-19 and verified.

A documentation review the next day found that **three setup runbooks still instructed the reader to create
the exact policies that work had removed**:

| file | what it told you to run |
|---|---|
| `docs/BETA.md` | `create policy "anon users read" on beta_users for select using (true)` |
| `docs/CLOUD_SQUADS.md` | four `using (true)` policies on `squads`, or `disable row level security` |
| `docs/ANALYTICS.md` | a `using (true)` **read** policy on `events` |

Nothing was broken. No test failed, because no code was wrong. The running system was hardened and correct.
**The instructions for building it were not**, and instructions are what a person follows when they set up a
second project, rebuild after an incident, or hand the thing to someone else.

⭐⭐ **A hardening changes the system; it does not change the documentation that describes how to build one.**
Those are two artefacts and only one of them had a test.

### The second failure, underneath the first

Each runbook carried **its own copy** of the setup SQL, written when that feature was built. Four copies of a
rule is how three of them end up wrong — the same drift ADR-123/127 recorded about code, reappearing in
prose. There was no single definition to update, so "update the docs" meant "remember all four places", and
the September work remembered none.

One of the three was wrong in a more interesting way than staleness. `ANALYTICS.md` justified its read policy
like this:

> *let the (server-side) anon key READ events too. The anon key lives in Streamlit secrets and is never sent
> to a browser*

That sentence is **true about the key and irrelevant to the policy**. A policy is granted to the *role*, not
to the place the credential happens to be stored — so `using (true)` on `events` exposed the table to anyone
holding that key from any source, not just to the Streamlit server. ⭐ *A permission is granted to a role, not
to a location.* The reasoning was careful and still reached the wrong conclusion, which is the kind of error
a re-read catches and a test never would.

---

## Decision

**1. One setup file.** `sql/setup.sql` creates all seven tables and all twelve functions in their hardened
form, is idempotent, and is what every runbook now points at. The three copies are deleted, not corrected —
⭐ *a pointer cannot drift from what it points at.*

**2. The runbooks say why, not just what.** Each now carries a short 🔴 note naming the SQL it used to print
and what that SQL would undo, because someone will find the old version in git history or in a screenshot and
wonder why it changed.

**3. Three guards, none of which is a word blacklist.**

- `tests/test_setup_sql.py` — builds a **real Postgres from the file alone** and proves the whole claim: it
  applies to a virgin database, `anon` cannot enumerate any of the six tables, every path the app needs still
  works, and re-running it over populated data keeps both the rows and the lock.
- `tests/test_setup_docs.py` — scans **fenced ` ```sql ` blocks** across all of `docs/` for statements that
  hand a table to `anon`. ⚠️ It deliberately does **not** grep for words: the paragraphs that *warn* against
  these statements contain them, and a guard that fires on its own warning gets weakened rather than obeyed
  (ADR-178). What makes SQL dangerous here is sitting in a block a reader is told to paste.
- `tests/test_readme_is_current.py` — checks the README's own factual claims.

**4. Everything under `docs/` is scanned by default**, with named exemptions (the ADRs, the sprint records,
and the three `SUPABASE_*.md` files whose subject matter *is* the dangerous SQL, including a rollback block
that has to keep working at 2am). ⭐ ADR-184's lesson was a guard that checked the two files someone thought
of; a new runbook is covered the day it is written.

---

## The wider finding: numbers in prose are untested claims

The same review found the README advertising **"121 ADRs · 1091 tests"** against an actual 212 and 2,039, and
**"🚨 GW1 = 2026-08-21 (tomorrow)"** a month after GW1 was played. `PRODUCT.md` carried the same two.

⭐⭐ **A number a document states is a claim the project makes about itself, and nothing was checking these.**
They are now checked, with tolerances wide enough to ignore normal growth — a guard that fails on every
commit gets deleted rather than obeyed.

The GW1 line is the more useful of the two, because the date in it was never wrong:

⭐⭐ **A document can carry a correct fact inside a claim that has expired.** *"GW1 = 2026-08-21"* is still
true. *"(tomorrow)"* is what rotted, and no date check would have caught it — so the guard tests for
**unplayed-season tense**, not for a date.

`PRODUCT.md` showed the richest version of the same shape. Its "⏳ Gated — lights up at GW1" table listed six
features as blocked on data that has since arrived. Four are now live and lit up on their own. The other
three xP terms are still dormant at weight `0.0` — but ⭐ **they stopped waiting on the calendar and started
waiting on a person**, and the page still gave the calendar as the reason. *A blocker that outlives its cause
is worse than a blocker that is simply wrong, because the stated reason keeps sounding plausible.*

---

## Consequences

**Good:** setting up a project is one file. The three runbooks cannot silently disagree with each other or
with production. A new doc is swept without anyone remembering to add it.

**Cost:** `sql/setup.sql` duplicates content that also lives in `sql/stage_b.sql` and `sql/stage_b3.sql`,
which remain as the *migration* files the cutover runbook references. ⚠️ **That is a second copy, and this
ADR is about second copies.** It is accepted because the two answer different questions — *"build one from
nothing"* versus *"move an existing one"* — and because `test_setup_sql.py` pins the behaviour of the file
that matters. 📅 **When the last project on the old schema is gone, the stage files should be deleted rather
than maintained.**

**Not fixed:** the ADRs and sprint records still contain the old permissive SQL, deliberately. They are the
record of how the system got here; rewriting one to match today would destroy the thing it exists for.

**Still open, and unchanged by any of this:** the functions stop *enumeration*, not *guessing*. A known or
guessed handle still reads a squad. Only real identity closes that — Supabase Auth, Stage C, Phase 3.

---

## Found along the way: the suite was writing to a committed file

Restoring `data/seed.db` after a test run kept leaving it modified again. Two tests in
`tests/test_postgres_cutover.py` exercise the Postgres **fallback**, which resolves to `config.SEED_DB_PATH`
— the committed snapshot. Opening `Storage()` on it runs `CREATE TABLE IF NOT EXISTS` for every table, and
the snapshot predates `player_transfer_flow` and `data_status`, so **every run added two empty tables to a
version-controlled binary**.

No data was wrong. Nothing went red. The only symptom was a `git status` that was always dirty — and ⭐ **a
signal that is always on carries no information**: "seed.db is modified" had become background noise to be
checked out, rather than a fact about what just ran.

⭐⭐ **The sharper part: one of the two tests is named
`test_a_WRITER_that_cannot_reach_postgres_raises_instead_of_writing_to_the_seed`, and its docstring warns
that a degrading writer would *"write live FPL data into the repository's snapshot … so the next `git status`
would show a modified binary"*.** Its own reader, one line above the warning, was doing precisely that.
⭐ *Describing a hazard accurately is not the same as being outside it.*

**Fixed** with `_redirect_the_seed`, which points the fallback at a `tmp_path` copy. ⚠️ Two details that each
cost a wrong answer:

- It must run **after** `_reloaded`, which re-imports config and would undo the patch.
- `shutil.copy` **carries the source's permission bits**, which mattered because of how the culprit was
  found: `chmod 444 data/seed.db && pytest` makes the writer fail loudly and name itself. The copy then
  inherited mode 444 and refused writes too — so the fix looked broken while working correctly, and the
  first reading of that was "the patch is not taking effect". ⭐ *A probe that alters the thing it measures
  will produce a confident wrong diagnosis.*

**Guarded** in `conftest.py` by `pytest_sessionstart`/`pytest_sessionfinish`, which hash the snapshot and
fail the run if it moved. ⚠️ Deliberately a **session-level** failure rather than a per-test one: the write
happens inside `Storage()`, far from whichever test triggered it, so blaming one test would be wrong more
often than right. The message names the `chmod 444` trick instead — ⭐ *finding it once by hand is not the
same as keeping it found.* Mutation-tested by restoring the bug: exit 1 with, exit 0 without.
