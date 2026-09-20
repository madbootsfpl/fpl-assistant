# ADR-213 — The pipeline publishes analytics, not just data

**Date:** 2026-09-20
**Status:** Accepted
**Follows:** ADR-211 (the pipeline runs without you) · `docs/03_Architecture/Mobile_Platform_Audit.md` §4.1, §5.1

---

## Context

The mobile audit draws the target pipeline as:

```text
a scheduled job → validate → run analytics → write Postgres → every client reads it live
```

ADR-211 built every box except **"run analytics"**. The pipeline fetches FPL data, validates it, and writes
players, teams, fixtures, availability and transfer flow. It stops there.

That is a problem for the thing the pipeline was built for. §4.1 commits to **direct Flutter → Supabase with
no API** for the majority of the app's read surface, and lists among it *"per-player xP over each horizon
(`decision_xp` output — this is board-wide and precomputable)"*.

**That table does not exist.** `decision_xp` is a pure Python function evaluated at read time inside
Streamlit. A Flutter client cannot call it.

⭐ **Same shape as ADR-212, one day later**: a document describing a capability the system does not have. The
audit is not wrong — it is ahead of the code, and nothing said so.

The three ways out, and why only one is open:

| option | verdict |
|---|---|
| publish the boards from the pipeline | ✅ what §4.1 assumes |
| put FastAPI in front of everything | 🅾️ §4.3: *"not a proxy in front of Supabase, and it should not become one"* |
| reimplement the analytics in Dart | 🅾️ the hazard ADRs 123, 127 and 181 are each about |

⚠️ **This is not a performance change, and it was nearly sold as one.** The first draft of this argument
claimed precomputing would speed the web app up. Measured: `decision_xp` is **8 ms** for 662 players at
horizon 5, 30 ms for four horizons. There is no performance problem here. The justification is architectural
— a client that cannot run Python needs the answer in the database — and inventing a second reason would
have been the kind of unexamined claim ADR-212 spent a day removing.

---

## Decision

### 1. One board, not eight

**One row per player**, holding a single **horizon-8** board — the maximum the UI's slider offers.

Measured on the real board: the **per-gameweek values are identical across horizons** — computing at 3, 5 and
8 gives byte-identical per-GW numbers, zero disagreements across 662 players. The model is
horizon-independent; the horizon only decides how many gameweeks are summed. So a horizon-3 total is the
first three values, and one row serves the whole 1–8 range.

**Size:** 662 rows, 242 KB as JSON, **12 ms** to compute — against a tick that currently takes 24 s.

### 2. Publish the per-gameweek values **unrounded**

⭐⭐ **This is the load-bearing detail, and it is not obvious.** Summing the published (rounded) per-gameweek
values does not reproduce the published total: at horizon 5, **253 of 662 players** disagree with their own
breakdown, by up to **0.20 points**. `xp` is `round(sum(unrounded), 1)` while `by_gameweek` rounds each value
separately — and a rounded sum is not a sum of rounded values.

Published rounded, every derived horizon would inherit that drift, and **the mobile app and the web app would
quote different xP for the same player** — the exact two-implementations failure this ADR is trying to avoid,
arriving through the back door of a rounding decision.

So the stored per-gameweek values keep full precision. Each client rounds at display, where rounding belongs.

### 3. Fix the breakdown so it sums to its own total

The existing comment reads `by_gameweek  # ADR-032: {gw → xP}, sums to xp`. **It does not** — the same 253
players. Each value is individually correct to 1dp; their sum is not the total, and a reader adding up a
column sees a number that disagrees with the one beside it.

Replaced with **largest-remainder apportionment**: round every value down, then hand the spare tenths to the
largest fractional parts. The parts now sum to the whole exactly, and no value moves more than one tenth from
its true value. Verified on 20,000 randomised cases: **0 failures** on either property.

⚠️ **This changes displayed numbers** — a per-gameweek cell may shift by 0.1. It is a correction, not a
regression: the column now adds up.

### 4. Refuse rather than corrupt

Validation runs **before the first write**, exactly as ADR-211 established for the raw data, and for the same
reason: ⭐ *once storing is publishing, a check that runs afterwards is not a check.*

⚠️ **A bad xP board is more dangerous than a stale one**, because nothing about it looks broken. Stale data
announces itself through `data_status`; a board where every keeper scores 40 announces nothing at all.

### 5. One recipe, checked

The pipeline calls **the same `decision_xp`** the CLI, the web app and `ask` call. Not a copy, not a
pipeline-shaped variant. A test recomputes the board and asserts the published rows match, so a divergence
**fails** instead of drifting — the lesson ADR-181 paid for, where an optional argument on a shared helper
silently priced a different player.

---

## Scope

**xP only.** DNA percentiles, the stat boards and Signals are on §4.1's list and are deliberately not in this
sprint. xP is what every other screen depends on, and doing one board end to end proves the
publish-validate-verify pattern before it is copied four times. ⭐ *Designing four validators before knowing
whether one works is how you get four wrong ones.*

## Consequences

**Good:** §4.1 becomes true rather than aspirational — a non-Python client can read the analytics. The
pipeline earns the "run analytics" box the audit drew for it. The remaining boards are mechanical once this
pattern exists.

**Cost:** the same number now lives in two places — computed in Python, and stored in Postgres. ⚠️ **That is
precisely the hazard ADRs 123/127/181 are about**, and it is accepted only because the second copy is
*generated by the first* on every tick and pinned by a test. The moment anything writes that table by another
route, this ADR is void.

