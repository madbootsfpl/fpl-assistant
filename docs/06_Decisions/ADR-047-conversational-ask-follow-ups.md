# Architectural Decision Record: Conversational `ask` — a chat mode with grounded follow-ups

**Decision ID:** ADR-047
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Extends the `ask` command (ADR-034) and its grounding (ADR-037) with a
stateful conversational layer; reuses the existing decision engines (captain ADR-029, transfer ADR-030,
shortlist ADR-042) via a rank offset.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`ask` answers one question at a time. "who should I captain for TS?" answers, but the natural
follow-ups — *"why?"*, *"and the second best?"*, *"what about defenders?"* — all fall straight through to
the help message. A conversation needs the second question to **build on the first**, without loosening
the discipline that made `ask` trustworthy: the **analytics decide, the LLM only narrates**, and every
answer is grounding-verified (ADR-037).

#### A planning probe pinned the safety property and the value
- **The decision engines already rank — a follow-up is an offset, not new logic.** `_decide_captain`
  computes `captain_picks(limit=3)` but surfaces only pick #1. On **TS**: captain top-3 = *B.Fernandes
  5.9 · Haaland 5.7 · Virgil 4.1*; transfer top-3 = *Ampadu→Zubimendi +9.3 · Kelleher→Roefs +5.4 ·
  Senesi→Mukiele +4.1*; best-MID top-3 = *B.Fernandes 7.4 · Gibbs-White 5.6 · Rice 5.6*. So *"and the
  second best?"* is a genuinely grounded answer at rank #2.
- **Every bare follow-up routes to None today.** *"why?"*, *"and the second best?"*, *"who else?"*,
  *"the next one"*, *"explain that"* all fall through — so a resolver placed **before** `route()` catches
  them with **zero collision** against the real intents.
- **"why?" is pure re-narration — the safest follow-up.** The last decision dict already carries `facts`
  + `subjects`; *"why?"* re-narrates *those same facts*, verified against the identical set.
- **"what about \<position\>?" needs continuity.** `"best midfielders under £8m"` then *"what about
  defenders?"* should keep *under £8m* — the stateless shortlist loses the constraint today.

#### Decision Drivers
- **Build on the last turn** — a real conversation, not repeated one-shots.
- **Grounding is non-negotiable** — every follow-up stays analytics-decided + verified.
- **Deterministic routing** — the LLM never decides the intent (ADR-034); a follow-up is detected by
  explicit triggers, not a model.
- **Simple & additive** — the one-shot `ask` is untouched; `chat` is a thin stateful layer on top.

---

### ✅ Decision

**1. The context.** A `Context` holds the last *successful* turn: `intent`, `squad`, the `decision`
(its `facts` + `subjects`), and a `rank` (which pick of the ranked list is "current", default 0). It is
replaced by every fresh answer and read by a follow-up.

**2. Detection — a resolver before `route()`, firing only on short, subject-less triggers.** If the line
carries its own routable content (*"why is Haaland good?"* has a subject), it is a **fresh** question, not
a follow-up. Only bare triggers match. Anything unmatched routes as today and *updates* the context.

**3. The three follow-up families — each analytics-decided:**
- **why / explain / how come** → re-narrate the last decision's *existing* facts with a more detailed
  task. No new analytics; verified against the same facts.
- **next / second best / who else / another / the next one** → re-run the last intent at a **rank
  offset** (`rank += 1`). Captain, transfer and shortlist already rank; the offset is exposed on those
  decisions. Past the end → a graceful "that's all I have".
- **what about \<position\> / and \<position\>** → **shortlist-only** (the owner's scope call): re-run the
  shortlist with the position swapped, **keeping the prior constraints** (price band, value/xP sort).
  After a non-shortlist turn this phrase is treated as a fresh question (no ambiguous "defenders after a
  captain pick"). 

**4. The context-update rule.** A **next** advances `rank` and updates the current subject, so a
following **why** explains the pick *just surfaced* (Haaland), not the original (B.Fernandes). A fresh
question replaces the whole context.

**5. The surface — a `chat` REPL.** `python app.py chat` runs an interactive loop; each line reuses the
proven `answer()` pipeline, prints the answer (with the ✓/⚠ trust line), then updates the context.
`quit`/EOF exits; a follow-up with no context yet gives a gentle nudge. The one-shot `ask` command is
unchanged.

**6. Grounding.** Unchanged (ADR-037) — the verifier runs on every turn, follow-ups included.

---

### 🔀 Alternatives Considered

- **Persist the last context to a file** so one-shot `ask "why?"` chains across shell invocations.
  Rejected — hidden state between separate commands is surprising and fragile; a REPL makes the
  conversation's scope explicit and needs no persistence.
- **An LLM intent/​follow-up classifier.** Rejected — routing stays deterministic (ADR-034); the model
  narrates, it never decides. Bare-trigger detection is enough and can't hallucinate an intent.
- **"what about \<X\>" after any intent.** Considered; deferred by the owner — the after-captain case
  ("defenders" = a DEF shortlist? re-captain among DEFs?) is ambiguous. Shortlist-only is the
  unambiguous, testable core; the rest can come later.
- **Pronoun resolution ("is *he* worth it?").** Deferred — needs entity tracking beyond the current
  subject; not required for the three families.

---

### 🧭 Consequences

**Positive**
- `ask` becomes a conversation: *captain → why → second best → what about defenders* each build on the
  last, every answer grounded and verified.
- No new analytics and no new dependency — follow-ups reuse the ranking the engines already do.
- The one-shot `ask` is untouched; `chat` degrades to decision + facts when Ollama is absent.

**Negative / risks (mitigations)**
- **A follow-up could free-narrate (ungrounded)** → every family is analytics-decided; "why"
  re-narrates the *same* facts; the ADR-037 verifier runs each turn.
- **Detection misfires** → triggers fire only when the line has no other routable content (proven on
  real phrasings); unmatched → a normal fresh question.
- **Stateful complexity** → in-memory, last-turn-only, reusing `answer()`.

---

### 📊 Validation

Prototyped on the live DB: the three ranking intents each return a meaningful top-3 (so *"next"* is
grounded); every bare follow-up routes to None today (so a pre-`route()` resolver is collision-free);
*"why is Haaland good?"* keeps its subject (so it stays a fresh question). Acceptance for the sprint: in
`chat`, "captain for TS?" → "why?" → "and the second best?" → "what about defenders?" each build on the
last, and every answer carries the ✓/⚠ trust line.
