# Lessons Learned

**Sprint:** Sprint 108 — A structured "Captain Pick" answer + a shared Model note

**Dates:** 2026-08-09

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Evolve the explainability presentation: the captaincy answer should read like the tester's mockup — a clear
**Captain Pick** card (medal · Team·Pos · Projected · Confidence · Why · Risks · **Alternatives** 🥈🥉) closed by
an honest **Model note** — and that Model note + sharper phrasing should carry across the whole explainability
family (transfer · squad · chips · gameweek). Presentation only; the analytics still decide and every number
still verifies (✓).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Separating presentation from computation** — a richer answer built entirely from data the engine already
  produced; not a single new heuristic.
- **Placing a cross-cutting element "once"** — appending a shared footer at each *answer* boundary, not inside a
  block that composites reuse.

### New Skills Acquired

- **Verify the mockup against real data first.** The engine already returned B.Fernandes 5.9 · 69/100 Medium
  with the exact reasons/risks — so the whole sprint was presentation, with zero analytics risk. Checking that
  at planning turned a "big new feature" into a safe reformat.
- **Change wording at the single source.** Nudging the strings inside `explain_captain` / `explain_transfer`
  propagated to the CLI, the web, the Ask answer and the gameweek composite at once — no per-surface edits.
- **A shared footer belongs at the answer boundary.** `MODEL_NOTE` went on each renderer tail / assembler, not
  inside `render_explanation` — otherwise the composite gameweek plan (which calls `render_explanation` three
  times) would have repeated it. "Once per answer" is a placement decision, not a string decision.
- **Delegation shrinks a module.** `render_captain_picks` collapsed from a bespoke table renderer to a thin
  wrapper over `render_captain_pick`; the `_table`/`expected_minutes` machinery in `ui/captain.py` fell away.

---

# What Went Well ✅

- **Pure presentation, low risk** — no engine change; the grounding + verification held throughout.
- **One wording source, many surfaces** — the CLI, web, Ask and gameweek plan all shifted together.
- **The Model note landed exactly once on all five explained answers** — confirmed with a live smoke.
- **A genuine consolidation** — one captain presentation everywhere; a smaller `ui/captain.py`.
- 710 → 713 tests; ruff + CI-parity green; the web Captain card verified via AppTest.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Model note risked repeating 3× in the gameweek plan | the composite calls `render_explanation` per sub-part | Append `MODEL_NOTE` once at the plan's foot, not in the shared block |
| The heuristic caveat cluttered the clean confidence line | it lived on every `render_explanation` line | Fold it into `MODEL_NOTE`; the line became `Confidence: NN/100 (Band)` |
| The card needed "Man Utd", the pick row only carried "MUN" | picks carry the team short code | Thread a `short_name → name` map from `get_teams` into every captain surface |
| `--limit N` vs a 3-deep card | the card shows 🥇 + 🥈🥉 | Alternatives grow past the medals with plain "N." markers |
| The all-players answer would hide its scope | the mockup omits a scope line | Always show the scope ("all players" / "from squad 'X'") |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Presentation vs computation | Verify the target against live output — often it's a reformat, not a feature |
| Single-source wording | Change the reason strings in `explain_*`, not each renderer |
| "Once per answer" | Put cross-cutting footers at the answer boundary, never inside a reused block |
| Delegation | A bespoke renderer can often become a thin wrapper — smaller module, one behaviour |

---

# Development Lessons 💻

- Check what the code already outputs before treating a request as new work.
- When a value doubles as data + a truthiness/label, thread the friendly form in rather than overloading it.
- Retiring code (the captain table) is a legitimate deliverable — but call out the behaviour it removes.

---

# AI Collaboration Lessons 🤖

- A precise mockup from the tester is the fastest possible spec — the job was to match its structure while
  keeping every number grounded, and to decide the few honest deviations (scope always shown; the opponent kept
  in the fixture lines).

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — both stories extend **ADR-089** (explainability presentation). New: `ui/captain.py::
render_captain_pick` (the card) + `render_captain_picks` now delegating to it; `ui/explain.py::MODEL_NOTE`
(the shared attribution, with the heuristic caveat folded in) closing all five explained answers;
`render_explanation`'s confidence line cleaned to `NN/100 (Band)`; wording nudges in `explain_captain` /
`explain_transfer`. A short **ADR-090** remains optional if `MODEL_NOTE` ever becomes a contractual element._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A web-native styled captain card** (medals/chips as HTML) — the standing visual follow-up to the text card.
- **Unify the two Why/Risk styles** (the card's "Why / Risks" vs `render_explanation`'s "Why / Risk") if a
  consistency pass is wanted.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the gated captain "why" signals light up (form · % of team goals · opponent xGC);
  Data Hardening + xP calibration; the Price Change Predictor.
- Flip the beta on (`docs/BETA.md`); a hosted LLM for the deploy (free-form chat).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep starting each display sprint by diffing the live output against the mockup — it right-sizes the work.

---

# Key Commands Learned

```text
python app.py ask "who should I captain?"    # now the structured Captain Pick card + a Model note
python app.py captain --squad my-team         # the same card in the terminal
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Captain Pick card | The structured captaincy answer — medal pick · Confidence · Why · Risks · Alternatives |
| Model note | The honest footer: analytics decide, AI explains; confidence is a heuristic, not a probability |
| Delegating renderer | A renderer kept for its callers but now forwarding to the shared one |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/ui/captain.py` (`render_captain_pick`) | The Captain Pick card, shared by Ask · CLI · web |
| `src/ui/explain.py` (`MODEL_NOTE`, `render_explanation`) | The shared footer + the clean Why/Risk/Confidence block |
| `src/analytics/explain.py` | The single source of the grounded reasons/risks + their wording |

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

- US-277 Structured "Captain Pick" answer — the mockup card in Ask/CLI/web (ADR-089)
- US-278 Shared Model note + phrasing — one honest footer across all five explained answers; CLI/web captain on the card (ADR-089)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
