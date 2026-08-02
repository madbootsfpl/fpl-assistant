# Lessons Learned

**Sprint:** Sprint 005 — Expected Points (xP v0)

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

A simple, transparent expected-points estimate per player for the next gameweek —
baseline scoring rate adjusted by fixture difficulty — comparable against FPL's own
`ep_next`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Composing a feature from existing seams instead of writing new logic.
- Reusing the migration pattern (now generalised to any table).
- Verifying data at plan time, not execution.

### New Skills Acquired

- Building a **cross-domain** metric (player rate × fixture difficulty).
- Joining two data threads in analytics via a shared key (`team_id`).
- Comparing a home-grown metric against a reference (FPL's `ep_next`).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- The whole sprint was reuse — xP composed five sprints of foundation.
- Data verified at planning, so the premise held from the start.
- The 3-part DoD (tests → smoke → docs) held for every story.
- Generalising the migration was safe (teams-migration test stayed green).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Our xP runs high vs FPL's ep_next | Full last-season ppg, no minutes/form dampening | Expected for v0; show ep_next beside it; refine later |
| Linking player → next fixture | Cross-domain join needed | Map `team_id → next fixture difficulty`, reuse FDR `_view` |
| ppg/ep_next are strings from the API | FPL quirk | Convert at the `from_api` boundary (`_to_float`) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Cross-domain metric | Two domains meet via a shared key (a player's `team_id`) |
| Composition | By sprint 5 a big feature is mostly wiring existing seams |
| Reference comparison | Showing FPL's `ep_next` keeps our estimate honest |
| Generalising | A pattern used twice earns being made a mechanism |

---

# Development Lessons 💻

- Verify a feature's data at plan time — it prevents mid-sprint pivots.
- Reuse over rebuild: compose seams before writing new logic.
- A home-grown metric is more trustworthy when compared to a reference.

---

# AI Collaboration Lessons 🤖

- Framing each story around *how it fits* (which seams it reuses) matched the
  learning goal better than walking through code.
- The most useful confirmations were structural (generalise the migration? reuse
  `_view`?), not syntactic.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-006 | xP v0 = ppg × (1 + (3 − difficulty) × 0.10); `--type custom|fpl`; next GW; status-based availability; compare vs `ep_next` | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

- how much difference between xP and FPL scores

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Refine xP with `form` + expected minutes (once populated).
- Consider double/blank gameweeks; revisit Attack/Defence FDR.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep verifying data at plan time + the 3-part DoD.

---

# Key Commands Learned

```text
python app.py xp --type custom --pos MID          # players by expected points vs FPL's ep_next
python app.py xp --type fpl --limit 30
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| xP (Expected Points) | A prediction of a player's points next gameweek |
| Cross-domain metric | Combines two domains (a player's rate × a fixture's difficulty) |
| Composition | Building a feature by wiring existing parts together |
| Reference comparison | Checking your metric against a known one (FPL's `ep_next`) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-006 | Records the xP v0 formula and decisions |
| FPL `ep_next` field | FPL's own expected points — a comparison baseline |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Analytics (composing metrics) |3 |4 |
| Cross-domain joins | 1| 2|
| Migrations | | |
| Reading/using real data | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?
the xP scoring

### What was the biggest lesson?
show we consider looking at xP across a number of fixtures?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-017 xP v0 design + ADR-006
- US-018 Store xP inputs (+ generalise the migration)
- US-019 xP analytics (cross-domain join)
- US-020 The `xp` command

**Stories Carried Forward:**

- None (form/expected-minutes xP + Attack/Defence FDR deferred — data-dependent)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
