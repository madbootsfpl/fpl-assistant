# Lessons Learned

**Sprint:** Sprint 006 — Multi-week xP

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Rank players by expected points over the next N gameweeks (not just the next one), so
decisions can weigh a run of games — and double gameweeks.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Extending a metric behind a single parameter (`horizon`).
- Reusing seams (xP, FDR `_view`) rather than rewriting.
- Presenting a metric honestly (hide a non-comparable column).

### New Skills Acquired

- Horizon/window thinking — a gameweek window captures DGW/BGW.
- Correcting a decision record when the mechanism doesn't match the intent.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- The sprint came from a Sprint 005 reflection — direction from Tony's instinct.
- A design flaw (ADR-007's "next N fixtures") was caught before any wrong code.
- FPL's `ep_next` shown only where comparable (N=1), hidden with a note otherwise.
- Pure reuse — the horizon threaded through tested xP/FDR seams.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| ADR-007 said "next N fixtures" | Per-team fixture count can't capture DGW | Corrected to "next N gameweeks" during US-022, before building |
| `ep_next` not comparable over a horizon | It's a single-GW number vs an N-GW sum | Show it only at N=1; hide + note at N>1 |
| No-fixture (blank) case | Empty sum = 0 | Correct: a blank gameweek → 0 xP (was neutral in v0) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| A recorded decision ≠ a verified one | The ADR flaw passed the gate story; caught only at implementation |
| Horizon design | A gameweek *window* captures DGW/BGW; a per-team fixture count doesn't |
| Honest display | Hiding a non-comparable column beats showing a misleading one |
| Composition | The horizon was one parameter threaded through existing seams |

---

# Development Lessons 💻

- Pressure-test an ADR's *mechanism* with a worked example, not just its intent.
- Catching a flaw before code is cheap — the discipline is to look.
- Reuse over rebuild: extend a signature before writing new logic.

---

# AI Collaboration Lessons 🤖

- The most valuable moment was flagging my own decision was wrong *before* building —
  the "check assumptions" discipline applied to the ADR itself.
- Framing the story around *how it fits* kept the focus on the design, not syntax.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-007 | Multi-week xP = sum of per-fixture xP over the next N **gameweeks** (DGW-aware); `xp --next`; `ep_next` shown only at N=1 | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Refine xP with `form` + expected minutes, or the Attack/Defence FDR split (data-dependent).
- Sanity-check each ADR mechanism with a worked example at write time.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep verifying data at plan time + the 3-part DoD.

---

# Key Commands Learned

```text
python app.py xp --type custom --next 1     # single gameweek (FPL ep_next shown)
python app.py xp --type custom --next 5     # sum over the next 5 gameweeks (DGW-aware)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Horizon | How many gameweeks ahead a metric looks |
| Double gameweek (DGW) | A team plays twice in one gameweek |
| Blank gameweek (BGW) | A team plays zero times in a gameweek |
| Gameweek window | The set of the next N gameweeks (captures DGW/BGW) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-007 | Records the multi-week xP decision and the mid-build correction |

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

- US-021 Multi-week xP design + ADR-007
- US-022 Multi-week xP analytics (gameweek horizon)
- US-023 The `xp --next N` command

**Stories Carried Forward:**

- None (form/expected-minutes xP + Attack/Defence FDR deferred — data-dependent)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
