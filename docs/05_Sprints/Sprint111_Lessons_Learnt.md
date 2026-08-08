# Lessons Learned

**Sprint:** Sprint 111 — Ask tab polish (readable rules, reliable scroll, an explained "worth")

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Three Ask-tab fixes from tester feedback: a multi-item rules answer should read as **bullets**; clicking an
**example question** should **scroll** to the answer; and *"is X worth it?"* should explain **why**. Presentation
+ explainability only; the analytics/grounding untouched, every number still ✓.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Diagnosing before fixing.** Each of the three had a precise, different cause — naming it kept the fix small.
- **Reusing the explainability framework** — a fifth decision got Why · Risk · Confidence with little new code.

### New Skills Acquired

- **Streamlit re-runs a component only when its inputs change.** A static `st.iframe` scroll script didn't
  re-run on later turns — so an example click never scrolled (typing worked only via `chat_input`'s native
  scroll). Making the script unique per turn (a `/*turn N*/` token) forces the re-render + re-run.
- **A display reformat can preserve grounding.** Bulleting a rules fact kept the same numbers/names, so the
  verifier + `match_rules` were untouched and the answer still verifies ✓ — presentation and truth stay
  separate.
- **The framework makes each new "explain X" cheap.** `explain_worth`/`worth_confidence` reused
  `render_explanation` + `MODEL_NOTE` + `confidence_band`; the marginal cost of explaining one more decision is
  tiny, and the confidence self-tempers (worse value → lower number).
- **An answer with no `detail` degrades to raw facts.** `worth` only set `facts`, so without Ollama the user
  saw a "Facts:" dump; giving it a `detail` block makes it explain itself offline, like the other decisions.

---

# What Went Well ✅

- **Three small, precise fixes** — no analytics touched; grounding + verification held.
- **The rules bullets read exactly as the tester drew them** (chips one-per-line).
- **The worth answer now explains itself without Ollama** — a Confidence · Why · Risk + Model note.
- 726 → 730 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Example click didn't scroll | a static `st.iframe` — Streamlit didn't re-run it | Embed `/*turn N*/` so it's unique per turn → re-renders + re-runs |
| A list fact was one dense bullet | the fact is a single string | Author the multi-item facts with embedded bullet lines; `render_rules` prints multi-line facts verbatim |
| "worth" showed only raw facts offline | it set `facts` but no `detail` | Render a Confidence · Why · Risk `detail` block + Model note |
| Which price is "premium"? | premium is position-relative | A flat `_PREMIUM_PRICE = £9.0m` display lens (noted as a follow-up) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Streamlit components | Re-run only on input change — vary the content to force a re-run |
| Display vs truth | Reformatting a grounded fact can keep the same tokens → grounding intact |
| Reuse the framework | A new "explain X" = a pure `explain_*` + a confidence + a few lines of wiring |
| `detail` vs `facts` | Give a decision a `detail` block so it explains itself without the LLM |

---

# Development Lessons 💻

- Find the precise cause before coding — three different one-liners beat one broad rewrite.
- Keep presentation changes token-preserving so verification isn't disturbed.
- When you add a value/verdict, add the "why" in the same pass — users ask it immediately.

---

# AI Collaboration Lessons 🤖

- The grounded pattern makes explanations safe to add anywhere: analytics compute every reason + the number,
  the LLM only phrases, and the verifier checks it — so a new "why" can't hallucinate.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-283 extends **ADR-085** (rules display) + **ADR-052** (Ask scroll); US-284 extends **ADR-089**
(explainability) + **ADR-061** (worth). New: `analytics/explain.py::explain_worth` + `worth_confidence`;
multi-line rules facts + a `render_rules` that prints them verbatim; a per-turn scroll nudge._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A web-native worth card / rich markdown rules** — the visual follow-ups (mono reads well for now).
- **Position-relative "premium"** in `explain_worth` if the flat threshold misleads.
- **A hosted LLM for the deploy** so the prose + free-form tail work on the cloud.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: Data Hardening + xP calibration; the Price Change Predictor; the gated captain +
  worth signals sharpen as xP/ownership spread.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep pairing a new number/verdict with its "why" in the same story.

---

# Key Commands Learned

```text
python app.py ask "how does bench boost work?"   # the chips now read one-per-line
python app.py ask "is Haaland worth the money?"  # now explains WHY (Confidence · Why · Risk)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Per-turn nudge | A scroll script made unique each turn so Streamlit re-runs it |
| `explain_worth` | The grounded Why/Risk/Confidence behind a value verdict |
| Value premium | A good-value pick that still ties up budget (a two-sided read) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/explain.py` (`explain_worth`) | The value explanation, reusing the ADR-089 framework |
| `src/ui/rules.py` (`render_rules`) | Bulleted, verbatim rendering of list facts |
| `src/web_streamlit/pages/4_Ask.py` | The per-turn scroll nudge |

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

- US-283 Readable rules (bullets) + reliable Ask scroll (extends ADR-085/052)
- US-284 An explained "worth" — grounded Why · Risk · Confidence + Model note (extends ADR-089/061)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
