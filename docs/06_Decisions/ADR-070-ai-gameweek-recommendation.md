# Architectural Decision Record: An AI gameweek recommendation ("this week")

**Decision ID:** ADR-070
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** new capability. Assembles existing primitives (captain ADR-029, lineup
ADR-039/040, transfer ADR-030/046, availability ADR-023) behind the grounded narrate-and-verify pipeline
(ADR-034/037). No change to any of those primitives. Triggered by tester request.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester feedback: *"Could we have an AI recommendation on your squad for the upcoming game week?"* Today a
manager must visit four separate tools — Captain, Health, Transfer, and check availability by eye — and
stitch the weekly decision together themselves. They want **one answer**: for *my* squad, this week, who do
I captain, is my lineup right, is there a transfer worth making, and is anyone flagged.

**Verified in code (real signatures, this sprint):** the four pieces already exist and compose cleanly —
`captain_picks(owned, upcoming, …)` (next-GW pick), `best_legal_xi(owned, xp_by_id)` vs the declared bench
(the lineup change), `suggest_transfers(owned, market, xp_by_id, bank=0, limit=1)` (one self-funding
upgrade), and `is_unavailable` / `status == "d"` (flags). The `ask` layer already turns a decision dict
(`facts` + `task` + `subjects`) into a narrated, **verified** `AskResult` via `assemble`/`verify_grounding`,
and squad-scoped intents already see the web's **session** squad through `active_squad`. So this is an
**assembly + narration**, not new analytics — and it degrades to the structured plan without Ollama, like
every other `ask` intent.

#### Decision Drivers
- **One weekly answer** — captain · lineup · a transfer · flags, in one place, for *your* squad.
- **Analytics decide; the LLM only narrates** — grounded + verified (✓/⚠), never a model opinion (ADR-037).
- **No analytics drift** — reuse the exact primitives the individual tools use, so answers can't diverge.
- **Useful without the LLM** — the structured plan (a `detail` block) is the truth; prose is a bonus.
- **Both surfaces** — a natural-language `ask`/`chat` intent *and* a one-click **Squads → This week** view.

---

### ✅ Decision

**1. A pure-ish assembler `gameweek_plan(...)` (analytics).** New `src/analytics/gameweek.py`:
`gameweek_plan(owned, market, upcoming, xp_by_id, *, baseline_by_code, minutes_weight, history_by_code,
bench_ids=(), bank=0.0)` → a dict `{captain, lineup, transfer, flags}`. It **only orchestrates** existing
primitives (no re-derived xP): captain = `captain_picks(…, limit=1)` (next GW); lineup = `best_legal_xi`
vs the declared bench (bring-in / drop / the recommended XI+bench); transfer = the single best positive-gain
`suggest_transfers` (bank 0); flags = owned players that are `is_unavailable` or doubtful (`status == "d"`),
with the reason + chance%. Captain uses its own next-GW xP (horizon 1); lineup/transfer use the caller's
5-GW `xp_by_id` — the horizons each decision actually wants.

**2. A grounded `ask` intent `gameweek` (ADR-034/037).** `_decide_gameweek(store, squad, active_squad)`
reuses `_squad_xp` (owned rows + 5-GW `xp_by_id`), calls `gameweek_plan`, and returns a decision dict:
`detail` (a `render_gameweek_plan` block — the exact plan, shown with or without Ollama), self-describing
`facts` (captain / lineup_change / transfer_to_consider / flagged_players — every number present so the
verifier can trace it), `subjects` = all owned names + the transfer buy (so `verify_grounding` doesn't flag
a legitimately-named starter), and a `task` for the narrator. Routing: a new `"gameweek"` keyword group
(*"this week", "this gameweek", "gameweek plan", "what should i do", …*) placed **after** the specific
intents, so "who should I captain this week" still routes to captain; it's squad-scoped in `_needs_squad`.

**3. A `render_gameweek_plan(plan, squad_name)` renderer (ui).** New `src/ui/gameweek.py` — a plain-text
block (Captain / Lineup / Transfer / Flags), the same "the table is the truth" shape the other `ask`
details use, rendered in the CLI and (via `render_ask`) the web.

**4. A "This week" Squads view (web).** Add **This week** to the Squads segmented control; `render_this_week`
calls `ask.answer("what should I do this week for <squad>?", active_squad=squad)` and shows `render_ask`
(the plan + the ✓/⚠ trust line) — reusing the session squad, no server writes. Degrades to the plan without
Ollama.

**5. Degradation + tests.** Without Ollama: the `detail` plan + facts show, no prose (unchanged pattern).
Tests: `gameweek_plan` assembles the four parts (a fake squad, offline); `_decide_gameweek` is grounded
(a stub narrator, verified ✓); routing sends "this week" → gameweek but "captain this week" → captain; the
Squads "This week" view renders. Existing **588** stay green.

---

### 🔀 Alternatives Considered

- **New analytics for the weekly call.** Rejected — the primitives exist and are already tested/trusted;
  re-deriving would risk divergence from Captain/Health/Transfer. Assemble, don't reinvent.
- **Let the LLM decide the plan.** Rejected outright — violates the project's core rule (analytics decide,
  the LLM only narrates, ADR-034/037). The LLM sees only the pre-made facts.
- **A bespoke web widget instead of the `ask` pipeline.** Rejected — it would bypass grounding/verification
  and duplicate rendering. Routing through `ask.answer` gives the ✓/⚠ line for free and keeps one engine.
- **One horizon for everything.** Rejected — captain is a one-week bet; lineup/transfer look at the 5-GW
  run. Mixing horizons matches how the standalone tools already decide.
- **Include chip advice (TC/BB/WC).** Deferred — out of scope; the roadmap's chip optimisers are a later
  phase. This is the weekly baseline plan.

---

### 🧭 Consequences

**Positive**
- One grounded weekly answer for a squad, on both surfaces (ask/chat + a Squads view), verified.
- Zero analytics drift — it *is* the Captain/Health/Transfer/availability tools, assembled.
- Useful without the LLM (the plan block is the truth); prose + trust line when Ollama is up.

**Negative / risks (mitigations)**
- **Preseason the numbers are quiet** (form/momentum 0 until GW1) → the plan still reads correctly (captain
  by baseline xP, availability flags live now); it gets sharper at GW1 with no code change.
- **A new routing keyword group could mis-catch** → placed after the specific intents and phrase-based
  ("this week"/"what should i do"), with a test pinning "captain this week" → captain.
- **`verify_grounding` false-positives on named starters** → subjects include all owned names + the buy, so
  a legitimately-named player isn't flagged.

---

### 📊 Validation

Verified: the four primitives compose on real data (offline fake squad). Acceptance: `ask "what should I do
this week for <squad>?"` and **Squads → This week** both return a coherent plan (captain · lineup · a
transfer · flags) that the LLM narrates and the verifier checks (✓/⚠); it degrades to the plan + facts
without Ollama; routing keeps captain/transfer/etc. pointed questions on their own intents; the web writes
nothing server-side; the existing 588 tests stay green (new tests added for the assembler, the intent,
routing, and the view).
