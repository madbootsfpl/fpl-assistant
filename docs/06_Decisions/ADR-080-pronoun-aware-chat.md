# Architectural Decision Record: Pronoun-aware chat

**Decision ID:** ADR-080
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** refines **ADR-047** (conversational `chat` / follow-ups). Adds pronoun
resolution to the conversational flow; US-248 threads the same context through the web Ask. No analytics
change. Triggered by a backlog item.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`chat` (ADR-047) holds the last turn and supports **why / next / what-about** follow-ups, but a **pronoun**
referring to the last player doesn't resolve: after *"is Haaland worth it?"*, *"compare him to Isak"* fails
because "him" isn't a player name.

**Verified in code:** the conversational flow threads `context` (the last successful turn, carrying
`decision["subjects"]`), and a pronoun line — having content words — isn't a why/next/what-about follow-up,
so it routes as a **fresh question** through `_fresh` (which *has* the context). Single-subject intents
(`captain`, `worth`) set `subjects=[one player]` — a clean antecedent; multi-subject intents (`compare`,
`analyse`, …) are ambiguous. The **web Ask** calls `answer` (one-shot, `context=None`), so nothing
conversational works there — threading `Context` fixes both follow-ups and pronouns (US-248).

#### Decision Drivers
- **Natural chat** — a pronoun should mean the last-mentioned player.
- **Unambiguous only** — don't guess when there are two candidates.
- **No pronoun assignment** — substitute the player's *name* for whatever pronoun the user typed; never infer
  or assign a pronoun.
- **Analytics decide, LLM narrates** — resolution is a deterministic text rewrite before routing; the
  grounding/verification contract is untouched.

---

### ✅ Decision

**1. Resolve a pronoun to the last turn's sole subject (US-247).** A pure `_resolve_pronoun(question,
context)`: when `context` has a decision with **exactly one** `subject` (one player) and the question
contains a pronoun (`he·him·his·she·her·they·them·their`), rewrite it — whole-word, case-insensitive;
possessives (`his·their`) → `"{name}'s"`, the rest → `"{name}"` — then route normally. Called as the first
step of `_fresh`, so it fires in `converse`/`chat` (which carry context) and is a **no-op for the one-shot
`answer`** (`context=None`). No pronoun, or 2+ subjects → the question is unchanged. Chained pronouns work
because each turn's new context carries the updated subject.

**2. Thread conversational context through the web Ask (US-248).** `pages/4_Ask.py` keeps a `Context` in
`session_state` and calls `ask.converse` instead of `answer`, so **pronouns and the existing follow-ups**
work in the web chat; the first turn (no context) is identical to today.

**3. Substitute the name, never a pronoun.** We replace the user's pronoun with the resolved player's name —
we do not assign or infer a pronoun for anyone (consistent with the project's they/them default).

---

### 🔀 Alternatives Considered

- **Resolve even with multiple subjects (pick the first / most recent).** Rejected — a `compare A and B`
  antecedent is genuinely ambiguous; guessing would mislead. Resolve only the unambiguous single subject.
- **Let the LLM resolve the pronoun.** Rejected — resolution must be deterministic + auditable (analytics
  decide); a text rewrite before routing keeps grounding intact.
- **Include "it/its".** Rejected — too ambiguous (could be a squad/price/anything); limited to person
  pronouns.
- **Leave it CLI-only.** Rejected — the tester uses the web; threading `Context` (US-248) makes pronouns +
  follow-ups work there, at low cost.

---

### 🧭 Consequences

**Positive**
- Chat feels natural: a pronoun means the last player, in both the CLI and the web.
- Deterministic + safe: a rewrite-then-route, no LLM in the loop, no pronoun assignment.
- The web Ask becomes properly conversational (follow-ups too), for free.

**Negative / risks (mitigations)**
- **A pronoun with an odd phrasing** (e.g. the antecedent already named) can produce a slightly awkward
  rewrite → harmless; it still routes correctly.
- **Multi-subject turns don't resolve** → intended; the user can name the player.
- **Web Ask now runs the follow-up path** → an improvement; the first turn is unchanged (a test pins it).

---

### 📊 Validation

Verified: `_fresh` carries the context; single-subject intents give a clean antecedent; the web Ask is
one-shot today. Acceptance: `_resolve_pronoun` rewrites a pronoun to the sole subject (possessives → `name's`),
and is a no-op with 2+ subjects / no pronoun / no context; a `converse` sequence (captain → "is he worth
the money?") routes to `worth` for the pick; the web Ask threads `Context` so a follow-up re-narrates and a
pronoun resolves; the analytics + grounding are unchanged; the existing 636 tests stay green (new tests
added).
