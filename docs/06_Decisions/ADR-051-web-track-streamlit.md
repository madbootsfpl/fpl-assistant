# Architectural Decision Record: The web track — adopt Streamlit; freeze the FastAPI edge

**Decision ID:** ADR-051
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Redirects the web track set by ADR-050 (a FastAPI edge) — Streamlit becomes
the UI we grow; the FastAPI edge is kept **frozen** as a lean reference, not retired.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

After the FastAPI slice (ADR-050, Sprint 051), the owner weighed a strategy question: *for a personal
analytics tool — and for **his** learning (architecture/why, not frontend syntax) — is it better to keep
hand-rolling a web UI (FastAPI + HTML), or to ship with a rapid Python tool (Streamlit/Gradio)?* Rather
than argue it, Sprint 052 **built a throwaway Streamlit edge over the same engine** and measured it
head-to-head — the project's "decide on real evidence" discipline (cf. the soccerdata spike → ADR-016,
the LLM spike → ADR-033).

#### The spike (US-154) measured the trade
Same three surfaces (`ask` + a players view + fixtures), both built over the **same** `ask.answer` /
`rank_players` / `team_fdr` engine:

| Axis | Streamlit spike | FastAPI edge (ADR-050) |
|---|---|---|
| **Learning fit** (architecture, *not* syntax) | Pure-Python wiring; zero HTML/CSS/JS | Routing + templating + (for interactivity) HTMX/JS |
| **Interactivity** | **Free** — sortable/searchable tables, live `selectbox`/`slider`, chat-able | **Static** `<pre>`; needs JS to go further |
| **Code (same 3 surfaces)** | **58 LOC, 1 file** | ~130+ LOC across 5 files |
| **Dependency footprint** | **+21 packages** (pandas/pyarrow/numpy/altair — a data-science stack) | **Lean** — pydantic/starlette/click/h11; no data stack |
| **Architecture fit** | A thin edge over the engine; but server+UI merge *inside* the script (a rerun model) | A thin edge; explicit request→response routes |
| **Python 3.14** | ✅ installs + runs (`AppTest`: no exceptions, ask works) | ✅ |

#### Decision Drivers
- **The owner's learning goal** — architecture/systems-thinking over frontend *syntax*. Growing the
  FastAPI UI mostly teaches HTML/CSS/JS craft; Streamlit keeps the effort on the analytics + the wiring.
- **Interactivity** — the thing the owner valued most; Streamlit gives it for free.
- **Less code** — Streamlit did the same surfaces in ~⅓ the lines.
- **Footprint** — Streamlit's ~21-package data stack is the one real cost; *low-stakes for a local,
  personal tool* (optional deps, a dev-machine concern, not a deployed service).

---

### ✅ Decision

**1. Adopt Streamlit as the web track (owner's call).** New UI work goes into a Streamlit app; the spike
**graduates** to `src/web_streamlit/` (a proper edge, `streamlit` added to `requirements.txt` as a
web-only extra) in the next sprint. It stays a **thin edge over the same engine** — it imports
`ask`/analytics and changes nothing in the core (the one-way-flow guardrail test still applies).

**2. Freeze the FastAPI edge (ADR-050), don't retire it.** `src/web/` stays as-is — lean, tested, the
"also-serves-over-HTTP" reference and the artifact that delivered the architecture lesson (edges,
one-way flow) and this comparison's baseline. We **don't grow it**; we don't delete it.

**3. Accept the dependency weight, kept optional.** Streamlit's ~21 packages are web-only in
`requirements.txt` (the CLI still runs without them, like the FastAPI extras). Justified because this is
a **local personal tool**, not a deployed service.

**4. The spike's immediate fate.** `spikes/052-streamlit/` remains as the proven prototype until it
graduates to `src/web_streamlit/` next sprint; this ADR records the decision, not the port.

---

### 🔀 Alternatives Considered

- **Stay FastAPI, discard the spike.** Keeps the lean footprint and teaches "real" HTTP/routing — but
  interactivity then costs the very frontend syntax the owner wants to avoid, at more code. Not chosen.
- **Adopt Streamlit *and retire* the FastAPI edge.** The cleanest "one UI" outcome, but it throws away a
  working, tested, lean artifact whose lesson is already banked; freezing keeps it at ~zero cost.
- **Keep both and grow both.** Maximum breadth + a literal "one engine, many faces," but two UIs to keep
  in step — unnecessary complexity for a solo project. (We keep both, but only Streamlit *grows*.)
- **Gradio.** A lovely conversational/IO surface, but narrower than a dashboard; Streamlit fits the
  tables + filters + ask better.

---

### 🧭 Consequences

**Positive**
- UI work becomes pure-Python wiring with interactivity for free — aligned with the owner's goal and
  what he valued; ~⅓ the code.
- The engine is still the one core; Streamlit is just another edge (the architecture holds; the guardrail
  test carries over).
- Nothing built is wasted — the FastAPI edge stays as a lean, working reference.

**Negative / risks (mitigations)**
- **Heavier dependency tree** → web-only + optional; a local-tool concern, not production.
- **Streamlit's rerun model / less-explicit flow** → accepted; keep the app a *thin* edge (logic stays in
  the engine, the script just renders).
- **Two UIs in the tree** → only Streamlit grows; FastAPI is explicitly frozen (not maintained in step).

---

### 📊 Validation

The spike ran on the live DB and on Python 3.14 (`streamlit run` + `AppTest`: no exceptions, the `ask`
box returns the grounded answer + trust line, two interactive tables render). The comparison is measured
(58 vs ~130+ LOC; +21 vs lean deps; interactive vs static). A `streamlit run` import bug (project root
not on `sys.path`) was found and fixed in the spike — a reminder that a smoke must mimic the *real* run
command. Acceptance: this ADR records the verdict; the graduation to `src/web_streamlit/` (with tests +
`requirements.txt`) is the next sprint.
