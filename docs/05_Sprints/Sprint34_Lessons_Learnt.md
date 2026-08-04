# Lessons Learned

**Sprint:** Sprint 034 — Deeper Phase 4: per-gameweek transfer plans + a table in `ask`

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Show each incoming player's per-gameweek xP in the transfer-plan table (both `transfer --count` and
`ask`), and give `ask` a structured table above its narration. A composition of ADR-035 (plan) and
ADR-032 (per-GW xP); tighten the plan-narration prompt. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Composing mature features (a join) instead of rebuilding.
- Evolving a result shape minimally (an optional `detail`) to add a capability.
- Reusing the shared renderer for dynamic per-gameweek columns.

### New Skills Acquired

- Giving a natural-language command structured output alongside prose.
- Fixing an LLM output artifact with a single prompt instruction.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **Pure composition** — the per-GW plan table is a join of the plan (ADR-035) + the per-GW breakdown
  (ADR-032); no new modelling; the engine and grounding contract untouched.
- **`ask` gained hard data** — a structured table *above* the prose, keeping the philosophy (table =
  truth, prose = summary). A minimal result-shape change (`detail`).
- **The prompt tighten worked** — the "Here is a summary…" echo is gone with one instruction.
- **Reused the shared renderer** — dynamic GW columns, as `analyse`/`xp` already do.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Plan showed only a total | The plan named IN players but not their weekly xP | Join `by_gameweek` (ADR-032) into the plan table |
| `ask` was prose-only | ADR-034 returned narration | `AskResult.detail` carries a pre-rendered table shown above the prose |
| The model echoed the instruction | Prompt quoted the task | "Write only the explanation — no preamble"; echo gone |
| Table width grows with horizon | Per-GW columns | Narrow columns; default 5; soft cap deferred |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Compose, don't rebuild | Two mature features join into a new capability with no new logic |
| Structured + narrated | A language command can show a table *and* a summary — table is the truth |
| Minimal shape change | An optional `detail` field added the capability without disturbing callers |
| Prompt hygiene | One instruction can remove a persistent output artifact |

---

# Development Lessons 💻

- Reach for a join before a rebuild when features already carry the data.
- Keep the exact data visible even in a natural-language surface (the table under the prose).
- A pragmatic layering call (`ask` importing a renderer) is fine if noted; purify later if it grows.

---

# AI Collaboration Lessons 🤖

- The probe joined the two features before code — and became the worked example.
- The LLM narrates; the table carries the truth — structure and prose side by side.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-036 | Per-gameweek transfer-plan table (compose ADR-035 × ADR-032; incoming player's per-GW xP; bank → footer); `ask` returns a structured `detail` table above the narration; tighten the plan prompt | Accepted |

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

- A compact/soft-capped per-GW table for large horizons; a data-only `ask` detail. Or Data Hardening
  (~GW1), more Phase 4, or the web UI.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; prove the join with a probe before building.

---

# Key Commands Learned

```text
python app.py transfer --squad TS --count 3      # plan + each incoming player's points per gameweek
python app.py ask "which 3 transfers for TS?"    # the same table + a grounded summary
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Feature composition | Joining two mature features into a new capability (no new logic) |
| Structured detail | Exact data (a table) shown alongside an LLM summary in `ask` |
| Per-GW plan table | The transfer plan with each incoming player's weekly xP |
| Prompt hygiene | Instructing the model to avoid preamble/artifacts |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-036 | The composition + the `ask` detail design |
| ADR-035 / ADR-032 | The plan and per-GW breakdown that were joined |
| Handbook Ch 21 | Analytics — "features compose; a language layer can show hard data" |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Composing features (a join, not a rebuild) | | |
| Structured output alongside NL | | |
| Minimal result-shape evolution | | |
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

- US-101 Per-GW plan table design + ADR-036 (gate)
- US-102 Per-GW columns in `transfer --count`
- US-103 `ask` structured detail table + prompt tighten

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
