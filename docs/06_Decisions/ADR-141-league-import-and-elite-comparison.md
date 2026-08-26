# Architectural Decision Record: Import a league — and compare against it

**Decision ID:** ADR-141
**Date:** 2026-08-26
**Status:** ✅ **Accepted — owner-gated ("go as planned"), built** (Sprint 195, 2026-08-26). **1354 → 1371
tests, ruff clean.** Owner-requested 2026-08-25 (*"can we import leagues? like fplstats.live — and do the
elite manager comparison"*), logged to the Roadmap the same day with the condition that **caching and
rate-limiting be settled before design**. This ADR settled them with measurements, then built to them.
**Superseded By / Replaces:** Merges the Roadmap's old "Elite Manager Comparison" line — the two share all
their plumbing. Reuses the ADR-058/113 manager-import pattern and the ADR-041 `decision_xp` unchanged.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Why this is worth building — measured, not assumed

The Roadmap flagged this as the first feature needing **many API calls per view**, so it was gated behind a
cost measurement. The cost was measured against the live API, and so was the payoff.

**The payoff first, because it is unusually clear.** Effective ownership across the **top 20 managers in the
world**, against global ownership, in GW1:

| player | EO in this league | global ownership | gap |
|---|---:|---:|---:|
| João Pedro | 125% | 65.2% | **+60** |
| **Palmer** | **90%** | **11.9%** | **+78** |
| Calafiori | 90% | 40.9% | +49 |
| White | 55% | 5.5% | +50 |
| Haaland | 85% | 68.7% | +16 |
| Szoboszlai | 35% | 42.5% | −8 |

**Palmer is the whole argument.** At 11.9% global ownership every existing surface in this app calls him a
**differential**. Among elite managers he is a **template pick at 90% EO**. Those are opposite decisions, and
nothing we currently ship can tell them apart — global ownership is the only ownership number the app has.

Two more facts fell out of the same calls at no extra cost: the **captain split** (João Pedro 6/20, Haaland
5/20, Palmer 4/20 — a genuine spread, not a consensus), and that **18 of the 20 played Bench Boost in GW1**.
An elite chip consensus, visible as one number.

### 💰 And the cost is 5× lower than the Roadmap feared

The Roadmap note estimated *"a 20-manager league over 5 gameweeks is 100 calls"*. **That was pessimistic by a
factor of five**, because the headline features need the **current gameweek only**, not a history:

| call | latency | size | notes |
|---|---:|---:|---|
| `leagues-classic/{id}/standings/` | **115 ms** | 9.5 KB | 50 rows/page, `has_next` for more |
| `entry/{id}/event/{gw}/picks/` | **51 ms** | 1.8 KB | carries `active_chip` + `entry_history` too |

- **The league table is ONE call.** And it already contains `rank`, `last_rank`, `total` and `event_total` —
  so *the standings and "who is climbing" are essentially free*.
- **The insight layer is N calls for one gameweek.** Measured end to end: **20 managers in 7.0 seconds**
  including a 0.3 s courtesy throttle. Note what that means — **the throttle is 85% of the wall time** (300 ms
  of sleep against 51 ms of API), so the pace is entirely our own politeness setting, not the API's limit.

---

### ✅ Decision

**1. Two layers, priced separately, because they cost three orders of magnitude apart.**
- **The table** (1 call) — always shown on import: rank, movement (`rank` vs `last_rank`), GW points, total.
- **The insight** (N calls) — behind an explicit action, never on page load. This is the rule that keeps a
  page render honest: *nothing that costs N network calls happens because someone navigated to a tab.*

**2. Caching turns on one fact: a completed gameweek's picks are immutable.** Once a deadline has passed, that
gameweek's picks can never change. So:
- **completed gameweek → cache effectively forever** (`ttl=None`, keyed on `(league_id, gameweek, size)`).
  Re-opening the view is free, and a whole season of gameweeks accumulates without ever re-fetching one.
- **the in-flight gameweek → a short TTL** (30 min, matching the ADR-093 news/Reddit convention already in
  this codebase), because picks can still change until the deadline.

This is why the feature is affordable at all, and it is the single most important line in this ADR.

**3. Rate-limiting: 0.3 s between calls, reusing `config.HISTORY_THROTTLE`** — the same courtesy the ADR-027
history backfill already applies. Not a new number, and not a new policy. FPL publishes no rate limit; we
behave well because it is someone else's server.

**4. A hard cap of one standings page (50 managers), stated, never silent.** A 500-manager league would be
~3 minutes of fetching. The view takes the top 50 and *says* it did, with the league's true size. **Silent
truncation reads as "we covered everything" when we did not** — and this project has a rule about that.

**5. The elite view is the same code pointed at league 314** (the global "Overall" league). Confirmed by the
measurement above, which *is* league 314. No second implementation, no second page — a preset id.

**6. Nothing is written to the snapshot.** The app deploys a read-only committed dataset (ADR-056); league
data is per-user and live. It lives in `st.cache_data` for the session and nowhere else.

**Layering, following the existing seams:** two new methods on `FplClient` (`get_league_standings`,
reusing `get_entry_picks`), a pure `analytics/league.py` (`effective_ownership`, `captain_split`,
`chip_usage`, `movers`) unit-tested offline against fixture payloads, and a thin view. No `decision_xp` change.

### ⚠️ Risks

- **A slow first load.** 50 managers ≈ 17 s. Mitigated by it being explicit (a button), a progress indicator,
  and the immutability cache making every later visit instant.
- **Private leagues.** `leagues-classic` is public for classic leagues; H2H (`leagues-h2h`) is a different
  endpoint and is **out of scope for v1** — stated so its absence is a decision.
- **The API could rate-limit us anyway.** The client already retries transient failures (ADR-021); a partial
  fetch should degrade to *"insight from 34 of 50 managers"* rather than an error, because a partial EO is
  still useful and an exception is not.
- **A league of one.** EO over 3 managers is noise. The view should say how many it is standing on — the same
  evidence-first idiom as ADR-126/136.

### 🧪 Definition of Done

1. **Tests** — pure analytics against fixture payloads (EO including the captain multiplier, captain split,
   chip usage, rank movement); the cap and its message; graceful partial fetches; a client test with a fake.
2. **Manual smoke** — league 314 (elite) and a real mini-league id from the owner.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, the Feedback_Log row, a sprint retro.

**Open for the gate:** where it lives (a new page, or a view on an existing one — note ADR-138 recorded that
**ten views is the ceiling** on Players, so this likely wants its own page), and whether v1 includes transfer
flow (needs `entry/{id}/transfers`, one more call per manager — cheap, but it is scope).

---

### 🔨 Built — and it behaves as the economics predicted

Driven end to end against the live API, over the full top 50:

```
table load:                 0.6s   (one call)
insight load, 50 squads:   17.5s   (throttle-bound, as designed)
second load:                0.0s   <- the immutability cache
```

The numbers it produces, over the top 50 rather than the 20 sampled for the gate:

| | |
|---|---|
| João Pedro | **134% EO** vs 65.2% global — **+69** |
| Palmer | **62% EO** vs 11.9% global — **+50** |
| captain split | João Pedro 21 · Haaland 8 · Palmer 7 (42% / 16% / 14%) |
| chips | **47 of 50 played Bench Boost** |

Palmer holds at a +50 gap across the wider sample, so the gate's headline was not an artefact of 20 managers.

**Answers to the two questions left open at the gate:** it lives on **its own page** (`5_Leagues.py`) — Players
is at ADR-138's ten-view ceiling, and this is about *managers*, a different entity; and **transfer flow is not
in v1**, so EO and the captain split get a chance to prove themselves first.

### 🐛 Two things the build turned up

1. **A test that passed alone and failed in company.** The two page tests both use the Elite preset (314), and
   `st.cache_data` is process-wide and keyed on the league id — so the second test silently read the first
   one's fake league. Correct caching, order-dependent tests; fixed with an explicit `st.cache_data.clear()`
   and a comment saying which of the two is at fault (the tests).
2. **I rewrote history and caught it in the diff.** Inserting a page meant renumbering seven files and their
   ~145 references. The sweep also hit `Architecture.md` — which is a **historical log**, so an entry reading
   *"rewrite `8_Help.py`"* became *"rewrite `9_Help.py`"*, making a true record of Sprint 148 false. Reverted;
   a forward-dated changelog entry now explains the renumber instead, and says explicitly that entries above
   it keep the filenames they were written with.

   **The rule: a mechanical rename is safe across code and tests, and unsafe across a log.** Code describes
   what *is*; a log describes what *was*. `sed` cannot tell them apart, so the person running it has to.

### 🧪 Definition of Done — met

1. **Tests: +17 (1354 → 1371).** `tests/test_league.py` (13) covers EO with the captain counted twice, bench
   exclusion, the partial-fetch divisor, the gap in both directions, captain-split shape, chip counts, rank
   movement including the `last_rank == 0` "new entry" case, and `last_completed_gameweek` against the ADR-123
   deadline rule. Client tests pin the paginated URL and that a failure raises `FplApiError` (the page catches
   it). Page tests assert **no per-manager fetch happens on load** and that a truncated league says so —
   driven through a fake client, so no test touches the live API.
2. **Manual smoke:** league 314 end to end, both loads timed, cache verified.
3. **Docs:** this ADR, the Architecture changelog (incl. the renumber note), the Roadmap, PROJECT_STATUS, the
   Feedback_Log row, `docs/05_Sprints/Sprint195.md`.
