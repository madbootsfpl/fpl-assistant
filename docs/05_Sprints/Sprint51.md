# Sprint 051: A thin web UI — the first slice (read-only, reuse the analytics)

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2–3 working sessions (a gate + an app skeleton + a couple of read-only pages + docs)
**Carried Over:** None (Sprint 050 closed clean)

> **Direction (owner):** open the **web UI** track — kept deliberately **thin**. A minimal, read-only,
> local-only web layer that **reuses the existing analytics/`ask` untouched** — the web as a new *edge*
> over the same core (**the CLI stays the engine**). A GW1-ready shell, not a full interactive app.

---

### 🔎 Verified at planning (the reuse path is real; the footprint grows for the first time)

- **`ask.answer()` is cleanly callable and structured.** It returns an `AskResult` (intent · headline ·
  `detail` table · facts · explanation · ✓/⚠ `trust`) with an injectable narrator — so a web handler is a
  **thin wrapper**: call the engine, render the result. Confirmed on the live DB.
- **The whole thing is thin-able.** The CLI renderers (`render_ask`, `render_fdr_table`,
  `render_squad_fixtures`, the table views) already produce aligned text — wrapping their output in
  `<pre>` is a **zero-new-logic** first slice (a page shell + a form is the only new UI). HTML tables are a
  later polish, not a slice-1 need.
- **A new dependency — the first real footprint growth.** `fastapi` / `jinja2` / `uvicorn` are **not
  installed** (today: stdlib + `requests` + `pulp`). This is *sanctioned* — the Charter names FastAPI and
  the handbook's Ch 12 says to add it "once there is data worth serving; the layered architecture means
  adding it later won't require a rewrite" — but it's a real gate call (which stack, how many packages).
- **Read-only + local-only keeps it safe & simple.** No auth, no writes, bind `127.0.0.1` — a personal
  tool. Jinja autoescaping covers the little HTML we render.
- Preseason (GW1 2026-08-21) — a calm window to build the shell so it's live when the data gets rich.

---

### 🧭 What's new — see the analytics in a browser

A new `src/web/` **edge**: a small web app whose routes call the **same** `decision_xp` / `ask.answer` /
optimiser the CLI does, render server-side, and return HTML. No JS build, no SPA. The flagship is an
**`/ask` page** — the grounded NL layer, in a browser, with its ✓/⚠ trust line intact.

---

### 🎯 Sprint Goal

**Objective:** a minimal, read-only, local-only web app (`src/web/`) that reuses the analytics/`ask`
untouched — a home **players** view and the flagship **`/ask`** page (plus a page or two more), server-
rendered, tested with the framework's test client. The CLI is unchanged. A gate settles the stack + the
rendering approach + the slice scope.

#### Success Criteria
- [ ] Approach agreed (**ADR-050**) — the stack (**FastAPI vs Flask**); the `src/web/` structure (a new
      edge, analytics untouched); the **rendering approach** (`<pre>`-reuse vs HTML templates);
      read-only/local-only/no-auth; the route scope; testing; the dependency footprint
- [ ] The app skeleton — `src/web/` (app + templates), a run entry point, added to `requirements.txt`
- [ ] **`GET /`** — a home players view (reuse the table/xP data)
- [ ] **`GET/POST /ask`** — a question box → `ask.answer(q)` → the rendered decision + explanation + the
      ✓/⚠ trust line (the flagship; degrades without Ollama, like the CLI)
- [ ] One or two more read-only pages — **fixtures** (FDR) and/or a saved-squad **analyse**
- [ ] Tests — the framework's test client + pytest (routes return 200; the `/ask` path renders a known
      decision; the CLI/analytics are untouched)
- [ ] The CLI is unchanged; the analytics layer gains **no** web imports (one-way dependency preserved)
- [ ] Docs: ADR-050 + index, Architecture, Handbook Ch 12 (FastAPI/Flask — fill it in), README (run it),
      PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-151 | **Gate.** Web-UI design (**ADR-050**): the stack (**FastAPI vs Flask**); `src/web/` as a new edge (analytics untouched, CLI stays the engine); the **rendering approach** (`<pre>`-reuse vs HTML); read-only/local-only/no-auth; the slice route scope; testing; the dependency footprint. Pressure-test (done: `ask.answer` callable, `<pre>`-reuse viable, deps assessed) | Critical | ✅ Done | 0.5–1 session |
