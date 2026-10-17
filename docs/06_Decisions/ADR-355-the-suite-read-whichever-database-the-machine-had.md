# ADR-355 — The suite read whichever database the machine had

**Date:** 2026-10-17
**Status:** Accepted
**Closes:** the hazard recorded unfixed in ADR-346 and ADR-349

---

## Context

```python
DB_PATH = DATABASE_URL or (LIVE_DB_PATH if os.path.exists(LIVE_DB_PATH) else SEED_DB_PATH)
```

**81 bare `Storage()` calls** in the test suite, and nothing pinned. So the tests read `data/fpl.db` — a
**gitignored, machine-specific file** whose contents depend on when someone last ran `refresh` — on a
developer's machine, and the committed `data/seed.db` on CI.

⚠️⚠️ **It does not fail, it disagrees.** ⭐⭐ *A disagreement reads as a wrong diagnosis rather than a
wrong setup*, which is why this survived two recordings.

**It has bitten three times:**

1. a local `ingest.refresh` turned **ten unrelated tests red** (ADR-346, recorded and left)
2. today a contract failure was called local-only — ⭐ it failed against the seed too, and the claim was
   mine, stated with the wrong confidence
3. `test_web_streamlit.py` **branched** on which database it got:
   ```python
   if config.DB_PATH != config.SEED_DB_PATH:        # a live cache locally
   ```
   so **half of two tests had never run on CI at all** — ⚠️ *a test with two behaviours and one name.*

## Decision

**Tests read the committed seed, everywhere.** `conftest.pytest_configure` sets
`DB_PATH = DATABASE_URL or SEED_DB_PATH`. 📌 A DSN is still honoured, because the Postgres job sets one on
purpose; the live **file** is what is never read.

### 🔴 And the pin could not reach the constructor

`Storage.__init__` declared `db_path: str = config.DB_PATH`. A default argument is evaluated **once, when
the `def` runs at import**, so patching the config afterwards did nothing at all.

⭐⭐ **A test already recorded this as a fact to work around rather than a bug to fix:**

> *"`Storage()`'s default argument was bound at import, so patching `config.DB_PATH` would do nothing —
> the seam has to be the name the service module actually calls."* — `test_service_squad.py`

⭐ It is the same trap `conftest` spells out for the language model, one layer down — *"a default argument
holds a reference to the original and never consults the module again."* The file that documents the trap
for Ollama sat beside a database doing it. `Storage` now resolves `config.DB_PATH` when asked.

## Consequences

✅ **The suite gives the same answer with and without a local cache** — 3,156 passed, both ways, run back
to back. That is the whole claim, and it is measured rather than argued.

✅ The two branching tests now arrange the condition, so both halves run everywhere.

🔴 **The first guard did not run.** It was written into `conftest.py`, which pytest **does not collect**,
so it passed when invoked by name and never once with the suite. ⭐ *A guard in the file that configures
the suite is the one place it cannot be a test.* It lives in `test_the_suite_reads_one_database.py` now.

🔴🔴 **A one-shot pin did not survive a module reload, and the guard caught it on its first full run.**
`test_postgres_cutover` calls `importlib.reload(config)` to prove the DSN is read at import — which
recomputes `DB_PATH` from the filesystem and silently handed `data/fpl.db` to **every test that ran
after it**. ⭐⭐ *The fix for this bug shipped with the same bug inside it, for about ten minutes*, and
only the guard said so. The pin is an autouse fixture now, re-applied before every test.

🔴 **And the guard's own first version only worked on SQLite.** It read `PRAGMA database_list` to see
which file had been opened — but CI's Postgres job runs this same suite with `db.connect` patched to hand
back Postgres *whatever path it is given*, so the assertion blew up there and nowhere else. ⭐⭐ *A test
that inspects the connection is testing the harness*; the claim was always about the **path asked for**,
so it now spies on the argument and opens nothing. ⚠️ Three attempts at one guard — in the wrong file,
then surviving a reload, then backend-specific — ⭐ *which is itself the argument for the guard: nothing
else in the suite could tell me any of that.*

📌 Not changed: the application's own resolution. ⭐ A developer running the CLI should still get their
live cache — that is what it is for. This is about what the **tests** read.
