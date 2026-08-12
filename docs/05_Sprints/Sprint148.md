# Sprint 148: MADBOOTS vocabulary — Edge · Risk · Radar (ADR-107)

**Dates:** 2026-08-12
**Status:** ✅ Complete — US-363 + US-364 (ADR-107). 972 tests (unchanged; display-only)
**Capacity:** ~1 short session (display-label sweep + docs)
**Carried Over:** none

> **Direction (ADR-107):** turn the last generic analytics labels into a small MADBOOTS lexicon — **clean, modern,
> not gimmicky**. Adopt **Radar** (players to watch) and **Edge** (the "why"), keep **Risk** (fix a Risks/Risk
> inconsistency) and **Captain**. **Defer "Pick"** — "AI Tips" is a whole-week plan, so "Pick" would mis-size it
> (owner's call). **Display-only** — no analytics, no `decision_xp`, no code identifiers touched.

---

### 🔎 Verified at planning (on the code — surface map)

- **"Why"** renders in **two** paths: `src/ui/explain.py:27` (`lines.append("Why")`, shown in the Squad Lab build
  explanation + Ask/CLI) **and** `src/web_streamlit/captain_card.py:67` (the card heading HTML). Both need the swap.
- **"Risk"** is **inconsistent**: `"Risk"` (singular) in `ui/explain.py:31` vs `"Risks"` (plural) in
  `captain_card.py:70`. Standardise on **"Risk"** (matches the Help copy at `8_Help.py:107`).
- **"Target by fixtures"** lives as `st.subheader("🎯 Target by fixtures")` at `pages/2_Fixtures.py:98` (**no tab of
  its own** — a section inside Fixtures) + a Help mention at `pages/8_Help.py:95`. The 🎯 emoji is **reused** for
  set-piece free-kicks elsewhere (`analytics/crowd.py`, `8_Help.py:47`) — **do not** find/replace the emoji; target
  the exact strings.
- **Code identifiers stay:** `render_ai_tips`, `analytics.target_by_fixtures`, the `target_pos/target_max_price/
  target_sort` session keys, and the `elif view == "..."` branch strings (label = logic on the My Squad control) are
  **not** touched by this sprint.
- **"AI Tips" and "Captain" unchanged** — AI Tips deferred (ADR-107 §5); Captain already on-brand.

---

### 🎯 Sprint Goal

The `explain` output and captain card read **Edge / Risk**; the Fixtures shortlist reads **🎯 Radar** — everywhere
each appears, consistently — with **no** behaviour change and the suite green.

#### Success criteria
- [ ] **US-363 (Edge + Risk)** — `Why` → **`Edge`** in `ui/explain.py` **and** `captain_card.py`; `Risks` →
      **`Risk`** in `captain_card.py` (reconcile to the singular used in `ui/explain.py` + Help). Update the tests
      that assert `"Why"` / `"Risks"` to the new wording. No other output change.
- [ ] **US-364 (Radar)** — `🎯 Target by fixtures` → **`🎯 Radar`** at `pages/2_Fixtures.py:98`; keep the descriptive
      caption (tweak to name "radar" if it reads naturally); update the Help mention (`8_Help.py:95`). The
      `target_by_fixtures` function + `target_*` session keys are **unchanged**. Update any test asserting the old
      subheader.
- [ ] **No drift** — display-only; no analytics / `decision_xp` / code-identifier change; ruff clean; the suite green.
- [ ] **Docs** — PROJECT_STATUS; Architecture (changelog line); Backlog (mark branding-E's Edge/Risk/Radar shipped,
      "Pick" deferred); memory. ADR-107 already written (the gate).

---

### 🧭 Design sketch

Two tiny, surgical edits — each a label swept across every surface it appears on:

```
US-363  ui/explain.py:27        "Why"   -> "Edge"
        captain_card.py:67      "Why"   -> "Edge"
        captain_card.py:70      "Risks" -> "Risk"
        tests: assert "Edge"/"Risk" (was "Why"/"Risks")

US-364  pages/2_Fixtures.py:98  "🎯 Target by fixtures" -> "🎯 Radar"
        pages/2_Fixtures.py:99  caption: name "your radar" if it reads clean
        pages/8_Help.py:95      "🎯 Target by fixtures" -> "🎯 Radar"
        tests: assert "Radar" (was "Target by fixtures")
```

**Definition of Done (3-part):** automated tests updated + green; a manual smoke (open the captain card → "Edge/Risk";
open Fixtures → "🎯 Radar"); docs updated.

---

### 📋 Sprint Review

**Delivered — both stories, display-only, 972 tests green (unchanged; ruff clean).**

- **US-363 (Edge · Risk)** — `Why`→`Edge` and `Risks`→`Risk` swept across **all four** surfaces that render the
  explanation block: `ui/explain.py` (CLI/Ask/Squad Lab), `web/captain_card.py`, `ui/captain.py` (CLI captain card),
  and `ui/gameweek.py` (the inline per-recommendation label in **AI Tips**). The planning map found only two of these
  — a `grep src/` for the heading strings caught the other two. Tests + comments updated; the `facts["why"]`
  **grounding key is unchanged** (it's a code identifier — grounding matches fact *values*, not keys).
- **US-364 (Radar)** — `🎯 Target by fixtures` → `🎯 Radar` on the Fixtures page (caption now names the radar) + the
  Help mention + the AppTest assertion. `analytics.target_by_fixtures` and the `target_*` session keys untouched.

**Held per owner:** "AI Tips" and "Captain" unchanged; **"Pick" deferred** (AI Tips is a whole-week plan). Owner
noted *"another pass to tweak later"* — revisit the lexicon once seen in the browser.

**Definition of Done:** ✅ tests updated + green · ✅ manual smoke (rendered Edge/Risk on CLI + web; AppTest confirms
the 🎯 Radar subheader) · ✅ docs (ADR-107 gate; PROJECT_STATUS; Architecture; Backlog; memory).

### 🧠 Lessons
*(see `Sprint148_Lessons_Learnt.md`)*
