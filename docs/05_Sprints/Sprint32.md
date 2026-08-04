# Sprint 032: Phase 4 — the `ask` command (grounded NL answers)

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~3–4 working sessions (the first Phase 4 production feature)
**Carried Over:** None (Sprint 031 spike green-lit this)

> **Direction:** the Sprint 031 spike (ADR-033) proved grounded local-LLM narration works and
> returned **COMMIT**. This sprint builds the production version: a real `ask` command that routes a
> question to the analytics, which **decide**, and has the LLM **narrate** — grounded, and fully
> usable even when the LLM is absent.

---

### 🔎 Verified at planning (the standing lesson — the pattern generalises)

The spike proved the pattern for **captain**. Before committing to a 3-intent command, checked it
**generalises to `transfer` and `analyse`** (live, `llama3.2`):

- **Transfer ✅** — *"replacing Kelleher with Benitez… a significant boost in expected points gain
  (15.4)"* — correct and grounded.
- **Analyse ✅ (with a caveat)** — *"278.1 projected XI points… weakest starters Ampadu, Kelleher,
  Truffert"* — right on the numbers, **but** it said *"concerns about the **availability**… of the
  weakest"* when `availability_problems: 0`. It **conflated two separate facts**.
- **The refinement:** multi-fact summaries need **explicit, self-describing facts** (e.g.
  `"availability_problems": "0 (none)"`, clearly separated from `weakest_starters`) and a prompt that
  says *don't merge fields*. Single-decision intents (captain, transfer) are more robust; the
  summary intent (analyse) needs the tightest framing.

**Also:** still preseason (0 GWs); ClubElo is **intermittent** (timed out this check, up earlier) —
best-effort, degrades fine, not a blocker. **No new pip dependency** (stdlib HTTP to Ollama).

---

### 🧭 What's new — a language layer on a tight leash, and *optional*

`ask` is the first production LLM feature — but it changes nothing about the numbers. It **routes**
a question (keyword-based — the LLM never decides the route either), the **analytics make the
decision** and emit **pre-humanised facts**, and the LLM turns that into a sentence, structurally
unable to rank/compute/invent. Crucially, the LLM is **optional**: if Ollama is absent, `ask` still
prints the analytics decision + facts with a note — the tool never *depends* on the model.

---

### 🎯 Sprint Goal

**Objective:** A production `ask "<question>"` command — keyword-routed to `captain`/`transfer`/
`analyse`, where the analytics decide and local Ollama narrates pre-humanised facts — grounded,
tested, and gracefully degrading when the LLM is unavailable.

#### Success Criteria
- [ ] Approach agreed (**ADR-034**) before code — the production grounding contract, keyword routing,
      graceful degradation, the analyse fact-framing refinement
- [ ] A small **LLM client** (`src/`, stdlib HTTP to Ollama; injectable; times out/degrades cleanly)
- [ ] A **grounding contract**: per intent, analytics **decide** → **pre-humanise facts** → a
      narrate-not-decide prompt → narration; the LLM never ranks/computes/invents
- [ ] **Keyword intent routing** (captain / transfer / analyse + squad extraction) — deterministic
- [ ] `ask "<question>"` command covering the **three intents**
- [ ] **Graceful degradation** — Ollama absent/down → show the analytics decision + facts + a note
      (the tool is fully usable without the LLM)
- [ ] Tests (routing, fact-humanising, the ask flow with an **injected fake narrator**, degradation)
      — the real LLM call is smoke-only; production suite stays green + **no new pip dependency**
- [ ] Docs: ADR-034 + index, Architecture changelog, Handbook, README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-095 | **Gate.** Phase 4 `ask` design (**ADR-034**): production grounding contract (analytics decide → pre-humanise → narrate-not-decide); keyword routing; graceful degradation (LLM optional); the analyse multi-fact framing refinement. Pressure-tested (spike + the transfer/analyse probe) | Critical | ✅ Done | 0.5 session |
| US-096 | **The LLM layer + `ask` (captain)** — an Ollama client (`src/`, stdlib HTTP, injectable, graceful) + the grounding contract + keyword router + `ask` command with the **captain** intent + degradation. Tests (injected narrator) | High | ✅ Done | 1.5 sessions |
| US-097 | **Extend `ask` to transfer + analyse** — the two remaining intents, with **explicit fact-framing** for the analyse summary (the conflation fix). Tests + live smoke | High | ✅ Done | 1.5 sessions |

