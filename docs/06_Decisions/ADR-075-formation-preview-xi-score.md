# Architectural Decision Record: The XI score in the formation preview

**Decision ID:** ADR-075
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** enhances the display-only formation preview (ADR-062). No analytics change —
reuses `select_squad` + the build's existing `scores`/`display_xp`. Triggered by tester request.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

On **Squads → Build**, the *"🔎 Preview the best XI in a given shape (display only — not saved)"* expander
shows the previewed XI (with per-player xP) but **no total**. The tester: *"Can you give the XI score so the
user can see the effect of different formations?"* Without a total, a user can't tell whether 3-4-3 or 4-4-2
projects more points.

**Verified in code (real data):** best-XI xP by shape (default `xp` objective, £100m) — **3-5-2 254.1 ·
3-4-3 251.4 · 4-4-2 251.4 · 4-5-1 249.5 · 4-3-3 248.7 · 5-3-2 247.9 · 5-4-1 246.0** — an **8.1 xP spread**.
So a score is decision-relevant. The preview **already solves** the selected shape
(`select_squad(..., formation, size=11, scores=…)`), so its total is a *free* sum of the shown `xP`. Perf
note: a Streamlit **expander body runs even when collapsed**, so a full all-formations comparison would add
~7 ILP solves to *every* Build render.

#### Decision Drivers
- **Answer the tester** — show the XI's projected points, and make the *effect across shapes* visible.
- **Cheap by default** — don't slow the (already heavy) Build page for users who don't want the comparison.
- **Display-only** — the saved build stays a full 15; no analytics change.

---

### ✅ Decision

**1. Show the selected shape's projected XI total (US-230).** In `render_build`'s preview expander, after
the XI table, sum the previewed XI's displayed `xP` (`sum(display_xp[p["id"]] for p in
xi_result["selected"])`) and show it — *"Projected XI: 254.1 xP"* (with the shape name). The score is the
projected **xP** of the shape's best XI **on the current objective**; for the default `xp` objective that is
the optimised total. It updates as the formation selector changes (the solve already runs).

**2. A gated all-formations comparison (US-231).** A **"Compare all formations"** checkbox, **off by
default**. When ticked: solve each of the 7 legal shapes, sum each XI's `xP`, and render a small table —
**Formation · XI xP · Δ vs best** (Δ = `xP − best`, `%+.1f`; the best row = `+0.0`), sorted by XI xP desc,
via `NumberColumn` formatting (ADR-072); an illegal shape shows "—". The **7 solves run only on tick** — the
expander runs collapsed, so gating keeps the default Build render at its current one-solve cost.

**3. No analytics / no save change.** Reuses `select_squad` and the build's `scores`/`display_xp`; the
preview stays display-only (the saveable build is always a full 15, ADR-062). No server writes.

---

### 🔀 Alternatives Considered

- **Always-on comparison table.** Rejected (owner) — ~7 ILP solves on every Build render (the expander body
  runs even collapsed) → a noticeable slowdown, especially on the Cloud.
- **Only the selected-shape score, no comparison.** Rejected as the primary answer — the tester wants the
  *effect across formations*; flipping the selector one shape at a time is weaker. (It's the default state;
  the comparison is the opt-in.)
- **Rank formations by the objective total instead of xP.** Rejected for interpretability — the visible
  metric is xP; for the default `xp` objective they coincide, and showing xP keeps the readout consistent
  with the per-row column.
- **Precompute/cache all 7.** Rejected as premature — `scores` (a dict, objective-dependent) is awkward to
  cache-key; the checkbox gate is simpler and sufficient.

---

### 🧭 Consequences

**Positive**
- The tester's question is answered: a projected-points total per shape, and a one-glance comparison on tick.
- No slowdown for the common case (the comparison is opt-in); the single-shape score is free.
- Display-only, no analytics change, no server writes.

**Negative / risks (mitigations)**
- **The comparison costs ~7 solves when ticked** → acceptable and user-initiated; it's a deliberate action.
- **For non-`xp` objectives the score is the XI's xP, not the optimised metric** → consistent with the
  existing per-row xP column; a caption already notes xP is the reference metric when optimising on another.
- **A shape may be illegal within budget/options** → shown as "—" (as the single-shape preview already does).

---

### 📊 Validation

Verified (real data): the 7 shapes span 246.0–254.1 XI xP (an 8.1 spread), so the score and comparison are
meaningful. Acceptance: the preview shows *"Projected XI: N xP"* for the selected shape and updates with the
selector; ticking **Compare all formations** renders a 7-row table ranked by XI xP with a Δ column, and it's
absent when unticked; the saved build is still a full 15; `select_squad`/the analytics are unchanged; the
existing 617 tests stay green (new tests added).
