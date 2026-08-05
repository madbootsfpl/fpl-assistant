# Chapter 12 — Web UI (FastAPI + Streamlit)

**Badges:** 💻

*The web UI over the analytics — a FastAPI slice (Sprint 051, [ADR-050](../06_Decisions/ADR-050-thin-web-ui.md))
then a Streamlit edge (Sprint 052–053, [ADR-051](../06_Decisions/ADR-051-web-track-streamlit.md) /
[ADR-052](../06_Decisions/ADR-052-streamlit-edge-structure.md)). This chapter records how they work in
**this** project.*

---

## Purpose

FastAPI is a Python framework for serving things over HTTP. Here it powers a **thin web UI**: a browser
view of the same analytics the CLI shows — a *second edge* over the one engine, not a rewrite.

---

## Why We Use It

Named in the Project Charter as the intended backend, and deferred by ADR-002 until "there was data worth
serving." That moment arrived after Phase 4: a mature analytics + `ask` engine to look at in a browser.
FastAPI (over Flask, the lighter alternative) was chosen for its first-class **test client** and typed
routes — used **sync-only**, so it carries no async complexity.

---

## How it works here (`src/web/`)

The web is a **new edge**. Its handlers call the *same* functions the CLI does and render the *same* text
renderers inside a `<pre>` block — so the page looks like the terminal and there's almost no new code.

```python
# src/web/app.py  (abridged)
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from src import ask
from src.ui.ask import render_ask

app = FastAPI()
templates = Jinja2Templates(directory=".../templates")

@app.get("/ask")              # a plain SYNC def — no async needed
def ask_page(request: Request, q: str | None = None):
    answer = render_ask(ask.answer(q)) if q else None      # reuse the engine + the renderer
    return templates.TemplateResponse(request, "ask.html", {"q": q or "", "answer": answer})
```

- **Routes / endpoints** — a URL the app answers on (`/`, `/fixtures`, `/squads`, `/squad/{name}`,
  `/ask`). Decorate a function with `@app.get(...)`.
- **Path & query parameters** — `/squad/{name}` (path) and `/ask?q=...` (query) arrive as function
  arguments; FastAPI reads them from the type hints.
- **Templates (Jinja2)** — `TemplateResponse(request, "name.html", {...})` renders HTML.
  **Autoescaping is on**, so a `<script>` typed into the Ask box is rendered harmlessly (a test checks
  this).
- **ASGI server (uvicorn)** — actually runs the app. `python -m src.web` calls `uvicorn.run(...)` bound to
  `127.0.0.1` (imported there, *not* in the CLI, so the CLI still runs without the web deps).
- **TestClient** — `from fastapi.testclient import TestClient; client = TestClient(app)` lets pytest hit
  routes with no live server (`tests/test_web.py`).

## The one rule — an edge never leaks into the core

An edge imports the analytics; **the analytics import nothing from an edge**. That one-way flow is what
keeps the web additive (the CLI is untouched, the core is testable without a server). A test —
`test_core_never_imports_a_web_edge` — statically asserts no core file mentions `src.web` (which, by
prefix, covers **both** `src/web` and `src/web_streamlit`).

## Two web edges over one engine (ADR-051/052)

A measured spike (ADR-051) chose **Streamlit** as the UI to grow; the FastAPI edge is kept **frozen** as a
lean reference. Both are thin edges over the same `ask.answer`/analytics — "one engine, many faces".

**Streamlit (`src/web_streamlit/`, the UI we grow).** Pure-Python, interactive, multipage:

```python
# src/web_streamlit/pages/4_Ask.py  (abridged) — a chat over the same engine
import streamlit as st
from src import ask
from src.ui.ask import render_ask

prompt = st.chat_input("Ask a question…")
if prompt:
    st.chat_message("assistant").code(render_ask(ask.answer(prompt)))   # grounded + trust line
```

- **Multipage** — `app.py` (home) + `pages/1_Players … 6_Build.py`; Streamlit builds the sidebar nav
  (Players · Fixtures · Squads · Transfer · Build · Ask).
- **Widgets, not markup** — `st.dataframe` (sortable/searchable), `st.multiselect`/`st.slider`/
  `st.number_input` (live filters + controls), `st.bar_chart`/`st.scatter_chart` (native charts, no
  charting library), `st.chat_input`/`st.chat_message` (a chat) — interactivity with no HTML/JS.
- **Pages are sliders wired to the engine** — Transfer (`suggest_transfers`) and Build (the `build_squad`
  `ask` intent) reuse the *same* functions the CLI does, so the web can't drift from the CLI's logic.
- **`AppTest`** — `from streamlit.testing.v1 import AppTest` runs a page headlessly for tests (set inputs,
  assert output); no live server (`tests/test_web_streamlit.py`).
- **The run quirk** — `streamlit run` puts the *script's* folder on `sys.path`, not the project root. The
  `python -m src.web_streamlit` runner launches `streamlit run` with the project root on `PYTHONPATH`, so
  the page files import `src` cleanly with **no path hack**.
- **Trade** — far less code + interactivity for free, at the cost of a heavy dependency tree (kept
  optional/web-only). See ADR-051 for the head-to-head.

**FastAPI (`src/web/`, frozen).** Read-only, server-rendered; the data views reuse the CLI renderers in
`<pre>`. Kept as-is (ADR-050).

---

## Run it

```bash
pip install -r requirements.txt     # streamlit / fastapi / uvicorn / jinja2 are web-only extras
python -m src.web_streamlit         # the Streamlit UI  → http://localhost:8501
python -m src.web                   # the frozen FastAPI edge → http://127.0.0.1:8000
```

---

## Related Documents

- [ADR-050 — A thin web UI (FastAPI)](../06_Decisions/ADR-050-thin-web-ui.md)
- [ADR-051 — The web track: adopt Streamlit](../06_Decisions/ADR-051-web-track-streamlit.md)
- [ADR-052 — The Streamlit edge structure](../06_Decisions/ADR-052-streamlit-edge-structure.md)
- [ADR-002 — UI Approach](../06_Decisions/ADR-002-ui-approach.md) (why it waited)
- [Architecture §3 (the two edges) + §12 changelog](../03_Architecture/Architecture.md)
