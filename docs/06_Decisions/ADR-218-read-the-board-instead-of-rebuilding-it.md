# ADR-218 — Read the board instead of rebuilding it

**Date:** 2026-09-21
**Status:** Accepted
**Follows:** ADR-213 (the pipeline publishes analytics) · ADR-217 (stop fetching the board on every click)
**Evidence:** spike 017

---

## Context

Three fixes had improved the app's timings and the owner's experience had not changed. Instrumenting the
legs that were never timed finally located it:

| | |
|---|---|
| `data_load` p50, warm | **110 ms** ✅ |
| `data_load` p90, **cold** | **10,786 ms** |
| payload per cold load | **2.41 MB at ~0.22 MB/s (~1.8 Mbps)** |

⭐⭐ **The cold load is the payload crossing a slow link.** Caching made every click after the first free and
could never touch the first. Reducing connections 6 → 1 changed it by nothing measurable, which is what
proved the point.

**81% of that payload — 1.94 MB — was history the app downloaded only to recompute an xP the pipeline had
already published** (ADR-213). The expensive half of the answer was sitting in a table nothing read.

---

## Decision

**Read the published board; compute only where the board cannot answer.**

### Which pages, established by measurement rather than by reading intentions

The history dicts were wrapped so every read announced its caller, and each view was rendered:

| view | reads history for | verdict |
|---|---|---|
| **This week · Transfer · Chips** | `minutes.weight`, `xp._rate_tier`, `in_season_share` — all inside `decision_xp` | ✅ the board serves it |
| **Captain** | `captain_picks` builds its own baseline and minutes weight | ⛔ needs the raw rows |
| **DNA · Lab** | `last_season_rows`, `squad_risk_rows`, `team_dna_all`, the `--no-xmins` option | ⛔ needs the raw rows |

⚠️ **Measuring only the default tab would have got this wrong**, and nearly did: an earlier pass concluded
*"My Squad reads history only for xP"* from the landing view alone, and Captain contradicts it. The same trap
caught a claim about Players an hour earlier — *"never reads `gw_history`"* was true of one tab out of six.

### The result

| | before | after |
|---|---|---|
| **This week** (where a login lands) | 2.35 MB | **0.81 MB** |
| Captain · DNA · Lab | 2.35 MB | 2.71 MB |

At the measured throughput that is **~10.7 s → ~3.7 s** on the journey people actually take.

### `ranked_for` falls back, and that is not a nicety

⚠️⚠️ **An empty board is a real state**, and three failing tests found it rather than any reasoning: the
committed snapshot has never had one published into it, a fresh project has none until the pipeline's first
tick, and **ADR-211's fallback serves that snapshot whenever Postgres cannot be read.**

Without a fallback, My Squad would have shown **zero xP with nothing saying why** — the silent degrade that
whole ADR exists to prevent, reintroduced by a performance change.

⭐ *Declining is right when the instrument cannot answer; falling back is right when another instrument can.*

### `board` is passed, not `ranked`

⭐ The views slice the board at the horizon they need — which is the shape they had when they called
`decision_xp` themselves. A first attempt passed a pre-sliced list and broke the per-gameweek card, because
that card needs a **longer** horizon than the page (a blank gameweek spreads three fixtures over four weeks)
and a list already cut to the page's horizon no longer holds them.

⚠️ And the argument is **required**, not optional (ADR-181): a call site that forgot it would silently go
back to downloading 1.9 MB.

## What made the board usable at all

It had to become a faithful stand-in first — verified **identical at every horizon 1–8, every field, all 659
players**. Three fields joined it: `defcon_xp` and `clean_sheet_xp` (both 0 while dormant — ⭐ *a value that
is zero by configuration is not the same as a value that is always zero*) and `games_by_gameweek`, because a
double gameweek is one key with two fixtures and the count cannot be derived from `by_gameweek`.

One field differed by **type** rather than value: `ep_next` was declared TEXT while `players.ep_next` is
REAL. ⚠️ Coerced on read rather than fixed in the DDL, because `_migrate` can add a column and **cannot
change one** — every database whose `xp_board` predates this keeps the old declaration, production's
included.

## Consequences

**Good:** the journey people take is under a megabyte. The pipeline's work is used rather than duplicated.

**Cost:** Captain, DNA and Lab each pay **2.71 MB** — more than before, because they now fetch the board as
well as the history. Accepted: they are deliberate destinations, not the landing page, and the alternative is
making the landing page carry their cost.

**Also reverted here:** ADR-217's one-connection bundle. It was justified by handshake cost that production
then showed was not the cost, and it forced every page to fetch everything — which is precisely what stops a
page from not fetching what it does not read. ⭐ *An optimisation never measured to work, which blocks the one
that does, is not a trade-off — it is in the way.*

📅 **Still open:** Captain could use the board if `captain_picks` took a ranked list rather than building its
own baseline. Not attempted here; it changes a decision surface rather than a data path.
