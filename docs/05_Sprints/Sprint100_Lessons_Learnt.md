# Lessons Learned

**Sprint:** Sprint 100 — The AI Chat Assistant (grounded rules KB + a labelled free-form mode)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

The Ask tab answers **FPL-rules** questions from a curated, **verified** knowledge base (✓) and open
**tactical** questions free-form with a clear **ℹ not-verified** label — every existing grounded squad/player
question unchanged. A real assistant, with the trust boundary always visible.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Extending a grounded router without weakening it** — new intents slot in *before* the fallback; the
  trust model (analytics decide → LLM narrates → verified) stays intact.
- **Curated-facts grounding** — answer from a small authoritative KB the LLM only phrases + is verified
  against, never the model's memory.

### New Skills Acquired

- The **verifier is the design driver**: because `verify_grounding` caught Ollama hallucinating chip facts,
  the answer was obvious — rules come from a **curated KB** (verified ✓), and open questions get a distinct
  **ℹ not-verified** lane. The trust model told us where the boundary must sit.
- **One seam serves the whole feature**: `route()==None` and a rules-no-match both become a single
  `{free_form: True}` decision in `assemble`, so the Ask tab + CLI `chat` inherited it with **no page code**.
- **A third trust state** slots cleanly into `_trust_line` (✓ / ⚠ / ℹ) — the render layer already centralised
  the trust line.

---

# What Went Well ✅

- **The trust boundary is always on screen** — ✓ grounded · ✓ rules · ℹ tactics.
- **No plumbing** — the fallback seam meant the web + CLI both worked immediately.
- **Routing collisions handled** — question-shaped rules cues placed first, pinned by tests, don't steal
  squad commands.
- **Honest degradation** — rules answer from facts without a model; free-form falls back to the help message.
- 663 → 672 tests; ruff + CI-parity green; the real LLM narrated a rules answer that **verified ✓**.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Can't trust the LLM on rules | it hallucinated chip facts (⚠ caught) | Answer rules from a curated KB, verified |
| A rules question hits a squad intent | "how does bench boost work" contains "bench" | A `rules` intent placed first on question-shaped cues |
| Two fallbacks (no-route, rules-no-topic) | both are "general" questions | Funnel both into one `{free_form: True}` branch |
| Free-form has no facts to verify | it's ungrounded by nature | A distinct `trust={free_form:True}` → an **ℹ** label |
| An old test expected `intent None` | unrecognised now takes the free-form path | Updated: intent `"chat"`, same help message |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Curated-KB grounding | The LLM phrases facts it can't be trusted to know; verify against them |
| Router extension | New intents before the fallback; the fallback is the free-form seam |
| One seam | `route==None` + rules-no-match → one `{free_form}` branch → web + CLI for free |
| Third trust state | ✓ / ⚠ / ℹ in one `_trust_line` |

---

# Development Lessons 💻

- Let the safety mechanism (the verifier) drive the design — it drew the line between grounded and free-form.
- Consolidate fallbacks to one branch so every caller inherits the behaviour.
- Label the ungrounded lane loudly; never let free-form wear the ✓.

---

# AI Collaboration Lessons 🤖

- A "24/7 chatbot" sounds like it wants an ungrounded LLM. The grounding-first read — curated facts for rules,
  a labelled ℹ lane for tactics — delivered the assistant *and* kept the trust guarantee the project is built
  on. The LLM stays a narrator, even in "chat".

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-085 | **AI Chat Assistant — a curated rules KB + a labelled free-form mode.** `fpl_rules.py` (authoritative FPL facts) + a grounded `rules` intent (verified ✓); a free-form tail for open tactics tagged **ℹ not verified** (never a squad decision); a third `_trust_line` state. Grounded squad questions unchanged; rules from curated facts, not the LLM's memory; degrades without a model | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A hosted LLM for the deploy** would light up free-form on the cloud (today it degrades to rules + grounded).
- **Grow the rules KB** as questions come in; consider RAG only if it outgrows a small file.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- **Chip Strategy — the gated half:** DGW/BGW detection (in-season) + mini-league position (leagues API, GW1).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the Price Change Predictor lights up.
- Backlog still open: persisted chat context; season countdown / deadline banner; the pitch-on-Build reuse;
  server-side squad persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep letting the trust model decide the architecture of anything LLM-facing.

---

# Key Commands Learned

```text
python app.py ask "how does bench boost work?"          # a rules answer from the curated KB, verified ✓
python app.py ask "any general advice for a newbie?"    # a free-form answer, labelled ℹ not verified
python app.py chat                                       # both, conversationally; grounded squad Qs unchanged
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Rules KB | The curated `fpl_rules.py` facts the assistant answers rules questions from |
| Free-form tail | The labelled ℹ answer for open questions no grounded intent (or rule) matches |
| Third trust state | ℹ "general, not checked" — beside ✓ (verified) and ⚠ (a flagged figure) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-085 | The chat-assistant design + why rules are curated, not LLM-sourced |
| `src/fpl_rules.py` | The curated FPL-rules knowledge base + `match_rules` |
| `src/ask.py` (`_decide_rules`, the `free_form` branch) | The grounded rules intent + the free-form seam |

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

- US-259 Curated rules KB + a grounded `rules` intent — answers from `fpl_rules.py`, verified (ADR-085)
- US-260 Labelled free-form tail — open tactics tagged ℹ not-verified, degrades without a model

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
