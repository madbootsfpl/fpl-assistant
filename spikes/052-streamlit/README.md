# Spike 052 — Streamlit edge (throwaway)

A minimal Streamlit UI over the **same engine** as the CLI and the FastAPI edge (`ask.answer` /
`rank_players` / `team_fdr`). Built to *feel* Streamlit against the FastAPI slice (Sprint 051) and gather
evidence for the web-track decision. **Throwaway** — changes nothing in `src/`; Streamlit is **not** in
`requirements.txt`. ADR-051 (US-155) decides its fate.

## Run

```bash
pip install streamlit          # spike-only; ~21 extra packages
streamlit run spikes/052-streamlit/app.py
```

Three tabs: **Ask** (the grounded answer + ✓/⚠ trust line, reusing `render_ask`), **Players** (a native
sortable/searchable table + live *Sort by* / *How many* controls), **Fixtures** (the FDR table).

## Raw evidence measured (for the US-155 comparison / ADR-051)

| Axis | Streamlit spike | FastAPI edge (Sprint 051) |
|---|---|---|
| Code (same 3 surfaces: ask + players + fixtures) | **58 LOC, 1 file** | app.py routes + shared Jinja templates (~130+ LOC across 5 files) |
| Interactivity | **Free** — sortable/searchable tables, live `selectbox`/`slider`, no reload | **Static** `<pre>` — needs forms/HTMX/JS to go further |
| Dependency footprint | **+21 packages** (pandas 3, pyarrow 24, numpy 2.5, altair, protobuf, pydeck — a data-science stack) | **Lean** — fastapi/uvicorn/jinja2 drag pydantic/starlette/click/h11; **no** data stack |
| Architecture fit | A thin edge over the engine — but server+UI merge *inside* the script (its own rerun model) | A thin edge; explicit routes; clean request→response |
| Look & feel | Native widgets (tables, inputs) | Terminal-style monospace `<pre>` |
| Verified on Python 3.14 | ✅ installs + runs (`AppTest`: no exceptions, 2 dataframes, ask works) | ✅ (Sprint 051) |

**The shape of the trade:** Streamlit = *far less code + interactivity for free*, at the cost of a *heavy
dependency tree* and a less-explicit (rerun-based) model. FastAPI = *more code + static views*, but a
*lean footprint* and a "real" production web stack. → weighed in **ADR-051**.
