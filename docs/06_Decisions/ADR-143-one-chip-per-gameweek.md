# Architectural Decision Record: One chip per gameweek — the sequence scan, scoped to what the data supports

**Decision ID:** ADR-143
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 197, 2026-08-26). **1387 → 1393 tests, ruff clean.**
The Roadmap's *"rank every valid chip sequence by projected xPts"* is **declined on evidence**; the legality
defect it would have incidentally fixed is **built**.
**Superseded By / Replaces:** Corrects `chip_advisor` (ADR-082), which chose each chip independently. Closes
the last open row of the fplapex column in the competitive table. No `decision_xp` change.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 What the Roadmap asked for, and what the data said

> **Full chip-sequence scan** *(fplapex)* — rank **every valid** Wildcard/Free Hit/Bench Boost/Triple Captain
> **sequence** across the season by projected xPts.

Two things had to be true for that to be worth building: the sequencing must **change the answer**, and the
change must be **worth something**. Measured across **200 random legal squads** on live data, over an 8-GW
horizon:

| question | answer |
|---|---|
| Do two chips ever want the same gameweek? | **Yes — 28% of squads.** Not a tree with one branch. |
| What is the best resolution worth? | **0.3 xP at the median, 1.5 xP at the very worst.** |

So the two halves split cleanly, and they point in opposite directions.

**The ranking is declined.** A "best sequence" would differ from the naive picks 28% of the time and be worth
a third of a point — the same order as ADR-131's ±3% per-GW noise. Shipping it would put a precise-looking
ordering on top of numbers that cannot support one. This is the third time measurement has killed a
sequence/tree feature here (ADR-132's transfer path, ADR-131's problem-week), and the reason is the same each
time: **our projections are smooth, and smooth projections make optimal ordering worthless.**

**But the collision itself is a real defect**, and it is not about points at all:

```
Chip strategy — squad 'ClashDemo' (next 8 GW)
  Triple Captain: GW3 — Watkins (AVL), xP 5.3
  Bench Boost:    GW3 — all 15 project 22.2 xP        ← two chips, one gameweek
```

**FPL forbids that**, and the app's own rules base says so: *"You can play only one chip per gameweek"*
(`fpl_rules`). So `ask` would tell a user chips cannot be stacked while the chip advisor advised stacking
them. **A 28% chance of advice that contradicts the app's own knowledge base is worth fixing whatever it is
worth in points.**

---

### ✅ Decision

**1. Chips are assigned distinct gameweeks, in `chip_advisor`** — not at a surface, so every caller (CLI,
`ask`, web) inherits legal advice.

**2. The chip that moves is the one with the least at stake, measured as a _share_ of its own value.**
`_relative_gap` = how much a chip loses dropping to its second choice, over its own best value.

Dimensionless on purpose, and this is the part that took two attempts. The obvious rule — *"move the chip
with the smaller raw margin"* — is wrong, and wrong in a way that looks right: Triple Captain's margin is one
player's ceiling, Bench Boost's is a whole-squad total, Free Hit's is a bad week's XI. **Comparing those picks
the chip with the biggest numbers, not the one with the most to lose.** Worse, Bench Boost's total *includes
the very spike* that made Triple Captain want that week — so on a crafted squad TC's margin read 24.1 and
BB's 29.4 **off the same player**, and the raw rule moved Triple Captain, exactly backwards.

A share of each chip's own scale is comparable: *"gives up 80% of what it came for"* means the same thing for
all three.

**3. A moved chip says so, and says what it cost.** `moved_from` and `cost`, rendered as
*"↪ moved off GW3 — one chip per gameweek (no projected cost)"*. Shown rather than silently corrected, for two
reasons: a manager who reasoned their way to that week deserves to know the app agreed and then had to move
it; and **the cost is the honest part** — 0.0 xP at the median means this is the app declining to advise
something illegal, not the app finding points.

**4. Wildcard is left out of the resolution.** It is a *window* ("reset before GW2–GW4"), not a single
gameweek, and it competes with Free Hit for the same bad week by design — you play one or the other. Forcing
it apart would invent a constraint FPL does not impose.

### ⚠️ Risks

- **The relative-gap rule is a heuristic, not an optimum.** Accepted, and stated: with the best resolution
  worth 0.3 xP, a heuristic that is legal and explainable beats an optimiser that is neither.
- **The two-chip-sets rule** (a fresh set unlocks around GW20) is not modelled. Out of scope while the horizon
  is ≤8 gameweeks; it would matter for a genuine season-long plan, which this ADR declines to build.

### 🧪 Definition of Done

1. **Tests: +6.** No two chips share a gameweek; the least-at-stake chip moves; the share-not-raw rule pinned
   with the exact 24.1-vs-29.4 case that broke the first version; a moved chip reports where from and what it
   cost; an unaffected squad gets no extra noise; fewer gameweeks than chips degrades without inventing a
   week. Re-measured on live data after the fix: **0 of 200 squads illegal**, 57 chips relocated.
2. **Manual smoke** — the colliding squad, before and after, through the real renderer.
3. **Docs** — this ADR, the Roadmap entry + the competitive row it closes, PROJECT_STATUS, a sprint retro.
