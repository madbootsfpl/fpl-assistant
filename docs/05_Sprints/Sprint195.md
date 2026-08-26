# Sprint 195: Import a league — and compare against it (ADR-141)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-141. 1354 → 1371 tests, ruff clean.

> **Owner:** *"Can we import leagues? like fplstats.live — and do the elite manager comparison."* Gated the
> ADR with *"go as planned"* after the cost and the payoff were both measured.

---

### 🔍 The gate: measure the cost, and measure the payoff

The Roadmap flagged this as **the first feature needing many API calls per view**, and gated it behind
settling caching and rate-limiting *before* design. Both were measured against the live API.

**The payoff, over the top 20 managers in the world in GW1:**

| player | EO in that league | global ownership | gap |
|---|---:|---:|---:|
| João Pedro | 125% | 65.2% | +60 |
| **Palmer** | **90%** | **11.9%** | **+78** |
| White | 55% | 5.5% | +50 |
| Szoboszlai | 35% | 42.5% | −8 |

**Palmer is the whole argument.** At 11.9% ownership every surface in this app calls him a *differential*.
Among the people actually winning he is *template*. Opposite decisions — and global ownership, the only
ownership number we had, cannot tell them apart.

**The cost was 5× lower than the Roadmap feared.** The note estimated *"a 20-manager league over 5 gameweeks
is 100 calls"*. The headline features need the **current gameweek only**:

| call | latency | size |
|---|---:|---:|
| `leagues-classic/{id}/standings/` | 115 ms | 9.5 KB |
| `entry/{id}/event/{gw}/picks/` | 51 ms | 1.8 KB |

The table is **one call** — standings already carry `rank`, `last_rank`, `total`, `event_total`, so movement
is free. And with a 0.3 s courtesy throttle, **the throttle is 85% of the wall time** (300 ms of sleep against
51 ms of API): the pace is our own politeness, not the API's limit.

---

### 🔧 What shipped

**Two layers, priced apart — and that split is the design.** The table renders on load. The insight layer
costs one call per manager, so it sits behind an explicit button. The rule, worth stating plainly:

> **Nothing that costs N network calls happens because someone opened a tab.**

**What makes it affordable: a completed gameweek's picks are immutable.** Once the deadline passes they can
never change, so they are cached with **no expiry** — a season of gameweeks accumulates without refetching
one. Only the in-flight gameweek would need a TTL, and it is simply not offered. Measured: **17.5 s** for 50
managers on first load, **0.0 s** after.

Also: throttled at the existing `config.HISTORY_THROTTLE` (not a new number), capped at one standings page
(50) **and it says so**, nothing written to the read-only snapshot, and the "elite" view is literally the same
code pointed at league 314.

Over the full 50 the numbers held: Palmer +50, João Pedro +69, a 21/8/7 captain split, and **47 of 50 played
Bench Boost**.

---

### 🐛 Two things the build turned up

**1. A test that passed alone and failed in company.** Both page tests use the Elite preset (314), and
`st.cache_data` is process-wide and keyed on the league id — so the second test silently read the first one's
fake league. The caching is *correct*; the tests were order-dependent. Fixed with an explicit
`st.cache_data.clear()` and a comment naming which of the two was at fault.

**2. I rewrote history, and caught it in the diff.** Inserting a page meant renumbering seven files and their
~145 references — mechanical and safe. The same sweep hit `Architecture.md`, which is a **historical log**: an
entry reading *"rewrite `8_Help.py`"* became *"rewrite `9_Help.py`"*, turning a true record of Sprint 148 into
a false one. Reverted, with a forward-dated changelog entry explaining the renumber instead, and saying
explicitly that entries above it keep the filenames they were written with.

> **A mechanical rename is safe across code and tests, and unsafe across a log.** Code describes what *is*; a
> log describes what *was*. `sed` cannot tell them apart, so the person running it has to.

Reviewing the diff is what caught it — the rename "worked", the tests passed, and the only symptom was one
wrong word in a two-year record.

---

### 💡 The lesson

**Gating on a measurement changed the feature twice, in opposite directions.** The cost came in **5× cheaper**
than the estimate that nearly deferred it, and the payoff came in far stronger than "a rival has one". Neither
was knowable from the Roadmap line; both took about ten minutes of live calls.

The specific thing worth carrying: **the estimate was wrong because it assumed a shape (N managers × N
gameweeks) rather than asking what the feature actually needs.** It needs one gameweek. Estimating the cost of
a design you have not chosen yet mostly measures your own pessimism.

### 🧪 Tests

**+17 (1354 → 1371).** `tests/test_league.py` (13) covers EO with the captain counted twice, bench exclusion,
the partial-fetch divisor, the gap in both directions, captain-split shape, chip counts, rank movement
including the `last_rank == 0` "new entry" case, and `last_completed_gameweek` against the ADR-123 deadline
rule. Client tests pin the paginated URL and that failures raise `FplApiError`. Page tests assert **no
per-manager fetch happens on load** and that a truncated league says so — all through a fake client, so no
test touches the live API.
