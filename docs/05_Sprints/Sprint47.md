# Sprint 047: Conversational `ask` — a chat mode with grounded follow-ups

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2–3 working sessions (a gate + a follow-up resolver + a `chat` REPL across surfaces)
**Carried Over:** None (Sprint 046 closed clean)

> **Direction (owner):** *more Phase 4* → a **conversational `ask`**. Today every question is one-shot:
> "who should I captain for TS?" answers, but "why?" or "and the second best?" fall straight through to
> the help message. Make a second question **build on the first** — while keeping the strict discipline
> that the **analytics decide every turn** and the LLM only narrates.

---

### 🔎 Verified at planning (the standing lesson — the ranked engines make follow-ups grounded)

- **The decision engines already rank — follow-ups are an offset, not new logic.** `_decide_captain`
  computes `captain_picks(limit=3)` but surfaces only `picks[0]`. On **TS** the top three are real and
  meaningful: *B.Fernandes 5.9 → Haaland 5.7 → Virgil 4.1*. So *"and the second best?"* → **Haaland** is
  a genuinely grounded answer — the analytics still decide; the follow-up just reads rank #2.
- **"why?" is pure re-narration — the safest follow-up.** The last decision dict already carries
  `facts` + `subjects`; *"why?"* re-narrates *those same facts* with a more detailed task. No new
  analytics, nothing to invent — the ADR-037 verifier checks it against the identical facts.
- **The gaps are real.** A routing probe showed *"why?"*, *"and the second best?"*, *"what about
  defenders?"* all fall through to the fallback today — there is no home for a follow-up.
- **Grounding still holds every turn.** *"next"* and *"what about X"* re-invoke the existing engines
  (with an offset / a swapped param), verified as today; *"why"* re-narrates existing facts. No
  follow-up is a free-text answer from the model.
- Still preseason (0 GWs; GW1 deadline 2026-08-21); FPL data fully populated (20 teams, 380 fixtures);
  ClubElo intermittent.

---

### 🧭 What's new — a question can build on the last one

`ask` gains a **conversational mode** (`chat`): a short REPL that holds the *last answer* in memory, so a
follow-up resolves against it. Three grounding-safe families — **why** (re-explain), **next** (the 2nd/3rd
pick), **what-about** (swap a parameter, e.g. position) — each rewritten into a full, analytics-decided
turn. The one-shot `ask` command is unchanged; `chat` is the additive, stateful layer on top of it.

---

### 🎯 Sprint Goal

**Objective:** a `chat` REPL where follow-ups build on the previous answer via an in-memory `Context`
(last intent + squad + decision). Three follow-up families — **why** (re-narrate the last decision),
**next** (re-run the last intent at a rank offset), **what-about** (re-run with a swapped param) — all
**analytics-decided** and grounding-verified. A gate settles the context model + the follow-up families.

#### Success Criteria
- [ ] Approach agreed (**ADR-047**) — the `Context` (what carries forward); the three follow-up families
      and how each stays analytics-decided; the `chat` REPL shape; the ambiguity rule; grounding unchanged
- [ ] A `Context` holding the last successful turn (intent, squad, decision/ranked results)
- [ ] A **follow-up resolver** — detect why / next / what-about and rewrite into a full intent+params;
      anything else is a normal fresh question that updates the context
- [ ] **Rank offset** in the decision layer — captain / transfer / shortlist can return the Nth pick
      (the engines already rank; expose it), so *"and the second best?"* is grounded
- [ ] A **`chat`** REPL command — an interactive loop; each turn reuses `answer()` then updates the
      context; `quit`/EOF exits; a follow-up with no context gives a gentle nudge
- [ ] The grounding verifier (ADR-037) runs on every follow-up; *"why"* re-narrates the same facts
- [ ] Tests (why re-explains the last decision; next returns pick #2; what-about swaps position; a
      no-context follow-up nudges; the one-shot `ask` is unchanged) + smoke
- [ ] Docs: ADR-047 + index, Architecture, Handbook, README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-139 | **Gate.** Conversational design (**ADR-047**): the `Context` (last intent/squad/decision); the three follow-up families (why = re-narrate; next = rank offset; what-about = param swap) and why each stays analytics-decided; the `chat` REPL shape; the ambiguity + reset rules; grounding unchanged. Pressure-test (done: the captain top-3 + a "why" on real data) | Critical | ✅ Done | 0.5–1 session |
| US-140 | **`Context` + follow-up resolver + rank offset** — a `Context` dataclass; a resolver that maps a follow-up to a full intent+params against the context; expose an `offset`/rank in captain + transfer + shortlist decisions so *"next"* is grounded. Tests | High | ✅ Done | 1 session |
| US-141 | **`chat` REPL + wiring + docs** — the interactive command; each turn = `answer()` then update context; `quit`/EOF; the no-context nudge; the one-shot `ask` unchanged. Tests + smoke + docs | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-047 recorded + added to the ADR index — _US-139_
- [x] Update Architecture changelog (conversational `ask`) — _US-140_
- [x] Update Handbook (a lesson: follow-ups stay analytics-decided) + README (`chat`) — _US-141_
- [x] Update PROJECT_STATUS — _US-141_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — *why* re-narrates the last decision (same facts); *next* returns the 2nd
   pick; *what-about* re-runs with a swapped position; a no-context follow-up nudges; the one-shot `ask`
   path is unchanged; existing **396** stay green; no new dependency.
