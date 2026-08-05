# Sprint 052: A Streamlit spike — one engine, two edges, then decide

**Dates:** 2026-08-05
**Status:** ✅ Complete (2/2 stories; retro done)
**Capacity:** ~2 working sessions (a spike build + a head-to-head comparison + a decision ADR)
**Carried Over:** None (Sprint 051 closed clean)

> **Direction (owner):** a **spike, not a pivot.** After the FastAPI slice (Sprint 051), the owner is
> weighing *"learn the how of web design (FastAPI/HTML) vs learn to ship fast with a 3rd-party tool
> (Streamlit/Gradio)"*. Rather than argue it, **build a minimal Streamlit edge over the same engine,
> compare it head-to-head with FastAPI on the axes that matter, and record the verdict as an ADR** — the
> project's "decide on real evidence" discipline, applied to a strategy question.

---

### 🔎 Verified at planning (the spike is feasible; the trade is real)

- **Streamlit installs on Python 3.14** — `streamlit 1.61.1` resolves with cp314 wheels (pyarrow 24,
  pandas 3, numpy 2.5, altair, protobuf, pydeck…). Not blocked. *(Gradio 6.22 also resolves — a fallback
  if a conversational-only surface is preferred.)*
- **The reuse path is already proven.** A Streamlit script calls the same `ask.answer` / `decision_xp` /
  `rank_players` the FastAPI edge and the CLI do — the engine doesn't change; only the edge does.
- **The trade is concrete, and measured:** *light code, heavy deps.* Streamlit pulls **~22 packages** vs
  **~5** for FastAPI + Jinja. That dependency weight is a real axis for a project that prizes a tiny
  footprint — so the spike keeps Streamlit **out of the runtime** (`spikes/`, not `src/`; not in
  `requirements.txt`) until/unless the decision adopts it.
- **This is a spike (evidence → decision), so the gate comes *last*** — like soccerdata (spike →
  ADR-016) and the LLM narration spike (→ ADR-033). Throwaway code is fine; the deliverable is a
  **measured comparison + an ADR verdict**, not a production feature.

---

### 🧭 What's new — feel the difference, then choose

A minimal **Streamlit edge** in `spikes/052-streamlit/` over the same engine (the interactive `ask` box +
a data view), so the owner can *feel* Streamlit's interactivity and code density against the FastAPI
slice — then a head-to-head on learning, effort, interactivity, deps and architecture fit decides where
the web track invests.

---

### 🎯 Sprint Goal

**Objective:** a working, minimal Streamlit edge over the analytics/`ask` (throwaway, in `spikes/`); a
**measured head-to-head** vs the FastAPI edge on agreed axes; and a **decision recorded as ADR-051** — the
tool for the web track going forward, and the fate of the spike code (graduate / keep / discard). The
core and the CLI are untouched; the 429 tests stay green.

#### Success Criteria
- [ ] A minimal Streamlit app (`spikes/052-streamlit/`) reusing the engine — an **`ask`** box (with the
      ✓/⚠ trust line) + at least one data view (players and/or fixtures); runs via `streamlit run`
- [ ] Streamlit installed **spike-only** (a dev note, **not** added to `requirements.txt` runtime)
- [ ] The engine/core is **unchanged** — no `src/` edits beyond none; the spike imports the engine
- [ ] A **head-to-head comparison** (a table) on: learning value · lines of code for the same feature ·
      interactivity (filters/charts/chat) · dependency footprint · architecture fit · look & feel
- [ ] **ADR-051** — the verdict: the tool for the web track (FastAPI polish vs Streamlit vs Gradio), the
      rationale, and the spike's fate (graduate to `src/` / keep as a spike / discard)
