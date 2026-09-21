# Spike 017 — why the app is slow

**Run:** 2026-09-21, after the owner reported slow loads and refreshes.
**Status:** measured. **Nothing changed** — ADR-211 set a decision rule and it deserves reading before acting.

---

## The finding

**Two of the three database connections a page opens are the sidebar's freshness caption.**

```
3 connections opened rendering Players:
  1. status.py:73  render_data_status → _player_count   → Storage.__init__
  2. status.py:75  render_data_status → _data_as_of     → Storage.__init__
  3. 5_Players.py:32                                    → Storage.__init__
```

`render_data_status` draws one line — *"667 players · data as of 2026-09-20"* — and opens **two separate
connections** to do it: one for a `COUNT(*)`, one for a timestamp. It renders on **every page**.

Each connection to Supabase is a DNS lookup, a TCP handshake and a TLS handshake before a single byte of
data moves. On a framework that re-runs the entire script on every interaction, that is paid on every click.

## What a render actually costs

| | SQLite (seed) | Postgres |
|---|---|---|
| queries | **40** | **10** |
| connections | 3 | **3** |
| of which schema probes | — | 3 × `SELECT 1 FROM players LIMIT 1` |

⭐ **The query mix differs by backend, and measuring only SQLite would have produced the wrong diagnosis.**
On SQLite, 22 of the 40 are `CREATE TABLE IF NOT EXISTS` — `_init_schema` running twice per render. On
Postgres those do not happen at all, because ADR-211 made a reader **return early and probe instead of
creating**. That design is working exactly as written; the cost has simply moved to connections.

*Ask which path the code takes. Do not infer it from the one you measured.*

## The network numbers

Measured against Supabase eu-west-1, five samples:

| | |
|---|---|
| new connection — TLS handshake | **~30 ms** |
| new connection — full request | **65–95 ms** |
| **reused** connection | **10–14 ms** |

So a connection costs roughly **50–80 ms more than a warm one**, and the app opens three per render.

⚠️⚠️ **These are from a laptop, and the number that matters is from Streamlit Cloud.** If Cloud runs in the
US and Supabase is in eu-west-1, every figure above multiplies by something like 5–10×, and three
handshakes plus ten queries become well over a second. ⭐ *Latency measured in the wrong place is not a
measurement of the thing.*

## Which is why the real answer is already in production

`analytics.timed("data_load")` has been writing a `perf` event on My Squad and Players since US-336 —
**from before the cutover and after it**. That is ADR-211's *"compare page timings against the seed"*, taken
in the real environment, and it has been sitting in the `events` table the whole time.

`sql/page_timings.sql` reads it, bucketed by day, with no date hard-coded — the cutover should appear as a
step rather than being asserted. ⭐ *A claim about when something changed is weaker than a shape in the data.*

## Recommendation — in order, and not yet acted on

1. **Read `sql/page_timings.sql` on production.** ADR-211's bar is *"cache the connection if the added cost
   exceeds ~200 ms per rerun"*, and nobody has read the number the rule applies to.
2. **Stop the freshness caption opening two connections.** It is one line of UI costing two thirds of the
   connection overhead on every page. This is true regardless of what step 1 says, and it is the cheapest
   thing on the list.
3. **Then, and only then, decide about connection caching.** It is real infrastructure — pooling, lifetime,
   what happens when Supabase drops an idle connection — and ADR-211 declined to build it precisely because
   nobody had measured the need.

⚠️ **Deliberately not done here.** The owner asked to measure before changing anything, and three separate
things today turned out to be a fix scoped to what was visible at the time. Reading the production number
first is what stops this becoming the fourth.

---

## Fixed, 2026-09-21

`_player_count` and `_data_as_of` merged into **one `_freshness()`** that opens a single connection.

| per page render | before | after |
|---|---|---|
| connections | **3** | **2** |
| queries (Postgres) | 10 | **9** |
| caption | `📅 667 players · data as of 2026-09-21` | unchanged |

⭐ The date still comes from the right place on each backend: `data_status.refreshed_at` on Postgres — the
last refresh that actually *passed* — and the snapshot's mtime on SQLite, which needs no query at all.

**Guarded** by `tests/test_status_connections.py`, which counts **connections, not milliseconds**. ⚠️ A
timing test against a local database would measure a latency the app never experiences and pass whatever the
code did — the same trap as benchmarking Supabase from a laptop. Mutation-tested by splitting it back in two.

