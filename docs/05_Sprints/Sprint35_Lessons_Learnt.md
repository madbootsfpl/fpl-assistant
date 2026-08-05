# Lessons Learned

**Sprint:** Sprint 035 — Phase 4: grounding verification

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Verify — not just instruct — that the LLM's narration is faithful: a pure `verify_grounding` that
flags numbers and player names in the prose not backed by the facts, shown in `ask` as a soft ✓/⚠
trust line. Makes "grounded, not a black box" provable and visible. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Verifying an LLM's output against a source of truth (not just prompting it).
- Designing a self-check that's itself trustworthy (false-positive-averse).
- Making a guarantee visible to the user (a ✓/⚠ line).

### New Skills Acquired

- Extracting and comparing numbers/names between prose and structured facts.
- A conservative name match (whole words ≥4 letters) to avoid collisions.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- **Instruction became proof** — we had *told* the LLM not to invent numbers; now we *verify* it.
- **The self-check is trustworthy** — the name check is deliberately conservative, so it doesn't cry
  wolf. A soft trust line is only useful if it's rarely wrong.
- **Proven before built** — the probe showed the number check passes real output and catches a
  fabrication; a test locks it in.
- **Grounding is now visible** — the ✓ line is the transparent thing vs a black-box companion.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Instructing ≠ guaranteeing | The prompt only asks | Verify the output against the facts |
| Name-check false positives | Short/common surnames | ≥4-letter whole-word tokens; compare to the answer's subjects |
| Number false positives (rounding) | Model might round 7.4→7 | Rare (verbatim copy); a soft ⚠ only; noted |
| Where the known names come from | The verifier needs them | `answer` supplies the DB's player names while the store is open |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Verify, don't just prompt | An anti-hallucination claim is a guarantee only when checked |
| Trustworthy self-check | Bias a safety check against false positives — it must be reliable |
| Visible guarantees | A ✓ line beats "trust me" — show the check |
| Honest scope | Say what's checked (numbers + names), not more |

---

# Development Lessons 💻

- Check the output, not just the instruction — the difference between hope and proof.
- Keep a safety heuristic conservative so it stays credible.
- Thread the data the check needs (known names) from where it's available (the open store).

---

# AI Collaboration Lessons 🤖

- The probe proved the check before code — and became the worked example.
- The LLM narrates; the verifier keeps it honest; the ✓ line shows the user both.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-037 | Grounding verification: `verify_grounding` flags prose numbers not in the facts + known FPL players named who aren't subjects (conservative); a soft, visible ✓/⚠ trust line in `ask` (facts/table always shown); never blocks; optional; scope = numbers + names, not full semantics | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Regenerate-on-fail; a semantic/second-model claim check. Or Data Hardening (~GW1), more Phase 4
  intents / a chat mode, or the web UI.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the gate + 3-part DoD; prove the check with a probe before building.

---

# Key Commands Learned

```text
python app.py ask "who should I captain from TS?"   # now ends with a ✓/⚠ trust line
#   ✓ Checked: every figure and name in the explanation traces to the data above.
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Grounding verification | Checking an LLM's output against the source facts (not just prompting) |
| Trust line | The visible ✓/⚠ that reports the verification result |
| Subjects | The players an answer is about (allowed to be named) |
| Cry wolf | A check that false-positives so often it's ignored — to be avoided |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-037 | The verification design + the honest scope |
| ADR-034 / ADR-033 | Instruct (the contract) + prove (the spike) — this sprint verifies |
| Handbook Ch 21 | Analytics — "verify the grounding, don't just instruct it" |

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

- US-104 Grounding-verification design + ADR-037 (gate)
- US-105 `verify_grounding` (numbers + names)
- US-106 Wire into `ask` + the ✓/⚠ trust line

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
