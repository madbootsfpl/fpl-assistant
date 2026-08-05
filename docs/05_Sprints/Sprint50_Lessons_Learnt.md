# Lessons Learned

**Sprint:** Sprint 050 — Documentation consolidation & status refresh

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Bring every doc surface up to date with the project as of Sprint 049 before opening the web-UI track:
consolidate the roadmap into **one** forward-looking page (retire the reconciliation doc), refresh the
journal, README, backlog, handbook and glossary, and make the canonical facts (ADR/test counts, phase
status, "web UI next") agree everywhere. No feature code.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Auditing docs against reality before editing (the same "verify first" discipline as code).
- Retiring a document without breaking its inbound links (a tombstone).
- Keeping a single source of truth for a fact, and cross-checking it.

### New Skills Acquired

- Consolidating a scattered, phase-numbered roadmap into a forward-looking Delivered/Next/Then/Later page.
- Writing a phase-milestone journal entry that reads as a narrative, not a changelog.

---

# What Went Well ✅

- **The staleness audit paid off** — probing the real docs found README omitting all of Phase 4, a
  17-line glossary, CI marked ⬜ though it's built, and CLAUDE.md two phases behind. None of that was
  guessable from memory.
- **A consolidation is also a correctness pass** — rewriting the roadmap *surfaced* that Phase 4 and CI
  were done; the single page is now honest.
- **A tombstone beat a delete** — the reconciliation doc retired without breaking the history links from
  ADR-026 / Sprint 25 / the Phase-1 milestone.
- **One home per fact** — PROJECT_STATUS is the single live status; a milestone-per-phase cadence should
  stop the drift recurring.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Retire vs preserve the Phase-1 audit | Live docs shouldn't carry it, but ADRs/sprints link to it | A tombstone: content → a pointer; links still resolve; detail in git |
| Editing the instruction file (CLAUDE.md) | It's operative, not just prose | Changed only on explicit owner OK; kept the original intent as "the gate" |
| Counts drifting between edit and commit | Docs quote 49 ADRs / 421 tests | Re-verified with a `pytest` run + an `ls` count at close |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Audit before you edit | Docs drift silently; grep the real files for the stale claims first |
| Consolidation = correctness | Rewriting a stale summary forces you to notice what's actually done (Phase 4, CI) |
| Tombstone, don't delete | Retire a linked doc by replacing its body with a pointer — no broken links |
| Single source of truth | Pick one home per fact (PROJECT_STATUS) and cross-check the rest against it |

---

# Development Lessons 💻

- Treat docs like code: verify the current state, make the change, then a consistency "test" (grep the
  canonical facts, check for dangling links).
- A milestone-per-phase journal entry is cheap insurance against the docs falling a whole phase behind.
- When in doubt about an instruction file, ask — then keep the original intent, reframed accurately.

---

# AI Collaboration Lessons 🤖

- The owner steered the sprint itself ("docs first, then the thin UI") — the right call before a new
  track; a good reminder that planning is a conversation, not a default.
- Flagging the CLAUDE.md edit for approval (rather than doing it silently) kept the operative file the
  owner's to control.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| — | No ADR this sprint — documentation is editorial, not an architecture decision. The one judgment call (retire `Phase1_Reconciliation.md` via a tombstone) is recorded in the sprint log. | n/a |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Sprint 051 — the thin web UI** (FastAPI + Jinja, read-only, reusing the analytics; the CLI stays the
  engine; a GW1-ready shell). Then Data Hardening (post-GW1).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep PROJECT_STATUS as the single live status; add a phase milestone as each phase closes; run the
  canonical-facts consistency check whenever docs change materially.

---

# Key Commands Learned

```text
# (a docs sprint — no new commands). Consistency check pattern used at close:
grep -rl "421" README.md docs/00_Project/PROJECT_STATUS.md docs/04_Roadmap/Roadmap.md
ls docs/06_Decisions/ADR-0*.md | grep -v ADR-000 | wc -l     # verify the ADR count
python -m pytest -q                                          # verify the test count
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Tombstone (a doc) | A retired document reduced to a short pointer, so old links still resolve |
| Canonical facts | The few numbers/claims (ADR/test counts, phase status) that must agree across docs |
| Consolidated roadmap | One forward-looking page (Delivered / Next / Then / Later), not a phase-by-phase audit |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/04_Roadmap/Roadmap.md` | The single forward-looking plan |
| `docs/00_Project/PROJECT_STATUS.md` | The single live status (the fact of record) |
| `docs/01_Journal/Phase4_Complete_Milestone.md` | The NL-layer milestone (Sprints 033–049) |

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

- US-148 Roadmap consolidation + Backlog reconcile (reconciliation doc tombstoned)
- US-149 Journal (Phase-4 milestone) + README refresh
- US-150 Handbook + Glossary refresh + CLAUDE.md (owner-approved) + consistency sweep

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
