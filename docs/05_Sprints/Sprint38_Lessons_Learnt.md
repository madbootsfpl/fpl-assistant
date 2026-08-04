# Lessons Learned

**Sprint:** Sprint 038 — two new `ask` intents: start/bench + compare

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Grow the natural-language layer with the two most-asked weekly questions — *"who should I
start/bench?"* and *"A or B?"* — both grounded (the ✓/⚠ trust line), both xMins-aware, both pure
composition of the existing analytics. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Probing the deceptively-simple part (string matching on real names) before building on it.
- Giving each intent a graceful, *specific* answer for its failure modes.
- Composing a feature from parts already built (optimiser + xP + xMins + verifier + shared table).

### New Skills Acquired

- Robust name extraction: bounded substring + drop-substring-overlap + ambiguity detection.
- A soft-`message` short-circuit so a decision can reply "can't do that, here's why" cleanly.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **The gate probe pre-solved the hard part** — the name-matcher looked trivial but the probe exposed
  `Fernandes` ⊂ `B.Fernandes` and duplicate `Palmer` before any code, so US-114 implemented settled
  rules instead of discovering them mid-build.
- **Pure composition again** — both intents reuse `select_squad`, xP, xMins, the verifier, and the
  shared table; the sprint added two renderers and glue.
- **Honest edge-cases as first-class answers** — "already optimal" and specific not-found / ambiguous
  messages beat a silent wrong pick or a generic error.
- **Grounding held for free** — both intents reuse `verify_grounding`; the ✓ line just works.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Name-match overlap | `Fernandes` is a substring of `B.Fernandes` | Drop a match that is a substring of another matched name |
| Ambiguous names | Two players named `Palmer` | Detect duplicates → a disambiguate message (never a silent pick) |
| A decision that must say "can't" | not-found / <2 / ambiguous aren't facts-to-narrate | A soft `message` on the decision + an `assemble` short-circuit |
| start/bench "no change" on TS | The squad is already optimal | Treat "already optimal" as a first-class answer; value grows in-season |
| "or" over-routing | `start X or Y` matches start/bench first | Accept for v0; compare needs ≥2 players and bails gracefully |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Probe the simple bit | String matching on real names is where the bugs hide — verify it early |
| Specific > generic failure | Each intent should explain its own failure, not fall back to a catch-all |
| Distinct overlapping surfaces | Lineup decision vs health check — keep them distinct; routing order disambiguates |
| Analytics decide, LLM narrates | compare states the higher xP as a fact; the model only explains it |
| Compose, don't rebuild | Two intents, zero new analytics — just renderers + glue |

---

# Development Lessons 💻

- A one-off probe of the fiddly input (overlapping/duplicate names) saved a mid-build rewrite.
- Model a soft failure as data (`{"message": ...}`) so the pipeline handles it uniformly.
- Reuse the seam you already have (the shared table, the verifier) rather than growing a new one.

---

# AI Collaboration Lessons 🤖

- One focused UX question up front (how to show the weight, last sprint) and a gate probe this sprint
  meant the builds were mechanical — the thinking happened before the code.
- The grounding verifier makes new intents cheap to trust: wire `subjects`, reuse the check, done.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-039 | Two new `ask` intents: **start/bench** (best legal XI on xMins-weighted xP vs the declared XI; "already optimal" is first-class) and **compare** (robust name-matching — bounded substring, drop-overlap, ambiguity, not-found; a side-by-side table; analytics decide the ranking, LLM narrates). Both grounded (✓/⚠), optional, pure composition | Accepted |

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

- A smarter router (reconcile "start X or Y" → compare when there's no squad + two players). More
  Phase 4 (further intents / a chat mode / stronger verification), the web UI, or GW1 Data Hardening.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep probing the fiddly input at the gate; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py ask "who should I start from TS?"   # best legal XI (xMins-weighted) vs your bench
python app.py ask "Haaland or B.Fernandes?"       # compare two players side by side
python app.py ask "compare Saka and Palmer"       # ambiguous name → a disambiguate message
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Intent (ask) | The question type keyword-routed before the analytics decide |
| Bounded substring | A name match flanked by non-letters (a whole name, not part of a word) |
| Ambiguous name | A web_name shared by >1 player → ask to disambiguate |
| Soft message | A decision's specific "can't do that, here's why" reply (not a generic error) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-039 | The two intents' design + the name-matching rules |
| ADR-037 / ADR-036 | The grounding verifier + structured-detail pattern both intents reuse |
| ADR-038 | xMins — both intents weight xP by it |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Robust text/name matching | | |
| Composing intents from existing parts | | |
| Grounded NL design | | |
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

- US-112 Gate — ADR-039 (name-matching + start/bench, pressure-tested)
- US-113 start/bench intent (best legal XI vs declared; "already optimal")
- US-114 compare intent (robust name-matching; side-by-side; analytics decide)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
