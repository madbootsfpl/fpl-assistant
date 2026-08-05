# Sprint 053: Graduate the Streamlit edge to `src/web_streamlit/`

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2–3 working sessions (a gate + the graduated edge + one interactivity upgrade + docs)
**Carried Over:** Graduate the Streamlit edge (from Sprint 052)

> **Direction (owner):** execute the ADR-051 decision — move the proven Streamlit spike out of `spikes/`
> into a real edge, `src/web_streamlit/`, with tests + `streamlit` in `requirements.txt`. Keep the FastAPI
> edge **frozen**. The Streamlit app becomes the UI we grow (interactive, pure-Python), still a **thin
> edge over the one engine**.

---

### 🔎 Verified at planning (the spike de-risked it; graduation is structure + tests)

- **Feasibility is proven** (Sprint 052): Streamlit **installs and runs on Python 3.14**; the engine
  reuse works (`ask.answer`/`rank_players`/`team_fdr`); **`AppTest`** runs the script headlessly for
  hermetic tests (no live server); the spike renders `ask` + two interactive tables in 58 LOC.
- **The run-entry quirk is known + fixed.** `streamlit run <file>` puts the *script's* folder on
  `sys.path`, not the project root (the bug the owner caught) — the spike fixes it with a path insert.
  For a graduated `src/` edge we want a **cleaner** entry (a runner that sets the path, so the app file
  stays clean) — a gate call.
- **Two edges will coexist.** `src/web` (FastAPI, **frozen** per ADR-051) + `src/web_streamlit` (new).
  The one-way-flow guardrail test (`test_core_never_imports_the_web_edge`) must be **extended** so the
  core imports **neither** edge.
- **The dependency weight is already accepted** (ADR-051): `streamlit` (~21 transitive pkgs) enters
  `requirements.txt` as a **web-only** extra; the CLI still runs without it.
- Preseason (GW1 2026-08-21).

---

### 🧭 What's new — a real, growing Streamlit UI

The spike becomes `src/web_streamlit/`: a proper edge (a run entry, tests, in `requirements.txt`) that
matches the FastAPI edge's coverage (Players · Fixtures · Squads · Ask) **plus one genuinely-interactive
upgrade** — the payoff for adopting Streamlit. Same discipline: it imports the engine and changes nothing
in the core.

---

### 🎯 Sprint Goal

**Objective:** a graduated `src/web_streamlit/` edge — a clean run entry, `streamlit` in
`requirements.txt` (web-only), pages matching the FastAPI edge + one interactive feature — reusing the
engine untouched, tested via `AppTest`, with the two-edge guardrail passing. FastAPI stays frozen. A gate
settles the structure, the run entry and the scope.

#### Success Criteria
- [ ] Approach agreed (**ADR-052**) — the edge **structure** (multipage `pages/` vs single-file tabs);
      the **run entry** (a clean `python -m src.web_streamlit` vs a path insert); the **page scope** + the
      interactive upgrade; testing (`AppTest`); the **two-edge guardrail**; FastAPI stays frozen
- [ ] `src/web_streamlit/` — the graduated app + a run entry; the spike removed from `spikes/`
- [ ] `streamlit` added to `requirements.txt` (web-only; noted as optional, like the FastAPI extras)
- [ ] Pages matching the FastAPI edge — **Players · Fixtures · Squads (analyse) · Ask** (the grounded
      answer + ✓/⚠ trust line, degrading without Ollama) — reusing the engine/renderers
- [ ] **One interactive upgrade** (the adoption payoff) — e.g. a filterable players table (position/price)
      or a chat-style `ask`
- [ ] Tests — `AppTest` per page (renders, no exception, `ask` works) + the **two-edge guardrail** (the
      core imports neither `src/web` nor `src/web_streamlit`)
- [ ] The core is unchanged; **FastAPI (`src/web`) is untouched** (frozen)
- [ ] Docs: ADR-052 + index, Architecture (the two edges), Handbook Ch 12 (the Streamlit edge), README
      (run the Streamlit UI), PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-156 | **Gate.** Streamlit-edge design (**ADR-052**): structure (multipage `pages/` vs tabs); the run entry (clean `python -m src.web_streamlit` vs a path insert); the page scope + the interactive upgrade; `AppTest` testing; the two-edge guardrail; FastAPI frozen. Pressure-test (done: feasibility + AppTest + the run-entry quirk on real data) | Critical | ✅ Done | 0.5–1 session |
