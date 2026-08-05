# Milestone — Phase 4 Complete (AI & Natural-Language Layer)

**Date:** 2026-08-05 · **Sprints:** 033–049 · **Decisions:** ADR-033 → ADR-049

---

## The milestone

**Phase 4 — the natural-language layer — is complete.** The app can now be *talked to*: ask a question
in plain English and get a grounded, checked answer; then keep the conversation going. Crucially, it
does this **without letting the model make anything up** — the discipline proven in the Sprint-033 spike
held for seventeen sprints.

The contract, unchanged from the first spike to the last intent:

> **The analytics decide; the LLM only narrates.** A question is routed by keyword (the model never
> picks the route either); the analytics make the decision and emit pre-humanised, self-describing
> facts; the model explains *those facts and nothing else*; and every answer is **verified** against
> the data — a ✓/⚠ trust line flags any figure or name that doesn't trace. The LLM (local Ollama) is
> **optional**: with it absent, `ask` degrades to the decision + facts.

## What shipped

- **`ask` — eight grounded intents.** captain · transfer · analyse · start/bench · compare ·
  **build-a-squad** · **best-players** · **fixtures** (ADR-034/039/041/042/048/049). Each reuses the
  Phase-1/3 engines; the NL layer adds *words, not intelligence*.
- **Grounding verification (ADR-037).** A verifier checks the narration's numbers and player names
  against the facts and prints a visible ✓/⚠ trust line — it repeatedly caught the model inventing
  figures, exactly as designed.
- **`chat` — a conversational mode (ADR-047).** Follow-ups build on the last turn — **why** (re-narrate
  the same facts), **next** (the 2nd/3rd pick, a rank offset), **what-about** (swap a parameter) — every
  turn still analytics-decided. `answer()` is simply `converse()` with no context, so the one-shot path
  is unchanged.
- **`fixtures` — three modes (ADR-048/049).** A league FDR ranking, a single team's schedule, and a
  **squad's players by their fixture run** — reusing `team_fdr`/`team_schedule`; team names resolve or
  ask, never guess.

Alongside the NL work, the decision engine itself matured in the same arc: **one xP metric** unifying the
optimiser with the decision layer (ADR-041), **sane low-evidence xP** (ADR-040), **xMins v0** weighting
every recommendation by expected minutes (ADR-038), **squad archetypes** and **bench-aware** builds
(ADR-043/044/045), and **XI-aware transfers** (ADR-046). Tests grew **279 → 421**; ADRs **32 → 49**; **no
new runtime dependency** across the whole phase (the LLM is optional and local).

## Why it stayed honest — grounding is engineered, not hoped

The spike (ADR-033) found the failure mode immediately: ask a small model to *rank* and it fabricates —
it once "recommended" the lower-xP player while claiming a higher number. The fix was structural, not a
better prompt:

1. **Analytics decide, the model narrates.** It receives a *pre-made decision* + facts, never the raw
   data to reason over.
2. **Pre-humanise the facts.** Self-describing keys (`"availability_problems": "none"`) so the model
   can't decode codes or conflate fields.
3. **Verify every answer.** The ✓/⚠ line makes trust *visible* — and it earned its keep repeatedly.

That contract is why adding a conversational mode (ADR-047) didn't loosen anything: a follow-up is an
*offset* into a ranking the analytics already produce, not new intelligence, so the verifier runs
unchanged.

## The recurring lesson — the cheapest feature reuses what exists

Over and over this phase, the biggest visible gap cost the least code because the engine was already
there. The `fixtures` intent was a router keyword + a decision function over `team_fdr` (which had existed
since Sprint 003). Squad-scoped fixtures was a *join* over that. `chat` was a thin stateful layer over the
existing `answer()` pipeline. **Clean layers keep paying interest.**

## Honest boundaries (recorded, not hidden)

- **Still preseason.** Form, per-GW history and over/under-performance only come alive after GW1
  (2026-08-21); today's numbers lean on last season + preseason data.
- **xMins is v0**, not the probabilistic ML model (that's data-gated, post-GW1).
- **A saved squad, not a live manager ID** — auth is still deferred.
- **Routing is deterministic keywords** — pragmatic, not a classifier; a broad word ("play") is placed
  last so specific intents win.

## What's next

The docs are being consolidated (Sprint 050) ahead of the next track: a **thin, read-only web UI**
(FastAPI + Jinja, reusing the analytics — the CLI stays the engine), timed to be ready for GW1. Then
**Data Hardening** once the season runs, which finally unlocks form and the richer xP the whole app has
been built to use.

## Notes for future me

- The grounding contract is the crown jewel — protect it. Any new surface (web, more intents) narrates
  *decisions*, never computes.
- A conversation didn't need a big framework: last-turn context + subject-less follow-up detection, run
  before routing so it can't collide. Small state, big payoff.
- The gate + 3-part DoD + "verify on real data at planning" caught real bugs every sprint (the plural
  team match, the possessive squad name, the £-escape grounding bug). Keep probing the messy phrasings.
