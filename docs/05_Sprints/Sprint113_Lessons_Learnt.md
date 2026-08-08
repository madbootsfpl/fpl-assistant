# Lessons Learned

**Sprint:** Sprint 113 — A robust Ask scroll + an explained differential shortlist

**Dates:** 2026-08-14

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Two Ask-tab items from tester feedback: make the example-question **auto-scroll reliable** (it "worked for some,
not all"), and give the **differential shortlist** a grounded **why** — the benefit of a differential, and the
standout signal behind each leader. Presentation + rationale only; the ranking untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Diagnosing flaky UI** — a "works sometimes" bug is usually a timing/ordering race, not a logic error.
- **Emphasis under thin data** — leading with the always-valuable part when the per-item detail is sparse.

### New Skills Acquired

- **A single scroll loses races; several instant scrolls win.** One smooth `setTimeout` fires once and can be
  overridden by Streamlit's scroll-restore + the expander collapse — so it lands only sometimes. Scrolling
  *instantly, several times* over ~0.8 s reliably ends at the bottom after layout settles.
- **Lead with the strategy when the signals are thin.** Preseason, per-pick differential signals are mostly
  "minutes" — so the *benefit* explanation (rank lever, variance) is what carries the answer now; the per-pick
  signals layer in where known and sharpen at GW1.
- **Placement keeps grounding safe.** Putting per-pick signals in the **detail** (the truth block) rather than
  the LLM's **facts** means no unverified number can reach the narration — the answer still ✓.
- **Gate an addition behind one optional param.** A single `rationale=` on `render_shortlist` added the whole
  "why" while leaving the plain shortlist byte-identical (a test pins it).

---

# What Went Well ✅

- **Both fixes small + precise** — a JS tweak and a rationale param; no analytics touched.
- **Honest per-pick nuance** — a high-xP but ~62-min differential reads "rotation risk", which is useful.
- **The plain path is unchanged** — the differential "why" is fully opt-in.
- 737 → 738 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Auto-scroll "works for some, not all" | one smooth scroll, fired before layout settles; scroll-restore wins | Multi-tick **instant** scroll over ~0.8 s, still unique per turn |
| Thin per-pick differential signals | preseason form/set-pieces/penalties are sparse | Lead with the *benefit*; layer signals where known (richer at GW1) |
| Keeping grounding intact | a "why" adds text | Signals in the **detail**, not the LLM facts → nothing to mis-verify |
| Not disturbing the plain shortlist | shared renderer | One optional `rationale=` param; plain output byte-identical (pinned) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Flaky UI timing | Repeat + go instant to beat layout races and scroll-restore |
| Emphasis | Lead with what's always valuable when the detail is data-gated |
| Grounding by placement | Keep un-factised text in the detail, not the narration input |
| Opt-in rendering | Gate an addition behind one param so the old path stays identical |

---

# Development Lessons 💻

- Treat "works sometimes" as a race and make the fix idempotent/repeated, not just earlier.
- When a feature is data-thin now, ship the durable part and let the rest light up with data.
- Add rationale to the grounded block, not the LLM's inputs, to protect verification.

---

# AI Collaboration Lessons 🤖

- The grounded contract makes "explain more" safe: the extra rationale is data-derived and shown in the truth
  block, while the LLM keeps narrating only from verified facts.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-287 extends **ADR-052** (Ask scroll); US-288 extends **ADR-042/061** (shortlist). New:
`ui/shortlist.py::_pick_signals` + a `rationale=` param on `render_shortlist`; a differential benefit lead in
`_decide_shortlist`; a multi-tick instant scroll nudge._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Soften the ~0.7 xMins "rotation risk" wording** if testers find it harsh for ~60-min players.
- **A hosted LLM for the deploy** so the prose + free-form tail work on the cloud.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: Data Hardening + xP calibration; the price/form/ownership signals (and the
  differential per-pick signals) sharpen as data arrives; calibrate the price predictor thresholds.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep translating "works sometimes" reports into race/ordering fixes, not one-off nudges.

---

# Key Commands Learned

```text
python app.py ask "best differential midfielders under £8m"   # now leads with the benefit + standout signals
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Multi-tick scroll | Several instant scroll attempts so it lands after layout settles |
| Differential benefit | The rank-lever upside of a low-owned pick (+ its variance) |
| Standout signals | Per-pick grounded reasons (nailed/rotation · set-pieces · form) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/pages/4_Ask.py` | The robust multi-tick scroll nudge |
| `src/ui/shortlist.py` (`_pick_signals`, `render_shortlist`) | The differential "why" — lead + signals |
| `src/ask.py` (`_decide_shortlist`) | The grounded benefit lead |

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

- US-287 Robust Ask auto-scroll — a multi-tick instant scroll, unique per turn (extends ADR-052)
- US-288 Explain the differential shortlist — a grounded benefit lead + per-pick standout signals (extends ADR-042/061)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