| US-157 | **The graduated edge** — `src/web_streamlit/` (app + run entry) matching the spike/FastAPI pages; `streamlit` → `requirements.txt`; remove the spike; `AppTest` tests + the two-edge guardrail. Architecture changelog | High | ✅ Done | 1 session |
| US-158 | **Interactivity + docs** — one interactive upgrade (filterable table / chat-style ask); docs (Handbook Ch 12, README run steps, PROJECT_STATUS). Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-052 recorded + added to the ADR index — _US-156_
- [x] Add `streamlit` to `requirements.txt` (web-only) + remove `spikes/052-streamlit/` — _US-157_
- [x] Extend the guardrail test to cover both edges — _US-157_
- [x] Update Architecture (two edges over one engine, US-157) + Handbook Ch 12 + README + PROJECT_STATUS — _US-158_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — `AppTest` renders each page (no exception; `ask` returns the grounded
   answer); the two-edge guardrail passes; the existing **429** stay green; the core + the FastAPI edge
   are unchanged.
2. **Manual smoke test done** — `python -m src.web_streamlit` (or `streamlit run …`): the pages load, the
   `ask` box works (with + without Ollama), the interactive feature works; `python -m src.web` (FastAPI)
   still runs (frozen, unaffected).
3. **Documentation updated & checked** — ADR-052 + index, Architecture, Handbook Ch 12, README, sprint
   board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Graduate the spike → `src/web_streamlit/`; run entry; tests | Any change to the FastAPI edge (`src/web`) — it's **frozen** |
| Pages matching FastAPI + one interactive upgrade | A big charting/dashboard build-out — a later sprint |
| `streamlit` as a web-only dependency | Deployment/hosting; auth; writes |
| The two-edge guardrail | Re-opening the Streamlit-vs-FastAPI decision (settled, ADR-051) |

**External Dependencies:** `streamlit` (web-only; resolves on 3.14). The CLI + the FastAPI edge run
without it.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| The `streamlit run` `sys.path` quirk resurfaces in `src/` | Med | The gate picks a clean run entry (a runner that sets the path); a smoke via the **real** run command (Sprint-052 lesson) |
| Two edges drift / the core leaks into one | Med | Extend the guardrail test to both edges; FastAPI frozen (untouched); only Streamlit grows |
| Heavier dependency footprint in `requirements.txt` | Low (accepted) | Web-only + optional (ADR-051); the CLI runs without it |
| `AppTest` can't exercise a widget/interaction | Low | Keep the interactive feature `AppTest`-drivable (set inputs, assert output); smoke the rest live |

---

### 🗝️ Gating decision (US-156 → ADR-052)

Settle before code — feasibility is proven; these are structure calls. Proposed (confirm/redirect at
"start US-156"):

