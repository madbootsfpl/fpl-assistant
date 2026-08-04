# Spike Findings — LLM Grounded Narration (Sprint 031, ADR-033)

**Date:** 2026-08-04 · **Model:** local Ollama `llama3.2` (3B) · **Latency:** ~5s/answer · **Decision: ✅ COMMIT to Phase 4** (with the design below)

---

## Question

Can a small local LLM answer an FPL question in plain English, **grounded** in our analytics —
without inventing or mis-stating numbers? (Boxed spike; not wired into `app.py`.)

## What we tried

1. **Naive (planning probe):** give the model the top-3 candidates and ask it to *recommend* a captain.
2. **Constrained (this spike):** the analytics (`captain_picks`) **decide** the pick; the LLM is handed
   the **chosen pick + only its facts** and told to *explain*, never rank/compare/compute/invent.
3. **Refined:** additionally **pre-humanise the facts** (venue `A` → "away against HUL") and forbid
   the model from expanding team codes.

## What we found

| Approach | Result |
|---|---|
| **Naive (LLM decides)** | ❌ **Hallucinated the decision** — picked Saka (xP 7.2) over B.Fernandes (7.4) and justified it with a *false* "higher xP" claim. A small model cannot rank numbers. |
| **Constrained (LLM narrates)** | ✅ Correct pick every run (B.Fernandes); no re-ranking, no invented players. ⚠️ But mis-read coded fields: `venue "A"` → "at home/hosting" (opposite); expanded `HUL` → "Huddersfield" (wrong club, it's Hull). |
| **Refined (pre-humanised facts)** | ✅ Fixed both — "playing **away** at HUL", no code expansion. Faithful, readable (if slightly generic 3B prose). |

**Final answer produced:** *"B.Fernandes is a good captain pick this gameweek because he has an
expected points total of 7.4… he will be playing away at HUL… As a penalty taker, his goal-scoring
potential increases."* — every fact traceable to the data; nothing invented.

## The design this proves (for Phase 4)

1. **Analytics decide; the LLM only narrates.** Never ask the model to rank/choose — it fabricates.
   Hand it a *pre-made decision* + supporting facts.
2. **Pre-humanise the facts.** The model must not decode abbreviations (`A`/`H`, team codes). Pass
   unambiguous phrases ("away against HUL"); forbid expansion. Grounding is *engineered*, not hoped.
3. **Pass only what's relevant** (the chosen pick's facts) — nothing to compare against.
4. **Local, lightweight.** Ollama via stdlib HTTP; no new pip dependency; private; free; ~5s.
5. **Verify grounding** — the output must name the analytics' pick and introduce no unlisted fact.

## Decision — COMMIT (green-light Phase 4), with conditions

The grounded-narration pattern **works and is worth building** — and it's genuinely differentiated
from FPL's black-box Companion: our answers are backed by *our transparent* numbers, with the LLM
structurally unable to invent them. Recommended Phase 4 scope (a proper sprint, `src/`, tests):

- A real `ask` command + a small **intent router** (captain / transfer / analyse → the right analytics).
- A **grounding contract** module: analytics produce pre-humanised facts + the decision; a prompt
  builder enforces narrate-not-decide; a light check verifies the output stays on the facts.
- Graceful degradation when Ollama is absent (the tool is fully usable without the LLM).
- (Optional) allow a larger model for fluency — the *pattern*, not the model, is the value.

**Not** a blocker to commit: prose is a little generic on a 3B model (acceptable for explanation),
and it's an added optional capability, not a core dependency.

*(Contrast: the soccerdata spike (ADR-016) ended in **defer** — narrow value, high cost. This one is
the opposite: real value, low cost, clear design → commit.)*
