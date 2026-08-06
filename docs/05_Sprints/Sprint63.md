# Sprint 063: Tester-feedback polish — centre the My Squad pitch photos

**Dates:** 2026-08-06
**Status:** ✅ Complete (1/1 story; retro done)
**Capacity:** ~0.5 session (a small, robust UI polish) — a lightweight feedback-polish cycle
**Carried Over:** None (Sprint 062 shipped both feature requests)

> **Direction (owner/tester feedback):** *"Could we centre-align the images on the My Squad view? They're
> currently left-aligned."* A focused polish on the Sprint-062 pitch card-grid. Room to fold in any further
> feedback that lands before close (triaged via `docs/00_Project/Feedback_Log.md`).

---

### 🔎 Verified at planning (the fix is robust + native)

- **The cause:** in `src/web_streamlit/pitch.py` `_card`, the photo is `st.image(url, width=54)` inside a
  bordered container in a position-row column — Streamlit **left-aligns** it by default.
- **A robust native fix exists** (no custom CSS): wrap the image in a **nested `st.columns([1, 2, 1])`** and
  place it in the **middle** column → centred. Probed under `AppTest` inside the pitch's row columns +
  container (level-2 nesting) → **renders without error** in Streamlit 1.61 (one level of nesting is
  allowed). Keeps the "robustness first" call — themeable, headless-testable, no HTML/CSS.
- **Scope-only-the-photo:** the ask is the *images*; native text-centring would need custom HTML, so the
  card text stays as-is (left) unless the owner wants otherwise.

---

### 🎯 Sprint Goal

**Objective:** centre the player photos in the My Squad pitch cards, using a robust native layout (nested
columns) — no custom CSS, no core change. Fold in any further tester feedback that arrives.

#### Success Criteria
- [ ] **Photos centred** — each pitch card's photo sits centred (a nested `[1, 2, 1]` sub-column), on the
      XI rows and the bench row
- [ ] **Robust** — native `st.columns` only (no custom HTML/CSS); renders headlessly under `AppTest`; the
      rest of the card (name · £ · xP · opponent · flags · (C)) unchanged
- [ ] **No regressions** — the pitch still lays out the XI + bench; the edit controls + legality banner +
      download unaffected; existing **504** stay green
- [ ] Feedback triaged in `docs/00_Project/Feedback_Log.md` (done at planning)
- [ ] Docs: PROJECT_STATUS note (no ADR — a UI polish over the settled edge)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-188 | **Centre the My Squad pitch photos** — wrap the `_card` photo in a nested `st.columns([1,2,1])` middle column so it centres; keep everything else. `AppTest` still green + a render check | Medium | ✅ Done | 0.5 session |

#### Technical Tasks & Maintenance
- [x] `pitch.py` `_card`: centre the photo via a nested column — _US-188_
- [x] PROJECT_STATUS note — _US-188_
- [ ] (If more feedback lands) triage into `Feedback_Log.md` + add stories here

---

### ✅ Definition of Done (this sprint)

1. **Automated tests pass** — the My Squad pitch still renders (≥11 cards, no dataframe); the existing
   My Squad tests (banner/download/swap/rename/bench) stay green; **504** total stay green.
2. **Manual smoke test done** — the pitch photos are visibly centred in their cards (XI + bench); the
   layout + edit controls still work.
3. **Documentation updated & checked** — PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Centre the pitch **photos** (native nested columns) | A custom-CSS pitch / full FPL-shirt look |
| Any further small tester-feedback polish that lands | Centring/​restyling card **text** (needs custom HTML) |
| A `Feedback_Log.md` triage entry | Any core / analytics / xP change |

**External Dependencies:** none. Works now.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Nested columns hit Streamlit's nesting limit | Low | Verified at planning (level-2 renders in 1.61); one level of nesting is allowed |
| Centring shifts the layout awkwardly on narrow cards | Low | `[1,2,1]` keeps the photo proportionate; smoke-check on the live app |

---

### 🗝️ Gating note — no ADR

A UI polish over the settled edge (Sprint 054/055/062 precedent). **No ADR.** The robust approach (nested
columns, not custom CSS) is settled here and verified.

---

### 📝 Session Progress Log

- **US-188 ✅** — **Centre the My Squad pitch photos.** In `pitch.py` `_card`, the photo is now placed in
  the middle of a nested `st.columns([1, 2, 1])` — centred within each card, on the XI rows and the bench.
  Robust + native (no custom CSS); the rest of the card (name · £ · xP · opponent · flags · (C)) and all
  edit controls are unchanged. Smoke: My Squad renders 15 centred cards, no nesting error, banner + edit +
  download intact; **504** tests still green (the existing pitch test — ≥11 cards, no dataframe — holds);
  `ruff` clean. (Alignment is a visual detail `AppTest` can't assert, so no new test — verified by smoke.)

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the first **tester-feedback item** shipped: the My Squad pitch photos are now
centred, via a robust native fix.

**Delivered**
- **US-188 ✅** — centred the pitch-card photos with a nested `st.columns([1, 2, 1])` (no custom CSS);
  the card content + edit controls unchanged.

**Verification** — 504 tests green (no change; the existing pitch test still holds), `ruff` clean. Smoke:
15 centred cards, no nesting error, banner + edit + download intact.

**Process** — the item went through the loop we built: logged + triaged in `Feedback_Log.md` (🟡 polish →
US-188), then fixed. A clean first turn of the feedback cycle.

**Carried forward** — none. Standing markers unchanged: **GW1 (2026-08-21)** (US-185 trends intent +
threshold calibration + Data Hardening) and the **tester-feedback loop** (ongoing).

**What went well** — verifying the nested-columns approach *before* planning meant the "robustness first"
constraint was met without guesswork (native, no CSS). A tiny, well-scoped feedback turn — logged, fixed,
closed — is exactly what the Sprint-059 loop was for.

**What to watch** — alignment is visual, so it's smoke-verified, not unit-tested (AppTest can't assert
centring); worth a quick eyeball on the live app after redeploy.

**Lessons captured:** `docs/05_Sprints/Sprint63_Lessons_Learnt.md`.
