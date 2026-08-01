# Lessons Learned

**Sprint:** Sprint 001 — Foundations & First Data Slice

**Dates:** 2026-08-01

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Establish the project's technical foundation and prove one complete vertical
slice: connect to the FPL API, persist player data locally, and display it.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Git: small, single-purpose commits with clear "why" messages.
- Python packages/modules and imports (`src/` layout, `__init__.py`).
- Working with an external API and JSON.

### New Skills Acquired

- Writing a testable HTTP client and mocking the network in tests.
- SQLite from Python: schema creation, parameterised queries, upsert.
- `pytest`: fixtures (`tmp_path`, `monkeypatch`), arrange–act–assert.
- Dataclasses as simple data models with a `from_api` mapper.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- Design-first: architecture + ADRs agreed before code → 4 tight stories, no roll-over.
- Layered design held end-to-end (client → storage → display), each layer isolated.
- Tests are fast and fully offline (mocked HTTP, temp DBs).
- Confirm-first (what/why/risks) surfaced real decisions instead of guesses.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Sprint doc drifted from reality | Status/checkboxes not updated as work landed | Did a "sync with reality" pass; action item to update as we go |
| `src/api` couldn't become a package | It existed as a stray 0-byte file, not a directory | Replaced the file with a real directory + `__init__.py` |
| Live data looked odd (players sharing a team_id) | 2026-season API returned off-season/placeholder assignments | Confirmed it's a data quirk, not a code bug |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Upsert | `INSERT … ON CONFLICT(id) DO UPDATE` makes re-runs idempotent (proven: ran app twice, counts unchanged) |
| Layering | Keeping display "pure" (returns a string, no I/O) makes it trivially testable |
| Caching | "Fetch once, read locally" is why the app works with no internet |
| SQL joins | `LEFT JOIN` keeps a player even when its team is missing (vs inner join dropping it) |

---

# Development Lessons 💻

- Writing decisions down (ADRs) before coding kept scope obvious and small.
- One story per commit keeps history readable and easy to review.
- A stray-file/scaffold sanity check saves time before building packages.

---

# AI Collaboration Lessons 🤖

- Confirm-first (explain what/why/risks, then a quick decision) caught real
  choices: mapping location, storage shape, row limit, team-name via JOIN.
- Small scoped stories are far easier to review and understand than big asks.
- Reviewing each change (and explaining the data flow back) built real
  understanding, not just working code.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-001 | Single-user / internal tool (multi-user deferred) | Accepted |
| ADR-002 | Console display now, FastAPI later, web UI deferred | Accepted |

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

- Build search, filter, Points-per-£m, and manual refresh (Sprint 002).
- Consider enabling SQLite foreign-key enforcement.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the sprint board in step with the work as it lands, not after.

---

# Key Commands Learned

```text
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

pytest
pytest -q

git add -A
git commit -m "message"
git log --oneline
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Upsert | Insert a row, or update it if the id already exists |
| Fixture (test) | A saved/sample input so tests don't hit the live API |
| Mock / monkeypatch | Replacing a real call (e.g. network) with a fake in tests |
| LEFT JOIN | Combine tables, keeping rows even when there's no match |
| Dataclass | A concise Python class that mainly holds data |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| FPL `bootstrap-static` endpoint | The project's primary data source (players/teams) |
| Developer Handbook (docs/08_Handbook) | Personal reference for every tool used |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Python | | |
| Git | | |
| VS Code | | |
| APIs | | |
| JSON | | |
| SQLite | | |
| Testing | | |
| Architecture | | |
| AI-assisted Development | | |

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

- US-001 Agree architecture v0.1
- US-002 FPL API client
- US-003 Persist players to SQLite
- US-004 Display player table

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
