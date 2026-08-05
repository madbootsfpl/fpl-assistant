# Lessons Learned

**Sprint:** Sprint 032 — Phase 4: the `ask` command (grounded NL answers)

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

A production `ask "<question>"` command — keyword-routed to captain/transfer/analyse, where the
analytics **decide** and a local LLM **narrates** pre-humanised facts — grounded, tested, and
gracefully degrading when the LLM is absent. Builds the Sprint-031 spike into production. No new
dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Grounding an LLM: analytics decide, the model narrates pre-humanised facts.
- Making an added capability *optional* (degrade to the deterministic core).
- Keeping a language layer testable offline (an injectable narrator).

### New Skills Acquired

- A small stdlib Ollama client that returns None (not raises) when unavailable.
- Keyword intent routing + matching questions to known saved-squad names.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- **Words, not intelligence** — the analytics keep deciding; the LLM only narrates. The feature
  reuses captain/transfer/analyse read-only.
- **The LLM is genuinely optional** — `narrate` → None when Ollama is absent, and `ask` degrades to
  the decision + facts. Tested first-class, so it's production-grade, not a demo.
- **The spike's findings were the spec** — analytics-decide + *pre-humanise the facts*; the analyse
  conflation was fixed with self-describing facts (`"none"`), verified live.
- **Grounded offline tests** — an injected narrator covers routing/humanising/degradation without a
  live model; the real call is smoke-only.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| LLM would rank/invent if asked to decide | It's a language model, not a calculator | Analytics decide; the LLM only narrates a pre-made decision |
| It mis-read `venue "A"` / conflated summary fields | It had to interpret data | Pre-humanise + self-describing facts (`"away against HUL"`, `"none"`); forbid merging |
| Squad parse missed "for TS" (only "from") | Preposition-based extraction is fragile | Match the question against *known saved-squad names* — phrasing-robust; keeps captain global |
| Don't want the tool to depend on a model | An LLM can be absent/slow | Optional narrator; degrade to the analytics decision |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| LLM role | Narrate, never decide — it ranks wrong and invents a reason |
| Engineered grounding | Pre-humanise + self-describe the facts; don't trust the prompt alone |
| Optional capability | Degrade to the deterministic core; nothing load-bearing on the model |
| Testable LLM code | Inject the narrator; unit-test offline, smoke the real call |

---

# Development Lessons 💻

- Reuse the decision-makers you already have; the LLM is a thin edge, not a new brain.
- Return None (don't raise) at an optional boundary so callers degrade cleanly.
- Match against known values (squad names) instead of guessing structure from prepositions.

---

# AI Collaboration Lessons 🤖

- The spike + planning probe wrote the design — both grounding rules came from running the model.
- Transparency is the differentiator: grounded-in-our-numbers vs a black-box companion.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-034 | The `ask` command: keyword routing (LLM routes nothing); analytics decide → pre-humanised self-describing facts → LLM narrates (invent/rank/merge/decode forbidden); the LLM is **optional** (degrade to the decision); stdlib Ollama, injectable narrator, no new dep | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Deepen Phase 4 (more `ask` intents / a chat mode; a larger model behind the same contract; a light
  output-grounding check), or wait for GW1 to do Data Hardening, or start the web UI (Phase 2).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the gate + 3-part DoD; run the risky part (spike/probe) before building.

---

# Key Commands Learned

```text
python app.py ask "who should I captain from TS?"     # captaincy, in plain English
python app.py ask "what transfer should I make for TS?"
python app.py ask "analyse TS"                         # squad health
#   analytics DECIDE; a local LLM NARRATES; works even with Ollama stopped
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Grounded narration | The LLM explains a decision using only supplied facts (invents nothing) |
| Pre-humanised facts | Data pre-formatted so the model needn't decode it ("away against HUL") |
| Self-describing fact | A fact that states its own meaning (`"availability_problems": "none"`) |
| Optional narrator | The LLM is additive; the tool degrades to the decision without it |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-034 + ADR-033 | The `ask` design + the spike that green-lit it |
| Handbook Ch 21 | Analytics — "a language layer that adds words, not intelligence" |
| src/ask.py | The route → decide → humanise → narrate pattern |

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

- US-095 `ask` design + ADR-034 (gate)
- US-096 LLM client + grounding contract + `ask` (captain) + degradation
- US-097 `ask` transfer + analyse intents (self-describing facts)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
