# Lessons Learned

**Sprint:** Sprint 028 — Transfer Suggestions (Phase 3, feature 2 of 3)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

A `transfer --squad <name>` command that recommends the best *single* transfers for a saved squad —
each a legal, affordable, same-position upgrade ranked by xP gain over a horizon, and explained
(OUT → IN, prices, Δ). Honest about the unknown bank (`--bank`) and single-move scope. FPL-native;
no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Encoding domain rules (≤3/club, budget, position) into a recommendation.
- Composing a feature from existing pieces (xP, saved squads, the club rule, the renderer).
- Testing each constraint in isolation — including a subtle edge case.

### New Skills Acquired

- A pure "suggest a change" engine (state in → ranked moves out) that's fully unit-testable.
- Being honest about unseen inputs (bank as `--bank`; bench as a flag, not a model).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **A rule-respecting recommendation** — a transfer must be *legal* to be useful, and the engine
  enforces same-position / ≤3-club / budget, reusing the optimiser's `MAX_PER_CLUB`.
- **Composition again** — the whole feature was ~one analytics fn + one view + one command, on top
  of xP, saved squads, and the shared renderer (its 2nd new consumer).
- **A test caught a *test*** — the ≤3/club freed-slot subtlety; my first test expected a block where
  a legal same-club swap existed. Code right, test wrong → fixed.
- **Honest about unknowns** — the bank is `--bank` (default £0), bench players are flagged.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The manager's bank is unknown | We deferred `/my-team/` auth | `--bank` input (default £0 = self-funding); stated in output |
| ≤3/club has a freed-slot subtlety | Selling a same-club player frees a slot | Encode it; a unit test per case caught a bad test |
| A bench upgrade looks as good as a starter's | xP doesn't model who starts | Flag the bench player (`(b)`); note the caveat; xMins is later |
| A GK topped the transfer board | GKs score consistently | *Include* GKs (a better keeper is a real upgrade — unlike captaincy) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Rule-respecting advice | A recommendation that breaks the domain's rules is worse than none |
| Test each constraint | Isolating the ≤3/club case surfaced a bad test and sharpened the logic |
| Honest unknowns | Make what you can't see an input or a flag, not a guess |
| Pure engines | Data in → moves out makes every rule trivially testable |
| Contrast decisions | GKs excluded for captaincy, included for transfers — same metric, different policy |

---

# Development Lessons 💻

- Compose over invent: transfers reused xP + squads + the club rule + the renderer.
- A pure function with the constraints as parameters is the easiest thing to trust.
- When a test and the code disagree, check which is wrong — here it was the test.

---

# AI Collaboration Lessons 🤖

- The gate probe (a real squad) drove the GK-include and bench-flag decisions before code.
- Deferring the multi-move planner kept the sprint focused on a solid, testable foundation.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-030 | Transfer suggestions: best single legal upgrades for a saved squad; budget = sale + `--bank`; xP gain over a horizon; constraints (position, ≤3/club w/ freed-slot, availability, not-owned); GKs included; bench flagged; multi-move/hits deferred | Accepted |

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

- Sprint 029 — Team Analyser: grade a saved squad's health over a horizon (xP + fixtures +
  availability), composing the same pieces. Then Sprint 030 — data hardening.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; probe on a real squad before designing; re-check ClubElo while down.

---

# Key Commands Learned

```text
python app.py transfer --squad TS               # best single transfers by xP gain over 5 GW
python app.py transfer --squad TS --bank 2.0     # add your bank to each sale's budget
python app.py transfer --squad TS --next 3       # compare over a 3-GW horizon
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Self-funding swap | A transfer whose incoming price ≤ the sold player's price (bank £0) |
| Freed slot (≤3/club) | Selling a same-club player lets you buy another from that club |
| Bench-blind | Ranking that doesn't distinguish starters from bench (flagged, not modelled) |
| Transfer planner | A future multi-move optimiser (hits vs roll) — deferred |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-030 | The transfer design + the constraint decisions |
| Handbook Ch 21 | Analytics — now with "recommending a change means respecting the rules" |
| ADR-008 / ADR-024 / ADR-028 | The optimiser rule, saved squads, and xP that transfers compose |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Encoding domain constraints | | |
| Composing features | | |
| Testing each rule in isolation | | |
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

- US-083 Transfer-suggestion design + ADR-030 (gate)
- US-084 `suggest_transfers` engine (pure, unit-tested)
- US-085 `transfer` command + explain-why view

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
