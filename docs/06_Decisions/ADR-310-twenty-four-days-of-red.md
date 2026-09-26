# ADR-310 — Twenty-four days of red

**Date:** 2026-09-26
**Status:** ✅ **Fixed — CI green on all three jobs** (`897f496`), first time since **2026-09-02**.
**From:** pushing ADR-308/309 and noticing the CI badge had been failing for longer than the work in front
of it.

---

## What was wrong

**CI had been red for 24 days and 100+ commits.** Last green: `c971e1a`, 2026-09-02 19:23. It broke at the
very next push and never recovered.

⚠️⚠️⚠️ **Nobody knew, and that is the finding.** ⭐⭐⭐ *A signal that is always red carries exactly as much
information as one that is always green* — this project has written that sentence before, about a `git status`
that was permanently dirty (ADR-211's seed-mutation note). Same failure, one layer up: **the suite was the
thing watching everything else, and nothing was watching it.**

Eight distinct root causes, each of which had to be removed before the next became visible.

| # | cause | why it was invisible |
|---|---|---|
| 1 | ⚠️ **`test_web_streamlit` asserted a picker [ADR-175](ADR-175-value-above-the-fold.md) deliberately removed** — *"one squad, no picker"* | Passed on a machine with extra squads in **gitignored** `data/squads.json`. **This was the original break.** |
| 2 | 🔴 **`pulp` unpinned; PuLP 4.0.0 landed 2026-09-25 and removed `PULP_CBC_CMD`** | **277 failures from one cause.** Nothing to see until the day it released. |
| 3 | ⚠️ **`test_android_icon` shelled out to `sips`** | macOS-only. Raised `FileNotFoundError` on every runner, ever. |
| 4 | 🔴 **The Postgres test schema list was written twice and the copies drifted** | **1,892 failures.** SQLite self-heals with `CREATE TABLE IF NOT EXISTS`; Postgres deliberately does not. |
| 5 | ⚠️ **10 `ruff` errors**, three of them `F821` | Accumulated over the same blind period. |
| 6 | ⚠️ **`shape()` in the contract test was data-sensitive** | Samples generated from a live cache could *never* match a runner's seed. |
| 7 | ⚠️ **GW5 hard-coded in three places** | The live cache had GW5; the committed seed stopped at GW4. |
| 8 | ⚠️ **The committed seed disagreed with itself** | Bootstrap said five gameweeks; history held four. |

## 🔴 One of them was not a test problem

**PuLP 4.0.0 removes the solver the optimiser calls.** The bundled CBC binary is gone and
`listSolvers(onlyAvailable=True)` returns `[]`, so `optimizer.select_squad` raises on the first solve.

⚠️⚠️⚠️ **Render installs the same `requirements.txt`**, so **the next deploy would have taken the solver out
in production** — every squad build, every gameweek plan, and the whole My Squad page, which calls it on
render. Checked while diagnosing: the live API was still answering `200 Optimal`, ⭐ *so the pin closed the
window rather than repairing a break* — but only because nothing had deployed in the ~18 hours since 4.0.0
was published.

⭐⭐ **Pinned rather than adapted, deliberately.** PuLP 4 means moving to **HiGHS**, and *the solver decides
which fifteen players the app recommends* — that needs its own gate and a re-validation of the optimiser's
output, not a `pip install -U`. 📌 Left open as exactly that.

## ⭐⭐⭐ The one lesson underneath eight causes

**A developer's machine and a runner were structurally different machines, and the project had four separate
mechanisms making them so.**

- **Config derived from whether a file happens to exist.** `config.DB_PATH` prefers `data/fpl.db` when
  present, else the committed seed; `config.SQUADS_PATH` prefers `data/squads.json`, else the demo. Both are
  *gitignored*, so every test reading through those constants tested **different data locally than on CI**.
  That is causes 1, 6, 7 and 8.
- **Unpinned dependencies.** Only `streamlit` was pinned — and its own comment already carried the argument:
  *"PINNED so the Community Cloud deploy matches the tested."* That is cause 2.
- **A platform-only tool.** Cause 3.
- **A fact written down twice.** Cause 4.

⭐ None of these is a bug in a feature. Every one is a way for *the thing that checks the work* to be
checking something other than what ships.

## What is now guarded

- ⭐ `shape()` compares **structure, not data** — data-keyed maps collapse to one entry, `null` is compatible
  with any scalar (*nullability is not knowable from one dataset*), and failures name the **path** rather
  than printing *"Omitting 10 identical items"*. Its own behaviour is tested: five kinds of real drift
  caught, two kinds of dataset noise tolerated.
- ⭐ The launcher icon is compared **by pixels**, with a tolerance *measured* against Flutter's real default
  (ours **2.6-5.8**, Flutter's **92.5-93.5** — a 16× gap), so it runs everywhere and no longer depends on one
  resampler on one OS version.
- ⭐⭐ **`storage.SCHEMA_DDL` is the only schema list.** `_init_schema` iterates it and `conftest` reads it;
  two tests pin that every `CREATE_` constant is in it and that `teams` precedes its dependents.
- ⭐ The gameweek tests **ask the fixture** for its newest played round — requiring a *scoreline*, not merely
  a row, since FPL writes a row for a fixture that is only scheduled.
- ⭐ `pulp` pinned, `pillow` declared rather than inherited from streamlit.

## Method, which cost more than any single fix

⚠️⚠️ **Moving `data/fpl.db` aside to emulate a runner was an approximation, and it hid two causes.** It
reproduced the *database* difference and nothing else — `data/squads.json` was still there, so cause 1 stayed
invisible through several rounds of "the last two failures".

⭐⭐⭐ **The reproduction is a clean clone plus a venv built from `requirements.txt`.** That found the
`sips` failure immediately and would have found cause 1 on the first attempt.

⭐⭐ **And the log was worth more than all the inference.** Four rounds went into deducing causes from failure
*counts* and step *durations* — real signal (pytest going 173s → 331s proved the pulp pin had worked) but
slow and partial. One read of the actual log named `sips` and `data_status` in a single pass. 📌 `gh` is
installed and authenticated now; **read the log first.**

## Consequences

- 📌 **Watch that CI stays green**, because the cost here was not any one bug — it was 24 days of no signal.
- 📌 **Open: pin the rest of what affects output.** `pandas` and `numpy` are still free to move, and the
  argument that pinned `streamlit` and now `pulp` applies to them.
- 📌 **Open: PuLP 4 / HiGHS** as a gated solver change (above).
- ⚠️ **Stated, not fixed:** `config.DB_PATH` and `config.SQUADS_PATH` still resolve from file existence. Every
  test fixed here was fixed by *not depending on which dataset it got* — ⭐ the right fix per test, but the
  mechanism is still there for the next one.
