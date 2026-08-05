# Lessons Learned

**Sprint:** Sprint 021 — Validate a Legal Bench (squad polish)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

When a full 4-man bench is declared, validate that the 11 starters form a legal XI (per the
`XI_FLEX` ranges) and warn clearly if not — closing the ADR-014 gap so the squad feature is
airtight. No new data or dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reusing a single definition (`XI_FLEX`) across two features to keep them consistent.
- Writing a small pure validator that's testable in isolation.
- Choosing warn vs block by what the tool actually is.

### New Skills Acquired

- Distinguishing "displayed" from "validated" — a shape can print yet be illegal.
- Gating a check to the case where it applies (a complete 4-man bench only).

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- Closed the ADR-014 gap — the squad feature is airtight; a backlog item ticked off.
- One rule reused (`XI_FLEX`) → bench-legality and formations can never disagree.
- Warn-not-block was the right product call (a proposer, not a submitter).
- Verified at planning, mechanical to build; DoD held (21st sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A shape could print yet be illegal | We displayed but didn't validate | `legal_xi_issues` checks each position vs `XI_FLEX` |
| Only a complete bench forms an XI | A partial bench has > 11 starters | Gate the check on `len(starters) == 11` |
| GK range `(1,1)` read as "need 1-1" | lo == hi | Special-case: "need 1" |
| An old test built 11 all-MID starters | Now illegal | Rewrote it to a legal 4-4-2 + added an illegal test |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Display ≠ validate | Showing a value doesn't check it's legal |
| Reuse the definition | Share `XI_FLEX`, not just the concept, to stay consistent |
| Gate the check | Run a validation only where it applies |
| Warn vs block | Match the response to what the tool does (propose, not submit) |

---

# Development Lessons 💻

- Keep the rule in the domain (`legal_xi_issues` with `XI_FLEX`); the UI just formats it.
- A message that names the exact problem (count + legal range) is far more useful than "invalid".
- When you tighten a rule, fix the tests that encoded the old, looser behaviour.

---

# AI Collaboration Lessons 🤖

- The gate settled the one real call (warn vs block) with its reasoning before code.
- The planning probe proved the check on legal / illegal / incomplete cases up front.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-022 | Validate a complete (11-starter) bench against `XI_FLEX`; **warn, not block**; reuse the one legal-XI definition | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Bench order; an auto-suggested legal bench; the other open backlog items toward completing
  the phase (combined defensive value, saved squad, small polish).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the gate + 3-part DoD; re-check ClubElo each session while it's down.

---

# Key Commands Learned

```text
python app.py squad --full --bench <3 forwards>   # warns: bench doesn't leave a legal XI
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Legal XI | 1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD (the `XI_FLEX` ranges) |
| Warn, not block | Inform the user but still proceed / print |
| Single source of truth | One definition (`XI_FLEX`) used by every feature that needs it |
| Complete bench | A full 4-man bench (leaving exactly 11 starters) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-022 | Records validate-a-complete-bench + the warn-not-block call |
| Handbook Ch 22 | Optimisation — now with the bench-validation section |

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

- US-062 Validate-a-legal-bench design + ADR-022
- US-063 `legal_xi_issues` + the `render_squad` warning

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
