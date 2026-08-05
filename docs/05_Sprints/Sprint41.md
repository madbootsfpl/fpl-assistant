# Sprint 041: Show what you optimised (squad-table xP) + a "best players" `ask` intent

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a display fix + a gate + a Phase-4 intent)
**Carried Over:** None (Sprint 040 closed clean)

> **Direction (owner's choice):** finish the "one metric" work *visually* — the squad table still shows
> **last-season points** while optimising **xP** (the exact confusion from Sprint 039/040) — **and** add
> one more Phase 4 intent. The season-gated work (full xMins / Data Hardening) is ~17 days out.

---

### 🔎 Verified at planning (the standing lesson)

- **Part A is a clean attach.** `squad`'s selected players carry `id`/`position`/`price`/`web_name`, and
  `decision_xp` gives xP (e.g. 19.4) + the xMins weight (→ 86 mins) per id — so the squad table can show
  **xMins + xP** (and a projected total) under `--objective xp`, instead of last-season `Pts`.
- **Part B's parser works.** A position + optional price-cap parse handled every probe:
  "best midfielders under £8m" → MID / £8m; "best forwards?" → FWD; "best value defenders" → DEF;
  "best keepers" → GK; "best players under 6m" → (all) / £6m; "best striker" → FWD.
- Still preseason (0 GWs); ClubElo up (intermittent). Both parts are preseason-buildable.

---

### 🧭 What's new — see the metric, and ask for the best

Sprint 040 made **xP** the one metric the tool *optimises*; this sprint makes it the one the squad view
*shows* (optimise on xP → display xP, with a projected total), closing the last display gap. And a new
grounded intent — **`ask "best <position> [under £Xm]"`** — gives the ranking/value views a
natural-language front, so a manager can hunt targets ("best midfielders under £8m") in plain English.

---

### 🎯 Sprint Goal

**Objective (Part A):** under `--objective xp`, the `squad` table shows **xMins + xP** columns and a
projected xP total (not last-season `Pts`); other objectives are unchanged. **(Part B):** a
`shortlist` intent — `ask "best <position> [under £Xm]"` — returns the top players by xP (position +
price filters), grounded + verified.

#### Success Criteria
- [ ] **Part A:** `squad … --objective xp` shows an **xMins** and **xP** column + a projected xP total;
      `--objective points`/`value`/`xgi` render as today (the `Pts` column)
- [ ] **Part B gate agreed (ADR-042)** — the shortlist intent: routing; position/price parsing (proven);
      what it returns (top-N by xP); grounding (`subjects` = listed players)
- [ ] `ask "best midfielders under £8m"` → a ranked table (xMins-weighted xP, position + ≤£8m),
      narration + the ✓ trust line; a clear message when nothing matches
- [ ] Reuses `decision_xp`, the shared table renderer, and `verify_grounding`
- [ ] Existing intents unchanged; existing 369 stay green
- [ ] Tests (squad xP display; the parser; the intent; routing precedence) + live smoke
- [ ] Docs: ADR-042 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-121 | **Squad table shows xP** (Part A) — under `--objective xp`, attach xP + xMins to the selected players; `render_squad` shows an `xMins`/`xP` column + a projected total; a clean fall-through for other objectives. Under ADR-041 (no new ADR). Tests + smoke | High | ✅ Done | 1 session |
| US-122 | **Gate.** The `shortlist` intent design (**ADR-042**): routing (`best <position>` / `best value`, after build_squad so "best squad" still builds); position + price parsing (proven); returns top-N by xP; grounding + a not-found message. Pressure-test the parse | Critical | ✅ Done | 0.5 session |
| US-123 | **`ask "best <position> [under £Xm]"`** (Part B) — parse position + price; rank the pool by `decision_xp`; a ranked detail table (reuse the xp/table renderer) + narration + ✓; `subjects`. Tests + smoke + docs | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-042 recorded + added to the ADR index — _US-122_
- [ ] Update Architecture changelog (squad-table xP; the shortlist intent) — _US-121/123_
- [ ] Update Handbook/README (`ask "best <position>"`; squad shows xP) — _US-123_
- [ ] Update PROJECT_STATUS — _US-123_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — squad xP display; the position/price parser; the intent + routing;
   existing **369** stay green; no new dependency.
2. **Manual smoke test done** — `squad --full --objective xp` shows xMins + xP + a projected total;
   `ask "best midfielders under £8m"` returns a sane ranked list + the ✓ line; a no-match message.
3. **Documentation updated & checked** — ADR-042 + index, Architecture, Handbook/README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Squad table xMins/xP columns under `--objective xp` | Changing the optimiser (ADR-041 stands) |
| A `best <position> [under £X]` shortlist intent | Ownership/differentials (needs `selected_by`; later) |
| Reuse `decision_xp`, the shared renderer, the verifier | An intent classifier (kept on the backlog) |
| Position + price parsing | Fuzzy team/fixture NL queries (later) |

**External Dependencies:** None beyond stored FPL data + the (optional) local LLM.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Squad table gets wide (xMins+xP+Pts) | Low | Under `--objective xp` show xMins/xP *instead of* Pts (a note points to `--objective points`) |
| "best" over-routing (e.g. "best squad") | Med | Route shortlist **after** build_squad; require a position word or "value"/"players"; else fall through |
| Ambiguous/absent position | Low | No position → all players; a clear message when nothing matches the filter |
| Squad projected total counts the bench | Low | Reuse the existing bench caveat note (ADR-012/014) |

---

### 🗝️ Gating decision (US-122 → ADR-042)

Settle before code — the parser is proven. Proposed (confirm/redirect at "start US-122"):

1. **Routing.** A `shortlist` intent, keyed on position words (`goalkeeper/keeper/defender/midfielder/
   forward/striker` + plurals + short forms) and `best value` / `best players`, checked **after**
   `build_squad` (so "best squad/XI" still builds) and before `compare`.
2. **Parse.** Position → `GK/DEF/MID/FWD` (else all); an optional price cap from "under £Xm" / "£Xm".
3. **Decide.** Rank the available pool by the unified `decision_xp` (xMins-weighted; the same xP
   everywhere), filter by position + `price ≤ cap`, take the top N (≈8). `subjects` = the listed players;
   facts = the top few humanised. A clear message when the filter matches nobody.
4. **Grounded + optional.** Reuse `verify_grounding` (✓/⚠) and the shared table renderer; degrade
   without the LLM. *(Alternative Part B if preferred: an intent classifier, or a fixtures/FDR intent.)*

**Worked example (to run at the gate):** "best midfielders under £8m" → MID ≤£8m top-8 by xP + ✓;
"best keepers" → GK; "best defender under £4m" → maybe empty → a clear message.

---

### 📝 Session Progress Log

- **US-121 (squad table shows xP) ✅** — Finishes the "one metric" work visually: under `--objective xp`
  (the default), the `squad` table now shows **`xMins` + `xP`** columns and a **projected xP total**
  instead of last-season `Pts` — the confusion from Sprint 39/40 is gone (optimise xP → *show* xP).
  `render_squad` branches on `show_xp` for the header/divider/rows/total/subtotal/notes; `cmd_squad` and
  `_decide_build_squad` attach `xp` + `minutes_weight` to the selected players from `decision_xp`. Other
  objectives (`points`/`value`/`xgi`) render exactly as before. **+1 test** (xp → xMins/xP + projected
  total; points → Pts, no xMins) → suite **369 → 370**; ruff clean; no new dependency; no new ADR
  (display completion of ADR-041). **Live smoke:** `squad --full` → *projected 305.8 xP* (the planning
  figure); `--objective points` → the Pts column; `ask "build me a squad"` shows xP too.
- **US-122 (gate) ✅** — Recorded **ADR-042**, parse + ranking proven on the live DB: "best midfielders
  under £8m" → Mbeumo (23.3)/Gibbs-White (22.2)/Rice…; "best forwards" → Haaland/Watkins…; "£4m DEF" →
  a thin honest list; "best value GK" ranks by xP/£m (Raya vs Roefs flips). Settled: a `shortlist`
  intent routed on **position words + "best value"/"best players"**, after `build_squad` (so "best
  squad" still builds) and before `compare`; parse = position → GK/DEF/MID/FWD (else all) + a "under
  £Xm" price cap + a `by_value` toggle; rank the available pool by `decision_xp` (or xP/£m), top ~8;
  grounded + a no-match message. ADR-042 indexed.
- **US-123 (shortlist intent) ✅** — Routed `shortlist` (position words + "best value"/"best players",
  after build_squad so "best squad" still builds). `_shortlist_query` parses position → GK/DEF/MID/FWD
  (else all) + a "under £Xm" cap + a `value` toggle; `_decide_shortlist` filters the available pool
  (before the xP calc — efficient + a clean no-match message), ranks by `decision_xp` (or xP/£m for
  value), top 8; new `ui/shortlist.py` table; grounded (`subjects` = the listed players). **+4 tests**
  (routing precedence; the parser; the no-match message; the renderer) → suite **370 → 374**; ruff
  clean; no new dependency. **Live smoke:** `ask "best midfielders under £8m"` → Mbeumo/Gibbs-White/…
  + ✓; `ask "best value goalkeepers"` ranks by xP/£m (Roefs above Pickford); `ask "best forward under
  £4m"` → a clear no-match message; `ask "best squad …"` still builds. Docs: Architecture, README.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories. **US-121** — the `squad` table shows **xMins + xP + a projected
  total** under `--objective xp` (finishing "one metric" visually). **US-122** — ADR-042 (the shortlist
  intent, parse + rank proven). **US-123** — `ask "best <position> [under £Xm]"`, ranked by the unified
  xP (or xP/£m for "value"), grounded. Tests 369 → **374**; one ADR; **no new dependency**. `ask` now
  answers seven questions.
* **Carried Forward:** None. (Ownership/differentials — "best low-owned MID" — is a later intent.)
* **Key Artifacts / Decisions:** ADR-042; `render_squad` xP columns; the `shortlist` intent
  (`_shortlist_query` + `_decide_shortlist` + `ui/shortlist.py`); the `by_value` (xP/£m) toggle.

#### Retrospective
* **What Went Well?**
  - **Closed the loop the owner opened.** The squad now *shows* the metric it *optimises* — the
    Pts-vs-xP mismatch that started three sprints of "trust the numbers" work is finally gone on screen.
  - **Composition, seventh time.** The new intent is `decision_xp` + a filter/sort + the shared renderer
    + the verifier — no new data, no new dependency. The unified xP keeps paying dividends.
  - **A small real-vocabulary win.** The gate surfaced that "best value" means xP-*per-£m*, not raw xP —
    a one-line toggle that matches how managers actually talk.
  - **Filter before compute.** Reordering `_decide_shortlist` (filter the pool before the xP calc) made
    the no-match path cheap *and* unit-testable without fixtures — a nice tidy that fell out of writing
    the test.
* **What Could Be Improved?**
  - **Routing keywords keep growing** (seven intents; "forward"/"value" are common words). It still
    holds, but an intent classifier is now a fair backlog item if this continues.
  - **Preseason xP** makes some shortlists thin/optimistic (£4m defenders); honest, improves at GW1.
* **Lessons Learned?**
  - Finish a fix *visually*, not just in the model — the display is where the user forms trust.
  - Match the tool's vocabulary to the domain's ("value" = per-£m) — small touches read as understanding.
  - Order operations so the cheap/early exit is also the testable one.
* **Action Items for Next:**
  - [ ] (Backlog) an intent classifier if intents keep growing; an ownership/differentials intent.
  - [ ] (GW1) partial-season baseline tuning; the full Phase-5 xMins.
  - [ ] Keep the gate probe broad; keep the 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4 (an intent classifier / differentials / a chat
mode), the web UI (Phase 2), or wait for GW1 for Data Hardening + the full Phase-5 xMins.

**Completion Date:** 2026-08-05
**Final Notes:** One metric, now optimised *and* shown; `ask` reached seven grounded intents. The
three-sprint "trust the numbers" arc (sane xP → one metric → show the metric) is complete. Sprint
outcome: **Successful** — 3/3 stories, zero roll-over, DoD held (41st).
