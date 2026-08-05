# Lessons Learned

**Sprint:** Sprint 049 — Squad-scoped fixtures

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add a third `fixtures` mode: name a saved squad and `ask`/`chat` rank **your players** by their team's
upcoming fixture difficulty — the squad-relative view a manager reads before a transfer or captain call.
A join (player → its team's FDR) + a sort over the existing engine; grounded and verified; in both `ask`
and `chat`. Precedence: a specific team → its schedule; else a squad → the squad ranking; else the
league ranking.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a mode as a *join over an existing engine*, not a new one.
- Precedence ladders inside one decision function (team → squad → league).
- Verifying routing on the exact words a user would type.

### New Skills Acquired

- Possessive-aware token matching (`TS's` → `TS`) for squad resolution.
- A per-player fixtures view (`render_squad_fixtures`) distinct from the league table.

---

# What Went Well ✅

- **A new mode as a join, not an engine** — *player → its team's `team_fdr` → sort* plus a small
  renderer; the cheapest feature was again the one that reused what existed.
- **The gate probe caught a real routing bug** — *"which of **TS's** players…"* resolved to no squad
  (the possessive is one token). A one-line fix rescued the natural phrasing *and* every other
  squad-scoped intent.
- **Live in `chat` for free** — the shared `_dispatch` threading meant no chat wiring, and *"why?"*
  re-narrates a squad-fixtures answer.
- **Precedence fell out cleanly** — one ladder in one function; a named team still beats a squad.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "which of TS's players…" → no squad | The possessive "TS's" is one token; `_squad_name` split on whitespace | Strip a trailing `'s` — a general fix for every squad-scoped intent |
| Precedence (team vs squad vs league) | Three modes share one intent | A clear ladder in `_decide_fixtures`; tests pin each branch |
| Overlap with `analyse` | Both talk about a squad | Keep this a *fixtures* lens (team difficulty per player), not xP |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| A mode can be a join | Squad-scoped fixtures = player → team FDR → sort; no new analytics, just a renderer |
| Verify the real phrasing | The exact words ("TS's players") exposed a routing bug the tidy phrasings hid |
| One fix, many wins | Possessive-aware `_squad_name` helps captain/analyse/transfer too, not just fixtures |
| Precedence in one place | team → squad → league as a ladder is clearer (and testable) than scattered checks |

---

# Development Lessons 💻

- Probe routing with the messiest natural phrasing, not the clean one — the apostrophe was the whole bug.
- When a fix lives in a shared helper (`_squad_name`), it pays back across every caller — prefer that to
  a local patch.
- Keep a new mode a thin join over an existing engine; reach for a new renderer, not new analytics.

---

# AI Collaboration Lessons 🤖

- The gate settled the one real decision (the ranking lens) up front, so US-146/147 were mechanical.
- The grounding verifier ran on the new per-player facts unchanged; every figure and name traced.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-049 | Squad-scoped fixtures: a third `fixtures` mode (precedence team → squad → league) ranking a saved squad's **players** by their team's FDR (player-level); `_squad_name` possessive-aware; a small `render_squad_fixtures`; works in `ask` + `chat`; needs a named squad; FPL difficulty | Accepted |

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

- A differentials/value `ask` intent; a persisted or pronoun-aware chat ("is *he* worth it?"); a
  team-level squad-fixtures view (counts) as an option; or (GW1, 2026-08-21) the full Phase-5 xMins; or
  the web UI (Phase 2).

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep probing routing with messy phrasing; keep new modes as joins over existing engines; keep the
  3-part DoD and the both-surfaces smoke.

---

# Key Commands Learned

```text
python app.py ask "which of TS's players have the best fixtures?"    # your players by their fixture run
python app.py ask "which of TS's players have the hardest fixtures?" # ...the hard end
python app.py chat                                                   # ...then "why?" to dig in
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Squad-scoped fixtures | A saved squad's players ranked by their team's fixture difficulty |
| Precedence ladder | team → squad → league: the order `_decide_fixtures` picks a mode |
| Possessive-aware match | Resolving "TS's" to the squad "TS" (strip a trailing `'s`) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-049 | The squad-scoped mode + the precedence + the possessive fix |
| ADR-048 | The fixtures intent this extends |
| ADR-004 / ADR-005 | The FDR analytics (`team_fdr`) the join reuses |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Modes as joins over engines | | |
| Precedence in one function | | |
| Verifying real phrasings | | |
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

- US-145 Gate — ADR-049 (precedence; player-level lens; possessive fix)
- US-146 `_decide_squad_fixtures` + possessive `_squad_name` + `render_squad_fixtures` + dispatch
- US-147 chat verification + docs

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
