# Lessons Learned

**Sprint:** Sprint 048 — A fixtures / FDR `ask` intent

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let `ask`/`chat` answer fixtures questions — *"who has the best fixtures over the next 5?"*, *"when does
Arsenal play?"* — the biggest routing gap the Sprint-047 probe found. Two modes (a league FDR ranking, a
single team's schedule), reusing the existing `team_fdr` / `team_schedule` and their renderers; grounded
and verified; working in both `ask` and `chat`. Team names resolve or ask — never a wrong guess.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Building a feature almost entirely from parts that already exist.
- Deterministic routing under a broad keyword ("play") without collisions.
- Entity resolution that declines to guess (name / code / alias → or a message).

### New Skills Acquired

- Reusing analytics *and* their renderers as an `ask` intent's `detail` table.
- Case-sensitive short-code matching to avoid common-word false positives.

---

# What Went Well ✅

- **The gap was cheap to close** — the analytics and the renderers already existed, so the whole feature
  was a decision function + one router keyword. Checking what's built beat designing anything new.
- **It came live in `chat` for free** — the shared `_dispatch` (ADR-047) meant no chat wiring, and the
  *"why?"* follow-up even re-narrates a fixtures answer (it stores a decision with facts).
- **Team resolution never guesses** — the ambiguous bare "City" and the out-of-league "Wolves" get a
  message, ≥2 teams get a clarify, and a typed code matches without "new" false-firing.
- **Both modes fell out of one check** — *is a team named?* — schedule if so, league ranking if not.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "play" is a broad keyword | It must catch "when does Arsenal play?" without stealing other intents | Place `fixtures` **last** in routing; a routing test pins it |
| "the new gameweek" → NEW | A lowercased short-code match | Match short codes **case-sensitively** (typed codes are uppercase) |
| The FDR footer said "easiest" always | `render_fdr_table` hardcoded it | A `hardest` flag for the footer (CLI default unchanged) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Check what exists first | The biggest visible gap cost almost no code because the engines + renderers were already there |
| Routing order is a lever | A broad keyword is safe when its intent is matched *last*, after every specific one |
| Case carries signal | Team codes are uppercase; matching case-sensitively removes common-word collisions for free |
| Never guess an entity | Name/code/alias → resolve, else say "which team?" — a wrong-but-confident answer is worse (the `compare` rule) |
| One question, two modes | "Is a team named?" split schedule vs league ranking with no extra plumbing |

---

# Development Lessons 💻

- Before building, list the analytics and renderers already in the tree — the cheapest feature is a
  wiring job.
- Reach for the smallest signal that disambiguates (case, a single keyword's position) before adding
  logic.
- Smoke the new intent in *both* surfaces (`ask` and `chat`) — the shared dispatch means one wiring
  serves both, but only a run proves it.

---

# AI Collaboration Lessons 🤖

- The gate settled the one real decision (squad-scoped in/out) up front, so US-143/144 were mechanical.
- The grounding verifier ran on the new intent unchanged; a loose LLM venue phrasing still traced its
  figures/names, so ✓ held — and the table stays the source of truth.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-048 | A fixtures `ask` intent: two modes (league FDR ranking / single-team schedule) reusing `team_fdr`/`team_schedule` + renderers; `_match_team` resolves name/code/alias and never guesses; FPL difficulty; wired via `_dispatch` (works in `ask` + `chat`); squad-scoped deferred | Accepted |

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

- Squad-scoped fixtures (*"which of my players have good fixtures?"*); a differentials/value `ask`
  intent; a persisted or pronoun-aware chat; or (GW1, 2026-08-21) the full Phase-5 xMins; or the web UI
  (Phase 2).

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep starting from "what's already built"; keep the never-guess rule for any entity; keep the 3-part
  DoD and the both-surfaces smoke.

---

# Key Commands Learned

```text
python app.py ask "who has the best fixtures over the next 5?"   # league FDR ranking (easiest)
python app.py ask "which teams have the hardest fixtures?"       # ...the hard end
python app.py ask "when does Arsenal play next?"                 # one team's schedule (venue + difficulty)
python app.py chat                                               # ...the same, then "why?" to dig in
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| FDR | Fixture Difficulty Rating — how hard a team's upcoming opponents are (1–5) |
| Schedule mode | A fixtures answer for one named team (its next N fixtures) |
| League ranking mode | Teams ranked by average fixture difficulty (easiest or hardest) |
| Never-guess resolution | Match a team by name/code/alias, else ask — don't pick one |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-048 | The fixtures intent + the two modes + the resolution rule |
| ADR-004 / ADR-005 | The FDR analytics (`team_fdr`, `team_schedule`) this reuses |
| ADR-034 / ADR-037 / ADR-047 | The `ask` routing, the grounding verifier, and the shared `_dispatch` it plugs into |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Building from existing parts | | |
| Routing / keyword ordering | | |
| Entity resolution (never guess) | | |
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

- US-142 Gate — ADR-048 (two modes; never-guess resolution; squad-scoped deferred)
- US-143 `_match_team` + `_decide_fixtures` (both modes) + routing + `_dispatch` branch
- US-144 chat verification + docs

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
