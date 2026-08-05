# Lessons Learned

**Sprint:** Sprint 052 — A Streamlit spike (one engine, two edges, then decide)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Answer a strategy question on evidence, not opinion: build a throwaway Streamlit edge over the same
engine, measure it head-to-head against the FastAPI slice (learning fit, code, interactivity, deps,
architecture), and record the verdict for the web track as an ADR. A spike, not a pivot.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Deciding a direction with a measured spike (the project's "evidence, not opinion" discipline).
- Adding yet another edge over the one engine — reuse proving itself again.
- Recording a decision (and its *why*) as an ADR.

### New Skills Acquired

- Streamlit basics (tabs, `st.dataframe`, live widgets) + testing a Streamlit app headlessly (`AppTest`).
- Making a script runnable regardless of how the tool sets `sys.path`.

---

# What Went Well ✅

- **A spike beat an argument** — "learn web syntax vs learn a rapid tool" dissolved once 58 vs ~130+ LOC,
  interactive vs static, and +21 vs lean deps were on the table. Felt, then decided.
- **The engine is the one core, again** — Streamlit was a thin edge; the same `ask.answer`/analytics,
  nothing in `src/` touched, the guardrail intact.
- **Nothing wasted** — FastAPI frozen as a lean reference (and the architecture lesson), not binned.
- **The verdict fits the stated goal** — architecture/wiring over frontend syntax; the ADR records the
  reasoning, not just the choice.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `streamlit run` → `ModuleNotFoundError: No module named 'src'` | `streamlit run` puts the *script's* dir on `sys.path`, not the project root | Insert the project root before importing the engine (a path fix in the spike) |
| The AppTest smoke had hidden that bug | It ran from the project root, where `src` was already importable | A smoke must mimic the **real run command**, not a convenient one |
| Heavy dependency footprint (+21) | Streamlit drags a data-science stack | Measured + accepted (optional, local-tool cost); recorded as FastAPI's one win |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Spike, then decide | A day of throwaway code + measurements beats weeks of debating a direction |
| Smoke the real command | The convenient smoke (from the project root) hid a real `streamlit run` failure |
| `sys.path` depends on the launcher | `python app.py`, `python -m`, `streamlit run` each set the path differently |
| Less code ≠ fewer deps | Streamlit: ⅓ the code, but a big dependency tree — two different kinds of "weight" |
| Freeze, don't bin | A working, tested artifact kept as a reference costs ~nothing and preserves the lesson |

---

# Development Lessons 💻

- When choosing a tool, build the *same small thing* both ways and measure — the numbers decide.
- Reproduce the user's exact command before declaring something works.
- Keep an experiment in `spikes/` (ruff-excluded, not in `requirements.txt`) until a decision graduates it.

---

# AI Collaboration Lessons 🤖

- The owner steered the strategy (a spike, not a pivot) and made the final call from the evidence — the
  right split: I measured, he decided.
- Running the spike himself surfaced a bug a headless smoke missed — hands-on review catches what
  automation frames away.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-051 | The web track — **adopt Streamlit** (pure-Python, interactive; ~⅓ the code; fits "architecture over frontend syntax"; heavier deps optional/web-only) and **freeze the FastAPI edge** (ADR-050) as a lean reference; graduate the spike to `src/web_streamlit/` next | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Graduate the Streamlit edge** to `src/web_streamlit/` — a proper edge (tests + `requirements.txt`),
  then grow the pages (interactive tables, charts, a chat), keeping it a thin edge over the engine.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep deciding tool/direction questions with a measured spike; keep smokes faithful to the real command;
  keep experiments quarantined in `spikes/` until they graduate.

---

# Key Commands Learned

```text
streamlit run spikes/052-streamlit/app.py     # run a Streamlit app (opens the browser)
# headless test of a Streamlit script (no server):
python -c "from streamlit.testing.v1 import AppTest; \
           at=AppTest.from_file('spikes/052-streamlit/app.py').run(); print(at.exception)"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Spike | A throwaway build to gather evidence for a decision (then discarded or graduated) |
| Streamlit | A Python framework that turns a script into an interactive data app (widgets, tables, charts) |
| Rerun model | Streamlit re-executes the whole script top-to-bottom on each interaction |
| AppTest | Streamlit's headless test harness — runs the script and asserts, no live server |
| Graduate (a spike) | Move proven spike code into `src/` as a real, tested edge |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-051 | The web-track decision + the measured head-to-head |
| `spikes/052-streamlit/README.md` | The raw comparison evidence |
| ADR-050 | The FastAPI edge (now frozen) this compares against |

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

- US-154 The Streamlit spike (`spikes/052-streamlit/`) + the measured trade
- US-155 The head-to-head + ADR-051 (adopt Streamlit; freeze FastAPI)

**Stories Carried Forward:**

- Graduate the Streamlit edge to `src/web_streamlit/` (next sprint)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
