# Architectural Decision Record: A thin web UI — a read-only FastAPI edge over the analytics

**Decision ID:** ADR-050
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Realises the web UI deferred by ADR-002/003 (CLI-first); adds a second
*edge* alongside the CLI over the same analytics core. First runtime dependency beyond
`requests`/`pulp`.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The app is a mature CLI (8 `ask` intents + `chat`, 49 ADRs, 421 tests) but has no browser presence. The
roadmap's next track is a **web UI**, and the owner asked to keep it **thin**: read-only, local-only,
reusing the analytics/`ask` untouched — a GW1-ready shell, not a full interactive app. The question is
*how* to add a web edge without disturbing the core or the project's lightweight ethos.

#### A planning probe settled the reuse path and the footprint
- **`ask.answer()` is a clean, structured, injectable call** — returns an `AskResult` (intent · headline ·
  `detail` table · facts · ✓/⚠ `trust`) with a swappable narrator. A web handler is a **thin wrapper**.
- **The whole UI is thin-able** — the CLI renderers (`render_ask`, `render_fdr_table`, …) already produce
  aligned text; wrapping their output in `<pre>` is **zero new rendering logic**.
- **First real dependency growth** — `fastapi`/`jinja2`/`uvicorn` are not installed (today: stdlib +
  `requests` + `pulp`). Sanctioned by the Charter + Handbook Ch 12, but a real call.

#### Decision Drivers
- **The CLI stays the engine** — the web is an additive edge; the analytics don't change.
- **Thin & reuse** — least new code; reuse the renderers.
- **Preserve one-way data flow** — the web imports the core, never the reverse.
- **Safe & simple** — read-only, local-only, no auth (a personal tool).

---

### ✅ Decision

**1. The stack — FastAPI, sync-only (owner's call).** A `src/web/` package: a **FastAPI** app with
**plain synchronous `def` handlers** (no `async` — we don't need it), Jinja2 templates, run with
`uvicorn` for local dev. The Charter's named backend, the Handbook Ch-12 scaffold, and a first-class
`TestClient` for the test-first discipline. *(Flask was the lighter alternative; the owner chose FastAPI,
sync-only so it carries no async complexity.)*

**2. A new edge — `src/web/`.** Its handlers call the **same** `decision_xp` / `ask.answer` / optimiser
the CLI does. **The analytics/CLI import nothing from `src/web/`** — one-way flow preserved, and a test
asserts the core stays web-free. The CLI keeps working with the web deps absent.

**3. Rendering — reuse the text renderers in `<pre>` (owner's call).** Slice 1 wraps the existing CLI
renderer output (`render_ask`, the FDR/table renderers) in a `<pre>` block inside a minimal page shell —
**zero new rendering logic**, the same output the CLI shows (trust line and all), in the browser. HTML
`<table>`s are a **later, optional polish**, not slice 1.

**4. Scope & safety.** **Read-only, local-only** (`127.0.0.1`), **no auth, no writes**. Jinja
autoescaping on. Slice-1 routes: **`GET /`** (players view) + **`GET/POST /ask`** (the flagship —
`ask.answer(q)` rendered with its ✓/⚠ trust line, degrading gracefully without Ollama exactly like the
CLI); then a **fixtures** and/or saved-squad **analyse** page (US-153).

**5. Dependency footprint.** `fastapi`, `uvicorn`, `jinja2` (+ `httpx` for the test client) added to
`requirements.txt`, noted as **web-only** (the CLI doesn't need them). Pin to reasonable minimums.

---

### 🔀 Alternatives Considered

- **Flask** — lighter and sync by nature, Jinja bundled, the classic server-rendered choice. A close
  call; the owner chose FastAPI to honour the Charter + the existing handbook scaffold, and because sync
  handlers remove its only real downside here.
- **Stdlib `http.server`** — zero deps, but you hand-roll routing/templating; more code, less real-
  framework learning. Rejected.
- **A JS SPA (React/Next) + a JSON API** — most polished, but a big build toolchain and syntax-heavy,
  against the "architecture not syntax" learning focus and the "thin" brief. Deferred (maybe never).
- **HTML `<table>` templates now** — nicer, but re-implements every renderer (a second place to maintain
  presentation). Deferred to a later polish; `<pre>`-reuse ships the slice.

---

### 🧭 Consequences

**Positive**
- The analytics — including the grounded `ask`/`chat` — are visible in a browser with **almost no new
  code**: handlers wrap the engine, templates wrap the renderers' text.
- The core is untouched and stays web-free (a test enforces it); the CLI runs with or without the web
  deps.
- A clean base to grow (more pages, HTML polish, later interactivity) without a rewrite — exactly the
  ADR-002 promise ("adding it later won't require a rewrite").

**Negative / risks (mitigations)**
- **First dependency growth** → isolated in `src/web/`; web-only in `requirements.txt`; the CLI is
  unaffected.
- **The edge leaking into the core** → analytics import nothing web; a test asserts it.
- **A monospace/terminal look** → accepted for a thin slice; honest and instant; HTML polish is a later
  option.
- **Local server security** → read-only, no auth, bound to `127.0.0.1`, Jinja autoescape — a personal
  tool, not exposed.

---

### 📊 Validation

Prototyped on the live DB: `ask.answer("who has the best fixtures over the next 5?")` returns a structured
`AskResult` (a `detail` FDR table + facts + trust) — an `/ask` handler renders exactly that, trust line
and all. Acceptance for the sprint: the FastAPI test client hits `/`, `/ask` and the extra page(s) (200 +
expected content); `/ask` renders a known decision with its trust line (and degrades without Ollama); the
analytics/CLI are unchanged and carry no web import; a local `uvicorn` run serves the pages.