#### Technical Tasks & Maintenance
- [x] ADR-034 recorded + added to the ADR index — _US-095_
- [x] Update Architecture changelog (a language layer; analytics decide / LLM narrates) — _US-096_
- [x] Update Handbook (Ch 21 — a language layer that adds words, not intelligence) — _US-097_
- [x] Update README (the `ask` command; Phase 4 natural language) + PROJECT_STATUS — _US-097_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — routing, humanising, the `ask` flow (with a fake narrator), and
   graceful degradation; the existing 279 stay green; **no new pip dependency**.
2. **Manual smoke test done** — `ask` on live data for all three intents (real Ollama); the answers
   stay grounded; and `ask` still works with Ollama stopped (degrades to the decision + a note).
3. **Documentation updated & checked** — ADR-034 + index, Architecture, Handbook, README,
   sprint board + PROJECT_STATUS (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| `ask` over three intents (captain/transfer/analyse) | A conversational multi-turn chat loop |
| Keyword routing + squad extraction | LLM-based routing (the LLM decides nothing, incl. the route) |
| Local Ollama via stdlib HTTP; graceful degradation | A cloud LLM / API keys / new pip deps |
| Grounded narration of a pre-made decision | Letting the LLM rank/compute/recommend |

**External Dependencies:**
- [ ] Local Ollama (`llama3.2`) for the smoke test; the tool degrades gracefully without it.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| LLM invents / re-ranks | High | Analytics decide; pass pre-humanised facts; forbid ranking/compute; verify output |
| Multi-fact summary conflation (seen in analyse) | Med | Explicit self-describing facts (`"0 (none)"`) + "don't merge fields"; single-decision intents are safer |
| The tool depends on the LLM being up | High | **LLM is optional** — degrade to the analytics decision + facts + a note |
| A misrouted question | Med | Keyword routing is deterministic + a clear "I can answer about captain/transfer/squad" fallback |
| New heavy dependency / tests need a live LLM | Med | Stdlib HTTP, no new pip dep; inject a fake narrator in tests; real LLM is smoke-only |

---

### 🗝️ Gating decision (US-095 → ADR-034)

Settle before code — the spike + probe pressure-tested it. Proposed (confirm/redirect at
"start US-095"):

1. **Production grounding contract.** Per intent: analytics **decide** the answer + emit
   **pre-humanised, self-describing facts**; a prompt builder enforces *narrate-not-decide, invent
   nothing, don't merge fields*; the LLM returns prose only.
2. **Keyword routing.** Map the question to captain / transfer / analyse by keywords, extract the
   squad name. Deterministic — the LLM never decides the route. Unknown → a helpful "I can answer
   about captaincy, transfers, or your squad's health" message.
3. **The LLM is optional (graceful degradation).** Ollama absent/down → `ask` prints the analytics
   decision + facts + "(start Ollama for a written explanation)". The tool is fully usable without it.
4. **Local Ollama via stdlib HTTP; injectable narrator** so tests use a fake and the real call is
   smoke-only. No new pip dependency. Config: `OLLAMA_URL`, `OLLAMA_MODEL`.

**Worked example (already run):** captain (spike), transfer, and analyse all narrated grounded on
real data — with the analyse conflation flagged, driving the explicit-fact-framing rule.

---

### 📝 Session Progress Log

- **US-095 (gate) ✅** — Recorded **ADR-034**: the production `ask` design. Module shape confirmed
  (`src/llm.py` client → `None` when Ollama absent; `src/ask.py` route/humanise/orchestrate;
  `src/ui/ask.py`). The grounding contract (analytics decide → **pre-humanised self-describing
  facts** → narrate-not-decide/no-merge/no-decode), **keyword routing** (LLM never routes), and
  **the LLM is optional** (degrade to the decision + facts + a note) all agreed. Injectable narrator
  → offline tests; real call smoke-only; no new pip dep. Pressure-tested by the spike + the
  transfer/analyse probe (incl. the analyse conflation → self-describing facts).
- **US-096 (LLM layer + `ask` captain) ✅** — Built `src/llm.py` (Ollama client, stdlib HTTP,
  **returns None when unavailable**), `src/ask.py` (keyword `route`, `_captain_facts` humaniser,
  `_build_prompt`, `assemble`, `answer` — injectable/optional narrator), `src/ui/ask.py`, and the
  `ask` command. **10 tests** (routing, humanising incl. venue A→"away against", prompt rules,
  narrated/**degraded**/no-result/unrecognised) → suite **279 → 289**; ruff clean; **no new pip
  dep**. Live smoke: grounded ("B.Fernandes… away against HUL… penalty taker… 7.4"); **degraded
  path** (narrator→None) shows decision + facts + note; unrecognised → help. The LLM is genuinely
  optional.
- **US-097 (transfer + analyse intents) ✅** — Added `_transfer_facts` / `_analyse_facts` (the latter
  **self-describing** — `availability_problems: "none"`, the conflation fix) + `_decide_transfer` /
  `_decide_analyse` (horizon 5, reuse suggest_transfers/analyse_squad/select_squad); registered in
  `answer`; a "name a squad" nicety for those intents. Also made squad matching **phrasing-robust**
  (match known saved names, not a preposition — "for TS"/"from TS" both work; captain stays global).
  **+8 tests** → suite **289 → 294**; ruff clean. Live smoke: all three intents grounded — analyse
  now correctly says "no availability problems". Handbook Ch 21 + README updated.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-095 (ADR-034), US-096 (LLM layer + `ask` captain), US-097
  (transfer + analyse). **Phase 4 has landed:** `ask "<question>"` answers captaincy, transfers, and
  squad health in plain English, grounded in the analytics. Tests 279 → **294**; one ADR; **no new
  pip dependency** (stdlib HTTP to local Ollama); the LLM is **optional** (degrades to the decision).
* **Carried Forward:** None. More intents / a chat mode are on the Backlog; Data Hardening waits on GW1.
* **Key Artifacts / Decisions:** ADR-034 (analytics decide / LLM narrates; keyword routing; the LLM
  optional); `src/llm.py`, `src/ask.py`, `src/ui/ask.py`, the `ask` command; the self-describing
  fact-framing (the conflation fix).

#### Retrospective
* **What Went Well?**
  - **A language layer that adds words, not intelligence.** The analytics keep deciding; the LLM only
    narrates. The whole feature reuses `captain_picks`/`suggest_transfers`/`analyse_squad` read-only.
  - **The LLM is genuinely optional** — `narrate` returns `None` when Ollama is absent and `ask`
    degrades to the decision + facts. Tested first-class (a `None`-returning narrator), so it's
    production-grade, not a demo.
  - **The spike's findings became the design** — analytics-decide, and *pre-humanise the facts*. The
    analyse conflation from planning was fixed with self-describing facts (`"none"`), verified live.
  - **Grounded offline testing** — an injectable narrator meant routing/humanising/degradation are
    unit-tested with no live model; the real call is smoke-only. No new dependency.
  - DoD held (32nd sprint): tests + live smoke (all three intents + the degraded path) + docs.
* **What Could Be Improved?**
  - **Keyword routing + name-matching is crude** — robust enough (match saved squad names, not a
    preposition), but it's not real NL understanding. Fine for three intents; a richer parser is a
    later job.
  - **3B-model prose is faithful but plain**, and occasionally imprecise in wording (e.g. calling a
    +gain "a higher gain than X"). Grounded on the facts, but a bigger model would read better.
* **Lessons Learned?**
  - Let the LLM narrate, never decide; and *engineer* the grounding (pre-humanised, self-describing
    facts) rather than trust a prompt.
  - Make an added capability *optional* — degrade to the deterministic core so nothing depends on it.
  - A spike's findings are the real spec: both design rules came from running the model.
* **Action Items for Next:**
  - [ ] (Backlog) more `ask` intents / a conversational mode; a larger/cloud model option behind the
        same contract; a light output-grounding check (assert the pick name appears).
  - [ ] **Data Hardening** at ~GW1 (2026-08-21).
  - [ ] Keep gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — deepen Phase 4 (more intents / chat), wait for GW1 to do
**Data Hardening**, or start the **web UI** (Phase 2). All live options.

**Completion Date:** 2026-08-04
**Final Notes:** Phase 4 arrived on strict, honest terms — grounded, transparent, and optional. The
analytics decide; a local model narrates pre-humanised facts and can't invent the numbers; and it all
works with the LLM switched off. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
