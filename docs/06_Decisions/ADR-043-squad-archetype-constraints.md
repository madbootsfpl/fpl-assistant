# Architectural Decision Record: Squad archetypes — build with low-cost + premium constraints

**Decision ID:** ADR-043
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Extends the squad optimiser (ADR-008/012) with min-count price-band
constraints; extends `build_squad` (ADR-041). Reuses `decision_xp`, `render_squad`, `verify_grounding`.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner wants a **multi-faceted** build — *"build me a squad for £100M with 3 low cost players and 1
premium player"*. The reasoning is real FPL structure: a couple of players sit on the bench (chip
fodder), so cheap **enablers** make sense, while you also want 1–3 **premiums**; a **differential** is a
third type "to define first". Today `build_squad`/`squad --full` optimise the best 15 on xP with no way
to shape it.

#### A planning probe pinned the design on real data
- **Thresholds:** prices run min £4.0 / p25 £4.5 / p90 £6.0 / max £15.5 → **low-cost ≤ £4.5m** (190
  players) and **premium ≥ £9.0m** (5: Haaland, B.Fernandes, Saka, Palmer, Isak) are defensible
  defaults.
- **The ILP takes it cleanly.** `select_squad` is a PuLP model; a band constraint is one line before
  `solve()`: `Σ pick[p] (lo ≤ price ≤ hi) ≥ count`.
- **The NL parse works** on every phrasing ("3 low cost … 1 premium" → 3/1; "2 premium … 4 budget" →
  4/2; none → none).
- **Differentials need data we don't have.** `selected_by_percent` (ownership) is **not stored** → the
  differential is **defined here and deferred**.

#### Decision Drivers
- **Shape the squad** the way a manager actually thinks (enablers + premiums).
- **Still optimal** — xP stays the objective; constraints only restrict the feasible set.
- **Honest when impossible** — an over-constrained ask gets a clear message, not a crash.
- **No new data / dependency** for what ships now; the differential deferred cleanly.

---

### ✅ Decision

**1. Archetypes** (tunable module constants):
- **low-cost** (bench enabler) = price **≤ £4.5m**;
- **premium** = price **≥ £9.0m**;
- **differential** (*defined, deferred*) = **low ownership** (`selected_by_percent` ≤ ~10%) with a
  decent xP — needs an **ownership ingest** (not stored), so a follow-up sprint. A requested
  differential returns a *"defined, coming soon"* note.

**2. Optimiser.** `select_squad(..., band_minimums=None)` where `band_minimums` is a list of
`(count, lo, hi)`; each adds an ILP constraint `Σ pick[p] (lo ≤ price ≤ hi) ≥ count`. The objective (xP)
is unchanged; **absent → today's behaviour, byte-identical**. An over-constrained model returns a
non-`Optimal` status (e.g. ≥6 premiums — only 5 exist) → the caller shows a clear message.

**3. Surface.**
- **CLI:** `squad --full --cheap N --premium M` → `band_minimums=[(N, 0, 4.5), (M, 9.0, ∞)]`.
- **NL:** `build_squad` parses "N low-cost / M premium" (a tested parser) and applies the same bands;
  a parsed differential count → the "coming soon" note; otherwise builds as today.
- **Infeasible → a clear message** ("couldn't fit N premium + M low-cost within £X — relax it").

**4. Grounded + optional**, like every intent — reuse `render_squad` (now showing xP, US-121) + the
verifier; degrades without the LLM.

---

### 🔀 Alternatives Considered

- **Post-filter instead of constrain** (build then swap to hit the counts). Rejected — it wouldn't be
  optimal; the ILP does it exactly.
- **Bake premium/cheap as fixed player lists.** Rejected — a price band is simpler and self-updating.
- **Ship a half-differential** (e.g. by price as a proxy). Rejected — a differential is about
  *ownership*, not price; a price proxy would mislead. Define it properly, defer until we have the data.
- **Per-position archetypes** ("a premium forward"). Deferred — the band interface generalises to it
  later; keep v1 to counts.

---

### 🧭 Consequences

**Positive**
- The manager can shape the squad (enablers + premiums) while keeping it xP-optimal.
- One small, general ILP addition (`band_minimums`) powers both the CLI and the NL build.
- Infeasibility is explicit and friendly; the differential is honestly scoped.

**Negative / risks (mitigations)**
- **Over-constraint** → infeasible → a clear message (the ILP status drives it).
- **Few premiums** (5 ≥£9m) → "≥1–3" is fine; a bigger ask hits the message.
- **Differential expectations** → "defined, coming soon" — no misleading proxy.

---

### 📊 Validation

Prototyped against the live DB + the actual `select_squad` PuLP structure: the band constraint is a
one-line addition before `solve()`; low-cost (190) and premium (5) pools make "≥3 cheap + ≥1 premium"
satisfiable and "≥6 premium" impossible; the NL parser handled every phrasing. Acceptance for the
sprint: `squad --full --cheap 3 --premium 1` and `ask "build me a squad for £100m with 3 low-cost
players and 1 premium player"` both satisfy the structure and stay optimal; an over-constraint gives a
clear message; a differential request gives the "coming soon" note.
