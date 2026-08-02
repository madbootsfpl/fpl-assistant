# Lessons Learned

**Sprint:** Sprint 008 — Squad Selector Include/Exclude

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let the user force players in (favourites) or out (dislikes), and have the optimiser
build the best legal XI around those choices — with clear errors for ambiguous names
or impossible sets.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Extending a solver with fixed decisions (`pick = 1` / `0`).
- Validating input at the boundary before it reaches the core.
- Pressure-testing a design with worked examples before building.

### New Skills Acquired

- Name resolution with ambiguity handling (non-unique keys).
- Disambiguating shared names via a `Name:TEAM` form.
- Returning (results, errors) so a command can fail early and clearly.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- Tony's Sprint 007 idea shipped — from a retro note to a working feature.
- The plan-time data check pointed at the real work (name resolution, not the algorithm).
- The gate story pressure-tested ADR-009 with worked examples — no flaw slipped.
- "Resolve at the edge, then optimise" kept the solver clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `web_name` not unique (14 shared) | Two+ players share a name | Exact match + `Name:TEAM` disambiguation; list candidates |
| Impossible forced sets (2 GKs, over budget) | Forced picks break a rule | Solver returns Infeasible; friendly message (free validation) |
| Include + exclude the same player | Conflicting user input | Pre-check with a clear "can't do both" message |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Fixed decisions | "Must include/exclude" are the simplest ILP constraints |
| Validate at the edge | Resolve names first; the solver only sees valid ids |
| Free validation | The solver reports infeasible forced sets on its own |
| Data check value | Verifying data at planning shows *where the effort goes* |

---

# Development Lessons 💻

- Verify data at plan time — it revealed the hard part was the input, not the algorithm.
- Keep the core simple by validating input before it reaches it.
- Return errors (not exceptions) from a resolver so the command can report them cleanly.

---

# AI Collaboration Lessons 🤖

- The gate's worked examples (a standing habit now) verified the design before code.
- Framing the story around "resolve then optimise" kept the focus on the boundary.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-009 | Forced picks (`pick=1`/`0`); exact `web_name` + `Name:TEAM` disambiguation; validate at the edge | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

- This is so cool

---

# Improvements for Next Sprint 🚀

## Project Improvements

- 15-man squad, flexible formations, xP-based objective, or fuzzy name matching (backlog).
- Revisit data-dependent work once the season starts.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --include Haaland --exclude Salah   # optimal XI around your picks
python app.py squad --include "João Pedro"              # quote multi-word names
python app.py squad --include Wilson:NFO                # disambiguate a shared name
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Forced pick | A decision fixed in the solver (`pick = 1` or `0`) |
| Name resolution | Turning a typed name into the right player id |
| Disambiguation | Choosing between players who share a name (`Name:TEAM`) |
| Validate at the edge | Check user input before it reaches the core logic |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-009 | Records the include/exclude + name-resolution design |
| Handbook Ch 22 | Optimisation, now with the forcing-choices section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Optimisation / constraints | | |
| Handling user input safely | | |
| Reviewing decisions critically | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with? 
Really easy to include or exclude players.

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?
what additional valude would other data sources bring to the project? 
is this a good time to be looking at this or should we park for later?
a quick analysis shows that there are a number of free sources out there tha would include some insights.
Examples are:
Source	API Key Required?	Best For	Advanced Metrics (xG, xA)?
SoccerData / FBref	No (Python Library)	Deep analytical metrics, shot/pass data	Yes
Football-Data.org	Yes (Free Tier)	Clean fixtures, standings & match scores	Basic
API-Football	Yes (Free Tier)	In-match events & live scores	Basic/Intermediate
ClubElo	No	Team strength modeling & Elo history	N/A (Elo Ratings)
TheSportsDB	Yes (Free Tier)	Team/League metadata, logos, & schedules	Basic



---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-027 Include/exclude design + ADR-009
- US-028 Optimiser forced picks + name resolver
- US-029 The `squad --include/--exclude` command

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
