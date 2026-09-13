# Sprint 251: Planning beats greedy by 4% (ADR-187)

**Dates:** 2026-09-13
**Status:** ✅ Complete — **ADR-187 resolved as CLOSED.** The measurement ran; it says no.
Last of the three gaps from the owner's two-team A/B.

---

### 🔬 What was measured

ADR-187 gated on a **measurement, not a planner** — so that is what was built
(`spikes/187-transfer-paths/`). Both strategies get the **same budget**: three transfers, one per gameweek,
no hits, money carried between moves. The only difference is foresight.

```
              mean over 24 squads, 6 gameweeks
  do nothing        178.8
  greedy            220.1     +41.3   ← what transferring at all is worth
  planned           222.0      +1.9   ← what foresight adds on top
```

**Greedy captures 96% of the available gain. Planning adds 4%.**

| | |
|---|---|
| squads where planning added **nothing at all** | **13 of 24 (54%)** |
| median gain | **+0.0** |
| p90 / max | +6.2 / **+14.3** |

More than half the time, foresight selects the **identical sequence**. That is ADR-132's original finding,
in its own words, now true of the corrected model:

> *"The gain moves; the decision does not."*

The tail is recorded rather than averaged away: 12% gained ≥5 points, one gained +14.3. So the honest answer
is not *"planning is worthless"* but *"worth nothing for the median squad, occasionally worth a lot, and we
cannot tell which in advance"* — a lottery ticket with a six-gameweek search attached.

---

### ⚠️ The measurement was wrong twice before it was right

Both faults produced plausible, tabulated, **confidently wrong** numbers.

**1. The two strategies had different budgets.** Greedy made one move per gameweek (**six**) against planned's
**three**. The first run reported planning *losing* by 12 points a squad — not a finding about foresight at
all, but a finding that six transfers beat three.

> **A comparison in which the two strategies get different budgets measures the budget.**

**2. Planned could lose to greedy** — structurally impossible for a strictly larger search space. Its
shortlist was computed **once** against the opening squad while greedy re-scanned the market after every
move, so it measured **shortlist size, not planning**. Seeding the search with greedy's own answer makes
`planned ≥ greedy` hold by construction, and the number becomes what it claims to be.

> ⭐ **The tell each time was a result that should have been structurally impossible.** Neither was caught by
> noticing a bug in the code; both were caught by noticing the *shape* of the answer was wrong. That is the
> only defence available when the thing under test is a measurement — there is nothing to assert against,
> because the number *is* the output.

---

### ✅ Resolution

**Closed, not deferred.** ADR-101's stopping rule applies: *"not left as a permanent revisit-later, which is
how a dormant weight becomes furniture."* ADR-132 is annotated with the re-measurement so it cannot be
reopened from memory a third time.

**What would legitimately reopen it**, written down so nobody re-derives it:

- a **double or blank gameweek** in the horizon — none of these 24 squads faced one, and a blank is exactly
  the structural event foresight exists for;
- **chips** — planning transfers into a Bench Boost is a different problem with a real deadline;
- **a larger search** beating +1.9 on these squads. The search here is bounded (10 candidates, ≤3 moves), so
  **+1.9 is a lower bound** — what is established is that the *easy* wins are not there.

---

### 🧭 The three gaps, closed

The owner's A/B produced three named gaps. All three are now answered:

| | outcome |
|---|---|
| **ADR-185** wildcard pricing | ✅ built — a **+99.6 xP** call that read *Confidence 42/100 · Low* |
| **ADR-186** bank to afford | ✅ built — *"£1.5m more makes this…"* |
| **ADR-187** multi-GW planning | ✅ **measured and declined** — 4% on top of greedy |

Two shipped, one closed on evidence. **The closure is worth as much as the builds**: the question had been
open in the roadmap since before GW1 and was reopened this week on good grounds. It is now answered on
current data, with the bound written down.
