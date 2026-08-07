# Sprint 105: Explainability for squad-build & chips

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (extend the ADR-089 framework to two more decisions)
**Carried Over:** none

> **Direction (owner):** *"explainability for squad build and chips."* Extends the Why · Risk · Confidence
> pattern (Sprint 104, ADR-089) — already live on **captain** + **transfer** — to the **squad build** and the
> **chip advisor**.

---

### 🔎 Verified at planning (real data)

- **The framework is in place** (ADR-089): an `Explanation` (✓ reasons · ⚠ risks · a transparent confidence +
  band), a shared `ui/explain.py::render_explanation`, and the "reasons are **computed from the data**, the
  LLM only phrases + is verified" contract. This sprint adds two more `explain_*` functions — **no new ADR**.
- **Squad build already exposes the signals** (`_decide_build_squad`): budget, `total_cost`, the XI/bench xP
  split, the standout picks, each pick's xP + `minutes_weight`, and any requested archetypes. So the ✓/⚠ and a
  confidence (reliability + value) are grounded from what the build already computed.
- **Chip timing has per-GW values** (`chip_advisor` computes `per_gw` internally: each GW's best-XI + squad
  totals). Exposing the **margin** of the recommended GW over the alternatives gives a grounded chip
  confidence — and, honestly, **preseason it's small** (the gameweeks are near-uniform), so chips read **Low /
  Medium** now and sharpen in-season (the DGW/BGW + mini-league caveats stay ⚠).

---

### 🎯 Sprint Goal

**Objective:** a built squad and each chip recommendation show **why** — a **Confidence · Why (✓) · Risk (⚠)**
block, every reason + the number computed from the signals the decision already used (never an LLM guess). The
same honest, self-tempering heuristic as captain/transfer; the block shows with or without the LLM, and any
narration still verifies.

#### Success Criteria
- [ ] **US-271 (squad-build explainability, extends ADR-089)** — `analytics/explain.py::explain_squad(result,
      xp_by_id, weight_by_id, *, budget, horizon, xi_ids)` → an `Explanation`: ✓ (optimised on xP · XI projects
      N over the horizon · spent £X of £Y · standout picks · a playing bench; requested archetypes met) + ⚠
      (£ unspent · rotation-risk players (xMins < 70%) · doubtful in the 15 · differential-heavy variance · weak
      bench). `squad_confidence(...)` — a documented heuristic from the XI's average expected-minutes
      **reliability** + **budget efficiency**. Wired into the **build** answer (Ask) + the **Build** page.
- [ ] **US-272 (chip explainability, extends ADR-089)** — `chip_advisor` gains a per-chip **`margin`** (the
      recommended GW's value vs the next-best GW); `explain_chips(advice)` → a **confidence per chip** (`Low`
      when the margin is small — honestly flagging preseason-flat weeks) + the DGW/BGW & mini-league **⚠
      caveats**. Rendered on each chip line (`… · Confidence NN/100 · Band`) in the chip block (Ask/chat + the
      Squads **Chips** view).
- [ ] **No drift** — display-only over existing signals; the engine/`decision_xp` unchanged; existing **700**
      stay green; ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help (ADR-089 covers the design — extended).

---

### 🧭 Design sketch

**US-271.** `explain_squad(...)`:
- `squad_confidence(xi_reliability, spent_fraction)` → `100 * (0.7*reliability + 0.3*spent)`, clamped 1–99
  (reliability = mean XI `minutes_weight`; spent = `cost/budget`) — a build of reliable, well-priced starters →
  High; one leaning on rotation risks / cheap enablers → lower. Documented alongside the captain/transfer
  formulas in `explain.py`.
- Reasons/risks from the build's own numbers (budget/cost, xi/bench xP, per-pick xMins, ownership, archetypes).
- `_decide_build_squad` sets `facts["confidence"/"why"/"risk"]` (so narration verifies) and prepends
  `render_explanation` to the `detail`; the **Build** page shows the block above the pitch/table.

