# Architectural Decision Record: Read the headlines we already fetch — resolve, then extract

**Decision ID:** ADR-151
**Date:** 2026-08-26
**Status:** 🚧 **Proposed — awaiting the gate.** Grounded in **spike 206**
(`spikes/206-headline-extraction/FINDINGS.md`), which measured the corpus, a rule-based baseline and a local
model before anything was designed.
**Superseded By / Replaces:** Gives ADR-146's unexplained exodus a *cause*. Extends the Signals page (ADR-150).
**Explicitly declines** the sentiment/ML framing the question arrived in. No `decision_xp` change — ever.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 The question, and why the answer is a different feature

The owner asked whether TensorFlow / ML could turn Signals into a **sentiment score**, and whether Trending
should blend in. Spike 206 answered all three parts with measurements:

- **No corpus.** 112 headlines · **6,227 characters** · median 51 chars · **zero** posts with body text · no
  labels · one gameweek of ground truth.
- **No sentiment.** The text is reported fact with named journalists. *"Cole Palmer is Player of the
  Matchweek"* is an event, not a positive opinion. A sentiment score would invent a dimension the data lacks.
- **But a real feature underneath.** The Watkins → Al-Hilal story is **already in the feed we fetch**, reduced
  to *"Watkins: 13 mentions"* — the exact story behind ADR-146's *"96,095 sold him and nothing explains it"*.

So: **extraction, not classification.**

### 🔬 And rules are not good enough — which is what justifies a model

A deliberately narrow rule-based extractor scored **7 of 12 correct — 58% precision**, failing in ways that
matter: two **negations** (*"Palmer in training — not injured"* read as an injury), a **wrong player**, and one
that matched **Enzo Maresca, a manager**. `qwen3:8b` zero-shot fixed four of the five, kept both controls, and
**every model error was silence rather than a false claim**.

58% would be fatal for a signal whose whole discipline is never to invent a cause.

---

### ✅ Decision

**1. The LLM proposes; the app verifies. It never decides.**

This project's standing rule is *analytics decide, the LLM only narrates* (ADR-034/037). Extraction looks like
an exception and must not become one, so it takes the same shape as `verify_grounding`: the model returns a
**candidate** `{player, kind}`, and the app keeps it only if

- the `kind` is in a closed set (`transfer` · `injury` · `return`), and
- the name **resolves to exactly one player in our own data**.

Anything else is dropped. **The model can suggest; it cannot assert.**

**2. Resolution is the hard part, and it must be allowed to say "I don't know".**

The model returns names as written; FPL stores `web_name`:

```
"Ollie Watkins"  → 1 match  ✅       "James Maddison" → 1 match  ✅
"Savinho"        → 0 matches ❌      surname-only     → often >1  ❌
```

Surname matching is exactly what produced the rules' *"Jaouen"* and *"Enzo"* errors. So resolution matches on
`web_name`, then `first_name + second_name`, and **drops on 0 or >1 candidates**. A missed story costs
nothing; a story attached to the wrong player costs the credibility of every flag on the page.

⚠️ **Prerequisite:** `community_buzz` currently lists **"Palmer" twice at 30 mentions** because two players
share the surname — a live instance of the same collision. Fix that first; it is the same resolver.

**3. Precision over recall, stated as a target.** ~10% of headlines carry a resolvable event and that is fine.
This is not a news reader; it exists to explain a flag we already show.

**4. It runs where a model exists, and the app degrades to today when it does not.**

Ollama is local-only; Streamlit Cloud has no model. So extraction is an **enrichment step at refresh time**
(local/CLI), storing resolved events with the data — which fits ADR-056's read-only deployment. With no model,
no events, and the exodus stays *"unexplained"*: exactly what it says now. Same fallback idiom as ADR-133.

**5. What it attaches to.** ADR-146's flag becomes:

> *96,095 managers sold **Watkins** this gameweek — and Fabrizio Romano reports an agreed move to Al-Hilal.*

Sourced, quotable, and checkable, because the headline is carried with it.

### ❌ Explicitly not built

- **A sentiment score** — no sentiment in the data (spike 206 §1).
- **A trained model** — no labels, 6KB of text.
- **A blended Signals+Trending index** — blending needs the *relative weight* of each signal, which needs the
  **evaluation loop** (roadmap, unbuilt): *did following the crowd beat xP-only?* Until that exists, any
  weighting is a guess with a decimal point. **Order matters: measure, then blend.**

### ⚠️ Risks

- **A wrong attribution is worse than silence.** The whole design is precision-first for this reason, and the
  quoted headline lets a reader check us.
- **Reddit rate-limits** (a 429 was hit during the spike). Extraction must run off cached text, never trigger
  fetches of its own.
- **Model drift / prompt fragility.** Mitigated by the closed `kind` set and hard resolution — a model that
  starts hallucinating produces *fewer* events, not wrong ones.
- **Staleness.** Enrichment is as fresh as the last refresh. Acceptable: the exodus it explains updates on the
  same cadence.

### 🧪 Definition of Done

1. **Tests** — resolution drops 0-match and >1-match names (with the real Palmer collision as a case); the
   `kind` set is closed; a malformed model response yields no events rather than an exception; the exodus note
   gains a cause only when one resolves, and is byte-identical otherwise.
2. **Manual smoke** — the 112-headline corpus in the spike, checked by hand for precision.
3. **Docs** — this ADR, the Roadmap, PROJECT_STATUS, a sprint retro.

**Open for the gate:** whether extraction runs at `refresh` (committed with the snapshot) or behind a gated
Haiku call on Cloud — and whether the fix to `community_buzz`'s surname collision ships first as its own small
change.
