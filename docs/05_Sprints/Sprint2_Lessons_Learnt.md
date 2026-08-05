# Lessons Learned

**Sprint:** Sprint 002 — Insight & Interaction

**Dates:** 2026-08-01

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Turn the static player dump into an interactive tool that gives real FPL insight —
refresh, search, filter, and rank players by value (Points-per-£m) from the CLI.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Layered architecture: adding a capability at the edge without touching the core.
- SQLite querying: parameterised `WHERE`, `LIKE`, combining filters with AND.
- Testing seams: dependency injection (a fake client) over monkeypatching.

### New Skills Acquired

- Building a command-line interface with `argparse` subcommands.
- Writing a derived metric in its own analytics layer (points ÷ price).
- Handling an "undefined" result honestly (None → "—", sorted last).

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- The same pattern worked for every story: new *entry point*, unchanged *core*.
- Confirm-first surfaced the real structural decisions (CLI location, ingest module,
  edge case, SQL-vs-Python filtering) before any code.
- The first analytics gave immediate insight — value-sort surfaces cheap high-scorers.
- Tests stayed fast and offline (9 → 29).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Two tech tasks slipped (FK enforcement, Handbook note) | Focused on the stories; side tasks deferred | Carried to Sprint 003 as explicit action items |
| Value undefined when price is 0 | Division by zero has no answer | Return None; show "—"; sort last |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Extending layers | Adding a command is a thin handler on top; the layers below don't change |
| Analytics layer | The first layer that *creates* a number rather than moving one |
| Where filtering lives | Storage owns querying — but only because every filter is a *stored* column |
| Parameterised SQL | `?` placeholders keep filters safe from injection |
| Dependency injection | Passing a fake client makes ingestion testable with no network |

---

# Development Lessons 💻

- A new capability should be additive and backward-compatible (optional args →
  `get_players()` still returns everything by default).
- Keep the interaction layer thin: it dispatches; the work lives in the layers.

---

# AI Collaboration Lessons 🤖

- The what/why/risks walkthrough was most valuable when the decision was structural
  (where does ingestion live? where does filtering happen?) rather than syntactic.
- Framing each story around *its role in the architecture* matched the learning goal
  better than walking through code line by line.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-003 | CLI = argparse subcommands in `src/cli.py`, thin `app.py`; analytics → `src/analytics/` | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Fixtures ingestion + a first Fixture Difficulty view (Roadmap Phase 2).
- Clear the carried tech tasks (FK enforcement; Handbook content).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Bump Handbook badges/chapters during a story, not in a separate sweep.

---

# Key Commands Learned

```text
python app.py refresh
python app.py table --sort value --limit 20
python app.py search haaland
python app.py filter --pos DEF --max-price 6

pytest -q
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Subcommand | A named action under one program (e.g. `app.py table`) |
| argparse | Python's standard library for parsing command-line arguments |
| Dependency injection | Passing a collaborator in (e.g. a fake client) instead of hard-coding it |
| Derived metric | A number the app calculates (e.g. points-per-£m), not read from source |
| Parameterised query | SQL using `?` placeholders for values — safe from injection |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-003 | Records why the CLI is argparse subcommands |
| Architecture §4 | The layer map, now including CLI + analytics |

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

- US-005 CLI skeleton + ADR-003
- US-006 Manual refresh command
- US-007 Points-per-£m value metric
- US-008 Search & filter players

**Stories Carried Forward:**

- None (2 technical tasks carried: FK enforcement, Handbook note)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
