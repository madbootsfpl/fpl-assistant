# Sprint 054: Streamlit polish — charts + Transfer & Build pages

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2–3 working sessions (two charts + two interactive decision pages + docs)
**Carried Over:** None (Sprint 053 closed clean)

> **Direction (owner):** *more Streamlit polish.* Build on the graduated edge (ADR-052): add **charts**
> (Fixtures FDR bar, Players price-vs-points scatter) and the two big interactive FPL features as pages —
> **Transfer** (XI-aware swaps for a saved squad) and **Build** (the optimiser under a budget). All
> **reuse the existing engines** — still a thin edge over the one core.

---

### 🔎 Verified at planning (the data + engines are ready; it's UI, not new analytics)

- **Chart data is clean.** `team_fdr` gives team → avg FDR (LIV 2.6 · TOT/MUN 2.8 …) for a **bar**;
  players carry price + total_points for a **scatter** (spot value visually). Streamlit's **native**
  `st.bar_chart` / `st.scatter_chart` render these directly — no charting library code.
- **The decision pages reuse proven engines.** `suggest_transfers` returns XI-aware swaps for **TS**
  (*Ampadu → Zubimendi +9.3* …); `select_squad` returns an **Optimal** 15 at £100.0m. Nothing new to
  compute — the pages wire sliders → the engine → a renderer.
- **Testing is proven** — Streamlit `AppTest` runs each page headlessly (set inputs, assert output).
- **Thin edge, unchanged core.** New pages import the engine/renderers; **no `src/` core change**; the
  two-edge guardrail still holds; FastAPI stays frozen.
- **No new ADR** — this is UI polish over the settled Streamlit edge (ADR-052), like US-153's FastAPI
  pages. The one decision (scope) is settled: **charts + Transfer + Build**.
- Preseason (GW1 2026-08-21).

---

### 🧭 What's new — see it, and decide with it

The Streamlit edge grows from "view the data" to "decide with it": **charts** make fixtures/value visual,
and two pages expose the flagship engines interactively — **Transfer** (pick a squad, a bank slider →
ranked XI-aware swaps) and **Build** (budget + archetype sliders → the optimal 15). Same discipline: the
analytics decide; the page just wires controls to the engine.

---

### 🎯 Sprint Goal

**Objective:** the Streamlit edge gains two **native charts** (Fixtures FDR bar, Players price-vs-points
scatter) and two **interactive decision pages** — **Transfer** (`suggest_transfers`, squad + bank/count)
and **Build** (`select_squad`, budget + archetypes) — all reusing the engines, tested via `AppTest`, the
core unchanged and FastAPI frozen.

#### Success Criteria
- [ ] **Fixtures** page gains a **bar chart** (teams by avg FDR) alongside the table
- [ ] **Players** page gains a **scatter** (price vs points, coloured by position) alongside the table
- [ ] A **Transfer** page — pick a saved squad + a **bank** slider (+ a count for a plan) → the ranked
      XI-aware swaps (reuse `suggest_transfers` / `suggest_transfer_plan` + `render_transfers`)
- [ ] A **Build** page — a **budget** slider + **archetype** controls (cheap / premium / differential) →
      the optimal 15 (reuse the build engine; grounded + rendered)
- [ ] Tests — `AppTest` per new/changed page (renders; a chart present; the decision pages drive
      controls → an answer)
- [ ] The core is unchanged; **FastAPI (`src/web`) frozen**; the two-edge guardrail still passes
- [ ] Docs: Architecture changelog, Handbook Ch 12 (the new pages/charts), README (pages), PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-159 | **Charts** — Fixtures FDR **bar** + Players price-vs-points **scatter** (native `st.*_chart`), each alongside the existing table. `AppTest` tests. Architecture changelog | High | ✅ Done | 0.5–1 session |
| US-160 | **Transfer page** — `pages/5_Transfer.py`: squad `selectbox` + **bank** slider (+ count) → XI-aware swaps via `suggest_transfers`/`suggest_transfer_plan` + `render_transfers`. `AppTest` tests | High | ✅ Done | 1 session |
| US-161 | **Build page + docs** — `pages/6_Build.py`: **budget** slider + **archetype** controls → the optimal 15 (reuse the build engine). `AppTest` tests + docs (Handbook Ch 12, README, PROJECT_STATUS) | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] Update Architecture changelog (Streamlit charts + Transfer/Build pages) — _US-159_
- [x] Update Handbook Ch 12 (the new pages) + README (pages list) — _US-161_
- [x] Update PROJECT_STATUS — _US-161_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — `AppTest` renders the charts (Fixtures/Players) and drives the decision
   pages (Transfer: squad + bank → swaps; Build: budget/archetypes → a squad); the existing **436** stay
   green; the core + the FastAPI edge are unchanged; the two-edge guardrail passes.
2. **Manual smoke test done** — `python -m src.web_streamlit`: the charts render, the Transfer page shows
   XI-aware swaps for a squad (bank slider changes them), the Build page returns an optimal 15 as the
   sliders move; without Ollama the grounded pages still work.
3. **Documentation updated & checked** — Architecture, Handbook Ch 12, README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Two charts (Fixtures bar, Players scatter) | Big dashboards / custom charting libraries (native `st.*_chart` only) |
| Transfer + Build pages reusing the engines | A **Compare** / **Captain** page — a later polish round |
| `AppTest` tests; docs | Any change to the engine/core or the frozen FastAPI edge |
| Interactive controls (sliders, selects) | Writes / saving squads from the web; auth |

