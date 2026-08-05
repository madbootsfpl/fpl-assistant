# Lessons Learned

**Sprint:** Sprint 033 — Deepen Phase 4: multi-transfer plans

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

A coordinated N-transfer plan (greedy: best legal move given the running state, repeated) — surfaced
as `transfer --count N` and via `ask "which N transfers for <squad>?"` — threading the shared bank,
≤3/club across the set, no re-buy. From the owner's Sprint-32 retro note. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Building a sequence recommendation by reusing a single-step engine over an evolving state.
- Making correctness structural (invariants that hold by construction) + a test per invariant.
- Sharing one engine behind two surfaces (a command + `ask`).

### New Skills Acquired

- A greedy coordinated planner that threads a shared budget across moves.
- Parsing a count from a natural-language question, robustly.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- **Coordination unlocked value** — threading the bank found Slater→Dasilva (+26.6) the independent
  shortlist couldn't afford; the TS 3-plan totals +49.0.
- **Correct by construction, by reuse** — the planner wraps `suggest_transfers` over the evolving
  state, so bank-can't-go-negative / no-double-buy / no-re-buy / ≤3-club-across-the-set fall out of
  rules already proven. Each pinned by a small test.
- **Two surfaces, one engine** — `transfer --count` and `ask "which N transfers"`; the LLM narrates
  the plan grounded.
- **Greedy over ILP** — explainable, and the probe showed it's strong.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Independent shortlist isn't a valid *plan* | Each assumes the whole bank | A coordinated greedy plan threading the shared bank |
| Bank could go negative across moves | Naive multi-move | Affordability checked on the *running* bank → invariant; unit-tested |
| Double-buy / sell-then-rebuy | Naive multi-move | Bought → owned (excluded); sold → out of market; tested |
| ≤3/club as a set | Naive multi-move | Club counts recomputed each step; per-candidate check on updated state |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Sequence recommendations | Reuse the single-step engine over an evolving state; don't write a new optimiser |
| Structural correctness | Prefer invariants that hold by construction; pin each with a test |
| One engine, two surfaces | A command + `ask` share the planner — no duplicated logic |
| Greedy vs ILP | Greedy is explainable and strong here; ILP would be optimal-but-opaque |

---

# Development Lessons 💻

- Thread the shared state (bank, clubs, used players) through a simple loop; reuse the checks.
- Test the invariants that make a plan *executable* (bank ≥ 0, no repeats) — not just the happy path.
- Be honest about scope: greedy (not optimal), digits-only count, hits not modelled.

---

# AI Collaboration Lessons 🤖

- The probe made the case (the £0.5 unlock) before any code — and became the worked example.
- The LLM narrates the plan from self-describing facts; it never computes the plan.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-035 | Multi-transfer plan: greedy coordinated N-transfers (thread the shared bank, update clubs, no re-buy) reusing `suggest_transfers`; count as input (`--count` / "N transfers"); positive-gain only; greedy-not-optimal + hits-deferred caveats | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A hit-aware / multi-week / ILP transfer planner; a richer count parse ("three"). Or Data Hardening
  (~GW1), more Phase 4, or the web UI.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the gate + 3-part DoD; prove the case with a probe before building.

---

# Key Commands Learned

```text
python app.py transfer --squad TS --count 3      # a coordinated 3-transfer plan (shared bank)
python app.py ask "which 3 transfers for TS?"    # the same plan, in plain English
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Coordinated plan | A set of transfers that are jointly legal (shared bank, ≤3/club, no repeats) |
| Bank threading | A later move spends what an earlier sale freed |
| Correct by construction | Invariants that hold because of how the code is built, not by luck |
| Greedy | Take the locally-best move each step (explainable, not guaranteed optimal) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-035 | The greedy plan design + the invariants |
| ADR-030 | The single-transfer engine the plan reuses |
| Handbook Ch 21 | Analytics — "a recommendation over a sequence" |

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

- US-098 Multi-transfer plan design + ADR-035 (gate)
- US-099 `suggest_transfer_plan` + `transfer --count`
- US-100 `ask "which N transfers"` intent

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
