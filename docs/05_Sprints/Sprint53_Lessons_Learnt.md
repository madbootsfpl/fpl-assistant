# Lessons Learned

**Sprint:** Sprint 053 — Graduate the Streamlit edge to `src/web_streamlit/`

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Execute the ADR-051 decision: move the proven Streamlit spike out of `spikes/` into a real edge,
`src/web_streamlit/` — multipage, a clean run entry, tests, `streamlit` in `requirements.txt` — matching
the FastAPI edge's coverage plus interactive upgrades (filters + a chat Ask). Keep the FastAPI edge
frozen. The core stays the one engine.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Graduating a spike into a maintained `src/` edge (structure, run entry, tests).
- Reusing the one engine across yet another edge — clean layers paying interest again.
- Enforcing an architectural rule with a test as the surface grows.

### New Skills Acquired

- Streamlit multipage apps (`pages/`), `st.columns`, live filters, `st.chat_input`/`st.chat_message`.
- A clean run entry for a tool with an awkward launcher (`python -m …` sets `PYTHONPATH`).
- Testing Streamlit pages headlessly with `AppTest` (inputs → asserts, no server).

---

# What Went Well ✅

- **All three gate calls paid off** — multipage = clean per-page files; the `python -m` runner = no path
  hack in `src/`; both interactivity upgrades = the feel that motivated adopting Streamlit.
- **The engine is the one core** — graduation was routes-over-the-engine; nothing in `src/` changed; the
  guardrail (now both edges) holds.
- **Smoked the real command** — `python -m src.web_streamlit`, so the run quirk couldn't hide.
- **Nothing wasted** — FastAPI frozen as the lean reference; the spike removed cleanly.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `AppTest` couldn't find the pages | `AppTest.from_file` resolves a *relative* path against the test file's dir | Use absolute paths from the project root |
| `streamlit run` `sys.path` quirk (Sprint-052 bug) | The launcher puts the script's dir on the path, not the project root | Design it out: the `python -m` runner sets `PYTHONPATH` once |
| Two UI edges coexisting | Streamlit grown + FastAPI frozen | Guardrail renamed to cover both (`src.web` prefix); only Streamlit grows |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Design the quirk out once | A single runner (`python -m`) hides `streamlit run`'s path oddity — keeps `src/` clean |
| Test paths ≠ run paths | `AppTest.from_file` resolves relative to the *test* file — absolute paths avoid surprises |
| A prefix can cover both | `src.web` matches `src/web` *and* `src/web_streamlit`, so one guardrail check covers both edges |
| Graduate = plumbing, not rewrite | Structure + run entry + tests; the engine and its reuse were already proven |
| Interactivity is cheap in Streamlit | Filters + a chat are a few widgets — the payoff the adoption was for |

---

# Development Lessons 💻

- When a third-party tool has an awkward launcher, wrap it in a project-native entry (`python -m …`) so
  callers don't learn the quirk.
- Reproduce the exact user command in a smoke — twice now the convenient path hid a real one.
- Keep the architectural boundary a test; extend it as edges multiply, don't add a second rule.

---

# AI Collaboration Lessons 🤖

- The owner settled the three structure calls at the gate, so the build was mechanical.
- Interactivity (filters + chat) came almost for free once Streamlit was the edge — the adoption
  rationale, delivered.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-052 | The Streamlit edge — multipage `pages/`; a clean `python -m src.web_streamlit` runner (no `sys.path` hack); filterable table + chat-style Ask; `streamlit` web-only; the two-edge guardrail; FastAPI frozen | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- More Streamlit polish (charts on Fixtures; a compare/transfer page; a squad picker) — or move to **Data
  Hardening** post-GW1 (per-GW history + form), the substance the whole app is built to use. GW1: 2026-08-21.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep wrapping awkward launchers in `python -m` entries; keep smokes faithful to the real command; keep
  the guardrail a test as edges grow.

---

# Key Commands Learned

```text
python -m src.web_streamlit          # the Streamlit UI  → http://localhost:8501
python -m src.web                    # the frozen FastAPI edge → http://127.0.0.1:8000
python -m pytest tests/test_web_streamlit.py   # AppTest — headless page tests, no server
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Multipage (Streamlit) | An app laid out as `app.py` + a `pages/` folder; Streamlit builds the sidebar nav |
| `python -m` runner | A project-native entry that launches a tool with the right environment (here, `PYTHONPATH`) |
| Graduate (a spike) | Move proven spike code into `src/` as a real, tested edge |
| Frozen edge | A working, tested surface kept as a reference but not grown (the FastAPI edge) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-052 | The Streamlit edge structure + run entry + interactivity |
| `docs/08_Handbook/12_FastAPI.md` | How both web edges work in this project |
| ADR-051 | Why Streamlit (the measured decision) |

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

- US-156 Gate — ADR-052 (multipage; `python -m` runner; filters + chat)
- US-157 Graduated `src/web_streamlit/` (runner + four pages) + tests + the two-edge guardrail
- US-158 Interactivity (Players filters + chat Ask) + docs

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
