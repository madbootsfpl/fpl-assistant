# Architectural Decision Record: Transfer flow — split the free half from the paid one

**Decision ID:** ADR-162
**Date:** 2026-08-28
**Status:** ✅ **Accepted — owner-gated, built** (Sprint 218, 2026-08-28). **1537 → 1545 tests, ruff clean.**
**Superseded By / Replaces:** Closes the *"not in v1, deliberately"* half of ADR-141. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-141 deferred transfer flow with a one-line reason: *"one more call per manager"*. That was the whole
analysis, and it turned out to be **half wrong** — because the cost is not uniform across what "transfer flow"
means.

Checking the payloads before designing anything:

* `/entry/{id}/event/{gw}/picks/` — **already fetched by this page** — carries `entry_history`, and that holds
  `event_transfers`, `event_transfers_cost`, `points_on_bench`, `bank` and `value`. **How much the league
  transferred, what its hits cost and what it left on the bench are free.**
* `/entry/{id}/transfers/` — a genuine extra call per manager — is needed only for **which players** moved.

And the data reality, probed live:

```
/entry/{1,100,12345}/transfers/ → 0 transfers each
```

Not a bug: **at GW1 nobody has transferred**, because every squad is still its opening pick. The identity half
has nothing to show until GW2.

---

### ✅ Decision

**1. The free half is always shown.** Movers, transfers, hits, points spent on hits, points left on the bench,
average bank — drawn from payloads already in hand, so it costs nothing and needs no button.

**2. `movers`, not just `transfers`.** How many managers moved *at all* is the number that says whether a
gameweek was quiet or frantic; a total hides one manager taking a −12 among thirty who did nothing.

**3. The identity half asks first, and latches.** ADR-141's rule — *nothing that costs N calls happens because
someone opened a tab* — applied to the second N-call step on the same page. Latched on `(league_id, gameweek)`
for the reason US-431 established the day before: a bare flag would carry across a league switch and spend the
calls silently.

**4. It is cached for 15 minutes, not forever.** `_picks` is cached with no expiry because a completed
gameweek's picks are **immutable**. A transfer list is not: a manager can transfer at any moment before the
next deadline, so the same caching would be cheap and wrong.

**5. One net-sorted table, not two top-tens.** A player with 6 in and 5 out is not popular, he is **churning**.
Two lists would have shown him twice and explained neither; the net says which, with both counts beside it.

**6. GW1 says why it is empty.** *"Nobody transferred in GW1 — which is expected in the first gameweek, when
everyone's squad is still their opening pick. This fills in from GW2."* An empty table with no explanation
reads as a broken feature.

### 🧪 Definition of Done

1. **Tests: +8.** Movers counted separately from transfers; empty-safe and surviving a payload with no
   `entry_history`; the season list filtered to one gameweek; a churning player appearing once with both
   counts; ranking by the size of the move in either direction; an empty gameweek yielding no rows. Plus the
   page keeping the free half out from behind the button and the paid half latched.
2. **Manual smoke** — the endpoint probed live (shape confirmed, 0 transfers as expected at GW1); analytics
   exercised on synthetic leagues covering churn, hits and empty weeks.
3. **Docs** — this ADR, the roadmap item closed, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**"One more call per manager" was a cost estimate that had never been checked against the payload.** It was
written once in ADR-141, carried forward as settled, and deferred a feature whose most useful half was already
sitting unread in a response the page was fetching anyway. The same ADR records the opposite error in the
other direction — the league table *"came in 5× below the estimate that nearly deferred it"*.

The rule: **before deferring on cost, open the response you are already getting.** Cost estimates decay in one
direction only — toward pessimism nobody re-checks, because being wrong that way never breaks anything.

Also worth noting: this is the second sprint running where the deferred half and the shipped half turned out
to have completely different evidence requirements (ADR-161 was the first). Roadmap lines that bundle two
things are worth splitting on sight.