**External Dependencies:** None new (`streamlit` already web-only). The CLI + the frozen FastAPI edge are
untouched.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| A page reaches into the engine and drifts from the CLI logic | Med | Reuse the *same* functions the CLI uses (`suggest_transfers`, `select_squad`, `render_*`); no new analytics |
| `AppTest` can't drive a slider/chart | Low | Keep controls `AppTest`-drivable (set slider/selectbox, assert output); a chart just needs to render |
| Build page performance (ILP per slider move) | Low | The optimiser is ~fast; a build runs on submit; note if any lag |
| The core/edge boundary slips | Low | New pages import the engine only; the two-edge guardrail test stays green |

---

### 🗝️ No gate this sprint

UI polish over the settled Streamlit edge (ADR-052) — **no ADR** (the framework, structure and adoption
are decided). The scope was the only real call and is settled (**charts + Transfer + Build**). Charting
uses Streamlit's **native** `st.bar_chart` / `st.scatter_chart` (no new library). Each page reuses the
same engine + renderer the CLI does.

---

### 📝 Session Progress Log

- **US-159 ✅** — **Charts** on the existing pages, native (no charting library): **Fixtures** gains a
  horizontal **`st.bar_chart`** of teams by avg FDR; **Players** gains a **`st.scatter_chart`** of price vs
  points, coloured by position, over the whole filtered set (the value landscape) beside the ranked table.
  - **Tests (437 total, +1):** the Fixtures/Players page tests assert a `vega_lite_chart` renders when data
    is present (native charts surface as vega-lite; `AppTest` has no named chart accessor, so
    `at.get("vega_lite_chart")` is used); pages with no local data still show the info branch.
  - **Smoke:** `python -m src.web_streamlit` boots clean (200, no errors) with the chart pages.
  - **Docs:** Architecture §12 changelog (Sprint 054 — charts + the coming Transfer/Build pages). _No ADR
    (UI over the settled edge)._
- **US-160 ✅** — The **Transfer** page (`pages/5_Transfer.py`): a squad `selectbox` + a **bank** slider +
  a **count** slider (1 → a shortlist, 2–3 → a coordinated plan) → the ranked swaps, reusing the SAME
  `decision_xp` / `suggest_transfers` / `suggest_transfer_plan` + `render_transfers`/`render_transfer_plan`
  the CLI's `transfer` uses (so the web can't drift). XI-aware by default (ΔXI).
  - **Tests (438 total, +1):** the page renders (swaps, a "no upgrades" note, or the no-squads info) and
    survives moving the bank slider; hermetic (works with or without local saved squads).
  - **Smoke (`AppTest`, real DB):** selecting **TS** produces *Ampadu → Zubimendi +9.3* … (the ΔXI column),
    byte-identical to the CLI; **RoboTS** (xp-optimal) correctly shows "no positive-gain transfers"; count
    = 2 switches to the plan header.
- **US-161 ✅** — The **Build** page (`pages/6_Build.py`): a **budget** slider + **archetype**
  number_inputs (cheap ≤£4.5m · premium ≥£9m · differential ≤5% owned) → a plain-English request handed to
  the **same `build_squad` `ask` intent** the CLI/`ask` use (so it runs the exact optimiser + archetype
  constraints + the XI/bench breakout, grounded). Only the archetypes you set are included (0 → no
  constraint).
  - **Tests (439 total, +1):** the page renders a squad (or the no-data note); moving an archetype control
    rebuilds without crashing. Verified the parser handles slider-built queries (budget 95, archetypes
    3/2/1; zeros → no bands).
  - **Smoke (`AppTest`, real DB):** the page renders the optimal 15 (the XI/bench breakout); server boots
    clean with all **6 pages**.
  - **Docs:** README (the full pages list — scatter/bar/Transfer/Build), Handbook Ch 12 (the new
    pages/charts + "pages are sliders wired to the engine"), PROJECT_STATUS (Web-UI pages, Tests 439).

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the Streamlit UI grew from *view the data* to *decide with it*: two **charts**
(Fixtures FDR bar, Players price-vs-points scatter) and two interactive **decision pages** — **Transfer**
(bank slider → XI-aware swaps) and **Build** (budget/archetype sliders → the optimal 15). All six pages
reuse the same engines the CLI does. **439 tests** (was 436, +3); **52 ADRs** (no new ADR — UI polish over
the settled edge). The core + the frozen FastAPI edge unchanged; the two-edge guardrail holds.

**Delivered**
- **US-159** — native charts (`st.bar_chart` on Fixtures, `st.scatter_chart` on Players).
- **US-160** — the Transfer page (`suggest_transfers`/`suggest_transfer_plan` + `render_transfers`).
- **US-161** — the Build page (the `build_squad` `ask` intent from sliders) + docs.

**What went well**
- **Every page was sliders wired to an engine** — near-zero new analytics; the Streamlit view of a
  transfer/build is *byte-identical* to the CLI (same functions + renderers), so it can't drift.
- **Charts came free and native** — `st.bar_chart`/`st.scatter_chart` on the existing data, no charting
  library.
- **The reuse styles both worked** — Transfer via the engine directly (for the bank slider); Build via an
  NL query to the `ask` intent (the thinnest path, reusing the whole build pipeline).
- **Hermetic tests despite local-only saved squads** — assert structure / drive controls, don't depend
  on which squads exist.

**Challenges / how they were handled**
- **`AppTest` has no chart accessor** — native charts render as `vega_lite_chart`; asserted via
  `at.get("vega_lite_chart")` (a bit of spelunking).
- **Slider values → an NL request** (Build) — built the query conditionally (only archetypes > 0) and
  verified the parser handles it (budget/cheap/premium/differential; zeros → no bands).
- **Default squad is xp-optimal (RoboTS)** — the Transfer page correctly shows "no positive-gain
  transfers" for it; TS shows real swaps. Honest, not a bug.

**Carried forward:** None. *(Optional next: a Compare/Captain page; or move to Data Hardening post-GW1.)*
