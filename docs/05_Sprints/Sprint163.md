# Sprint 163: UX Sprint D — My Squad density redesign (US-404–406)

**Dates:** 2026-08-17
**Status:** ✅ Complete — US-404–406 (ADR-115), display/IA only. 1005 → 1007 tests. **Completes the UX audit
(A·B·C·D).**
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

**Delivered — the golden page, decluttered. ~350-line function roughly halved, no feature loss.**
- **US-404 compact status:** 5-across metrics → a **3-number strip** (Projected XI · Captain · Bench); the 4 stacked
  captions → **one availability + price line** (Unavailable/Doubtful folded into the flagged line).
- **US-406 progressive disclosure:** pitch-led; the primary block renamed **⚙ Players & lineup** (card · Boot
  Battle · captain · substitute · bench reorder); **Rename + Set-whole-bench** fold into one **flat ⚙ Manage**
  expander (expanders can't nest).
- **US-405 transfers consolidated on the Transfer tab.** The edit view loses its in-page transfer → a pointer.
  **Correction:** verification showed the in-page transfer was the **manual** out→in picker, **not** a duplicate of
  the tab's **suggested** transfers — so it was **moved** to the Transfer tab (now: suggested **+** a "✋ Manual
  transfer" expander), not deleted. The 5 manual-transfer tests repointed to the tab.
- **Tests:** +2 (pointer-not-picker · ⚙ Manage) and updated the metric/transfer tests. **1007 total.** **The UX
  audit (A·B·C·D) is complete.**

**Owner smoke (post-deploy):** My Squad is visibly shorter + pitch-led; the 3-number strip + one status line;
transfers (suggested *and* manual) on the Transfer tab; Rename/Set-bench under ⚙ Manage; mobile no longer cramps.

### 🧠 Lessons

- **"Duplicate" was wrong — verify before you delete.** The audit (and my plan) called the in-page transfer a
  duplicate; reading `render_transfer` showed it's the **suggested** tool while the in-page one is the **manual**
  picker. Deleting it would have removed real capability — the fix was to **move** it. Twice this audit (Ask
  markdown, this) the naive reading was wrong; reading the code first saved a regression.
- **Progressive disclosure ≠ hiding features.** Everything the page did, it still does — grouped and collapsed.
  The win is *legibility*, not fewer capabilities.
- **Streamlit can't nest expanders** — ⚙ Manage holds Rename + Set-bench as **flat** subsections; the Your-team
  panel (which owns an expander) stays top-level under the banner. Design around the constraint.
- **A big single-function diff rides on its tests.** ~350 lines reorganised; the ~20 My-Squad tests caught every
  moved/removed control — repoint them to where the feature went, don't just delete.
