# fpl-assistant - Claude Code Instructions

## Project Purpose

Build a Fantasy Premier League assistant that helps analyse:

- player performance
- fixtures
- transfers
- captain choices
- team optimisation


## Project Philosophy

This is a learning project.

Priorities:

1. Understanding
2. Documentation
3. Maintainability
4. Functionality


## Development Approach

Before making significant changes:

1. Explain what will change
2. Explain why
3. Identify risks
4. Confirm approach


## Documentation Rules

Major changes should update:

- docs/01_Journal
- docs/03_Architecture
- docs/04_Roadmap
- docs/06_Decisions


## Coding Principles

- Prefer simple solutions
- Avoid unnecessary complexity
- Keep modules small
- Write readable code
- Comment why, not what
- Add tests for important logic


## AI Team Roles

ChatGPT:
- Product owner
- Architecture
- Planning
- Documentation

Claude Code:
- Implementation
- Refactoring
- Testing

Ollama:
- Local AI experiments


## Current Phase

**All six build phases are complete.** The CLI is the engine; a Streamlit web app runs a **closed beta**.

⚠️ The web UI shipped as **Streamlit**, not the thin FastAPI edge the older plan described — if you read that
plan anywhere, it is history, not a pending task.

**Just landed (September 2026), and both change how the project works day to day:**

- **The data refreshes itself** (ADR-211). Squad data lives in **Postgres** (Supabase); a scheduled GitHub
  Action keeps it current. ⚠️ `reseed` still exists but now only rebuilds the **SQLite test fixture** — it is
  no longer a deploy step.
- **The Supabase store is hardened.** Tables holding emails and saved squads are closed to the publishable
  key; the app reaches them through twelve `security definer` functions. Setup is one file —
  `sql/setup.sql` — explained in `docs/SUPABASE_RLS.md`. 🔴 **Never add a `using (true)` policy or
  `disable row level security` to those tables**; that is the hole this closed, and `tests/test_setup_docs.py`
  guards the docs against re-teaching it.

**Next: a Flutter mobile app** — see `docs/03_Architecture/Mobile_Platform_Audit.md`. The driver is feedback,
not architecture: people don't want a browser for FPL.

For the live status and forward plan, see:
- docs/00_Project/PROJECT_STATUS.md (the single live status)
- docs/04_Roadmap/Roadmap.md (the consolidated forward plan)


## Working Rhythm

Each feature runs on a gate-per-feature loop:

1. Plan the sprint — verify the design on **real data** before committing to it.
2. Gate — agree the approach and record it as an **ADR** *before* building.
3. Implement — every feature meets a **3-part Definition of Done**: automated
   tests, a manual smoke test, and updated docs.
4. Retro — fill the sprint review + lessons, update PROJECT_STATUS, commit + push.

Still true: **do not build a feature before its design is agreed** (that is the gate).