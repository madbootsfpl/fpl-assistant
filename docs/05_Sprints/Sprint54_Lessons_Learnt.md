# Lessons Learned

**Sprint:** Sprint 054 — Streamlit polish (charts + Transfer & Build pages)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Grow the Streamlit edge from "view the data" to "decide with it": add native charts (Fixtures FDR bar,
Players value scatter) and two interactive decision pages — Transfer (XI-aware swaps) and Build (the
optimiser under a budget). All reuse the existing engines; still a thin edge over the one core; no new
ADR.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Wiring interactive controls to existing engines — a page is sliders + a renderer.
- Reusing the *same* functions the CLI uses so the web can't drift.
- Hermetic tests for a data-dependent UI (assert structure / drive controls).

### New Skills Acquired

- Native Streamlit charts (`st.bar_chart`, `st.scatter_chart`) from list-of-dicts data.
- Asserting a chart in `AppTest` via `at.get("vega_lite_chart")` (no named accessor).
- Two reuse styles: call the engine directly, or build an NL request for the `ask` intent.

---

# What Went Well ✅

- **Every page was sliders wired to an engine** — near-zero new analytics; the web view of a
  transfer/build is byte-identical to the CLI (same functions + renderers).
- **Charts came free and native** — no charting library; a few lines on the existing data.
- **Both reuse styles worked** — Transfer via the engine directly (needs the bank param); Build via an NL
  query to the `ask` intent (reuses the whole build pipeline, the thinnest path).
- **Hermetic despite local-only saved squads** — tests assert structure / drive controls.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `AppTest` couldn't assert a chart | Native charts have no named `AppTest` accessor | They render as `vega_lite_chart` → `at.get("vega_lite_chart")` |
| Slider values → a build request | The `build_squad` intent parses plain English | Build the query conditionally (only archetypes > 0); verify the parser handles it |
| The default squad shows no swaps | RoboTS is xp-optimal (ADR-041) | Correct behaviour, not a bug — TS shows real swaps |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| A page = controls + engine + renderer | Interactive features are cheap when the engine already exists |
| Reuse beats re-implement | Calling the CLI's own functions means the web can't diverge from it |
| Two valid reuse styles | Engine-direct (fine control, e.g. a bank slider) vs an NL query to `ask` (thinnest) |
| Native charts are enough | `st.bar_chart`/`st.scatter_chart` on the same data — no library, no new deps |
| Test what the tool exposes | Discover the `AppTest` element type (`vega_lite_chart`) rather than guess an API |

---

# Development Lessons 💻

- When a control maps to an existing engine parameter, wire it directly; when it maps to an existing NL
  intent, build the sentence — pick the thinnest reuse.
- Keep UI tests hermetic: assert the page renders / a control drives it, not specific local data.
- A "no result" that's actually correct (an optimal squad has no upgrades) is a feature — show it plainly.

---

# AI Collaboration Lessons 🤖

- The owner picked the scope up front (charts + Transfer + Build), so the build was a straight execution.
- Reuse kept the surface honest — no chance for the web to compute something the CLI wouldn't.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| — | No ADR — UI polish over the settled Streamlit edge (ADR-052). Scope (charts + Transfer + Build) was the only call, settled at planning. | n/a |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A **Compare** / **Captain** page (round out the decision pages); small chart polish (a per-GW xP line).
  Or move to **Data Hardening** post-GW1 (per-GW history + form) — GW1: 2026-08-21.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep pages as controls-wired-to-engine; keep tests hermetic; keep reusing the CLI's own functions.

---

# Key Commands Learned

```text
python -m src.web_streamlit          # the Streamlit UI (Players/Fixtures/Squads/Transfer/Build/Ask)
python -m pytest tests/test_web_streamlit.py   # AppTest — headless page tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Native chart | `st.bar_chart`/`st.scatter_chart` — Streamlit's built-in charts (no library) |
| `vega_lite_chart` | The element type native charts render as (how `AppTest` sees them) |
| Controls-wired-to-engine | A page is inputs → an existing engine call → a renderer; no new analytics |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/08_Handbook/12_FastAPI.md` | How the web edges + pages work |
| ADR-046 / ADR-041/043/044 | The Transfer (XI-aware) + Build (archetype) engines the pages reuse |
| ADR-052 | The Streamlit edge these pages extend |

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

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-159 Charts (Fixtures FDR bar + Players value scatter)
- US-160 Transfer page (bank/count → XI-aware swaps)
- US-161 Build page (budget/archetypes → optimal 15) + docs

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
