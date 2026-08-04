# Lessons Learned

**Sprint:** Sprint 031 — Phase 3 Wrap-up + Phase 4 LLM Spike

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the docs reflect Phase 3 completion, then **spike** Phase 4 — prove whether a local LLM can
answer FPL questions grounded in our analytics (no invented numbers), and **decide** commit-or-defer.
A spike in the spirit of Sprint 015 (soccerdata): evaluate, decide, minimal throwaway code.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Running a cheap, boxed spike that ends in a decision with evidence.
- Grounding an LLM: pass a pre-made decision + only the relevant facts.
- Keeping the front door (README) honest as capabilities grow.

### New Skills Acquired

- Calling a local LLM (Ollama) from Python via stdlib HTTP — no new dependency.
- Engineering grounding: analytics decide, the LLM narrates *pre-humanised* facts.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **A decisive spike, cheaply** — ~1.5 sessions, no new dependency, no production risk, a clear
  **commit** (vs the soccerdata spike's defer).
- **Verify-on-real-data earned it twice** — the probe proved the LLM *fabricates if asked to decide*;
  running the spike proved it *mis-reads coded fields*. Two design rules the theory wouldn't give.
- **Grounding is engineered, not hoped** — the model is structurally unable to invent the numbers.
- **Honest docs first** — fixed a README that listed built features as "planned".

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| LLM picked the wrong captain + fabricated why | Asked it to *decide* / rank numbers | Analytics decide; the LLM only narrates the pre-made pick |
| LLM read `venue "A"` as "home"; `HUL` → "Huddersfield" | It had to decode abbreviations | **Pre-humanise the facts** ("away against HUL"); forbid code expansion |
| Prose a little generic | A small 3B model | Acceptable for explanation; a bigger model is a Phase-4 option |
| Don't want production risk from an experiment | It's a spike | Boxed in `spikes/` (excluded from lint), not wired into `app.py` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| LLM decisions | Never let it make a numeric decision — it will rank wrong and invent a reason |
| Engineered grounding | Hand it the decision + pre-humanised facts; it narrates honestly |
| Decode nothing | The model must not interpret codes/abbreviations — pre-format them |
| Spikes | A spike's deliverable is a decision with evidence — run it, don't just design it |

---

# Development Lessons 💻

- Prove the risky part first (grounding) before committing to a build.
- Box experiments so production stays green and uncommitted.
- Refresh user-facing docs the moment they drift from reality.

---

# AI Collaboration Lessons 🤖

- The planning probe *and* the spike each changed the design — running the model beats reasoning about it.
- Differentiation matters: grounded-in-our-numbers is the honest answer to FPL's black-box Companion.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-033 | LLM grounded-narration spike: local Ollama (`llama3.2`), stdlib HTTP, no new dep; **analytics decide, LLM narrates** pre-humanised facts (never rank/compute/invent); boxed in `spikes/`. **Outcome: COMMIT to Phase 4** | Accepted |

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

- **Phase 4 (green-lit):** a real `ask` command — intent router (captain/transfer/analyse) + a
  grounding-contract module (pre-humanised facts, narrate-not-decide, a verify check) + graceful
  Ollama-absent handling + tests. Or wait for GW1 to do Data Hardening — both are live.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; run the risky thing (a probe/spike) before committing.

---

# Key Commands Learned

```text
python spikes/031-llm/ask_spike.py "who should I captain from TS?"
  # analytics DECIDE the pick; local llama3.2 NARRATES it from pre-humanised facts
  # (a spike — not wired into app.py)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Grounded narration | An LLM explaining a decision using only supplied facts (inventing nothing) |
| Analytics-decide / LLM-narrate | The pattern: our code makes the call; the model only puts it in words |
| Pre-humanise the facts | Pre-format data (venue "away", full phrases) so the model needn't decode it |
| Boxed spike | A throwaway experiment kept out of production, ending in a decision |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-033 + spikes/031-llm/FINDINGS.md | The spike design, evidence, and the commit decision |
| ADR-016 | The soccerdata spike — the evaluate/decide pattern (that one deferred) |
| Phase3_Complete_Milestone.md | Records the decision-support trio |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Grounding an LLM (no hallucinated numbers) | | |
| Running a spike to a decision | | |
| Local LLMs (Ollama) | | |
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

- US-092 Phase 3 docs celebration (README / Roadmap / milestone)
- US-093 LLM spike design + ADR-033 (gate)
- US-094 The spike → grounded narration works → COMMIT to Phase 4

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
