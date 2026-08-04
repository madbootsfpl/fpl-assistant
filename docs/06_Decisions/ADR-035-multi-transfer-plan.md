# Architectural Decision Record: Multi-transfer plan (coordinated, greedy)

**Decision ID:** ADR-035
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Extends ADR-030 (single-transfer engine)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`transfer` (ADR-030) recommends the best **single** transfers — a shortlist of independent options.
But a manager often has several free transfers banked and wants *"which 3 transfers should I make?"*
(owner's Sprint-32 retro note). The top-N independent suggestions aren't a valid *plan*: each assumes
it has the whole bank to itself, so together they can overspend, double-buy, or break ≤3/club.

A planning probe confirmed a **coordinated** plan is both correct and materially better. On squad
"TS", a greedy 3-transfer plan (start bank £0):

| # | Move | Gain | Why coordination matters |
|---|---|--:|---|
| 1 | Kelleher £5.0 → Benitez £4.5 | +15.4 | frees **£0.5** into the bank |
| 2 | Slater £4.5 → **Dasilva £5.0** | **+26.6** | affordable *only* because of that £0.5 |
| 3 | Ampadu £5.5 → Adli £5.0 | +7.0 | Dasilva already owned → picks Adli (no double-buy) |

**Total +49.0 xP.** The naive independent top-3 never reaches Slater→Dasilva (unaffordable at bank £0
→ settles for Slater→Reed +9.9). **Threading the shared bank unlocks better moves.**

#### Decision Drivers
- **A valid *plan*** — jointly legal (shared bank, ≤3/club across the set, each player once).
- **Explainable** — a manager should be able to follow the reasoning.
- **Honest about the unknowns** — free-transfer count and hits.

---

### 💡 Decisions

**1. A greedy coordinated plan.** `suggest_transfer_plan` repeatedly takes the **best legal single
transfer given the current state** and applies it, up to `count` times:

```
running_bank = bank; owned = [...]; sold = {}
repeat up to count:
    market = players − sold                    # no sell-then-rebuy
    move   = suggest_transfers(owned, market, xp, bank=running_bank, limit=1)  # best legal move NOW
    if no positive move: stop
    owned  = owned − OUT + IN                   # bought player joins owned (no double-buy)
    running_bank += OUT.price − IN.price        # thread the shared bank
    sold.add(OUT); record(move, running_bank)
```

It **reuses `suggest_transfers`'** constraint logic (position, ≤3/club, budget, availability) on the
*evolving* state, so every rule already proven for single transfers holds across the plan. Positive
gains only; stops early when none remain.

**2. Correct by construction.**
- **Bank never negative** — `suggest_transfers` only allows `IN.price ≤ OUT.price + bank`, so after a
  move `bank += OUT.price − IN.price ≥ 0` (a provable invariant; unit-tested).
- **No double-buy** — bought players are in `owned`, which is excluded from candidates.
- **No re-buy** — sold ids are removed from the `market`.
- **≤3/club across the whole plan** — club counts are recomputed from the current `owned` each step.

**3. `count` is an input** (`transfer --count N`; "N transfers" in `ask`), default 1. The tool can't
know your banked free transfers (no auth), so the manager states how many. `--count` is **opt-in**
for plan mode; without it, `transfer` keeps today's independent shortlist (backward-compatible).

**4. Greedy ≠ globally optimal (stated caveat).** Each move is the best given the last, not a joint
optimum — greedy won't deliberately take a worse move 1 to fund a better move 2. Acceptable: it's
explainable, and the probe shows it's strong. A jointly-optimal ILP would be marginal and opaque —
deferred.

**5. Hits deferred.** The count assumes N *free* transfers; the −4 hit optimisation (gain vs the hit)
stays on the Backlog (the full multi-move *planner*). Stated in the output.

**Not in scope:** ILP/global optimisation; hit (−4) maths; multi-*week* sequencing (which GW to move);
knowing the real free-transfer count or bank.

---

### 🧪 Worked example (pressure-testing — real squad, before code)

The TS 3-plan above: threads a £0.5 sale into an otherwise-unaffordable Slater→Dasilva (+26.6), total
+49.0, no double-buy, ≤3/club held — vs the naive shortlist that can't reach it. Confirms the greedy
plan is legal, coordinated, and strong before any code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the first *plan* (a sequence, not a single call) — jointly legal and materially better
  than a shortlist. Reuses the single-transfer engine; no new dependency; `transfer` unchanged by default.
* **Negative / Trade-offs:** greedy isn't guaranteed optimal (caveat); the count and hits are the
  manager's to supply/weigh (no auth).
* **Risks & Mitigations:**
  - *Bank negative / double-buy / club-break* → prevented by construction; each unit-tested.
  - *Greedy suboptimality* → honest caveat; probe shows strength; ILP deferred.
  - *Over-reading "N transfers"* → state count = your free transfers; hits not modelled.

---

### 🛠 Implementation & Migration
* **Components Affected:** a pure `suggest_transfer_plan` in `src/analytics/transfer.py` (wraps
  `suggest_transfers`); `transfer --count` + a plan view (`src/ui/transfer.py`); `ask` gains the
  N-transfer parse + a plan humaniser (`src/ask.py`). No schema change; the single-transfer path untouched.
* **Action Items:**
  - [x] Record the greedy design + the probe evidence (US-098)
  - [ ] `suggest_transfer_plan` + `transfer --count` + view + tests (US-099)
  - [ ] `ask "which N transfers…"` parse + humanise + narrate + smoke (US-100)
  - [ ] (Backlog) the hit-optimising / multi-week planner; a globally-optimal (ILP) variant

---

### 🔄 Review & Reconsideration
* **Review Date:** If greedy plans look visibly suboptimal in real use, or hits/multi-week become wanted.
* **Triggers for Reconsideration:**
  - [ ] A jointly-optimal plan matters → an ILP variant behind the same interface.
  - [ ] Hits/sequencing wanted → the full planner (gain vs −4, which week).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-098 (this), US-099, US-100
- **External Docs:** [ADR-030 (single-transfer engine)](./ADR-030-transfer-suggestions.md) · [ADR-034 (`ask`)](./ADR-034-ask-command-grounded-nl.md) · [ADR-008 (optimiser / MAX_PER_CLUB)](./ADR-008-squad-selector.md) · [Sprint 033](../05_Sprints/Sprint33.md)
