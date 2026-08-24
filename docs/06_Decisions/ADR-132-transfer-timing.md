# Architectural Decision Record: Transfer *timing* arithmetic, not a transfer-path search

**Decision ID:** ADR-132
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved ("build the arithmetic as scoped"), built** (Sprint 184). It is
deliberately **smaller and different from the roadmap item it answers**, on evidence from a prototype against
the live squad; that divergence was the decision gated.
**Superseded By / Replaces:** Extends `suggest_transfer_plan` (ADR-035) with the time dimension. Scopes down
the roadmap's "Multi-GW transfer-path planner".
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The roadmap item, from the fplapex review:

> **Multi-GW transfer-path planner** + horizon decay weights — plan transfers several GWs ahead as a **path /
> tree**, pricing in **hits (−4 now vs rolling)** + total xPts. MadBoots spin: a grounded *why* per move.

The intuition is that *when* you make a transfer matters, so the plan should search over gameweeks as well as
players.

---

### 🔬 What the prototype found

**1. The best move barely changes by gameweek.** Best single transfer computed independently for each of the
next six gameweeks:

```
GW2  Gibbs-White → Cunha        +1.20
GW3  Gibbs-White → Szoboszlai   +0.80
GW4  Gibbs-White → Szoboszlai   +0.60
GW5  Gibbs-White → Cunha        +0.80
GW6  Gibbs-White → Cunha        +0.50
GW7  Gibbs-White → Cunha        +0.50
```

**The player to sell is identical in all six**, and the two buy candidates are near-interchangeable. The
*gain* moves; the *decision* does not. This follows directly from what ADR-131 measured — a squad's per-gameweek
projection varies by ±3%, because the fixture multiplier is ±20% at its extremes and one player's share of a
squad is small.

**2. There is no path to search.** Over the same horizon the whole market yields **one** positive-gain move for
this squad:

```
Gibbs-White → Cunha   +3.00      ← the only beneficial single transfer over six gameweeks
```

The existing greedy planner stops after it, because there is no second move to make. A tree search needs
branches; this tree has one.

**3. And the hit arithmetic settles itself.** A hit costs 4 points. The single best move over six weeks is
worth **+3.0**. Taking a hit here is not a close call, and no search is needed to say so.

*(This is an early-season reading: cold-start xP is flat, so few moves clear the bar. Mid-season, with real
form spread, more will. What will **not** change is finding (1) — the sell target being week-independent is
structural, not seasonal.)*

---

### ✅ Proposed Decision

**Build the timing *arithmetic*, not the path search.** The questions a manager actually faces are rule-driven
and small, and every one of them is answerable exactly:

1. **Is this move worth making at all?** — the existing gain, over the chosen horizon.
2. **Use the free transfer now, or bank it?** — banking gives two next week (rolling to a maximum of five),
   which is worth it only when a second move worth having is likely, and costs the gain forgone by waiting.
3. **Is the second move worth −4?** — compare its gain with the hit, plainly. Most weeks the answer is no, and
   saying so with the number is more use than a plan that quietly assumes yes.
4. **What does the run of free transfers look like** across the horizon, given one per gameweek and a cap of
   five?

Presented as a short, grounded sequence — *"Use your free transfer on Gibbs-White → Cunha (+3.0). Don't take a
hit: the next-best move is worth less than the 4 points it costs."* — with the same Edge/Risk framing the rest
of the app uses.

**Reuse only:** `suggest_transfer_plan` for the moves, `by_gameweek` for per-week gains, `fpl_rules` for the
transfer and hit rules (which the KB already states correctly). A new pure `analytics/transfer_timing.py`.

---

### 🔀 Alternatives Considered

- **Build the full path/tree search as written.** Rejected on the evidence: the branching it would explore does
  not exist in our data, and the one dimension it would optimise — which week — has the same answer every week.
  It would be substantial machinery producing a conclusion the arithmetic already gives, and it would need
  **horizon decay weights**, a constant we would have to invent and could not calibrate. Building a search
  whose search space is a single point is how a codebase gets heavy without getting better.
- **Wait until mid-season to decide.** Tempting, and finding (2) is genuinely seasonal. Rejected because
  finding (1) is not — and the timing arithmetic is useful *now*, every week, whereas the tree would only
  become interesting if the market's shape changes in a way we can check for later.
- **Ship the arithmetic and add the search behind it later.** This is in fact the recommendation — the
  arithmetic is the load-bearing part, and if mid-season the per-gameweek best moves genuinely diverge, the
  search becomes a well-posed extension rather than a guess. **The trigger is written down below.**

---

### 🧭 Consequences

**Positive** — answers the questions a manager actually asks, exactly, from rules we already encode; no
invented decay constant; small enough to be obviously correct; complements ADR-131 (that says *when* something
is coming, this says *what to do about it*).

**Negative / risks (mitigations)** — it is less than the roadmap promised, and less than a competitor ships
(*mitigation:* what fplapex ships is a solver, and the roadmap's own strategy note says not to try to
out-solver a solver — the recorded edge is explanation, and an honest "don't take that hit, here's the number"
is that edge); the early-season reading may understate how many moves exist later (*mitigation:* the
arithmetic scales to any number of moves — it is the *search* that is being declined, not the multi-move plan);
declining a roadmap item on one squad's data is a small sample (*mitigation:* finding (1) is structural and
follows from ADR-131's measurement, not from this squad; finding (2) is flagged as seasonal).

---

### 🧾 Status & follow-ups

- **Accepted and built (Sprint 184).** `analytics/transfer_timing.py` (pure) + the advice on My Squad ▸
  Transfer, above the moves. 14 new tests. 1236 → **1250**, ruff clean.
- **The build fixed three copy faults its own first output exposed.** Advising *"bank your transfer"* and
  *"a second move is worth the hit"* in the same breath reads as two opinions rather than one plan — when the
  answer is to bank, a second move that would justify a hit is precisely the *reason* to bank, and the verdict
  now says so. The zero-move case claimed "only one move is worth making". And the headline mentioned hits
  even with no second move to take one for.
- **Live output:** *"Use your free transfer on **Gibbs-White → Cunha** (+1.2 next gameweek)."* /
  *"Don't take a hit: the next-best move gains 0.4, less than the 4 points it costs."*
- **The trigger to revisit the search** — written down so it is checkable rather than remembered: once the
  season has real form spread, re-run the prototype. If the **best move differs by gameweek** for a typical
  squad, or if **more than three** positive-gain moves regularly exist at once, the tree becomes well-posed and
  worth building. Until then it would be searching a space with one point in it.
