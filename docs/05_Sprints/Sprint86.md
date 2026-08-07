# Sprint 086: The XI score in the formation preview (see the effect of a shape)

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (a total-xP readout on the existing preview + a gated all-formations comparison)
**Carried Over:** none

> **Direction (owner, tester feedback):**
> On **Squads → Build**, the *"🔎 Preview the best XI in a given shape (display only — not saved)"* expander
> shows the XI but **no total score**. *"Can you give the XI score so the user can see the effect of
> different formations?"*

---

### 🔎 Verified at planning (real data)

- **Formations differ meaningfully.** Best-XI xP on today's data (default xp objective, £100m):
  **3-5-2 254.1 · 3-4-3 251.4 · 4-4-2 251.4 · 4-5-1 249.5 · 4-3-3 248.7 · 5-3-2 247.9 · 5-4-1 246.0** — an
  **8.1 xP spread**. So a total-score readout genuinely helps a user pick a shape, and an all-formations
  comparison makes "the effect" visible at a glance.
- **The preview already solves the selected shape.** `render_build`'s expander runs
  `select_squad(..., formation, size=11, scores=…)` and renders the XI (per-row `xP`) — it just doesn't
  **sum** it. So the selected-shape score is *free* (a sum of the shown `xP`).
- **Perf note (owner's call: gate the comparison).** A Streamlit **expander body runs even when collapsed**,
  so a full 7-formation comparison would add ~7 ILP solves to **every** Build render. → put the comparison
  behind a **checkbox (default off)** so the cost only lands when the user asks for it.

---

### 🎯 Sprint Goal

**Objective:** the preview shows the selected shape's **projected XI xP**, and — on request — a ranked
**all-formations comparison** so a user can see how much each shape is worth. Display-only; the saved build
is still a full 15; no analytics change (reuses `select_squad`/the build's `scores`).

#### Success Criteria
- [x] **US-230 (the XI score, ADR-075)** — the preview expander shows the selected shape's **Projected XI**
      total (the sum of the previewed XI's `xP`), e.g. *"Projected XI: 254.1 xP (best 3-5-2)"*. Always shown
      (the solve already runs); updates as the formation selector changes.
- [x] **US-231 (compare all formations)** — a **"Compare all formations"** checkbox (**off by default**);
      when ticked, a small table ranks all 7 legal shapes by best-XI xP (with **Δ vs best**), so the effect
      is visible without flipping the selector. The 7 solves run **only when the box is ticked**.
- [ ] **No drift** — display-only; the saved build stays a full 15; `select_squad`/the analytics are
      unchanged; existing **617** stay green; ruff clean.
- [ ] Docs: ADR-075 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-230 | **XI score in the preview** — show the selected shape's total projected XI xP in the "Preview the best XI" expander. ADR-075. | High | ✅ Done | ~¼ session |
| US-231 | **Compare all formations** — a gated (default-off) checkbox → a table of all 7 shapes ranked by XI xP (Δ vs best). | Medium | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

**US-230 (ADR-075).** In `render_build`'s preview expander: after the XI table, compute
`xi_xp = sum(display_xp.get(p["id"], 0) for p in xi_result["selected"])` and show it — a `st.metric` or a
caption *"Projected XI: {xi_xp:.1f} xP"* next to the "display only" note. (The score is the projected **xP**
of the shape's best XI on the current objective; for the default `xp` objective that's the optimised total.)

**US-231.** A `st.checkbox("Compare all formations", value=False, help=…)` inside the expander. When `True`:
loop the 7 `_FORMATIONS`, run `select_squad(xi_pool, budget, formation, size=11, include/exclude, scores)`
for each, sum each XI's `xP`, and render a small `st.dataframe` sorted by XI xP desc — columns **Formation ·
XI xP · Δ vs best** (Δ = xP − best, `%+.1f`; best row = `+0.0`) with `NumberColumn` formatting (ADR-072). An
illegal shape (no XI within budget/options) shows "—". Only runs on tick (the 7-solve cost is opt-in).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the preview shows a "Projected XI … xP" readout for a shape; ticking "Compare all
   formations" renders a 7-row table ranked by XI xP with a Δ column, and it's **absent** when unticked.
   Existing **617** stay green.
2. **Manual smoke** — Build → the preview shows e.g. *Projected XI: 254.1 xP*; tick Compare → 3-5-2 tops the
   table, 5-4-1 ~8 xP behind; the saved build is still a full 15.
3. **Docs updated** — ADR-075 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-230 (the XI score, ADR-075).** The "🔎 Preview the best XI in a given shape" expander (`render_build`)
now shows a `st.metric("Projected XI — {shape}", "{xi_xp:.1f} xP")` above the XI table — `xi_xp = sum of the
previewed XI's displayed xP`. Free (the shape's solve already runs); it updates as the formation selector
changes, and its help points at the upcoming "Compare all formations". Display-only; the saved build stays a
full 15; no analytics change. Smoke (real data): 3-4-3 → **251.4 xP** (matches the planning check).
+1 test (`test_build_formation_preview_shows_the_xi_score`). ruff clean, full suite **618** green.

**US-231 (compare all formations).** A `st.checkbox("Compare all formations", value=False)` inside the
preview expander (**off by default** — the 7 extra ILP solves run only on tick, since an expander body
executes even collapsed). On tick, a `_formation_xi_scores(...)` helper solves the best XI for each of the 7
shapes and a `st.dataframe` ranks them **Formation · XI xP · Δ vs best** (desc; `NumberColumn` `%.1f`/`%+.1f`,
ADR-072), an illegal shape → blank. Reuses `select_squad` + the build's `scores`/`display_xp`; display-only.
Smoke (real data): 3-5-2 254.1 (+0.0) → 5-4-1 246.0 (−8.1). +1 test (`test_build_compare_all_formations_is_
gated` — absent by default, 7 rows ranked on tick). ruff clean, full suite **619** green.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **617 → 619** (+2); ruff clean; CI-parity green.

**Delivered**
- **US-230 — the XI score (ADR-075).** The Build "🔎 Preview the best XI in a shape" expander shows a
  `st.metric("Projected XI — {shape}", "{xi_xp} xP")` — a free sum of the previewed XI's xP.
- **US-231 — compare all formations.** A default-off checkbox → a table ranking all 7 shapes by XI xP with
  Δ vs best; the 7 extra ILP solves run only on tick.

**What went well**
- **Real data justified the feature and the shape.** The 8.1 xP spread (3-5-2 254.1 → 5-4-1 246.0) made the
  score clearly decision-relevant, and the comparison table surfaces it at a glance.
- **The perf trap was spotted at planning** — a Streamlit expander runs its body even collapsed, so the
  comparison was gated behind a checkbox rather than slowing every Build render.
- **Zero analytics change** — reused `select_squad` + the build's `scores`/`display_xp`; display-only, the
  saved build still a full 15.

**Watch-outs / follow-ups**
- For non-`xp` objectives, the score is the XI's projected xP (not the optimised metric) — consistent with
  the existing per-row xP column + the "xP is the reference metric" caption.
- The comparison is 7 ILP solves on tick — acceptable and user-initiated; if it ever feels slow, caching
  keyed on (objective, budget, include/exclude) is the next lever.

See `Sprint86_Lessons_Learnt.md` for the detailed retro.
