# Lessons Learned

**Sprint:** Sprint 104 — Explainability in Ask (Why · Risk · Confidence)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

An Ask recommendation shows **why** — a **Confidence** (score + band), a **Why** list (✓ the grounded signals
for it) and a **Risk** list (⚠ against) — so a user can understand, trust, or challenge it. A reusable
framework applied to **captain** and **transfer**; grounded + verified; the LLM never invents a reason or the
number.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Grounding a "reasoning" feature** — compute the reasons from the data; the LLM phrases + is verified.
- **Reusing existing signals** — the picks/moves already carried what the "why" needed.

### New Skills Acquired

- **Explainability is an analytics feature, not an LLM one.** The ✓/⚠ and the confidence come from the
  signals a decision already used; the LLM's role is unchanged (narrate the facts, verified).
- **A confidence heuristic must temper itself.** The same pick reads 99/High within its squad (a clear lead)
  but 69/Medium against the whole pool (a +0.2 coin-flip) — because "clearness" (the xP lead over the
  runner-up) is a real input. That self-tempering is what makes a heuristic honest.
- **Put the confidence into the facts** so a narrated number still traces (`verify_grounding`) — the ✓/⚠ list
  IS the number's transparent basis.
- **A self-contained `detail`** (scope + the block) is needed because `render_ask` shows `detail` *instead of*
  the headline — the block must carry the context.

---

# What Went Well ✅

- **Grounding held under a feature about reasoning** — an explanation can't be a hallucination; it's data.
- **Honest confidence** — score + band + a "heuristic, not a probability" caption; coin-flips read Medium.
- **No engine change** — one reusable `Explanation` shape for captain + transfer, from existing signals.
- **Auditable** — the confidence weights sit in one documented place (`explain.py` + ADR-089).
- 693 → 700 tests; ruff + CI-parity green; the LLM restated the confidence + reasons and verified ✓.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A confidence number implies precision | it's a heuristic | Score + band + a "not a probability" caption; ✓/⚠ as the basis |
| The captain `detail` hid the scope line | `render_ask` shows detail *instead of* the headline | Make the detail self-contained (scope + block) |
| Narrated confidence must verify | verify checks numbers vs facts | Put confidence/why/risk into `facts` |
| The move summary was too lean | it carries only id/name/team/price/xp | Pass the buy's **full row** for penalties/ownership/status |
| RoboTS had "no transfer" | it's already optimal | Pre-existing (no positive-gain move) — not a bug |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Explainability | Reasons are computed, not written; the LLM stays a narrator |
| Self-tempering confidence | The xP lead over the runner-up keeps a coin-flip honest |
| Facts carry the number | Put confidence in `facts` so a narrated figure verifies |
| Self-contained detail | `render_ask` shows detail over headline → include the context |

---

# Development Lessons 💻

- For anything that "explains", compute it from the data — never let the model author the justification.
- Make a heuristic self-tempering (a real "clearness" input) so it's honest by construction.
- When you add a `detail`, remember it replaces the headline in the renderer — make it self-contained.

---

# AI Collaboration Lessons 🤖

- The tester wanted the model to "show its reasoning"; the grounding-first read flipped it — the *analytics*
  show the reasoning, the model just phrases it, verified. That delivered explainability without weakening the
  trust guarantee (the ✓/⚠ can't be invented).

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-089 | **Explainability — grounded Why / Risk / Confidence.** A pure `analytics/explain.py` turns a decision's signals into an `Explanation` (✓ reasons · ⚠ risks · a transparent confidence score + band). `explain_captain`/`explain_transfer`; a documented confidence heuristic (auditable, self-tempering, capped by chance/doubt). Rendered in Ask/CLI/web; the values enter the facts so narration verifies. Every reason + the number is computed from the data, never an LLM guess | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Explainability for squad-build + chips** (same framework) — the natural next extension.
- **A richer web-native render** (a confidence metric + markdown Why/Risk) beyond the monospace block.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the gated "why" signals light up (form · % of team goals · opponent xGC rank);
  the Data Hardening flip + xP calibration; the Price Change Predictor.
- Backlog: flip the beta on (`docs/BETA.md`); a hosted LLM for the deploy (free-form chat).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep computing justifications from data — it's what makes "explainable" also mean "trustworthy" here.

---

# Key Commands Learned

```text
python app.py captain --squad TS     # now prints Confidence / Why (✓) / Risk (⚠) for the top pick
python app.py ask "what transfer should I make for TS?"   # a swap's Why/Risk/Confidence, verified
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Explanation | The grounded ✓ reasons + ⚠ risks + confidence for a recommendation |
| Clearness | How far ahead the pick is of the runner-up — the self-tempering confidence input |
| Confidence band | High (≥75) / Medium (≥55) / Low — a word for the heuristic score |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-089 | The explainability decision + the exact confidence formula |
| `src/analytics/explain.py` | The pure Explanation framework (captain + transfer) |
| `src/ui/explain.py` | The shared Confidence / Why / Risk block |

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

- US-269 Explainability framework + captain — Why/Risk/Confidence in Ask/CLI/web (ADR-089)
- US-270 Transfer explainability — Why/Risk/Confidence for a swap in Ask

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
