# FPL Assistant Development Journal

## Session 1 -- Environment Setup

### Goal

Prepare the Mac mini for Python development and create the foundation
for the FPL Assistant project.

## What we installed/configured

### Homebrew

Installed the native Apple Silicon Homebrew.

Verified: - `which brew` → `/opt/homebrew/bin/brew`

### Python

Initially: - `python3 --version` → `3.10.4`

Discovered: - Homebrew Python 3.14 was installed but the shell was still
using the older Python.

Fixed by:

``` bash
hash -r
```

Verified:

``` bash
which python3
python3 --version
```

Expected:

``` text
/opt/homebrew/bin/python3
Python 3.14.6
```

## Project structure

Created:

``` text
~/Projects/fpl-assistant
```

Created a virtual environment:

``` bash
python3 -m venv venv
source venv/bin/activate
```

Verify:

``` bash
which python
python --version
```

## Initial project files

-   app.py
-   README.md
-   requirements.txt
-   .gitignore

Suggested docs folder:

``` text
docs/
    Vision.md
    Backlog.md
    Sprint1.md
    Architecture.md
```

## Git

Initialise:

``` bash
git init
git add .
git commit -m "Initial project structure"
```

## Tips learned

-   Use one Python virtual environment per project.
-   Keep documentation in Git.
-   Commit little and often.
-   Build one user story at a time.
-   Use GitHub Issues as your backlog.
-   Think in sprints rather than giant feature lists.
-   Keep architecture decisions written down.

## Suggested Sprint 1

1.  Create project structure
2.  Connect to FPL API
3.  Download player data
4.  Display player table
5.  Search players
6.  Filter players
7.  Calculate Points per £m
8.  Refresh latest data

## Commands reference

``` bash
python3 -m venv venv
source venv/bin/activate
python app.py
git init
git add .
git commit -m "Initial project structure"
```

## Personal notes

Treat this as a product, not just a coding exercise. The aim is to learn
modern software development while building a useful FPL analytics
platform.

---

## Session 2 -- Planning & Architecture

**Date:** 2026-07-31
**Sprint:** Sprint 001 (Foundations & First Data Slice)
**Related:** US-001, ADR-001, ADR-002

### Goal

Turn the documentation into an agreed plan before any code is written —
per the project rule "do not build features before the design is agreed."

### Starting state

Docs only, no application code. Architecture doc empty; PROJECT_STATUS
held placeholder text; a docs reorganisation was uncommitted.

### What we did

- **Reviewed the whole docs folder** and identified gaps (empty
  Architecture, empty Sprint1, placeholder status, uncommitted reorg).
- **Wrote the Sprint 001 plan** (`docs/05_Sprints/Sprint1.md`) — a
  foundation sprint scoped to one vertical slice: fetch → store → display
  player data. Deliberately capped at 4 user stories to avoid scope creep.
- **Fixed PROJECT_STATUS.md** — replaced placeholder ("Sprint test",
  "Story X") with the real phase/sprint/story.
- **Drafted Architecture v0.1** (`docs/03_Architecture/Architecture.md`) —
  a three-layer design (ingestion → storage → presentation) with a strict
  one-way data flow, a small SQLite schema (teams + players), and a
  proposed `fpl/` package layout.
- **Recorded two decisions** as ADRs:
  - **ADR-001** — build a single-user / internal tool for now (multi-user
    deferred, but the schema stays multi-manager-friendly).
  - **ADR-002** — console display now, FastAPI later, web-UI framework
    choice deferred.
- **Marked Architecture v0.1 as Agreed** once the ADRs were accepted.

### Commits

```text
5b53cef  Add Sprint 001 plan, update project status, reorganise docs
d67c085  Add architecture v0.1 draft and ADR-001/ADR-002
e05b084  Mark architecture v0.1 as agreed
```

### Decisions made

- Keep Sprint 001 small: one end-to-end slice, no analytics yet.
- No web framework in v0.1 — a console table is enough to prove the
  pipeline; the layered design lets us swap in FastAPI later without a
  rewrite.

### Next steps

- Begin **US-002**: build the FPL API client that fetches
  `/bootstrap-static/`.
- Then US-003 (persist players to SQLite) and US-004 (display table).
- Open questions still to settle later: caching TTL strategy, and
  when/whether to move from SQLite to PostgreSQL.

### Lessons / notes

- Agreeing the architecture and writing decisions down *before* coding
  made the scope obvious and kept Sprint 001 from ballooning.
- ADRs are cheap to write and mean "future Tony" can see *why* a choice
  was made, not just what it was.