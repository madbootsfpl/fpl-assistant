# ADR-217 — Stop fetching the board on every click

**Date:** 2026-09-21
**Status:** Accepted
**Answers:** ADR-211's deferred question — *"if the added cost exceeds ~200 ms per rerun, cache…"*
**Evidence:** spike 017

---

## Context

The owner: *"the app is still slow, useable but far from a good experience."*

Production's own `perf` events, recorded since US-336, gave the number:

| | |
|---|---|
| `data_load` p50, oldest day (SQLite seed) | **16 ms** |
| `data_load` p50, now (Supabase) | **3,026 ms** |

ADR-211 pre-registered the bar at ~200 ms of added cost per rerun. This is **fifteen times over**, so the
rule fires without argument.

⭐⭐ **But ADR-211 also pre-registered the remedy — "cache the connection" — and that was aimed at the wrong
mechanism.** Nine round-trips at even 100 ms each is 900 ms, not 3,000. Measuring the payload found the
cause:

| query | bytes |
|---|---|
| `get_gw_history_by_code()` | **1,197,474** |
| `get_history_by_code()` | **746,950** |
| `get_players()` | **517,835** |
| fixtures + teams | 60,056 |
| **per page render** | **2.41 MB** |

**2.41 MB crosses the Atlantic on every render**, on a framework that re-runs the whole script on every
click. A connection pool would have saved the handshakes and left the megabytes moving — built, measured,
found not to help, and the conclusion would have been *"Postgres is just slow"*, which is false.

⭐ *The decision rule was right and its guessed remedy was wrong, and only measuring could separate them.*

---

## Decision

**Cache the data, not the connection.** One module — `web_streamlit/dataload.py` — owns every board-wide
read, each wrapped in `st.cache_data`. Every page calls it; no page opens `Storage` for board data.

Result, measured per page render:

| | before | after (warm) |
|---|---|---|
| queries | 9–13 | **0** |
| connections | 2–3 | **0** |

The first visitor after an expiry fills the cache for everyone; every click after that touches no database.

### `TTL = 300`, and it is a product decision wearing a constant

ADR-211's cadence is **10 minutes at its fastest** (in play). At five minutes a reader is never more than
half a tick behind what was published. ⚠️ Lower it and the app is slower and fresher; raise it and the
reverse. One number, one place, and a test pins it below the 10-minute cadence so the two cannot drift apart.

### The caption is cached **with** the board

⭐⭐ **And that reverses what this session first proposed.** The initial plan said the freshness caption must
*not* share a cache key with the data. That is backwards: reading the timestamp live while serving a cached
board lets the sidebar announce a refresh whose data the reader cannot see — the *fresh-looking but stale*
failure ADR-211 exists to prevent, arriving from the opposite direction.

*A caption describes what is on the screen, or it is not a caption.*

### Three things checked before relying on them

⚠️ **`sqlite3.Row` cannot be pickled**, and `st.cache_data` pickles what it returns — so the loaders convert
to `dict`. Verified first that nothing in the app indexes a player, team or fixture row positionally, which
makes `dict` a drop-in at every call site.

⚠️ **The app mutates rows it is handed** — `render_build` does `p["xp"] = …`. Two independent checks: the
optimiser returns **fresh dicts** (0 of 15 selected rows are the same object as the pool), and `st.cache_data`
**hands each caller its own copy** (tested in a real runtime, not assumed). Either alone would be enough;
both together is why this is safe.

⚠️ **A process-wide cache in a one-process test suite leaks between tests.** A test that monkeypatches
`Storage` would be silently defeated by a cache filled before the patch existed — and would **pass**, because
the real snapshot is usually close enough. An autouse fixture empties it between tests, so ordering cannot
matter.

---

## Consequences

**Good:** the app stops paying 2.41 MB per click. Board reads have one home instead of six, so a page can no
longer quietly start fetching something it does not read — the fault this same spike found in FDR.

**Cost:** a cold load is *worse* — six connections instead of two, because each cached loader opens its own.
Accepted deliberately: it happens once per five minutes across all visitors, and the alternative (one bundled
fetch) would make Signals and Trending load the history they were just stopped from loading.

⚠️ **The freshness trade is real and it is now the app's behaviour, not a detail.** A reader can see a board
up to five minutes behind the pipeline. The caption says so honestly because it shares the window.

**Not done:** connection caching. Still undecided, and now clearly secondary — with warm renders at zero
queries there is nothing left for a pool to save except on the cold path.
