# Architectural Decision Record: The minutes you have actually played

**Decision ID:** ADR-173
**Date:** 2026-09-02
**Status:** ✅ **Accepted — owner-reported, measured, gated, built** (Sprint 234, 2026-09-02).
**1667 → 1679 tests, ruff clean.**
**Superseded By / Replaces:** **Partly supersedes ADR-125's blanket defer** of the in-season minutes share —
which was re-affirmed as recently as 2026-09-01 and was correct on the evidence then. Completes the pair
ADR-172 opened (it fixed the *rate*; this is the *minutes*). Surfaces **ADR-132**'s existing banking
arithmetic where it was never wired. **Changes `decision_xp` for 186 players.**
**Deciders / Participants:** Tony Sheridan (Owner, reported it), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner read his own gameweek plan and rejected it:

> *"I would not start Calafiori — he has been on fire, and while I might not start him this gameweek, there
> is no chance I would transfer him. The transfer decision is being made based on next week's game… there is
> value in letting your transfers build up and making some together."*

Three claims. **One is wrong, and it matters that it is wrong**, because acting on it would have made the
advice worse.

---

### 🔬 What the measurement found

**1. ❌ The horizon is not the problem.** The owner proposed looking 3-5 gameweeks ahead. Measured, the
recommended transfer gets *stronger* the further out you look:

| horizon | Calafiori | Truffert | gain |
|---|---|---|---|
| 1 GW | 2.00 | 4.30 | **+2.30** |
| 3 GW | 6.50 | 12.60 | **+6.10** |
| 5 GW | 11.30 | 21.30 | **+10.00** |

A longer horizon would have recommended selling Calafiori **with more confidence**. It multiplies a
suppressed rate over more games; it cannot correct one.

**2. ✅ But the recommendation is wrong, and the cause is minutes.** His rate is sound — **5.29 pp90**. What
is wrong is the minutes it is multiplied by:

| | |
|---|---|
| xMins the model uses | **0.43** — last season's injury-hit 1,697 minutes |
| xMins he has earned | **0.94** — 170 minutes across 2 played gameweeks |

Correct that one number and **Calafiori 4.43 vs Truffert 4.30 → the transfer gain is −0.13 and is not
advised.** The owner's instinct was right and his diagnosis was not, which is exactly why the hypothesis was
tested rather than implemented.

**3. ✅ Banking is a real gap — and we already built the arithmetic.** `bank_or_use` (ADR-132) decides
precisely the owner's point: banking is worth it when the hit it saves exceeds the gain you skip. It is wired
into **the Transfer tab only**. The week's answer — the thing most people read — has never called it.

---

### ✅ Decision

**1. Use the minutes a player has actually played — but only when he has played them all.**

```
qualifies  ⇔  he has a row for EVERY completed gameweek  AND  minutes > 0 in each
share      =  total minutes ÷ (completed gameweeks × 90)
otherwise  →  today's historical share, unchanged
```

**The guard is the decision, not a caveat.** ADR-125 deferred this on sample size, and that objection is
real: two gameweeks cannot tell a player rested once from one being phased out. So the rule refuses to try —
**a player who sat out any completed gameweek falls back to history and cannot be cratered by a single rest.**
What is left is the case where there is no ambiguity at all: he has started every week, and last season's
minutes are simply the wrong number.

A gameweek counts as completed only when it carries a **scoreline** — `yet_to_play`'s test (ADR-138), which
is the guard ADR-125 asked for and did not know existed.

**2. The week's answer calls `bank_or_use`.** No new logic; the ADR-132 module is imported and its verdict
rendered as a line beside the transfer. When there is no second move worth having, the answer says *bank it*
rather than presenting one option as the only one.

**3. A transfer states its weekly gain and its horizon gain.** The line already says *"+1.5 XI xP next GW"*,
so the window is not hidden — but a one-week number reads as a verdict when it stands alone. Showing both
lets *"good this week, marginal over five"* be visible, which is the distinction the owner was reaching for.

---

### 📊 Measured effect

**186 of 626 players** move by ≥0.5 xP; **258 qualify** for the in-season share (207 move ≥0.10 in weight).

| player | before | after | why |
|---|---|---|---|
| **Calafiori** | 2.00 | **4.50** | the case that prompted this |
| **Kinsky** | 0.50 | **2.60** | ⭐ **the bug reported 2026-08-18 and open ever since** — a role change last season's minutes could not see |
| **Mendy** | 2.80 | **1.90** | corrected *down* — 60 minutes a game, modelled as nailed |
| **Haaland** | 6.30 | **7.60** | plays 90 every week; his weight was being held below 1.0 by last season |

**Calafiori → Truffert: +2.30 → −0.10. The transfer disappears**, which is the owner's judgement reached by
arithmetic.

The top of the board also stops being strange: Haaland, Isak, Foden, B.Fernandes, Semenyo, Mbeumo, Saka.

---

### 🔀 Alternatives Considered

