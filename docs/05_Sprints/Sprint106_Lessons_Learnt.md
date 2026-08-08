# Lessons Learned

**Sprint:** Sprint 106 — Explainability for the AI Tips gameweek plan

**Dates:** 2026-08-08

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Extend the Why · Risk · Confidence pattern (ADR-089) to the **AI Tips gameweek plan** — the last major decision
without it — so each recommendation (captain, lineup, transfer) shows a Confidence + Why, and the week gets an
overall read. Grounded + verified; the LLM never invents a reason or the number.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Composing explanations** — a composite decision explained by reusing the explanations of its parts.
- **Empty-safety** — tolerating stubbed/partial inputs (missing ids) so the framework never crashes.

### New Skills Acquired

- **A composite decision is mostly reuse.** The gameweek plan's captain + transfer already had
  `explain_captain`/`explain_transfer`; `explain_gameweek` just orchestrates them + a lineup rationale + an
  overall read — no new heuristics beyond a simple plan-level confidence.
- **The plan already surfaced its own risks.** The availability flags *are* the week's ⚠ Risk — the explanation
  points at existing data rather than computing anything new.
- **Expose the runner-up where a reused explanation needs it.** `gameweek_plan` picked the captain with
  `limit=1`; bumping to 3 + returning `captain_ranked` gave `explain_captain` its lead-margin — a tiny additive
  change unlocked the reuse.
- **A plan-level confidence should be driven by the dominant lever.** The captain is the week's biggest single
  decision, so the overall confidence = the captain's, tempered by flagged players.

---

# What Went Well ✅

- **Small, low-risk, and it *finished* the rollout** — reuse meant a thin `explain_gameweek` + a render tweak.
- **Grounding held across a composite** — every confidence + reason is data; the narration still verifies ✓.
- **Hardening fell out** — a stubbed test caught that `explain_*` assumed an id; now they tolerate its absence.
- 705 → 707 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| No runner-up for the captain explanation | `gameweek_plan` used `limit=1` | `limit=3` + return `captain_ranked` (additive) |
| A stubbed plan lacked player ids | unit test used minimal dicts | Make `explain_*` tolerate a missing id (`_get`) |
| What's a "plan confidence"? | a week isn't a single choice | Captain-driven (the biggest lever), −8 per flag |
| Two confidences on screen | plan-level + captain | Deliberate; copy links them ("clear captain: X (69/100)") |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Composite explanations | Reuse the parts' explanations; orchestrate, don't re-derive |
| Risks for free | The plan's flags are the week's ⚠ Risk |
| Expose the runner-up | A tiny additive change unlocks a reused explanation |
| Plan confidence | Drive it by the dominant lever (the captain) |

---

# Development Lessons 💻

- Before writing new logic, check whether a composite can reuse the explanations of its parts.
- Make shared helpers tolerate partial inputs — real edge cases (and stub tests) will hit them.
- A plan-level score should reflect the decision that matters most, not an average of everything.

---

# AI Collaboration Lessons 🤖

- The framework from Sprints 104–105 made this almost free: "explain the week" reduced to "reuse the captain +
  transfer explanations you already have." The marginal cost of explaining one more decision is now tiny.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — extends **ADR-089** (explainability). New in `analytics/explain.py`: `explain_gameweek` (reuses
`explain_captain`/`explain_transfer` + a lineup rationale + an overall read) and `gameweek_confidence`
(captain-driven, −8 per flagged player)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A richer web-native explainability render** (a confidence metric + markdown Why/Risk) beyond the monospace
  block — the one remaining polish across all the explained decisions.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the gated "why" signals light up (form · % of team goals · opponent xGC); the
  chip confidences sharpen as fixtures spread; Data Hardening + xP calibration; the Price Change Predictor.
- Flip the beta on (`docs/BETA.md`); a hosted LLM for the deploy (free-form chat).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep leaning on the framework — explaining the next decision is now a small, predictable job.

---

# Key Commands Learned

```text
python app.py ask "what should I do this week for TS?"   # the plan now leads with Confidence · Why · Risk
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Composite explanation | Explaining a bundle by reusing the explanations of its parts |
| Plan confidence | The week's overall read — captain-driven, tempered by flagged players |
| Lineup rationale | A short grounded 'why' for a start/bench swap (higher projected xP) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-089 | The explainability framework all five decisions now share |
| `src/analytics/explain.py` (`explain_gameweek`) | The composite explanation (reuse + a lineup rationale + overall) |
| `src/ui/gameweek.py` | The plan renderer with the Confidence · Why · Risk block |

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

- US-273 Per-recommendation explainability — captain/transfer reuse + lineup rationale in the plan (ADR-089)
- US-274 Plan-level Confidence · Why · Risk — a captain-driven overall read at the top of the plan

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
