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

Active build — sprint by sprint. Phases 1 (CLI Analytics MVP), 3 (Decision Support)
and 4 (natural-language `ask`/`chat`) are complete. Next: a thin, read-only web UI
(FastAPI + Jinja, reusing the analytics — the CLI stays the engine), then Data
Hardening once the season starts.

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