# Chapter 12 — FastAPI

**Badges:** 💻

*Built in Sprint 051 ([ADR-050](../06_Decisions/ADR-050-thin-web-ui.md)) — a thin, read-only web UI over
the analytics. This chapter records how it works in **this** project.*

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

## The one rule — the edge never leaks into the core

`src/web/` imports the analytics; **the analytics import nothing from `src/web/`**. That one-way flow is
what keeps the web additive (the CLI is untouched, the core is testable without a server). A test —
`test_core_never_imports_the_web_edge` — statically asserts no core file mentions `src.web`.

## Deliberately small (slice 1)

Read-only, local-only, no auth, no writes; the data views reuse the CLI renderers in `<pre>` (not HTML
tables — that's a later polish). See ADR-050 for the scope and the reasons.

---

## Run it

```bash
pip install -r requirements.txt     # fastapi / uvicorn / jinja2 are web-only extras
python -m src.web                   # http://127.0.0.1:8000
```

---

## Related Documents

- [ADR-050 — A thin web UI](../06_Decisions/ADR-050-thin-web-ui.md)
- [ADR-002 — UI Approach](../06_Decisions/ADR-002-ui-approach.md) (why it waited)
- [Architecture §3 (the two edges) + §12 changelog](../03_Architecture/Architecture.md)
