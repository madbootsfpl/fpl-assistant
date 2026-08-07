# Architectural Decision Record: The AI Chat Assistant — a curated rules KB + a labelled free-form mode

**Decision ID:** ADR-085
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** extends the grounded `ask`/`chat` router (ADR-034/037/047). Adds a **rules**
intent (grounded from a curated KB) and a **free-form** tail (labelled, not verified). Triggered by the owner
intake ("AI Chat Assistant").
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner intake: *"an AI Chat Assistant — a 24/7 chatbot for FPL **rules**, squad questions, and **tactical
advice**."* Today `ask`/`chat` is strictly **grounded**: analytics DECIDE, the LLM only **narrates**, every
number/name is **verified** (✓/⚠, ADR-037). Rules and open tactics are things the analytics can't answer — so
a chatbot must extend the router **without breaking the trust model**.

**Verified:** this session the local Ollama **hallucinated chip facts** (invented a number, miscounted) and
`verify_grounding` flagged it — proof the LLM can't be trusted on FPL **rules**. `route()` returns
`intent=None` for unrecognised questions, handled at one point in `_fresh` (the `_FALLBACK` help text) — a
clean seam for a general handler *after* every grounded intent. `narrate()` already degrades to None without
Ollama.

#### Decision Drivers
- **Rules must be right** — answer them from a **curated, authoritative KB**, not the model's memory.
- **Keep the trust boundary visible** — verified (✓) for grounded + rules; a distinct **ℹ "not verified"** for
  free-form.
- **Don't regress grounded questions** — squad/player questions route grounded exactly as today.
- **Degrade honestly** — rules show their facts without the LLM; free-form needs the LLM (else the help text).

---

### ✅ Decision

**1. A curated FPL-rules knowledge base + a grounded `rules` intent (US-259).** `src/fpl_rules.py` — a `RULES`
list of `{topic, cues, fact}` entries (scoring · chips · transfers/hits · deadlines · price changes · squad
rules · formations · autosubs · captaincy · DGW/BGW), each `fact` a short **authoritative** string. A pure
`match_rules(question) -> [(topic, fact)]` (topic cues → the relevant facts). A `rules` intent, routed **first**
on **question-shaped** cues (*how does / how do / what is a / what are the / the rules / how many points /
scoring / clean sheet points / bonus points / price change / auto-sub / when is the deadline*) that **don't
collide with squad commands**, dispatches to `_decide_rules`: it selects the matching facts, narrates them, and
**verifies** the prose against them (✓) — degrading to the raw facts block without Ollama. If routed but no
topic matches, it lists the topics it can explain.

**2. A labelled free-form tail (US-260).** When no grounded intent **and** no rules topic matches, a
`_free_form(question, narrator)` asks the LLM a **scoped** general-FPL question (*"answer briefly; do NOT
recommend specific players/picks — those come from the tools"*) and returns `trust={"free_form": True}`, which
`render_ask` shows as **ℹ General FPL advice — not checked against your data**. Without Ollama → the existing
help text. It never makes a squad/player **decision** (those stay grounded + verified).

**3. The trust line gains a third state.** `_trust_line`: `✓ Checked` (grounded/rules) · `⚠ Unverified …`
(a flagged figure) · **`ℹ General … not checked`** (free-form). Always shown, so the boundary is explicit.

---

### 🔀 Alternatives Considered

- **Free-form for everything (label it "not verified").** Rejected — leans on the LLM's FPL knowledge, which is
  stale/wrong on rules (it hallucinated chips this session). Facts must be curated.
- **Grounded rules only, no open chat.** Rejected — doesn't deliver the "24/7 tactical chatbot"; open questions
  stay a dead-end help message.
- **RAG over a big knowledge base.** Deferred — heavier (embeddings/store) than the value now; a small curated
  KB covers the real rules questions and stays auditable.
- **A hosted LLM so the deploy has free-form.** Deferred — the deployed app has no Ollama; it degrades to
  **rules + grounded** (still useful), and free-form works locally. Revisit if a hosted model is added.

---

### 🧭 Consequences

**Positive**
- A real assistant: rules answered **correctly + verified**; open tactics answered **honestly labelled**.
- The grounded path is untouched; the curated KB keeps rules auditable; everything degrades without the LLM.
- The trust boundary is always on screen (✓ / ⚠ / ℹ).

**Negative / risks (mitigations)**
- **KB staleness** — FPL tweaks rules between seasons → the KB is one small file, easy to update; facts are
  phrased current-season and dated in the ADR/file.
- **Routing collisions** (a rules question containing "transfer"/"bench") → rules routes on **question-shaped**
  cues placed first; squad commands keep their intents; pinned by tests.
- **Free-form is ungrounded** → clearly labelled **ℹ not verified**, scoped away from squad decisions, and
  absent without a model. It never wears the ✓.

---

### 📊 Validation

Verified: the LLM hallucinates rules (⚠ caught); `route()==None` is a single seam; `narrate()` degrades.
Acceptance: `match_rules` maps rules questions to the right facts; `_decide_rules` verifies clean (✓) when the
narration restates only KB facts and flags (⚠) an invented number; the free-form path yields
`trust={"free_form": True}` → an **ℹ** line and degrades to the help text without a narrator; the routing guard
keeps *"how does bench boost work"* → rules, *"which chip for TS"* → chips, *"fix my bench"* → start_bench,
*"what transfer should I make"* → transfer; existing **663** tests stay green (new tests added); ruff clean.