- [ ] The existing **429** tests stay green (the spike touches nothing in the core)
- [ ] Docs: ADR-051 + index; the Roadmap/Backlog note the web-track decision; PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-154 | **Build the Streamlit spike** — `spikes/052-streamlit/app.py`: the `ask` box (reusing `ask.answer` + the trust line) + a data view (players/fixtures), over the same engine; install Streamlit spike-only; capture LOC + interactivity notes + the measured dep footprint. Manual smoke (`streamlit run`) | High | ✅ Done | 1 session |
| US-155 | **Compare + decide (ADR-051)** — a head-to-head table (Streamlit vs FastAPI) on the agreed axes; write **ADR-051** (the web-track tool + rationale + the spike's fate); update Roadmap/Backlog + PROJECT_STATUS | Critical | ✅ Done | 0.5–1 session |

#### Technical Tasks & Maintenance
- [x] ADR-051 recorded + added to the ADR index — _US-155_
- [x] Roadmap notes the web-track decision — _US-155_
- [x] Update PROJECT_STATUS — _US-155_

---

### ✅ Definition of Done (this sprint — a spike)

Adapted for a spike (evidence → decision, not a production feature):
1. **The spike runs** — `streamlit run spikes/052-streamlit/app.py` serves the `ask` box + a data view,
   reusing the engine; the comparison axes are **measured on real data** (LOC, deps, an interactivity
   demo). The existing **429** tests stay green; the core is unchanged (Streamlit is spike-only, not a
   runtime dependency).
2. **The decision is recorded** — **ADR-051**: the tool for the web track, the head-to-head evidence, and
   the spike's fate. Honest either way (adopt Streamlit / stay FastAPI / a Gradio surface).
3. **Documentation updated & checked** — ADR-051 + index, Roadmap/Backlog (the decision), sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A throwaway Streamlit edge in `spikes/` + a measured comparison + ADR-051 | Porting the whole FastAPI UI to Streamlit (that's a *later* sprint, if adopted) |
| Reuse the engine (`ask`/analytics) unchanged | Any `src/` / core change; a new runtime dependency |
| Streamlit installed spike-only (a dev note) | Adding Streamlit to `requirements.txt` runtime (only if adopted) |
| The `ask` box + 1–2 data views (enough to compare) | Deployment/hosting; auth; charts beyond a quick interactivity demo |

**External Dependencies:** Streamlit (spike-only; resolves on 3.14). The CLI + the FastAPI edge are
untouched.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| The spike bleeds into `src/` prematurely | Med | It lives in `spikes/052-streamlit/`; nothing in `src/` changes; the guardrail test still passes |
| Heavy dependency footprint (~22 pkgs) | Med (the point) | Spike-only; not in `requirements.txt`; the weight is *recorded* as a comparison axis, not adopted by default |
| Python 3.14 runtime quirks (install ≠ runs) | Low | The manual smoke (`streamlit run`) is the check; Gradio is a resolved fallback |
| A biased comparison | Med | Fix the axes up front (below); measure LOC/deps objectively; ADR records both sides honestly |

---

### 🗝️ The comparison axes (fixed up front, so US-155 is objective)

The same small feature (an `ask` box + a players view) built both ways, judged on:

1. **Learning value** — what each *teaches* (web mechanics/HTTP/templating vs rapid analytics→UI in pure
   Python) — weighed against the owner's goal (architecture/why, not syntax).
2. **Effort / lines of code** — for the same feature.
3. **Interactivity** — how easily you get filters, charts, a chat box (Streamlit's strength).
4. **Dependency footprint** — ~5 (FastAPI+Jinja) vs ~22 (Streamlit) — measured.
5. **Architecture fit** — does it stay a clean *edge* over the engine? (Streamlit merges server+UI within
   its script; the *core* stays clean either way.)
6. **Look & feel** — terminal-style `<pre>` (FastAPI slice) vs native widgets.

**No gate up front** (spike-first): the design is "build a throwaway and measure it"; the *decision* is
the gate, recorded as ADR-051 at the end.

---

### 📝 Session Progress Log

- **US-154 ✅** — Built the throwaway **Streamlit edge** (`spikes/052-streamlit/app.py`) over the same
  engine: three tabs — **Ask** (`render_ask(ask.answer(q))`, trust line and all), **Players** (a native
  sortable/searchable `st.dataframe` + live `selectbox`/`slider`), **Fixtures** (the FDR table). Streamlit
  installed **spike-only** (NOT in `requirements.txt`).
  - **Feasibility (the planning risk):** Streamlit **installs *and* runs on Python 3.14** — verified with
    Streamlit's `AppTest` (headless script execution): no exceptions on load or after driving the ask box,
    3 tabs, 2 dataframes, the ask produced a grounded answer. Also boots under `streamlit run` (HTTP 200,
    health `ok`). Fixed a deprecation (`use_container_width` → `width='stretch'`).
  - **Raw evidence measured (for ADR-051):** same 3 surfaces — **Streamlit 58 LOC / 1 file with
    *interactive* tables** vs the FastAPI edge's ~130+ LOC across 5 files with *static* `<pre>`;
    dependency footprint **+21 packages** (pandas/pyarrow/numpy/altair — a data-science stack) vs
    FastAPI's lean tree (pydantic/starlette/click/h11, no data stack). Captured in the spike README.
  - **Core untouched:** the **429** tests stay green; `requirements.txt` has no Streamlit; the spike lives
    only in `spikes/`. The trade is clear — *far less code + free interactivity* vs *a heavy dependency
    tree + a rerun model*. → weighed in US-155/ADR-051.
  - **Owner review + a real bug found:** the owner ran `streamlit run` himself and hit
    `ModuleNotFoundError: No module named 'src'` — `streamlit run` puts the *script's* folder on
    `sys.path`, not the project root. Fixed in the spike (insert the project root before importing the
    engine). The `AppTest` smoke had masked it by running from the project root — **lesson: a smoke must
    mimic the real run command**, not a convenient one.
- **US-155 ✅** — **ADR-051**: the head-to-head (Streamlit vs FastAPI — 58 vs ~130+ LOC · interactive vs
  static · +21 vs lean deps · learning-fit vs footprint) and the owner's verdict — **adopt Streamlit** as
  the web track (pure-Python, interactive; fits "architecture over frontend syntax"; heavier deps kept
  optional/web-only) and **freeze the FastAPI edge** (ADR-050) as the lean "also-serves-HTTP" reference
  (kept, not retired). The Streamlit edge **graduates to `src/web_streamlit/`** (with tests +
  `requirements.txt`) next sprint; the spike stays as the proven prototype until then; the core stays the
  one engine (the one-way-flow guardrail carries over). Docs: ADR-051 + index, Roadmap (the web track),
  PROJECT_STATUS (ADRs → 51, the decision). Tests unchanged (429) — a spike touches no `src/`.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — a strategy question answered on **real evidence**, not opinion. A throwaway
Streamlit edge over the same engine, measured head-to-head with the FastAPI slice, led to a clear owner
verdict: **adopt Streamlit** as the web track, **freeze the FastAPI edge**. **51 ADRs**; the **429** tests
stayed green (a spike touches no `src/`); no runtime dependency added.

**Delivered**
- **US-154** — the Streamlit spike (`spikes/052-streamlit/`): `ask` + two interactive tables in **58 LOC,
  1 file**, over the same engine; feasibility on Python 3.14 proven; the trade **measured** (58 vs ~130+
  LOC · interactive vs static · +21 vs lean deps).
- **US-155** — **ADR-051**: the comparison + the verdict (adopt Streamlit; freeze FastAPI; graduate the
  spike to `src/web_streamlit/` next); Roadmap + PROJECT_STATUS updated.

**What went well**
- **A spike beat an argument** — the "learn web syntax vs learn a rapid tool" question dissolved once the
  numbers were on the table; the owner *felt* the interactivity before committing.
- **The engine is the one core, proven again** — Streamlit was just another thin edge; the same
  `ask.answer`/analytics, nothing in `src/` touched, the guardrail intact.
- **Nothing wasted** — the FastAPI edge is frozen (a lean reference + the architecture lesson), not
  binned; the spike lives in `spikes/` until it graduates.
- **The decision fits the owner's stated goal** — architecture/wiring over frontend syntax; the ADR
  records the *why*, not just the *what*.

**Challenges / how they were handled**
- **A real `streamlit run` bug the owner caught** — `ModuleNotFoundError: No module named 'src'` (the run
  command puts the script's dir on `sys.path`, not the project root). Fixed with a path insert in the
  spike. The `AppTest` smoke had hidden it by running from the project root — the lesson: **a smoke must
  mimic the real run command**.
- **Heavy dependency footprint** — measured (+21) and accepted as a low-stakes, optional cost for a local
  tool; recorded as the one axis where FastAPI wins.

**Carried forward:** Graduate the Streamlit edge to `src/web_streamlit/` (next sprint).
