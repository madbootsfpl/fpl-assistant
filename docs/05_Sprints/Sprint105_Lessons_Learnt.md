# Lessons Learned

**Sprint:** Sprint 105 — Explainability for squad-build & chips

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Extend the Why · Risk · Confidence pattern (ADR-089) — live on captain + transfer — to the **squad build** and
the **chip advisor**, so those recommendations also show *why*, computed from the signals the decision already
used (never an LLM guess), verified.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Applying a framework across decisions** — one `Explanation` shape + `confidence_band`, four `explain_*`.
- **Honest heuristics** — a confidence that reads *low* when the evidence is thin is more trustworthy.

### New Skills Acquired

- **A relative margin normalises confidence across different scales.** Triple-Captain ceilings (~a few xP),
  Bench-Boost totals (~tens) and Free-Hit/Wildcard XI-xP aren't comparable in absolute terms — dividing the
  margin by each chip's own value let one `chip_confidence` serve all four.
- **Preseason-flat is a feature, not a bug.** Near-uniform gameweeks → tiny chip margins → all chips read
  **Low** — the correct, honest signal (no window is clearly best yet); it sharpens as fixtures spread.
- **A squad "confidence" is fuzzier than a pick.** Framing it as XI expected-minutes **reliability** + budget
  **efficiency** kept it grounded and defensible (not a probability).
- Adding a `detail`/code block to a page breaks tests that assumed one — search for the block by content
  (`"Total:"`) rather than by index.

---

# What Went Well ✅

- **One pattern, four decisions** — small diffs, no engine change; each `explain_*` reads existing signals.
- **Honest chip confidence** — Low preseason, by construction; a low number beats a confident-looking guess.
- **Grounding held** — every confidence + reason is data; the build narration still verifies ✓.
- 700 → 705 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Chip margins live on different scales | TC/BB/FH/WC measure different things | A **relative** margin (÷ the chip's own value) |
| A squad's "confidence" is vague | it's a whole 15, not a choice | Frame as XI reliability + budget efficiency |
| Build page tests assumed one code block | the explanation added a second | Find the squad table by `"Total:"`, not by index |
| The chip block already explained "why" | `chip_advisor` facts are self-describing | Chips only needed a **confidence** + the caveat |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Relative margin | Normalises confidence across incomparable chip scales |
| Honest low | A low confidence when evidence is thin is the trustworthy answer |
| Reuse the framework | New `explain_*` over existing signals — no engine change |
| Test by content | Find a code block by its text when the page adds more |

---

# Development Lessons 💻

- Normalise before you score, when the inputs live on different scales.
- Let a heuristic read low when the data is flat — don't manufacture confidence.
- When a UI gains a block, hunt the tests that index blocks positionally.

---

# AI Collaboration Lessons 🤖

- The same "analytics explain, LLM phrases, verified" contract scaled cleanly to two more decisions — the
  framework from Sprint 104 meant Sprint 105 was mostly new *reasons* + a *confidence formula* per decision,
  not new plumbing.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — extends **ADR-089** (explainability). New heuristics documented in `analytics/explain.py`:
`squad_confidence` (reliability × budget-use) and `chip_confidence` (a relative GW-separation margin)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Explainability for the "AI Tips" gameweek plan** (same pattern) — the last big decision without it.
- A **richer web-native render** (a confidence metric + markdown Why/Risk) beyond the monospace block.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the gated "why" signals light up (form · % of team goals · opponent xGC); the
  chip confidences sharpen as fixtures spread; Data Hardening + xP calibration; the Price Change Predictor.
- Flip the beta on (`docs/BETA.md`); a hosted LLM for the deploy (free-form chat).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep building on the framework — the marginal cost of "explain the next decision" is now tiny.

---

# Key Commands Learned

```text
python app.py ask "build me a squad for £100m"           # a build's Why/Risk/Confidence, verified
python app.py ask "which chip should I use for TS?"      # a confidence per chip (Low preseason, honestly)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Relative margin | A chip GW's separation from the next-best, ÷ its own value — comparable across chips |
| Squad reliability | The mean expected-minutes of the starting XI — the build's confidence base |
| Honest-low | A confidence that reads low because the evidence genuinely is thin |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-089 | The explainability framework these extend |
| `src/analytics/explain.py` | `explain_squad`/`explain_chips` + their confidence heuristics |
| `src/analytics/chips.py` (`_gap`) | The per-chip margin the confidence reads |

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

- US-271 Squad-build explainability — Why/Risk/Confidence in the build answer + Build page (extends ADR-089)
- US-272 Chip explainability — a per-chip confidence (from the GW margin) in the chip block

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
