# Lessons Learned

**Sprint:** Sprint 051 — A thin web UI (first slice)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Open the web-UI track, kept deliberately thin: a read-only, local-only FastAPI edge that reuses the
analytics/`ask` untouched — Players / Fixtures / Squads / **Ask** — the CLI stays the engine, the web is
just a second view. A GW1-ready shell, not a full interactive app.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a new *edge* to a layered app without touching the core.
- Enforcing an architectural rule with a test (the core stays web-free).
- Choosing the thinnest reuse (routes + a page shell over the existing renderers).

### New Skills Acquired

- FastAPI with **sync** handlers + Jinja2 templates + `TestClient`.
- Running an ASGI app locally (`uvicorn`, bound to 127.0.0.1) via `python -m src.web`.
- Keeping a new dependency **optional** (web-only in `requirements.txt`; the CLI runs without it).

---

# What Went Well ✅

- **`<pre>`-reuse paid off** — every data view is a reused CLI renderer; the web added routes + a shell
  and almost no rendering code. The gate's "thinnest first" call was right.
- **"The CLI stays the engine" is now literal** — handlers call the same `ask.answer`/analytics; a test
  asserts the core never imports the edge, so the one-way flow survives.
- **The flagship shipped intact** — the grounded `/ask` answer renders with its ✓/⚠ trust line and
  degrades without Ollama, exactly like the CLI.
- **Reuse decided scope** — `/squad/{name}` is just `ask.answer("analyse <name>")`, not a re-write of
  `cmd_analyse`.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| First dependency growth vs the lightweight ethos | A web framework is real weight | Web-only in `requirements.txt`; isolated in `src/web/`; the CLI runs without it (verified) |
| Hermetic web tests | Saved squads are local/gitignored | Assert structure (renders, graceful-on-unknown), not specific local names |
| Async framework, sync app | FastAPI is async-first | Plain `def` handlers — no async cost here |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| An edge, not a rewrite | The layered core meant the web is routes calling the same engine — ADR-002's promise, cashed in |
| Enforce architecture with a test | `test_core_never_imports_the_web_edge` makes "one-way flow" a checked fact, not a hope |
| Thinnest rendering first | Reusing the text renderers in `<pre>` shipped a working UI with ~no new presentation code |
| Keep new deps optional | Web-only extras keep the CLI's tiny footprint intact |
| Sync is fine | FastAPI supports sync handlers — take the modern framework without the async tax |

---

# Development Lessons 💻

- When adding a surface, first ask "what can I reuse verbatim?" — here, the renderers *and* the `ask`
  engine.
- Make an architectural boundary a test, not a comment — it can't rot.
- Grow the dependency footprint deliberately and visibly (a labelled, optional section), not silently.

---

# AI Collaboration Lessons 🤖

- The owner steered the two real calls at the gate (FastAPI vs Flask; `<pre>` vs HTML) — both settled
  before any code, so the build was mechanical.
- The grounded `ask` moved to a new surface unchanged — the discipline (analytics decide, verified) is
  portable because it lives in the engine, not the edge.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-050 | A thin web UI: a read-only, local-only **FastAPI** (sync) edge in `src/web/` reusing the analytics/`ask`; slice-1 reuses the CLI text renderers in `<pre>`; the core stays web-free (a test asserts it); pages `/` · `/fixtures` · `/squads` · `/squad/{name}` · `/ask` | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

-

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Web polish (HTML tables, small styling) if wanted; a `/compare` or `/transfer` page; or move on to
  **Data Hardening** (post-GW1: per-GW history + form) — the substance the whole app is built to use.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep enforcing boundaries with tests; keep new deps optional + labelled; keep the both-surfaces smoke
  (CLI unchanged + the web serves).

---

# Key Commands Learned

```text
pip install -r requirements.txt     # fastapi / uvicorn / jinja2 (web-only)
python -m src.web                   # serve the web UI at http://127.0.0.1:8000
# tests:
python -m pytest tests/test_web.py  # FastAPI TestClient — no live server needed
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Edge | A presentation surface (CLI or web) over the shared analytics core |
| ASGI / uvicorn | The async server spec / the server that runs the FastAPI app |
| TestClient | FastAPI's in-process HTTP client for tests (no live server) |
| One-way flow | The core imports nothing from an edge — enforced here by a test |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-050 | The web-UI design (stack, rendering, edge, scope) |
| `docs/08_Handbook/12_FastAPI.md` | How the web edge works in this project |
| ADR-002 / ADR-003 | Why the UI waited, and why the CLI came first |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| FastAPI (sync) + templates | | |
| Adding an edge to a layered app | | |
| Enforcing boundaries with tests | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?
- simple but effective readonly frontend, ask feature is interactive

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?
- I am thinking should we pivot to Streamlit or Gradio or stay with the web polish
- agin my thinking, from a learning perspective, is learning the how of web design or learning how to push using a 3rd party tool more advantageous to me.
- Can we develop that thought?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-151 Gate — ADR-050 (FastAPI sync; `<pre>`-reuse; the web edge)
- US-152 The `src/web/` app + `/` · `/fixtures` · `/ask` + the guardrail test
- US-153 `/squads` + `/squad/{name}` (analyse) + docs (README, Handbook Ch 12, PROJECT_STATUS)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
