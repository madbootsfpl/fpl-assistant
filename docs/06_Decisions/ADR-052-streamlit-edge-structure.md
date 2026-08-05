# Architectural Decision Record: The Streamlit edge — structure, run entry, and interactivity

**Decision ID:** ADR-052
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Executes ADR-051 (adopt Streamlit as the web track). Sits alongside ADR-050
(the FastAPI edge, now **frozen**). A second UI edge over the one engine.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-051 chose Streamlit as the UI to grow and to **graduate the spike** (`spikes/052-streamlit/`) into a
real edge, `src/web_streamlit/`. The strategy is settled; this ADR pins the **structure** of that edge —
how it's laid out, how it's run (the `streamlit run` `sys.path` quirk the owner hit), and the first
interactive features — so US-157/158 are mechanical. The FastAPI edge (`src/web`, ADR-050) stays frozen.

#### Already proven (Sprint 052 spike)
Streamlit installs + runs on Python 3.14; the engine reuse works (`ask.answer` / `rank_players` /
`team_fdr`); **`AppTest`** runs the script headlessly for hermetic tests; the `ask` box renders the
grounded answer + ✓/⚠ trust line, and tables are interactive.

#### Decision Drivers
- **A structure that scales** — the UI will grow (charts, more pages), so favour the idiomatic shape.
- **Clean `src/` code** — no `sys.path` hack sitting in a graduated `src/` file.
- **The adoption payoff** — interactivity is *why* Streamlit was chosen; show it.
- **The engine stays the one core** — the edge imports the engine; the core imports no edge.

---

### ✅ Decision

**1. Structure — multipage (`pages/`) (owner's call).** The idiomatic Streamlit app:

```
src/web_streamlit/
  __init__.py
  __main__.py            # the run entry (below)
  app.py                 # home / landing
  pages/
    1_Players.py
    2_Fixtures.py
    3_Squads.py
    4_Ask.py
```

Streamlit builds the sidebar nav from `pages/` automatically; each page is a small script that imports
the engine + a renderer. Scales cleanly (add a `5_…py`).

**2. Run entry — `python -m src.web_streamlit` (owner's call).** A `__main__.py` launches `streamlit run
src/web_streamlit/app.py` in a subprocess with the **project root on `PYTHONPATH`**, so every page's
`from src import …` resolves — and the app/page files carry **no `sys.path` hack**. Parallels `python -m
src.web` (FastAPI); `streamlit run …` directly still works for anyone who prefers it (with the path set).

**3. Interactivity — both upgrades (owner's call).**
- **Players** — live **position multiselect + max-price slider** (+ the native sortable/searchable
  `st.dataframe`): instant filtering, no reload.
- **Ask** — a **chat interface** (`st.chat_input` + `st.chat_message`, history in `st.session_state`);
  each turn calls `ask.answer` and renders the grounded answer + ✓/⚠ trust line (degrades without Ollama,
  like the CLI).

**4. Reuse + the frozen edge.** Pages import `ask`/analytics/renderers — the **same** engine the CLI and
FastAPI use; nothing in the core changes. **`src/web` (FastAPI) is untouched** (frozen, ADR-051).

**5. The two-edge guardrail.** Extend `test_core_never_imports_the_web_edge` so the core imports
**neither** `src/web` **nor** `src/web_streamlit` — the one-way flow holds across both edges.

**6. Dependency + cleanup.** `streamlit` added to `requirements.txt` as a **web-only** extra (~21
transitive pkgs; the CLI runs without it — the ADR-051-accepted weight). `spikes/052-streamlit/` is
**removed** (it has graduated).

**7. Testing.** `AppTest.from_file(...)` per page (run from the project root, so `src` resolves): each
page renders with no exception; the Ask chat returns a grounded answer; the filters drive the table.

---

### 🔀 Alternatives Considered

- **Single-file tabs** (the spike's shape). Simplest and proven, but one crowded file that scales poorly
  as pages/charts are added. Not chosen — multipage is the idiomatic, growable shape.
- **Keep the `sys.path` insert** in each app/page file. Simplest (no runner), but a path hack repeated in
  `src/`. Not chosen — the `python -m` runner keeps `src/` clean.
- **One interactive upgrade** (chat-only or filters-only). Enough to demonstrate, but the owner chose
  **both** — the clearest "why we picked Streamlit" payoff.
- **Retire the FastAPI edge.** Rejected in ADR-051 (kept frozen as a lean reference).

---

### 🧭 Consequences

**Positive**
- An idiomatic, growable Streamlit app (sidebar nav, one file per page) with real interactivity — the
  adoption payoff, in pure Python.
- Clean `src/` (no path hack), a familiar `python -m …` run entry, hermetic `AppTest` tests.
- The engine stays the one core; two edges, both web-free-core (a test enforces it).

**Negative / risks (mitigations)**
- **The `streamlit run` path quirk** → the `python -m` runner sets `PYTHONPATH`; the smoke uses the
  **real** run command (the Sprint-052 lesson).
- **Two UI edges in the tree** → only Streamlit grows; FastAPI frozen; the guardrail covers both.
- **Heavier dependency** → web-only + optional (ADR-051).
- **`AppTest` and chat/session state** → keep the chat `AppTest`-drivable (set `chat_input`, assert the
  reply); smoke the rest live.

---

### 📊 Validation

The spike already renders `ask` (grounded + trust line) + interactive tables over the engine, tested with
`AppTest`, on Python 3.14. Acceptance for the sprint: `src/web_streamlit/` has the four pages + the two
interactive upgrades, runs via `python -m src.web_streamlit`, passes `AppTest` per page + the two-edge
guardrail; the existing 429 stay green; the CLI and the frozen FastAPI edge are unchanged; the spike is
removed.