| US-152 | **App skeleton + core pages** — `src/web/` (app + templates + run entry); add the dependency to `requirements.txt`; **`/`** (players) + **`/ask`** (the flagship, with the trust line). Tests (test client) | High | ✅ Done | 1 session |
| US-153 | **More pages + docs** — a **fixtures** page and/or a saved-squad **analyse** page; run instructions; docs (Architecture, Handbook Ch 12, README, PROJECT_STATUS). Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-050 recorded + added to the ADR index — _US-151_
- [x] Add the web dependency to `requirements.txt` (+ note it's optional for the CLI) — _US-152_
- [x] Update Architecture changelog + the layer diagram (a second edge alongside the CLI) — _US-152_
- [x] Fill in Handbook Ch 12 (the chosen framework, for real this time) + README run steps — _US-153_
- [x] Update PROJECT_STATUS — _US-153_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — the test client hits `/`, `/ask`, and the extra page(s) (200 + expected
   content); `/ask` renders a known decision with its trust line; the existing **421** stay green; the
   analytics/CLI are unchanged (no new web import in the core).
2. **Manual smoke test done** — `uvicorn`/`flask run` locally: the home view, an `/ask` question (with and
   without Ollama — the trust line and the graceful degrade both show), a fixtures/analyse page.
3. **Documentation updated & checked** — ADR-050 + index, Architecture (+ the two-edge diagram), Handbook
   Ch 12, README (how to run the web UI), sprint board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A read-only, local-only web app reusing the analytics/`ask` | Any **write** action (saving/editing squads via the web) |
| Home players view + the `/ask` flagship + 1–2 more pages | Auth / a live manager-ID fetch (still deferred) |
| Server-rendered (`<pre>`-reuse or Jinja HTML per the gate) | A JS SPA / React / a build toolchain |
| The framework's test client + pytest | Deployment/hosting (local dev server only) |

**External Dependencies:** a web framework (**new** — FastAPI or Flask) + a template engine + a dev
server; assessed at the gate. The CLI keeps working without them (the web is an additive edge).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| First real dependency growth vs the lightweight ethos | Med | Gate the stack choice; keep the web edge isolated (`src/web/`); the CLI runs without it; pin minimal packages |
| Async complexity we don't need (if FastAPI) | Low | Use **sync** `def` handlers (FastAPI supports them) — no async unless a reason appears; or choose Flask (sync) at the gate |
| The web edge leaking into the core (breaking one-way flow) | Med | `src/web/` imports analytics; analytics import **nothing** web — a test/asserts the core has no web import |
| Security of a local server | Low | Read-only, no auth, bind `127.0.0.1`; Jinja autoescape on; it's a personal tool |
| Rendering rabbit hole (HTML polish) | Med | Slice 1 reuses the text renderers in `<pre>` (thinnest); HTML tables are a later, optional polish |

---

### 🗝️ Gating decision (US-151 → ADR-050)

Settle before code — the reuse path + the footprint are probed. Proposed (confirm/redirect at "start
US-151"):

1. **The stack — the key call.** **FastAPI + Jinja2 + uvicorn** (the Charter's named choice; a great test
   client; sync handlers so no needless async) **vs Flask** (lighter, sync, the classic server-rendered
   choice; arguably more aligned with "avoid unnecessary complexity"). *Propose FastAPI (honours the
   Charter + the handbook scaffold), sync-only — confirm/redirect at the gate.*
2. **The edge.** A new `src/web/` package: routes call the same analytics/`ask`; the analytics import
   nothing web (one-way flow preserved, enforced by a test). The CLI is untouched.
3. **The rendering — the other call.** *Propose:* reuse the **existing text renderers wrapped in `<pre>`**
   for slice 1 (zero new logic; the tables already align) inside a minimal page shell; HTML tables are a
   later polish. *(Alternative: Jinja HTML tables now — nicer, more code, duplicates the renderers.)*
4. **Scope & safety.** Read-only, local-only (`127.0.0.1`), no auth, no writes. Slice-1 routes: `/`
   (players) + `/ask` (flagship); then `fixtures` and/or `analyse`.

**Worked example (probed):** `ask.answer("who has the best fixtures over the next 5?")` returns a
structured `AskResult` (a `detail` FDR table + facts + trust) — an `/ask` handler renders exactly that,
trust line and all, in the browser.

---

### 📝 Session Progress Log

- **US-151 (gate) ✅** — Recorded **ADR-050**, both owner decisions settled: **stack = FastAPI, sync-only**
  (the Charter's choice + the Ch-12 scaffold + a first-class `TestClient`; plain `def` handlers so no
  async cost — Flask was the lighter alternative), and **rendering = reuse the text renderers in `<pre>`**
  for slice 1 (zero new logic; the same terminal-style output, trust line and all, in the browser; HTML
  tables a later polish). Settled the rest: a new **`src/web/`** edge whose handlers call the same
  `decision_xp`/`ask.answer`/optimiser, with the **core kept web-free** (a test will assert it) — one-way
  flow preserved; **read-only, local-only (`127.0.0.1`), no auth/writes**; Jinja autoescape; slice-1
  routes **`/`** (players) + **`/ask`** (flagship, degrades without Ollama), then fixtures/analyse;
  `fastapi`/`uvicorn`/`jinja2` (+`httpx` for tests) added web-only to `requirements.txt` (the CLI runs
  without them). Worked example: `ask.answer("best fixtures next 5")` → a structured `AskResult` the
  `/ask` handler renders verbatim. ADR-050 indexed.
- **US-152 ✅** — The **`src/web/`** edge. `app.py` — a FastAPI app (sync handlers): **`/`** (players via
  `render_player_table`), **`/fixtures`** (FDR via `render_fdr_table` — a free bonus off the shared
  `page.html`), **`/ask`** (the flagship: `render_ask(ask.answer(q))`, trust line and all, degrades
  without Ollama). Templates: `base.html` (a minimal shell + nav, theme-aware, `<pre>` styling),
  `page.html`, `ask.html` (a GET form). `__main__.py` runs it (`python -m src.web`, 127.0.0.1:8000 —
  `uvicorn` imported here, not in the CLI). `fastapi`/`uvicorn`/`jinja2` added web-only to
  `requirements.txt` (+`httpx` for the test client).
  - **Tests (427 total, +6; `test_web.py`):** `/`, `/fixtures`, `/ask` (with + without a question) return
    200 with the reused renderer output; Jinja **autoescaping** verified (a `<script>` in the query is
    escaped); and the **guardrail** — `test_core_never_imports_the_web_edge` statically asserts the core
    (analytics/ui/api/ask/cli/storage/…) contains no `src.web` import, so one-way flow survives.
  - **Smoke (real server):** `python -m src.web` served `/` (players table), `/fixtures` (Avg FDR), and
    `/ask?q=best fixtures next 5` (the grounded decision) — startup clean.
  - **Docs:** Architecture §12 changelog + the §3 diagram (two edges; core web-free). _More pages
    (analyse) + README/Handbook run steps are US-153._
- **US-153 ✅** — **`/squads`** (an index of saved squads → links) + **`/squad/{name}`** (a saved squad's
  health, via `ask.answer("analyse <name>")` + `render_ask` — so it reads identically to the CLI/`ask`);
  a `squads.html` template + a "Squads" nav link. Chose the thinnest reuse (route → the `ask` analyse
  intent) over duplicating `cmd_analyse`.
  - **Tests (429 total, +2):** `/squads` renders (with or without saved squads); `/squad/<unknown>` is
    graceful (a "name a saved squad" message, not a crash) — both hermetic (no dependence on local saved
    data).
  - **Smoke (real server):** `/squads` listed RoboTS + TS as links; `/squad/TS` rendered the analysis.
  - **Docs:** **README** — a "Web UI (optional)" section with run steps + the pages; **Handbook Ch 12
    (FastAPI)** filled in for real (the edge, the sync handlers, the TestClient, the one-way-flow rule,
    run steps) — no longer a stub; **PROJECT_STATUS** — Current Phase → Phase 4 complete + building the
    web UI, a Web UI line, Commands + Tests 429 / ADRs 50.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the web UI's first slice is live. `python -m src.web` serves **Players ·
Fixtures · Squads · Ask** as a thin, **read-only, local-only** FastAPI edge that reuses the analytics
untouched — the grounded `ask` answer, trust line and all, now renders in a browser. **429 tests** (was
421, +8), **50 ADRs**, ruff clean. The first sprint to grow the runtime footprint (fastapi/uvicorn/jinja2)
— kept **web-only**, so the CLI is unaffected.

**Delivered**
- **US-151 (gate)** — ADR-050: the stack (**FastAPI, sync-only**), `<pre>`-reuse rendering, `src/web/` as
  a new edge, read-only/local-only, the route scope.
- **US-152** — the `src/web/` app + templates + run entry; `/` (players) · `/fixtures` · `/ask` (the
  flagship); the dependency added web-only; the one-way-flow guardrail test.
- **US-153** — `/squads` + `/squad/{name}` (analyse, via the `ask` intent); README + Handbook Ch 12
  (filled for real) + PROJECT_STATUS.

**What went well**
- **The `<pre>`-reuse call paid off exactly as hoped** — every data view is a reused CLI renderer; the
  web added routes + a page shell and *almost no rendering code*.
- **"The CLI stays the engine" is now literal** — the handlers call the same `ask.answer`/analytics, and
  a test (`test_core_never_imports_the_web_edge`) enforces that the core never imports the edge.
- **The flagship shipped intact** — the grounded answer with its ✓/⚠ trust line renders in the browser,
  and degrades without Ollama exactly like the CLI.
- **Reuse decided scope again** — `/squad/{name}` is just `ask.answer("analyse <name>")`, not a
  re-implementation of `cmd_analyse`.

**Challenges / how they were handled**
- **First dependency growth vs the lightweight ethos** — contained: the deps are web-only in
  `requirements.txt`, isolated in `src/web/`, and the CLI runs without them (verified).
- **Hermetic web tests** — saved squads are gitignored/local, so the `/squads` and `/squad` tests assert
  *structure* (renders, graceful-on-unknown) rather than specific local names.
- **Sync in an async framework** — used plain `def` handlers, so FastAPI carries no async cost here.

**Carried forward:** None.