2. **Manual smoke test done** — in `chat`: "who should I captain for TS?" → "why?" → "and the second
   best?" → "what about defenders?" each build on the last, and every answer carries the ✓/⚠ trust line.
3. **Documentation updated & checked** — ADR-047 + index, Architecture, Handbook, README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A `chat` REPL + an in-memory `Context` (the last turn) | Persisted history across separate process runs — later |
| Three follow-up families: why / next / what-about | Pronoun resolution ("is **he** worth it?") — later |
| Rank offset in captain / transfer / shortlist decisions | An LLM-based intent classifier (routing stays deterministic) |
| The one-shot `ask` command unchanged | Cross-intent memory beyond the last successful turn |

**External Dependencies:** None (the Ollama narrator stays optional; `chat` degrades to decision + facts).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| A follow-up lets the model free-narrate (ungrounded) | High | Every follow-up is analytics-decided (why = re-narrate the *same* facts; next/what-about re-invoke the engines); the ADR-037 verifier runs each turn |
| Follow-up detection misfires on a fresh question | Med | A small, explicit trigger set (why/next/what-about); anything unmatched is a normal fresh question that *updates* the context; verify phrasings on real data |
| Stateful REPL complexity | Med | In-memory only, the *last* turn only; no persistence; each turn reuses the proven `answer()` pipeline |
| "next" past the ranked list | Low | The engines already cap (limit=3 / shortlist length); an offset past the end gives a graceful "that's all I have" |

---

### 🗝️ Gating decision (US-139 → ADR-047)

Settle before code — the ranked engines + the "why = re-narrate" safety are probed. Proposed
(confirm/redirect at "start US-139"):

1. **The context.** A `Context` holds the last *successful* turn: `intent`, `squad`, and the `decision`
   (facts + subjects + any ranked results). Updated after every fresh answer; read by a follow-up.
2. **The follow-up families** (each analytics-decided):
   - **why / explain / how come** → re-narrate the last decision's *existing* facts with a detailed task
     (no new analytics; verified against the same facts).
   - **next / second best / who else / another** → re-run the last intent at a **rank offset** (captain,
     transfer, shortlist already rank; expose it).
   - **what about \<X\> / and \<position\>** → re-run (shortlist, or the last intent) with a swapped
     parameter (position first; the obvious, testable case).
3. **The surface.** A **`chat`** REPL (`python app.py chat`) — an interactive loop; each line runs the
   normal pipeline, then updates the context; `quit`/EOF exits; a follow-up with no context nudges. The
   one-shot `ask` command is untouched.
4. **Grounding.** Unchanged (ADR-037) — it runs on every turn, including follow-ups.