**US-272.** `chip_advisor` adds `margin` to each chip dict (best value − 2nd-best GW's value, from `per_gw`).
`explain_chips(advice)` → `{triple_captain: conf, bench_boost: conf, …}` via a shared
`chip_confidence(margin)` (small margin → Low), plus a one-line caveat (*"double/blank gameweeks + mini-league
position sharpen this in-season"* stays the honest ⚠). `ui/chips.py::render_chip_advice` appends
`· Confidence NN/100 · Band` to each chip line; `_decide_chips` puts the confidences in `facts`.

**Deferred:** explainability for the gameweek "AI Tips" plan (same pattern, later); the gated squad signals
(form / news) enrich the "why" at GW1.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-271 | **Squad-build explainability** — `explain_squad` (Why/Risk/Confidence) in the build answer + the Build page. | High | ⬜ To do | ~½ session |
| US-272 | **Chip explainability** — a per-chip confidence (from the GW margin) + caveats, in the chip block. | High | ⬜ To do | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `squad_confidence` is bounded + rewards reliability/value; `explain_squad` lists the right
   ✓/⚠ for a crafted build (unspent budget / a rotation-risk pick / met archetypes); the build answer carries
   the block + verifies. `chip_confidence` maps a small margin → Low and a big one → High; `explain_chips`
   yields a confidence per chip; `chip_advisor` exposes the margin; the chip block shows the confidences.
   Existing **700** stay green.
2. **Manual smoke** — `ask "build me a squad for £100m"` shows Confidence/Why/Risk; the Build page shows it
   above the squad; `ask "which chip should I use for RoboTS?"` shows a confidence per chip (Low preseason,
   honestly), each verified.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help (ADR-089 extended — noted in each).

---

### 📝 Session Progress Log

**US-271 — squad-build explainability (extends ADR-089).** ✅ Done.
- `analytics/explain.py`: `squad_confidence(xi_reliability, spent_fraction)` (documented — `100·(0.7·reliability
  + 0.3·spent)`, clamped 1–99) + `explain_squad(selected, xp_by_id, weight_by_id, *, budget, xi_ids, horizon)`
  → ✓ (optimised on xP · XI projects N over N GW · spent £X of £Y · top picks · a playing bench) + ⚠ (£
  unspent · rotation-risk starters (xMins < 70%) · doubtful in the 15 · differential-heavy variance · weak
  bench). Exported.
- `_decide_build_squad` (Ask): computes it, sets `facts["confidence"/"why"/"risk"]` (so narration **verifies
  ✓**), prepends `render_explanation` to the `detail`. The **Build** page shows the block above the pitch/table.
- **Tests (+2, 2 updated):** `squad_confidence` rewards reliability + budget-use + bounded; `explain_squad`
  lists the build signals + flags £-unspent / a rotation-risk starter + empty-safe; the two Build page tests
  updated for the extra explanation code block. **702** green, ruff clean.
- **Manual smoke:** `ask "build me a squad for £100m"` → *Confidence 90/100 · High* + Why (✓ optimised on xP ·
  XI 233.6 · spent £100 · top picks · bench 72.2) + Risk (⚠ 1 rotation-risk starter); shown in Ask (verifies
  ✓) and on the web Build page above the squad.

**US-272 — chip explainability (extends ADR-089).** ✅ Done.
- `chip_advisor` now exposes a per-chip **`margin`** (a `_gap` helper — how clearly the recommended
  gameweek/window beats the next-best: TC/BB by the max, FH/WC by the min).
- `explain.py`: `chip_confidence(margin, value)` (a **relative** separation — margin ÷ the chip's own value;
  ≥15% → clear/High; near-flat → Low) + `explain_chips(advice)` → `{chip: {confidence, band}}`. Exported.
- `ui/chips.py::render_chip_advice(confidences=…)` appends `· Confidence NN/100 · Band` to each chip line + a
  note on what confidence means; `_decide_chips` computes it, passes it, and adds it to `facts`. The web
  **Chips** view inherits it (it routes through `ask.answer`).
- **Tests (+3):** `chip_confidence` Low-when-flat / High-when-clear + bounded; `explain_chips` a confidence per
  chip (clear beats flat) + empty-safe; `chip_advisor` exposes a margin per chip. **705** green, ruff clean.
- **Manual smoke (RoboTS):** all four chips read **40–49/100 · Low** preseason — honest (the gameweeks are
  near-uniform, so no window is clearly best); they sharpen in-season as fixtures spread. The block explains
  the confidence.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
