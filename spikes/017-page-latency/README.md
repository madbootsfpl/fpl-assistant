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