**Not addressed:** the board is anchored to the moment it was computed — `by_gameweek` is keyed by real
gameweek numbers, so the window shifts after every deadline. The row carries its anchor; a client that
ignores it will misread the board after a deadline. That is a contract to state, not a thing to prevent.

**Observation, not in scope:** on the current board **Tzolakis (HUL, GK) is the 3rd highest xP overall**, above
Haaland. Possibly genuine fixtures, possibly the clean-sheet or minutes term behaving oddly for keepers.
📅 Worth a look at the GW6 sitting alongside ADR-195's clean-sheet sweep.

---

## What the build found

Five things the design did not anticipate. Each is recorded because each was a wrong first answer.

### 1. Apportionment makes a cell depend on its neighbours — measured, then kept

⚠️ Making the parts sum to the whole means a spare tenth lands wherever the largest fractional part is. So a
cell is **no longer a pure function of that gameweek**: two players whose exact GW6 values are identical can
*display* 0.1 apart. An existing flag-horizon test caught it immediately — *"beyond the window he must be
worth exactly what an unflagged twin is worth"*, which stopped being true at 1dp.

Rather than guess which mattered more, both were counted on the real board:

| | |
|---|---|
| breakdowns that disagreed with their own total (the bug fixed) | **253 of 662 players — 38%** |
| equal-value groups that now display unequally (the cost added) | **4 of 2,141 groups — 0.2%** |

⭐ Kept, on those numbers. The failing test was re-pointed at `by_gameweek_exact` — **after** verifying the
model claim holds there exactly (GW6 is `0.06` for both players; GW5 is `0.045` against `0.06`). ⚠️ The
fixture uses a deliberately tiny baseline where one tenth exceeds the values themselves, so the clash is
guaranteed there and rare everywhere else. *The claim is about the model, so it belongs on the model's
numbers; asserting it on a 1dp rendering is testing the renderer.*

⭐⭐ **The rejected alternative is worth naming**: making `xp` the sum of the *rounded* parts would keep cells
independent and still make the column add up — but it lets the **total** drift by up to 0.2, and ADR-209
measured the median best-vs-second transfer gap at **0.20 on a one-gameweek window**. A rounding error the
size of a real decision margin is not a rounding error.

### 2. An empty breakdown is not a broken one

The first validator rejected any row without gameweeks. ⚠️ A player with **no fixtures in the window**
legitimately has `{}` — end of season, or a club whose next game is past the horizon. Caught by an existing
pipeline test on a 650-player fixture with nothing upcoming, which the check failed for being *correct*.

⭐ *A check that blocks good data is worse than one that admits slightly odd data* (ADR-211). It now
distinguishes a **missing field** (a code fault) from an **empty one** (a fact about the calendar), and a
board with no window at all is **skipped and said so** rather than refused — refusing would fail an otherwise
healthy tick every day of the summer.

### 3. `counts` is a tuple, and my own fixture hid it

`run()` returned `counts | {"xp_board": n}`. `ingest.refresh` returns a **4-tuple**, which `describe()`
unpacks positionally — so the real call raised `TypeError`.

⚠️ **The test written alongside it stubbed `ingest.refresh` to return a dict**, so it passed while the code
was broken. ⭐ *A fixture that models less than reality will confirm a broken mechanism* — the eighth time
this month. The board count moved to its own key; the stub returns a tuple.

### 4. Twelve tests passed on SQLite and failed on Postgres

The fixture copied the snapshot to a `tmp_path`. Under `MADBOOTS_TEST_DSN` the harness ignores the path and
seeds the snapshot **only when the caller asks for `config.DB_PATH` or `config.SEED_DB_PATH`** — a bare
`tmp_path` reads as *"this test builds its own fixture"*, so the store came back empty and every board test
failed.

⚠️ Marking them `sqlite_only` would have been the easy way out and the wrong one — **the pipeline runs on
Postgres**, so these are the tests that matter most there (ADR-178: *a skip is not a pass*). Pointing
`config.SEED_DB_PATH` at the copy satisfies both backends at once.

### 5. A rejected board must still report the data as refreshed

The first version withheld `refreshed_at` when the board failed. ⚠️ By that point `ingest.refresh` has
**already written the players** — the data genuinely refreshed, and the sidebar reads that field and nothing
else. Withholding it reports **stale data that is actually fresh**: a false alarm, undiagnosable from the
screen.

⭐ *Each artefact reports its own freshness.* `refreshed_at` is the FPL data; `xp_board.computed_at` is the
board, and it stays put precisely because the refused board never replaced it. `ok=False` plus a note says
something failed without lying about which thing.

## Verified

**Smoke test** — a real FPL fetch into a fresh Postgres:

```
Published 667 players, 20 teams, 380 fixtures, 0 Elo, xP board 667 players from GW6 (bootstrapping).
```

Second tick declined in **0.22 s** with the board untouched. Suite: **2,037 on SQLite · 2,045 on Postgres**.
Mutation-tested: eight mutants across the apportionment, the publish path and the freshness reporting, all
red — including *validate-after-write*, and including one that proved three apportionment tests were passing
without ever checking that `decision_xp` **calls** it (⭐ *testing a component is not testing that anything
uses it*).

⚠️ **On a bootstrapped database every row is `cold_start`**, because the history backfill runs on its own
clock — so the first published board ranks João Pedro and Mendy above Haaland. That is ADR-192's known
cold-start inflation, not a fault here, and `rate_source` is stored per row so a client can see it.
