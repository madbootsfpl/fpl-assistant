# Sprint 248: Bank to afford (ADR-186)

**Dates:** 2026-09-13
**Status:** ✅ Complete — ADR-186. **1746 → 1751 tests, ruff clean.**
Second of the three gaps from the owner's two-team A/B. ADR-187 remains proposed.

> **Owner:** *"You are not suggesting to hold on making transfers for a couple of weeks to say buy a more
> expensive player than you can afford with current budget."*

---

### 🔧 What shipped

```
Transfer: Watkins (AVL) → Havertz (ARS)  (+7.4 XI xP over 5 GW)  · Confidence 95/100 · High
          Worth saving for: £1.5m more makes this Watkins → Isak (+13.8 XI xP, +6.4 on the move above)
```

`affordability_cliff` sweeps the best move at budgets above today's bank and reports the **cheapest** one
that unlocks something materially better — *"£1.5m more"*, not *"£2m more"* when £1.5m suffices.

The move you can make today stays the headline. The cliff sits after it and never replaces it: a manager who
cannot raise the money must still be told what to do now.

---

### 💡 The lesson

> **"Bank" meant a spare transfer everywhere in the code, and money to the user.**

The feature was not missing because it was hard — it is a loop over `suggest_transfers` with a bigger number.
It was missing because the word had been claimed by a different concept. `bank_or_use` answers *"bank the
transfer?"*; nothing answered *"bank the money?"*, and the shared word made the absence invisible.

**A term that means one thing in the code and two things to the user hides the half you did not build.**

**And it ships the arithmetic while refusing the forecast.** The step from £0 to £1.5m is a fact about
today's market, computed exactly. The step from *having* £0 to *having* £1.5m is a prediction about price
movement we have not verified — modelling it would stack the unverified price predictor (ADR-092) on top of
a heuristic. Same line ADR-161 drew when it shipped the H2H decomposition and gated the win-probability sim.

⚠️ The two thresholds (**£2.0m** reach, **2.0 xP** minimum uplift) are **provisional** — chosen so the notice
stays rare, not calibrated. Recorded in the ADR with a re-measure, so the next person tunes them against data
rather than taste.

---

### 🔬 The wiring guard skipped instead of failing

The first attempt asserted `"cliff" in plan` and then **returned early when the value was `None`** — which is
exactly what the mutation produces. It skipped precisely when it should have failed.

> **A test that skips is not a test that passes** (ADR-178).

**Third sprint running** in which the guard I wrote for a new feature protected nothing on its first attempt:
ADR-181 (a test that rebuilt the thing under test), ADR-185 (two tests of components with no test of the
wiring), and now this. The pattern is consistent enough to name: **the guard for a new feature is written by
the person least able to see what it misses, immediately after building it.** Mutation-testing is not a
finishing flourish here; it is the only thing catching these.

Rewritten to assert **the call** — `gameweek_plan` must ask `affordability_cliff`, with this squad, this
market and **this bank**. That holds whether or not today's data contains a cliff, and it kills two mutations:
dropping the call, and passing a hard-coded `bank=0.0` instead of the squad's real bank.

---

### 🔬 And the fixture had to grow three times

It reached `affordability_cliff` fine, then failed on `team` (the renderer prints it), then `status`, then
`points_per_game` — because `gameweek_plan` also picks a captain, which prices players through `decision_xp`.

> **A fixture aimed at one function has to satisfy every function on the path to it.**

Each failure was the same shape — modelling less than the payload — which remains this repo's most
persistent test defect.

---

### 🧪 Tests

**+5**, all mutation-checked: a better move just out of budget is reported · the **cheapest** unlocking
budget is the one named · silence in all three no-cliff cases · the immediate move is never replaced · and
`gameweek_plan` actually makes the call, with the real bank.