- **Extend the transfer horizon to 3-5 GW** (the owner's proposal). **Rejected on measurement** — it
  strengthens the wrong recommendation. Recorded because it is the intuitive fix and would look reasonable to
  the next person who has the same instinct.
- **Keep deferring to GW4-6** (yesterday's decision). Rejected: the hold was justified on sample size, and
  that argument is answered by the guard rather than by waiting — the ambiguous cases *still* defer. Waiting
  now has a known cost: a wrong transfer on a real squad, and the Kinsky bug entering its third week.
- **Blend in-season minutes with the historical share by evidence** (ADR-125's original design). Rejected
  *for now*: it is the better long-run answer and needs a weighting constant nobody can calibrate on two
  gameweeks. The guard is the honest version of the same idea — full weight where there is no doubt, no
  opinion where there is.
- **Lower the bar to "played in at least one gameweek".** Rejected: that is the crater case. One appearance
  says nothing about the next.

---

### 🧭 Consequences

**Positive** — fixes the reported transfer; closes the Kinsky bug at last; corrects over-projections
(Mendy) and under-projections (Calafiori, Haaland) in the same change; makes banking visible where it is
read; uses machinery that already exists (`yet_to_play`, `bank_or_use`) rather than adding any.

**Negative / risks (mitigations)** — 186 players move and recommendations will visibly change between
gameweeks (*mitigation:* say so; they were wrong before). The share is computed from **two** gameweeks, so it
is noisy (*mitigation:* the guard removes the ambiguous cases, and every additional gameweek shrinks the
noise; this is a floor on quality that only rises). A player who plays every game but is about to be dropped
gets full weight (*mitigation:* true today as well, and no minutes-based model can see the future). **The
`FORM_WEIGHT` half is still 0**, so the model still cannot see that Calafiori is *scoring* well — only that
he is *playing* (*mitigation:* stated plainly; that remains ADR-125/the GW4-6 calibration).

---

### 🧾 Implementation notes

- `minutes_share` gains an in-season path; `availability_weight` and every caller keep their shape.
- The qualification test belongs next to `yet_to_play` in `analytics/minutes.py` — same data, same scoreline
  rule, and putting it anywhere else invites a second opinion about what "played" means.
- Tests must pin **the guard**, not the outcome: a player who sat out one completed gameweek must keep his
  historical share, and a player with a row for only some gameweeks must not qualify. A test that only
  asserted "Calafiori is higher" would pass on any change that raised him.
- Not a navigation change, so the ADR template's nav checklist is N/A. The index row is not.


---

### 📊 Built — measured after (2026-09-02)

All three parts shipped. The week's answer now reads:

```
  Transfer: Senesi (TOT) → De Cuyper (BHA)  (+2.5 XI xP next GW)  · Confidence 86/100 · High
            Edge: +2.5 to your starting XI over 1 GW · Higher projected points (5.5 vs 3.0)
            Longer view: +10.4 XI xP and still ahead over the next 5 GWs
```

…and where banking wins, an *"Or bank it: it saves 3.0 (the hit avoided on a second move worth 3.0) and
costs 0.3 by waiting a week"* line appears beneath it. It is shown **only** when banking is the better
answer — an alternative offered every week is noise, not advice.

**The longer view names the disagreement.** *"still ahead over"* when the move holds up, *"but worth less
over"* when it does not — which is the case the owner hit and the one a weekly number hides.

**Deliberately the same players re-priced, not a second search.** Re-running `suggest_transfers` over five
gameweeks could name a *different* move, and then the two numbers would be answering different questions
while sitting on adjacent lines.

---

### 🔬 What building it found — three tests and a fake modelling less than reality

**1. `gw_history_by_code` stopped being optional, and a test was relying on it being so.**
`test_build_starts_the_bench_in_recommended_order` recomputed xP *without* it and asserted the app's bench
order matched. Harmless before — the per-GW data only fed the dormant form term, so omitting it changed
nothing — but it now drives the minutes weight too, so the test was checking one ranking against a different
one and failed for the correct behaviour.

**2. Two `_FakeStore`s had no `get_gw_history_by_code`.** The real `Storage` has always had it; the fakes
modelled less than the thing they stand in for, and passed only while nobody read that method.

**3. A stubbed transfer had no `gain`.** `test_gameweek_plan_assembles_...` faked `suggest_transfers` as
`[{"out": {"id": 4}}]`, which the real function never returns — every move carries `gain` and `in`. Fixed the
fake rather than making the code tolerate a shape that cannot occur.

> **All three are the same species as ADR-172's `_worth_player`: a test fixture modelling less than reality,
> which passes right up until the code looks at the part that was missing.** They are not caught by review —
> they are caught by a change that reads one more field, which is a poor early-warning system.

**Every guard was mutation-checked**, in both directions where a direction exists: dropping the *"played
every completed gameweek"* check fails; accepting rows without a scoreline fails; showing the banking line
always fails; never naming the disagreement fails.