⚠️ **One wrong turn:** the degradation test patched `Storage` to raise, left `DB_PATH` pointing at the real
seed, and expected `"unknown"` — so it failed on **correct** behaviour, because falling back to the
snapshot's date is right when the snapshot is what is being served. ⭐ *Check what the code actually falls
back to before asserting what it should say.* There are now two tests: one for a broken database with a
snapshot present, one for nothing readable at all.

## Still open

📅 **Read `sql/page_timings.sql` on production.** This change removes one of three connections; whether that
is enough is a question about real Streamlit-Cloud-to-Supabase latency, and ADR-211's bar (~200 ms per
rerun) has still not been read against real numbers. Connection caching remains undecided, deliberately.

---

# The production numbers — and they change the diagnosis

**Read from `events` on production, 2026-09-21.** `data_load` p50:

| | |
|---|---|
| oldest day recorded (SQLite era) | **16 ms** |
| newest day (Postgres era) | **3,026 ms** |

Added cost per rerun: **~3,010 ms**, against ADR-211's bar of ~200 ms. **Fifteen times over**, so the rule
fires without ambiguity.

## ⭐⭐ But the cause is not the one ADR-211 pre-registered

ADR-211 wrote: *"if the added cost exceeds ~200 ms per rerun, **cache the connection**."* That names a
remedy, and the remedy is aimed at the wrong mechanism.

Nine round-trips at even 100 ms each is 900 ms, not 3,000. The gap is explained by **volume, not latency**:

| query | rows | bytes |
|---|---|---|
| `get_gw_history_by_code()` | 2,547 | **1,197,474** |
| `get_history_by_code()` | 2,097 | **746,950** |
| `get_players()` | 662 | **517,835** |
| `get_all_fixtures()` | 380 | 58,360 |
| `get_teams()` | 20 | 1,696 |
| **total** | | **2,522,315 — 2.41 MB** |

**2.41 MB crosses the Atlantic on every page render**, on a framework that re-runs the whole script on every
click. At ~8 Mbps that is ~2.4 s, which lands on the observed 3,026 ms.

⭐ **A connection pool would save the handshakes and leave 2.4 MB still moving.** The pre-registered fix
would have been built, measured, and found to barely help — after which the obvious conclusion would have
been "Postgres is just slow", which is false.

⭐⭐ **The decision rule was right and its proposed remedy was wrong, and only measuring could tell them
apart.** *A rule that says "measure, then act" is worth more than the action it guesses at.*

## What the fix probably is — not yet agreed, not yet built

**Cache the data, not the connection.** Streamlit re-runs the script on every interaction; `st.cache_data`
with a TTL matched to the pipeline's cadence would turn 2.4 MB per click into 2.4 MB per refresh window.

⚠️ **It is a freshness trade and therefore a decision, not a detail.** ADR-211 exists because stale data that
looks fresh is the failure this project most wants to avoid, and a cache is exactly that mechanism pointed
the other way. The TTL has to be shorter than the pipeline's cadence, and the freshness caption has to keep
telling the truth — it reads `data_status`, so it must not be cached with the same key as the board.

⚠️ **Also worth asking before caching: why does every page load `get_gw_history_by_code()` at all?**
1.2 MB — half the payload — for per-gameweek history. A page that does not draw a form curve may not need
it, and not fetching something beats caching it.

## Timeline: the owner's observation pins it to the hour

> *"end of day Saturday speed was good on each page, end of day Sunday when I noticed it"*

```
Sun 20 17:17  a45f8f2  docs: the pipeline is live — GitHub writes it, the app reads it
```

Saturday the app read the local SQLite seed — **16 ms**. Sunday afternoon `FPL_DATABASE_URL` reached
Streamlit, the app began reading Supabase, and by evening it was **3,026 ms**.

⚠️ **I had called that step "the cutover" before checking when the cutover was**, and when the owner's
timeline seemed not to fit I said it contradicted the diagnosis. It did not — the date was wrong, the cause
was right. ⭐ *An observation that seems to contradict you is worth checking against the record before it
changes your mind or is dismissed.*

## Which pages pay it

| page | gw_history | history | players | **MB** |
|---|---|---|---|---|
| My Squad | ×1 | ×1 | ×1 | **2.35** |
| FDR | ×1 | ×1 | ×1 | **2.35** |
| Team DNA | ×1 | ×1 | ×1 | **2.35** |
| Players | ×1 | ×1 | ×1 | **2.35** |
| Signals | · | · | ×1 | 0.50 |
| Trending | · | · | ×1 | 0.50 |

