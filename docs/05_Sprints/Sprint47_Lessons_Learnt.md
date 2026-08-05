# Lessons Learned

**Sprint:** Sprint 047 — Conversational `ask` (a chat mode with grounded follow-ups)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make `ask` conversational: a `chat` REPL where a second question builds on the first — *"why?"*, *"and
the second best?"*, *"what about defenders?"* — while keeping the discipline that made `ask` trustworthy:
the **analytics decide every turn**, the LLM only narrates, and every answer is grounding-verified. Three
follow-up families (why / next / what-about), an in-memory `Context`, no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding state to a stateless pipeline *without* loosening its guarantees.
- Deterministic intent/follow-up detection (the model never routes).
- Refactoring to a single shared path (`answer` = `converse`-with-no-context).

### New Skills Acquired

- A conversational context model (last turn: intent, squad, decision, rank).
- Keeping a stateful REPL loop I/O-free so it's unit-testable.

---

# What Went Well ✅

- **The gate probe pinned the safety property** — every bare follow-up routes to None today, so a
  resolver *before* `route()` is collision-free; the build was mechanical after that.
- **A follow-up is an offset, not new intelligence** — the engines already rank, so "second best" is
  rank #2 and "why" re-narrates the *same* facts. Grounding never had to change.
- **One pipeline for one-shot and chat** — `answer()` became `converse()`-with-no-context, so there's
  less code and the one-shot behaviour is provably unchanged.
- **The REPL smoke worked first time end-to-end** (with Ollama up): captain → why → second best → what
  about defenders, each grounded with a ✓ trust line.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "what about defenders?" returned None | Position match was singular-only ("defender" ≠ "defenders") | Match position words singular *and* plural |
| …and it silently dropped the £8m cap | It fell through to a *fresh* shortlist, losing the constraint | The fix restored the continuity (kept ≤£8m) |
| Testing a stateful REPL | input()/print() aren't unit-test friendly | Keep `chat_transcript` I/O-free; a thin CLI shell does the stdin/print |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| State without losing guarantees | Memory of the last turn is fine *if* every turn is still analytics-decided + verified |
| Detection on subject-less lines | A line is a follow-up only when every word is filler — so "why?" is one but "why is Haaland good?" isn't; that makes it collision-free |
| Reuse the ranking you already have | "second best" is an offset into a list the engine already produces — not a new query |
| Collapse to one path | `answer = converse(no context)` removes duplication and pins one-shot behaviour |
| I/O-free cores test better | The loop threads context over an iterable of lines; the CLI shell adds input/print |

---

# Development Lessons 💻

- Probe the *routing* on real phrasings before designing detection — the "all bare follow-ups fall
  through today" finding is what made a pre-route resolver safe.
- Smoke broadly: the plural blind spot (and the dropped price cap it caused) was invisible to the gate
  and the unit tests — only the real conversation showed it.
- When adding a mode, make the old path a special case of the new one, not a fork.

---

# AI Collaboration Lessons 🤖

- The gate walk-through + a live-DB probe settled the one real decision (what-about scope) before code.
- The grounding verifier kept doing its job every turn — a follow-up doesn't get a pass; "why"
  re-narrates the *same* facts and is checked against them.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-047 | Conversational `ask`: a `chat` REPL + an in-memory `Context`; follow-ups detected by subject-less trigger *before* routing; three families — **why** (re-narrate the same facts), **next** (rank offset), **what-about** (shortlist-only position swap, keeping constraints); analytics decide every turn; grounding (ADR-037) unchanged | Accepted |

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

- A **fixtures / FDR `ask` intent** (the biggest remaining gap — the analytics already exist); a
  differentials/value intent; then a persisted or pronoun-aware chat ("is *he* worth it?"); or (GW1) the
  full Phase-5 xMins; or the web UI (Phase 2).

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep probing routing on real phrasings; keep smoking the full conversation; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py chat                 # interactive; follow-ups build on the last answer
#   > who should I captain from my-team?
#   > why?                         # re-explains the last pick
#   > and the second best?         # the next-best pick
#   > what about defenders?        # (after a shortlist) swap position, keep the price filter
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Follow-up | A short, subject-less question that builds on the last turn (why / next / what-about) |
| Context | The last successful turn held in memory: intent, squad, decision, rank |
| Rank offset | Reading the Nth-best from a list the engine already ranks ("second best") |
| converse | The per-turn engine: a follow-up on the context, else a fresh question |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-047 | The conversational design + the three follow-up families |
| ADR-034 / ADR-037 | The `ask` routing + the grounding verifier this builds on |
| ADR-029 / ADR-030 / ADR-042 | The ranking engines (captain / transfer / shortlist) the offset reads |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Adding state safely | | |
| Deterministic detection | | |
| Refactoring to one path | | |
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

- US-139 Gate — ADR-047 (the conversational design; the safety property; what-about scope)
- US-140 `Context` + `detect_followup` + rank offset + `converse` (the mechanics)
- US-141 the `chat` REPL (`chat_transcript` + `cmd_chat`) + docs

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
