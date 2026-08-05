# Lessons Learned

**Sprint:** Sprint 025 — Phase 1 Close-Out & Roadmap Reconciliation

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Reconcile 24 sprints against the original Roadmap, review for anything left before close, then
**declare Phase 1 (CLI Analytics MVP) complete** and reframe the Roadmap so all unbuilt items live
in Phase 2+ / the backlog — nothing dropped. A documentation sprint; no code.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reconciling a built system against an aspirational plan (two-way, no orphans).
- Naming a milestone precisely (for what was built) instead of flatteringly.
- Running a close-out review that looks for drift rather than rubber-stamping.

### New Skills Acquired

- Building a built-vs-plan audit matrix as the evidence base for a declaration.
- Reframing a roadmap so nothing is dropped — every deferred item traces to an original bullet.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- **An honest close.** The reconciliation named the real shape — analytics/optimisation core (across
  original P1/2/5) built as a CLI; the P1 infra spine deferred — so "complete" got the precise
  qualifier *CLI Analytics MVP*, deferrals listed not buried.
- **A two-way matrix caught everything** — every roadmap bullet classified *and* every one of the
  24 sprints accounted for. No orphans in either direction; the declaration is defensible.
- **The completeness review earned its keep** — caught the README overstating the tool (FastAPI +
  unbuilt features as current). A close-out that *found* something.
- **Nothing dropped** — the reframed Phase 2+ traces back, item by item, to the original plan.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "Phase 1 complete" wasn't literally true | We built across phases, skipped P1 infra | Name it *CLI Analytics MVP*; list deferrals openly (ADR-026) |
| Risk of silently dropping ideas in a rewrite | A reframe can lose items | Two-way matrix; carry-forward, never delete |
| README overstated the tool | Aspirational front-door (FastAPI, transfers, AI) | Split Goals into today vs planned; fix the stack |
| Dev Journal had stalled at Session 1 | The per-session habit lapsed early | A milestone entry patches it; sprint docs + ADRs were the real record |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Plan vs reality | Building by learning means code outruns the roadmap; reconcile periodically |
| Precise milestones | Name for what was built; list what was deferred — beats a flattering headline |
| Two-way audit | Classify every plan item *and* account for every sprint — no orphans either way |
| Close-out reviews | Worth running even when you expect "nothing left" — it found the README |

---

# Development Lessons 💻

- A close-out sprint should *find* drift, not certify its absence — the review is the point.
- When reframing docs, make the audit trail explicit so "nothing dropped" is verifiable, not asserted.
- Keep the front door (README) honest — split current capability from roadmap ambition.

---

# AI Collaboration Lessons 🤖

- The framing decision was genuinely the owner's — surfaced it as a question before planning, not
  buried in a proposal.
- The matrix let the "declare complete" call rest on evidence (both directions balance), not a vibe.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-026 | Declare Phase 1 (CLI Analytics MVP) complete; reframe the Roadmap carrying every unbuilt item to Phase 2+ (nothing dropped); the reconciliation matrix is the evidence; deferred infra named openly | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Prioritise the reframed **Phase 2** (infrastructure + data depth) and pick the next direction —
  web UI, CI/CD, historical data, or a jump to a Phase 3 decision-support feature.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Decide whether the dev Journal habit resumes, or sprint docs + ADRs remain the record.
- Keep the gate + 3-part DoD; re-check ClubElo while it's down.

---

# Key Commands Learned

```text
# No new commands (documentation sprint). The reconciliation lives at:
#   docs/04_Roadmap/Phase1_Reconciliation.md   — built-vs-roadmap, two-way
#   docs/04_Roadmap/Roadmap.md                 — reframed (Phase 1 ✅ + Phase 2+)
#   docs/06_Decisions/ADR-026-phase1-cli-mvp.md
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| CLI Analytics MVP | The Phase 1 milestone — named for what was actually built (a CLI), not the original plan |
| Reconciliation matrix | A two-way audit: every plan item classified + every sprint accounted for |
| Carry, don't drop | Reframing moves unbuilt items forward (Phase 2+ / backlog); nothing is deleted |
| Map vs territory | Keeping the plan (map) honest about the built system (territory) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| Phase1_Reconciliation.md | The evidence behind declaring Phase 1 complete |
| ADR-026 | Records the declare + reframe decision |
| Phase1_Complete_Milestone.md | The journal milestone marker |

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

- US-073 Reconciliation matrix + ADR-026 (declare + reframe) — gate
- US-074 Completeness review (verdict: nothing blocks; README drift found)
- US-075 Execute the reframe (Roadmap, README, Backlog, Journal, PROJECT_STATUS)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