⭐ **FDR is the clearest waste**: it loads all 1.9 MB of player history *unconditionally at the top of the
page*, for an optional "My squad only" checkbox that defaults to off. A fixture-difficulty grid does not
need per-player gameweek history to draw itself.

⭐⭐ **But per-page trimming is the smaller half.** The real multiplier is that **every rerun refetches
everything** — Streamlit re-runs the whole script on every click, so moving a slider on Players costs another
2.35 MB. Caching fixes all six pages and every interaction; trimming fixes one page once.

## Fixed (2), 2026-09-21 — FDR stops fetching what it never read

| page | before | after |
|---|---|---|
| **2_FDR.py** | **2.35 MB** | **~0 MB** (clubs only, 1.7 KB) |

`get_history_by_code()` and `get_gw_history_by_code()` were assigned at the top of the page and **never
referenced again** — not "rarely used", never used. `get_players()` moved into the "My squad only" branch,
which is the only thing that wants it and defaults to off.

⭐ **No freshness trade at all**, which is what makes this the right thing to do before caching. *Not
fetching something beats caching it.*

Guarded in `tests/test_page_payloads.py` — **both halves**: that the waste stays gone, and that the lens
still narrows the ticker. ⚠️ The second matters because the page renders identically either way, so a broken
lens would say nothing. Mutation-tested in both directions.

⚠️ **And the lens test was wrong before it was right**: it used the session key `_active_squad` instead of
`squad`, saw 20 rows, and looked exactly like a regression in the code I had just changed. ⭐ *Confirm the
fixture reaches the code path before believing its verdict* — otherwise a broken test reads as a broken fix.

## Remaining

| page | MB per render |
|---|---|
| My Squad · Team DNA · Players | **2.35** |
| Signals · Trending | 0.50 |
| FDR | ~0 |

These three genuinely use the history they load, so trimming cannot help them. 📅 **The decision still open
is caching** — and it is a freshness trade, so the TTL is the owner's call, not an implementation detail.

---

# Production, the morning after (2026-09-21)

`data_load` p50, by the hour — the daily bucket was too coarse once the change landed mid-afternoon.
⭐ *A bucket wider than the change you are looking for hides it.*

| hour | p50 | fastest | worst |
|---|---|---|---|
| 20th 08:00–15:00 (SQLite seed) | **26–42 ms** | 24 | 125 |
| 20th 16:00 → 21st 08:00 (Postgres, no cache) | **~3,000–3,260 ms** | 2,902 | 4,733 |
| 21st 10:00 (deploy landing) | **1,535 ms** | **16** | 10,865 |
| **21st 11:00 (cached)** | **23 ms** | **15** | 10,863 |

✅ **The warm path is fixed.** p50 **23 ms**, level with the local-SQLite era. The owner's description
matches exactly: *"once the initial login and squad is loaded takes a few seconds, the movement from tab to
tab is quick."*

## ⚠️ But the cold path regressed, and worse than ADR-217 priced it

| | connections | payload | observed |
|---|---|---|---|
| before caching | 2 | 2.41 MB | **~3,000 ms** |
| after caching | **6** | 2.41 MB | **~10,800 ms** |

Four extra connections cost **~7,800 ms** → **~1,950 ms each**.

ADR-217 accepted "six connections instead of two" as a deliberate trade, priced against the **~30 ms** TLS
handshake measured **from a laptop**. From Streamlit Cloud it is **65× that**.

⭐⭐ **That is spike 017's own warning, applied to my own trade-off**: *latency measured in the wrong place is
not a measurement of the thing.* I wrote that about benchmarking the fix and then priced the cost of the fix
the same wrong way.

🔬 **What it is not:** the dict conversion and pickling that caching added total **~16 ms** on the largest
read. Measured before blaming it.

## The next lever, and it is already half-built

**Nothing in the web app reads `xp_board`.** The pipeline computes and publishes the whole board every tick
(ADR-213) — and the app then downloads **1.9 MB of raw history** (`gw_history` 1.2 MB + `history` 747 KB) to
recompute the same numbers.

That 1.9 MB is **79% of the cold payload**, and two of the six connections.

⚠️ Not a clean swap: the history also feeds Player DNA percentiles, form curves and the minutes weighting, so
what can be dropped needs establishing before anything is. But it attacks the one part a cache cannot — the
first load — and the expensive half of it is already computed and sitting in a table.
