# Sprint 163: UX Sprint D — My Squad density redesign (US-404–406)

**Dates:** 2026-08-17 →
**Status:** 🚧 Planned — gated by **ADR-115** (owner-approved wireframe). Display/IA only. The audit's last slice.
**Capacity:** ~1 session

> **Why:** My Squad (the golden page) is the app's densest — 14 stacked blocks, a 5-metric wall, 4 caption lines,
> three overlapping bench controls, and an in-page Transfer that duplicates the Transfer tab. Reorganise via
> progressive disclosure — **no feature loss**.

---

### 🎯 Scope (reorganising `render_my_squad`)

**US-404 — compact status.** The **5-across metrics → a 3-number strip** (`st.columns(3)`: Projected XI · Captain ·
Bench). The **4 stacked captions → one availability + price line** ("✓ N available · M doubtful · 💷 price note");
the legal/cost becomes the strip's leading pill. Keep the captain ×2 / benched note **conditional**.

**US-405 — remove the duplicate Transfer.** Delete the in-page **Transfer expander**; replace with a one-line
pointer to the **🔄 Transfer tab** (the full transfer UI already lives there).

**US-406 — progressive-disclosure restructure.** Order: banner → ⚙ Your-team panel → **status strip** → **pitch** →
**⚙ Players & lineup** (selection → card · ⚔️ Boot Battle · 👑 captain · 🔁 substitute · **bench order + Reorder
folded in**) → Transfer pointer → **⚙ Manage** expander (**flat** Rename + Set-whole-bench — expanders can't nest).

**Reuse everything** — `render_pitch` · `render_player_card`/`render_player_compare` · `substitute` · `set_captain`
· `move_bench_sub` · `set_bench` · `rename` · `apply_transfer` (now only on the tab). No analytics/engine change.

---

### ✅ Definition of Done
1. **Tests:** the 3-metric strip renders (Projected XI · Captain · Bench); one availability/price line (not 4);
   **no in-page Transfer** control on the edit view (the pointer is present; the Transfer *tab* still works);
   the ⚙ Players & lineup selection still drives card/captain/substitute; ⚙ Manage holds Rename + Set-bench.
   Update the My-Squad tests that assert the old in-page Transfer / 5 metrics. Full suite green + ruff.
2. **Manual smoke** (owner): the page is visibly shorter, pitch-led; the primary action is obvious; transfers via
   the tab; mobile no longer cramps.
3. **Docs:** this plan + retro; ADR-115; PROJECT_STATUS; the audit's Sprint-D row ticked (**audit complete**); memory.

### 📋 Sprint Review
*(filled at retro)*

### 🧠 Lessons
*(filled at retro)*
