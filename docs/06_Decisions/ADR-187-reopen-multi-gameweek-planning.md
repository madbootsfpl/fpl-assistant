# Architectural Decision Record: Reopen multi-gameweek transfer planning

**Decision ID:** ADR-187
**Date:** 2026-09-13
**Status:** 📋 **Proposed** — gate before building. **Reopens a decision, so the gate is whether the new
evidence is sufficient, not what to build.**
**Superseded By / Replaces:** **Reopens [ADR-132](./ADR-132-transfer-timing.md)'s decline** of the roadmap's
multi-GW transfer-path planner, on re-measurement. Third of three gaps from the owner's A/B; see ADR-185 and
ADR-186.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner:

> *"You are looking one GW ahead for transfers — you do calc for multiple GWs but you are not… looking at
> fixture runs and making 2 or 3 transfers to target a run."*

He is 40 points ahead of the MADBOOTS team after four gameweeks.

**ADR-132 declined exactly this, on 2026-08-24**, and the decline was good practice: it prototyped against the
live squad rather than accepting the roadmap item, and found the search space empty.

> *"The best sell was the same player in all six gameweeks and the market yielded **one** beneficial move —
> a tree with one branch."*

#### The re-measurement

Same prototype, run today:

```
h=1  Watkins→Wissa +2.50 · Rice→Foden +2.20 · Mukiele→Canvot +1.70
h=2  Watkins→Wissa +4.20 · Rice→Barnes +3.30 · Virgil→Calafiori +2.60
h=3  Watkins→Wissa +5.70 · Rice→Foden +5.00 · Virgil→Calafiori +3.40
h=4  Watkins→Wissa +6.90 · Rice→Barnes +5.90 · Mukiele→Canvot +4.10
h=5  Rice→Foden   +8.50 · Watkins→Wissa +8.40 · Virgil→Calafiori +4.60
h=6  Watkins→Wissa +10.40 · Rice→Foden +9.80 · Virgil→Calafiori +6.00

distinct beneficial moves : 5      (ADR-132 found 1)
moves at every horizon    : 1
```

**Five branches, not one — and the ranking reorders with the horizon.** At h=5 Rice→Foden overtakes
Watkins→Wissa and then falls back at h=6. That reordering *is* the planning signal ADR-132 concluded did not
exist: which move is best genuinely depends on how far ahead you are looking.

#### Why the original finding expired

⚠️ **ADR-132 was measured on 24 August — preseason — with an xP model that has since been corrected twice:**

| | |
|---|---|
| **ADR-172** (2026-09-01) | FPL publishes `ep_next == points_per_game` for 513 of 626 players, so ADR-124's shrink was **inert**. 8 of the top 20 by xP were affected. |
| **ADR-173** (2026-09-02) | The minutes weight ignored the minutes actually played this season. **186 players moved.** |

A search that finds one branch because most players are mispriced will find several once they are priced
correctly. **This is ADR-180's lesson landing a second time: a constraint recorded in an ADR is a fact about a
version.** ADR-132 was right about the model it measured; that model no longer exists.

---

### 🎯 Decision & Justification

**Reopen it — and make the first deliverable a measurement, not a planner.**

ADR-132's method was sound and should be repeated rather than replaced. What follows is the evidence a build
decision needs, and none of it is a feature:

**1. Does a 2-3 move sequence beat the same number of greedy single moves?** The whole premise. Compare, over
a 6-GW horizon: the greedy path (best move each week) against the best sequence found by search. **If the gap
is small, the decline stands and this ADR closes.** ADR-132's real finding was *"the decision does not change"*
— that is the claim to re-test, not *"how many branches are there"*.

**2. Does it survive the constraints that make it real?** Budget carried between moves, one free transfer a
week, a −4 for a second. A sequence that needs three transfers in one week is not a plan.

**3. Is it stable?** ADR-183 found the optimiser returning different tied optima between runs. **A planner
built on an unstable base would produce a different plan every refresh** — that fix is a prerequisite, and it
is already in.

⚠️ **What is explicitly not proposed:** a full path search over the market. ADR-132 scoped that down for good
reasons that have not changed — the branching factor is enormous and most of it is noise. The measurable
question is narrower: **is a short, budget-aware sequence better than the greedy move repeated?**

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the largest strategic gap the owner named gets tested rather than cited; either it
  ships or the decline is re-grounded on current data — both are worth having.
* **Negative Impact / Trade-offs:** a measurement sprint that may conclude "no", exactly as ADR-132 did. That
  is the cost of a gate, and cheaper than a planner nobody needed.
* **Risks & Mitigations:**
  - **Risk:** a plan looks authoritative and is one injury from wrong. **Mitigation:** whatever ships must
    say what invalidates it, the way ADR-161's H2H states its picks are last week's.
  - **Risk:** the horizon reordering is noise, not signal. **Mitigation:** that is measurement 1's job. The
    reordering is the *reason to look*, not the conclusion.

---

### 🛠 Implementation & Migration
* **Components Affected:** measurement first; code only if it passes
* **Action Items:**
  - [ ] Prototype: greedy path vs best 2-3 move sequence over 6 GWs, several squads
  - [ ] Constrain by budget carry-over, 1 free transfer/week, −4 for extras
  - [ ] Record the result **either way**, in this ADR, with the squads and date
  - [ ] Gate on the number — build only if the sequence materially beats greedy
  - [ ] If it closes: update ADR-132 with the re-measurement so nobody re-opens it from memory

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A decline needs a re-measure date, the same as a feature needs a review date.**

ADR-132 did everything right except leave a tripwire. It measured, it declined, it recorded the evidence — and
then the evidence quietly expired, because two later ADRs changed the model it rested on and neither knew it
was load-bearing for a decision made a week earlier.

**The mechanical fix, cheap and worth adopting: when an ADR declines something on measured evidence, record
what would have to change for the answer to change.** ADR-132 could have written *"re-measure if
`decision_xp` changes materially"* — and ADR-172 would have tripped it on day one.

---

### 🔗 References & Related Artifacts
- **Reopens:** [ADR-132](./ADR-132-transfer-timing.md)
- **Why the evidence expired:** [ADR-172](./ADR-172-a-shrink-needs-something-to-shrink-toward.md) ·
  [ADR-173](./ADR-173-minutes-you-have-actually-played.md)
- **Same lesson, second time:** [ADR-180](./ADR-180-the-accent-belongs-to-the-theme.md) — a constraint in an
  ADR is a fact about a version
- **Prerequisite, already in:** [ADR-183](./ADR-183-the-same-build-twice.md) — a deterministic optimiser
- **Sibling gaps:** ADR-185 (wildcard) · ADR-186 (banking)
