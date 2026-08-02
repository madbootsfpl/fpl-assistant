# Lessons Learned

**Sprint:** Sprint 003 — Fixtures & Difficulty

**Dates:** 2026-08-01 to 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Bring fixtures into the app and give the first fixture-based insight — rank teams by
how easy or hard their upcoming matches are (FDR), so decisions can weigh *who a team
plays*, not just past points.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Layered design: adding a whole new entity through each layer, predictably.
- SQL: filtering by stored columns, joining a table to itself (home + away teams).
- Refactoring safely behind tests (extract a shared helper, confirm green).

### New Skills Acquired

- Foreign-key enforcement in SQLite and why it matters with relationships.
- Aggregating analytics (per-team averages), not just per-row transforms.
- The "perspective" idea — the same fixture read differently by each team.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- The carry-over gate worked: tasks that slipped twice were done first; nothing slipped.
- A new entity (fixtures) was *boring* to add — it flowed through each layer like players.
- DRY refactors (`_get_json`, `_view`) paid off, and tests proved them safe.
- Storage-vs-analytics boundary held again: query in storage, compute in analytics.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `--help` didn't reveal Sprint 2 features (value/£m) | Subcommand options only show in that command's own help | Enriched command summaries + added an examples epilog |
| `.claude/settings.local.json` got staged | `git add -A` swept in a local file | Untracked + gitignored; review `git status` before commit |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Foreign keys | With relationships (a fixture → two teams), FK enforcement guarantees valid references — and dictates save order (teams first) |
| Aggregating metrics | FDR summarises a group (a team's next N), not one row |
| Perspective | The same fixture is easy for one side, hard for the other; each team reads its own difficulty |
| Refactoring | A shared helper is safe to extract when tests would catch a regression |
| Test limits | Tests verify behaviour, not discoverability — manual testing found the `--help` gap |

---

# Development Lessons 💻

- Gate carried tasks at the *start* of a sprint, with a Definition of Done — it stops slippage.
- A good layered design makes new work predictable; the boundaries do the thinking.
- Review `git status` before committing so local files don't sneak in.

---

# AI Collaboration Lessons 🤖

- The most valuable walkthroughs were the structural choices (where ingestion lives,
  SQL-vs-Python filtering, DRY helpers) — matching the goal of learning architecture.
- Small confirmations (DRY helper? shared perspective?) kept design decisions explicit.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-004 | Fixtures schema; FPL's own difficulty for v1; derive "upcoming" from unfinished fixtures (no events table) | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | | Need to do more testing at complete

---

# Things That Surprised Me 💡 _(for Tony)_

- how good Claude Code is

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Choose Sprint 004 direction: custom FDR (Attack/Defense, home/away) or the xP engine.
- Add a short per-sprint manual smoke-test checklist (does the UX reveal new features?).

## Personal Improvements _(for Tony)_

- No need to learn Phyton, learnings more geared on how things work, flow end to end and how the project is architectec

## Workflow Improvements

- Keep reviewing `git status` before each commit.

---

# Key Commands Learned

```text
python app.py refresh                          # players, teams, fixtures
python app.py table --sort value               # rank by value (points per £m)
python app.py fdr --next 5                      # teams by easiest upcoming run
python app.py fixtures --team ARS               # a team's upcoming fixtures

python app.py --help                            # now lists examples
sqlite3 data/fpl.db "SELECT COUNT(*) FROM fixtures;"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Foreign key | A column that must match a row in another table (referential integrity) |
| FDR | Fixture Difficulty Rating — how hard a team's upcoming matches are |
| Aggregate | A summary over many rows (e.g. an average), vs a per-row value |
| Perspective (fixtures) | Reading a fixture from one team's side (home vs away) |
| Self-join | Joining a table to another (here, fixtures → teams twice: home and away) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| FPL `/fixtures/` endpoint | Source of matches + per-side difficulty |
| ADR-004 | Records the fixtures/FDR decisions |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Python | | |
| SQL / joins | | |
| Foreign keys | | |
| Testing / refactoring | | |
| Analytics (aggregate) | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_
Great sprint and delighted i could add value manually testing. I have noticed that we are not keeping up with th eHandbook entries, like glossary etc. Need to do a better job there.

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-009 Fixtures data model + ADR-004
- US-010 Fixtures ingestion
- US-011 First FDR view
- US-012 Fixtures listing
- (+ carry-over: FK enforcement, Handbook chapters 20/21)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