**Worked example (probed):** on TS, captain top-3 = *B.Fernandes 5.9 · Haaland 5.7 · Virgil 4.1*, so
"who should I captain for TS?" → B.Fernandes, then "and the second best?" → **Haaland** (rank #2), then
"why?" re-explains Haaland from the same facts — all grounded.

---

### 📝 Session Progress Log

- **US-139 (gate) ✅** — Recorded **ADR-047**, the conversational design settled after a walk-through +
  a live-DB probe. Confirmed the **safety property**: every bare follow-up (*"why?"*, *"and the second
  best?"*, *"who else?"*, *"explain that"*) routes to None today, so a resolver placed **before**
  `route()` catches them collision-free; a line with its own subject (*"why is Haaland good?"*) stays a
  fresh question. Settled: a `Context` (last intent/squad/decision + a `rank`); three families — **why**
  (re-narrate the same facts), **next** (rank offset; the engines already rank — captain
  *B.Fernandes→Haaland→Virgil*, transfer *Ampadu→Zubimendi…*, shortlist *B.Fernandes→Gibbs-White→Rice*),
  **what-about** (owner's call: **shortlist-only**, swap position keeping prior constraints; ambiguous
  after-captain case deferred); a **next** advances the current subject so a following **why** explains
  the pick just surfaced; a **`chat`** REPL reusing `answer()`; grounding (ADR-037) runs every turn.
  ADR-047 indexed.
- **US-140 ✅** — The conversational **mechanics** in `src/ask.py`. Added a **`Context`** (intent, squad,
  question, count, `rank`, decision) + a **`FollowUp`**; **`detect_followup`** (subject-less trigger
  classification into why/next/what-about); a **rank offset** on `_decide_captain` / `_decide_transfer`
  (Nth pick, `limit=rank+1`, graceful past-end message) and `_decide_shortlist` (next page of
  `_SHORTLIST_N`); **`_swap_position`** (keeps price/value); a shared **`_dispatch`**; **`_apply_followup`**
  (why = re-narrate the *same* facts with a deeper task; next = `rank+1`, doesn't advance past the end;
  what-about = shortlist-only, else returns None to fall through); and **`converse(question, context)`**
  as the per-turn engine, with `answer()` refactored to `converse`-with-no-context (one-shot behaviour
  unchanged). A follow-up with no context nudges.
  - **Bug caught in smoke:** *"what about defenders?"* returned `None` from detection (plural not matched
    → it silently fell through to a *fresh* shortlist that **dropped the £8m cap**). Fixed by matching
    position words singular *and* plural; the cap is now preserved (*Best DEF ≤£8.0m*).
  - **Tests (405 total, +9):** `detect_followup` classifies triggers and ignores fresh questions
    (*"why is Haaland good?"* → None); `_swap_position` keeps price/value; *why* re-narrates the same
    facts + leaves the context; *next* advances the rank and stops at the end; *what-about* swaps position
    (shortlist-only, resets the page); a no-context follow-up nudges; one-shot `answer` unchanged.
  - **Smoke (live DB):** a TS conversation — *captain → why → second best (Haaland) → why (now explains
    Haaland) → third best (Virgil)*; and *best midfielders under 8m → what about defenders? (keeps ≤£8m)
    → who else? (next page)* — all grounded.
  - **Docs:** Architecture §12 changelog (Sprint 047 mechanics). _The `chat` REPL + Handbook/README/
    PROJECT_STATUS are US-141._
- **US-141 ✅** — The **`chat`** REPL. Added `chat_transcript(lines, *, store, narrator)` to `ask.py` —
  the I/O-free heart of the loop (threads a `Context`, skips blanks, stops on an exit word); `cmd_chat`
  in `cli.py` wraps it with a stdin prompt generator (`_prompt_lines`, clean EOF/Ctrl-D) + a greeting;
  a `chat` subparser (no args). The one-shot `ask` is untouched.
  - **Tests (407 total, +2):** `chat_transcript` threads context turn-to-turn, skips blanks and stops
    at "quit" (hermetic, fake `converse`); the `chat` command parses with no args → `cmd_chat`.
  - **Smoke (live DB + Ollama up):** `printf '…' | app.py chat` ran a full conversation — *captain for
    TS → why (re-explains B.Fernandes) → and the second best? (Haaland #2) → what about defenders? (a
    DEF shortlist)* — each turn built on the last and carried the ✓ trust line.
  - **Docs:** README (feature + a chat example), Handbook §21 ("a conversation that stays honest"),
    PROJECT_STATUS (commands + Tests 407 / ADRs 47 + the conversational line).

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — all three stories delivered under the gate (US-139 / ADR-047). `ask` gained
a **`chat`** mode where a second question builds on the first — *captain → why → second best → what
about defenders* — while the discipline held: **analytics decide every turn**, the LLM only narrates,
and grounding (ADR-037) runs on each. **407 tests** (was 396, +11), **47 ADRs**, ruff clean, no new
dependency.

**Delivered**
- **US-139 (gate)** — ADR-047: the `Context`, the three follow-up families (why = re-narrate; next =
  rank offset; what-about = param swap) and why each stays analytics-decided; the owner's scope call
  (what-about is **shortlist-only**).
- **US-140** — the mechanics: `Context`/`FollowUp`, `detect_followup`, a rank offset on the
  captain/transfer/shortlist decisions, `_swap_position`, a shared `_dispatch`, and `converse` (with
  `answer` refactored to `converse`-with-no-context).
- **US-141** — the `chat` REPL (`chat_transcript` + `cmd_chat` + a subparser); docs across README,
  Handbook, PROJECT_STATUS.

**What went well**
- The gate probe pinned the safety property up front — *every bare follow-up routes to None today*, so a
  resolver placed **before** `route()` is collision-free — and the build followed mechanically.
- A follow-up turned out to be an **offset, not new intelligence**: the engines already rank, so "second
  best" is rank #2 and "why" just re-narrates the same facts. Grounding never had to change.
- `answer() = converse()`-with-no-context collapsed the one-shot and conversational paths into one
  pipeline — less code, and the one-shot behaviour is provably unchanged.

**Challenges / how they were handled**
- **Plural blind spot (caught in smoke, not the gate):** *"what about defenders?"* returned `None` from
  detection because the position match was singular-only — so it silently fell through to a *fresh*
  shortlist that **dropped the £8m cap**, the exact continuity the family exists to preserve. Fixed by
  matching position words singular *and* plural. (The "probe/smoke broadly" lesson, again.)
- **Hermetic tests for a stateful REPL:** kept `chat_transcript` free of I/O (input/print) so it's
  tested with a list of lines + a fake `converse`; the prompt/stdin wiring stays a thin CLI shell.

**Carried forward:** None.
