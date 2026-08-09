# Lessons Learned

**Sprint:** Sprint 137 — Analytics coverage: feature events, perf timers, a gated admin view

**Dates:** 2026-08-09

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Turn the Sprint 136 analytics *foundation* into full coverage: the **feature events** + `error`, **perf timers** on
the key operations, and a **gated admin view** so the owner reads the numbers in-app. Still opt-in, anonymous, and
fail-silent (ADR-100).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Instrument at the seam, not the engine** — every event/timer is at the web layer; `decision_xp` stays clean.
- **Make anonymity a test, not a promise** — assert the handle/message never appear in any payload.

### New Skills Acquired

- **Don't time a Streamlit render — time the compute.** A view render contains `st.rerun()` (a `RerunException`
  from button handlers), so wrapping a whole render in `timed` would record `ok=False` on every click. Wrapping
  just the calculation/IO (the optimiser, the `Storage` reads, the store save/load) keeps `ok` honest and avoids a
  `perf` event per rerun. The boundary of "what to time" matters as much as timing itself.
- **The first *read* of a write-only table needs its own RLS + gate.** `events` was INSERT-only; the admin view is
  the first SELECT. Because the anon key is **server-side** (Streamlit secrets, never in a browser) and events are
  anonymous, an **anon SELECT policy** is safe — the *server* reads, testers can't. Pair it with an owner-password
  gate (`FPL_ADMIN_KEY`) so the tab is inert on the public deploy.
- **PostgREST won't do percentiles — so aggregate in Python.** Fetch recent rows and compute counts/median/P95 in
  a **pure** `summarise` (unit-tested), keeping the page a thin renderer. For hobby-beta volume that's simpler and
  ample; no SQL functions or a BI tool.
- **Anonymity has sharp edges at specific events.** `squad_saved`/`squad_loaded` naturally *want* to log the
  handle — the very thing that mustn't be logged. Naming that trap up front (and testing it) is how the
  minimal/anonymous contract survives new instrumentation.

---

# What Went Well ✅

- **Anonymity held under new events** — the handle/message are pinned out of every payload.
- **Perf timing avoided the rerun trap** — timed the compute/IO, not the render.
- **The read stayed small + safe** — a pure `summarise` + a thin gated page; best-effort, can't crash.
- **One-liner wiring** — the no-op-when-off client meant instrumenting changed nothing for the suite.
- 885 → 898 tests (+13); ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Timing a render marks failures | a render raises `RerunException` on button clicks | Time the compute/IO only, not the render |
| The admin view can't read `events` | RLS was INSERT-only | An anon SELECT policy (server-side key, anonymous data) + a password gate |
| No percentiles in PostgREST | it's a thin REST layer | Fetch rows, aggregate in a pure `summarise` (median/P95 in Python) |
| `squad_saved` wants the handle | the handle is the save key | Log the event only — no handle/contents; a test pins it |
| A 10th page broke fixed tests | the page-list/emoji tests enumerate pages | Update them to include the Admin tab |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| What to time | Wrap the calculation/IO, not a render (which reruns) — keeps `ok` honest |
| First read of a table | Add a scoped RLS SELECT + an owner gate; the anon key is server-side |
| Aggregate where it's easy | PostgREST can't percentile; do it in a pure, tested `summarise` |
| Anonymity per event | Some events (save/load) tempt PII (the handle) — pin it out with a test |

---

# Development Lessons 💻

- Put telemetry at the web seam; never reach into the engine to time or count.
- For a background/side-effect read, keep the pure aggregation separate from the I/O and the rendering — test the pure part.
- When you add a page, remember the tests that enumerate pages (page-list, per-tab header) and update them.

---

# AI Collaboration Lessons 🤖

- Analytics still **observes the app, not the model**: the events record *that* an analysis ran / a squad saved,
  never *what* the engine decided or *which* squad. The admin view is a **read** of anonymous aggregates, gated —
  it adds no write and doesn't touch the grounded/analytics-decide posture (ADR-037/041).

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — extends **ADR-100** (which named these as the fast-follow). US-335: feature events + `error` at the web
sites (anonymity-tested). US-336: perf timers on the compute/IO (not renders). US-337: the first analytics read — a
pure `summarise` + a thin `pages/9_Admin.py` gated by `FPL_ADMIN_KEY`, needing an anon SELECT policy on `events`.
Docs: ANALYTICS.md (SELECT policy + admin key + the view), BETA.md, PROJECT_STATUS, Architecture._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (the smoke):** add the anon **SELECT** policy on `events` + set **`FPL_ADMIN_KEY`** → open the 📊 **Admin**
  tab → confirm the dashboard reads real events. Then the analytics epic (ADR-100) is fully closed.
- **Deferred:** event **batching** (if volume grows); a full **BI dashboard**; **cohort/funnel** analysis.
- **GW1 (2026-08-21):** the big body — calibrate the set-piece / DefCon / form weights + backtest; momentum;
  live manager import.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep telemetry at the seam, anonymity tested per event, and the pure aggregation separate from I/O + rendering.

---

# Key Commands Learned

```text
python -m pytest tests/test_analytics.py tests/test_web_streamlit.py -q   # the events, perf timers, summarise, admin gate
# enable the admin tab: FPL_ADMIN_KEY = "…"  + the anon SELECT policy on events (docs/ANALYTICS.md)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Time the compute, not the render | Wrap the calculation/IO in `timed`, not a Streamlit render (which reruns) |
| Anon SELECT policy | An RLS rule letting the server-side anon key read anonymous events (for the admin view) |
| Pure summarise | The aggregation (counts/median/P95) as an I/O-free function, unit-tested |
| Returning device | An anonymous device id seen on 2+ distinct days |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/analytics.py` (`recent_events`, `summarise`, `timed`) | The read + the pure aggregation + timing |
| `src/web_streamlit/pages/9_Admin.py` | The gated admin dashboard (thin renderer) |
| `docs/ANALYTICS.md` | Owner setup — the SELECT policy, the admin key, the view + SQL |
| `tests/test_analytics.py` | `summarise`/gate/anonymity tests |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful (owner smoke to light up the Admin tab) ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-335 Feature events + `error` at the action sites (anonymity-tested)
- US-336 Perf timers (`data_load`/`analysis`/`squad_save`/`squad_load`) — compute/IO, not renders
- US-337 The gated admin view — `recent_events` + a pure `summarise` behind `FPL_ADMIN_KEY`

**Stories Carried Forward:**

- None. (Batching, a BI dashboard, cohorts, and `player_viewed` remain deferred.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