1. **Structure — multipage `pages/`** (idiomatic Streamlit; a real nav; each page a file → scales as we
   add charts/chat) *vs* single-file **tabs** (the spike's shape; simplest). *Propose multipage.*
2. **Run entry — a clean `python -m src.web_streamlit`** (a small runner that launches `streamlit run`
   with the project root on the path, so the app file has **no** `sys.path` hack; parallels `python -m
   src.web`) *vs* keeping the path insert. *Propose the runner.*
3. **Scope** — match the FastAPI edge (**Players · Fixtures · Squads · Ask**) + **one** interactive
   upgrade. *Propose a filterable players table and/or a chat-style `ask`* (owner to pick the upgrade).
4. **Testing & guardrail** — `AppTest` per page; extend `test_core_never_imports_the_web_edge` to assert
   the core imports **neither** `src/web` nor `src/web_streamlit`. FastAPI stays frozen.

**Worked example (proven, Sprint 052):** the spike already renders `ask` (grounded, trust line) + two
interactive tables over the engine, tested headlessly with `AppTest` — graduation moves it to `src/`,
cleans the run entry, adds tests, and grows one interactive page.

---

### 📝 Session Progress Log

- **US-156 (gate) ✅** — Recorded **ADR-052**, all three owner calls settled: **structure = multipage**
  (`src/web_streamlit/app.py` + `pages/1_Players … 4_Ask.py`; Streamlit builds the sidebar nav; scales as
  we add pages); **run entry = `python -m src.web_streamlit`** (a `__main__.py` that launches `streamlit
  run` with the project root on `PYTHONPATH`, so the app/page files carry **no `sys.path` hack** — parallels
  `python -m src.web`); **interactivity = both** upgrades — Players gains a live position-multiselect +
  max-price slider (atop the native sortable table), and Ask becomes a **chat** (`st.chat_input` +
  `st.chat_message`, history in `session_state`), each turn grounded + trust-lined, degrading without
  Ollama. Also settled: pages reuse the engine/renderers (core unchanged); **`src/web` FastAPI stays
  frozen**; the guardrail test extends to assert the core imports **neither** edge; `streamlit` → web-only
  in `requirements.txt`; the `spikes/052-streamlit/` prototype is removed on graduation; `AppTest` per page
  (run from the project root). ADR-052 indexed.
- **US-157 ✅** — Graduated the spike to **`src/web_streamlit/`**: `__init__.py`, `__main__.py` (the
  runner — `subprocess` launches `streamlit run app.py` with the project root on `PYTHONPATH`), `app.py`
  (home), and `pages/1_Players · 2_Fixtures · 3_Squads · 4_Ask.py` — each reusing the engine/renderers
  (Players sortable table + sort/limit; Fixtures FDR; Squads = `ask.answer("analyse …")`; Ask =
  input→grounded answer). **No `sys.path` hack** in any app/page file. `streamlit` added **web-only** to
  `requirements.txt`; `spikes/052-streamlit/` **removed**. The guardrail renamed/clarified to
  `test_core_never_imports_a_web_edge` — the `src.web` prefix covers **both** `src/web` and
  `src/web_streamlit`.
  - **Tests (435 total, +6; `test_web_streamlit.py`):** each page renders via `AppTest` (no exception; a
    table or the "run refresh" note); the Ask page answers a grounded FDR question; the runner module
    targets `app.py`. (Fixed a gotcha: `AppTest.from_file` resolves a *relative* path against the test
    file's dir → used **absolute** paths from the project root.)
  - **Smoke (the REAL run command — the Sprint-052 lesson):** `python -m src.web_streamlit` boots clean
    (HTTP 200, health `ok`, **no `ModuleNotFoundError`**); the frozen FastAPI edge (`src.web`) still
    imports.
  - **Docs:** Architecture §12 changelog + the §3 diagram (now two web edges: Streamlit grown + FastAPI
    frozen). _The interactivity upgrades (filters + chat) + Handbook/README/PROJECT_STATUS are US-158._
- **US-158 ✅** — The interactivity upgrades (the adoption payoff). **Players** gained live **position
  multiselect + max-price slider** (in `st.columns`, atop the sortable table) with a live "N match" count;
  **Ask** became a **chat** (`st.chat_input` + `st.chat_message`, history in `session_state`) — each turn
  grounded + trust-lined, degrading without Ollama.
  - **Tests (436 total, +1):** a filter test (multiselect→GK + slider→£5.0m never crashes) and the Ask
    test upgraded to drive `chat_input` and assert the grounded answer + a history entry.
  - **Smoke:** `python -m src.web_streamlit` boots clean (200, no errors); filters + chat work.
  - **Docs:** **README** — the Web UI section now leads with Streamlit (interactive; filters + chat) with
    FastAPI as the frozen reference; **Handbook Ch 12** retitled "Web UI (FastAPI + Streamlit)" with a
    Streamlit section (multipage, widgets, `AppTest`, the run quirk) + the guardrail rename + ADR-051/052
    links; **PROJECT_STATUS** — Web UI = Streamlit line, commands, Tests 436 / ADRs 52.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the Streamlit spike graduated to a real, interactive, **multipage**
`src/web_streamlit/` edge (Players with live filters · Fixtures · Squads · a chat-style **Ask**), run via
`python -m src.web_streamlit`. Two web edges over the one engine now — Streamlit (grown) + FastAPI
(frozen) — with the core importing neither (a test asserts it). **436 tests** (was 429, +7); **52 ADRs**.

**Delivered**
- **US-156 (gate)** — ADR-052: multipage `pages/`; the clean `python -m` runner (no `sys.path` hack);
  both interactivity upgrades; the two-edge guardrail.
- **US-157** — `src/web_streamlit/` graduated (runner + four pages reusing the engine); `streamlit` →
  `requirements.txt` (web-only); the spike removed; `AppTest` tests + the guardrail extended.
- **US-158** — the interactivity payoff (Players filters + a chat Ask); README + Handbook Ch 12 +
  PROJECT_STATUS.

**What went well**
- **All three gate calls paid off** — multipage gives clean per-page files; the `python -m` runner means
  no path hack in `src/`; both interactivity upgrades deliver the interactive feel that motivated adopting
  Streamlit.
- **The engine is the one core, again** — graduation was routes-over-the-engine; nothing in `src/`
  changed, the guardrail (now covering both edges) holds.
- **Smoked the real command** — `python -m src.web_streamlit` (the Sprint-052 lesson), so the run quirk
  couldn't hide.
- **Nothing wasted** — FastAPI frozen, kept as the lean reference; the spike removed cleanly.

**Challenges / how they were handled**
- **`AppTest` relative-path gotcha** — `AppTest.from_file` resolves a relative path against the *test
  file's* dir, not the project root (the first test run failed). Fixed with absolute paths from the
  project root.
- **The `streamlit run` `sys.path` quirk** (Sprint-052 bug) — designed out via the `python -m` runner
  (`PYTHONPATH` set once), so the app/page files stay clean.
- **Two UI edges coexisting** — the guardrail renamed/clarified to cover both (`src.web` prefix); only
  Streamlit grows, FastAPI is frozen.

**Carried forward:** None. *(Optional next: more Streamlit polish — charts, a compare/transfer page — or
move to Data Hardening post-GW1.)*
