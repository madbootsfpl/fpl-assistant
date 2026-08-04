# Architectural Decision Record: Two new `ask` intents — start/bench + compare

**Decision ID:** ADR-039
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Extends ADR-034 (`ask`) with two intents; reuses ADR-037 (grounding
verification) and ADR-036 (structured detail) and ADR-038 (xMins).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`ask` answers captain / transfer / analyse today. This sprint adds the two questions a manager actually
asks each week — **"who should I start/bench?"** and **"A or B?"** — both grounded (the ✓/⚠ trust line),
both showcasing **xMins** (a lineup decision *is* a minutes decision). As ever: the **analytics decide;
the LLM only narrates**.

#### A planning probe pressure-tested the two risks on real data

1. **start/bench composes cleanly — and "no change" is a real answer.** The xMins-weighted best legal
   XI for TS (via `select_squad`) **equals its declared XI** → *no swap to recommend today*. Forcing a
   premium onto the bench correctly surfaces the swap (bring in Haaland, drop Diop). So the decision is
   `select_squad` (on xMins-weighted xP) **diffed against the declared XI**, and *"already optimal"* is a
   first-class answer. Its value grows in-season when injuries force changes.
2. **compare hinges on name-matching — and the naive version breaks.** A substring probe matched real
   players but `"B.Fernandes"` also matched **`Fernandes`** (a different player), and `"Palmer"` matched
   **two** players. The robust rules below fixed every case: `"Haaland or B.Fernandes?"` →
   `[Haaland, B.Fernandes]`; `"compare Saka and Palmer"` → `[Saka, Palmer(ambiguous ×2)]`;
   `"Isak or Watkins"` → clean; `"foo and bar"` → not found.

#### Decision Drivers
- **The weekly questions** — the highest-frequency manager decisions.
- **Grounded & optional** — reuse `verify_grounding` + degrade without the LLM (Phase 4's contract).
- **Composition, not new analytics** — reuse `select_squad`, xMins, xP, the structured-detail table.
- **Robust name-matching** — never silently pick the wrong player.

---

### ✅ Decision

**1. Routing.** Add two intents to `_INTENT_KEYWORDS`, checked **after** captain/transfer/analyse and in
this order:
- **start/bench** — keywords `start`, `bench`, `lineup`, `line-up`.
- **compare** — keywords `compare`, `versus`, ` vs `, `better`, and ` or ` (weakest — last).

First-match-wins, so a captain/transfer/analyse question still routes there even if it contains "or".
The **compare decision requires ≥2 matched players**; if it can't find two, it returns a clear message
(so a stray " or " never forces a bogus comparison).

**2. start/bench decision** (`_decide_start_bench`). For a saved squad: the best legal XI via
`select_squad` on the **xMins-weighted** `xp_by_id`, **diffed against the declared XI** (bench = the
declared bench's complement; no declared bench → the optimal XI is the answer). The result:
- swap(s) — players to **start** (bench → XI) and to **bench** (XI → bench); or **"already the best
  legal XI"** when the diff is empty.
- `subjects` = the swapped players (or the XI when none).
- `detail` = a ranked **XI + bench** table (position, xMins, xP), reusing the shared renderer.

**3. compare decision** (`_decide_compare`). Extract player names from the question by matching stored
`web_name`s, with these rules (all validated at the gate):
- **Bounded substring** — the web_name appears in the lowercased question bounded by non-letters (so
  "Isak" doesn't match inside "mistaken").
- **Longest-match-wins / drop overlaps** — a match that is a substring of another match is dropped
  (`Fernandes` ⊂ `B.Fernandes` → dropped).
- **Question order** — matches are ordered by position in the question.
- **Ambiguity** — a web_name shared by >1 player is flagged → a *disambiguate* message (never a silent
  pick).
- **Not-found / only-one** — a clear message naming what was (not) found.

For ≥2 unambiguous players: a **side-by-side** table (xP over the horizon, xMins, next fixture, penalty)
and a **fact** stating which has the higher (xMins-weighted) xP — *the analytics decide the ranking; the
LLM only explains it*. `subjects` = the compared players.

**4. Grounded + optional, like the rest.** Both run `verify_grounding` (with their `subjects`) and show
the ✓/⚠ trust line; both degrade to the decision + facts without the LLM; the facts/table are always
shown.

---

### 🔀 Alternatives Considered

- **Naive substring name-matching.** Rejected — the probe showed it double-matches overlapping names and
  can't see ambiguity.
- **Fuzzy / spell-corrected names.** Deferred — exact/bounded-substring covers the real questions; fuzzy
  matching adds a dependency and false-positive risk for little gain now.
- **Let the LLM pick / rank the players.** Rejected — it fabricates rankings (the Sprint 031 lesson).
  The analytics state the higher xP; the LLM only narrates.
- **Fold start/bench into `analyse`.** Rejected — analyse is a *health check*; start/bench is the
  *lineup decision* (the explicit swaps). Distinct questions, distinct answers.
- **Make "already optimal" an error/empty.** Rejected — it's the correct, useful answer; show it plainly
  with the ranked XI/bench.

---

### 🧭 Consequences

**Positive**
- The two most-asked weekly questions are answerable in plain English, grounded and xMins-aware.
- Pure composition — no new analytics; reuses `select_squad`, xMins, xP, the detail table, the verifier.
- Name-matching is robust and honest (disambiguation + not-found messaging).

**Negative / risks (mitigations)**
- **start/bench often "no change"** on a well-built squad → treat as first-class; value grows in-season.
- **Ambiguous / missing names** → explicit messages, never a silent wrong pick.
- **" or " over-routing** → compare needs ≥2 matched players, else it bails with a message.

---

### 📊 Validation

Prototyped on the live DB before code: the robust matcher returns `[Haaland, B.Fernandes]` (drops the
spurious `Fernandes`), flags `Palmer` as ambiguous ×2, handles `Isak or Watkins` cleanly, and reports
`foo and bar` as not found; start/bench reports TS as already optimal and surfaces *bring in Haaland,
drop Diop* when a premium is force-benched. Acceptance for the sprint: both intents show a detail table
+ the ✓ line, degrade without the LLM, and give clear messages on not-found / ambiguous names.
