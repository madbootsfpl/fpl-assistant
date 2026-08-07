# Sprint 094: Pronoun-aware chat

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a pronoun-resolution helper + threading conversational context through the web Ask)
**Carried Over:** none

> **Direction (owner — from the backlog, "pronoun-aware chat"):**
> `chat` holds the last turn in memory (ADR-047). A later step: resolve **pronouns** — *"is **he** worth
> captaining?"* after a pick should mean the last player.

---

### 🔎 Verified at planning (code)

- **The conversational flow already threads context.** `converse(question, context, …) → (result,
  new_context)`; a fresh question goes through `_fresh` which **has the `context`** (the last successful
  turn, with its `decision["subjects"]`). So pronoun resolution slots in at the top of `_fresh`.
- **Single-subject intents are the clean antecedents** — `captain`/`worth` set `subjects=[one player]`;
  `compare`/`analyse`/`start_bench`/`gameweek` set many. Resolve a pronoun **only when there's exactly one
  subject** (unambiguous); otherwise leave the question alone.
- **A pronoun line isn't a "why/next/what-about" follow-up** — it carries content words, so `detect_followup`
  returns None and it routes as a fresh question; today "he" isn't a player name → the intent fails. Resolve
  the pronoun *before* routing.
- **The web Ask isn't conversational.** `pages/4_Ask.py` calls `ask.answer(...)` (one-shot, `context=None`),
  so neither the existing follow-ups **nor** pronouns work there. Threading `Context` via `session_state` +
  `converse` fixes both — and makes the tester's (web) chat genuinely conversational.
- **No pronoun assignment risk** — we *substitute the player's name* for whatever pronoun the user typed
  (he/him/she/her/they/them/his/their); we never infer or assign a pronoun.

---

### 🎯 Sprint Goal

**Objective:** in chat, a pronoun that refers to the last-mentioned player resolves to that player — *"is
Haaland worth it?"* → *"is he a differential? / compare him to Isak"* just works — in both the CLI `chat`
and the web **Ask** tab. Analytics decide as ever; the LLM only narrates.

#### Success Criteria
- [x] **US-247 (pronoun resolution, ADR-080)** — a pure `_resolve_pronoun(question, context)`: when the last
      turn had **exactly one subject** and the question contains a pronoun (he/him/his/she/her/they/them/
      their), rewrite it (whole-word, case-insensitive; possessives → `name's`) to that player, then route.
      Wired into `_fresh` (so it fires in `converse`/`chat`, not the context-less one-shot). No pronoun / no
      single antecedent → unchanged.
- [ ] **US-248 (conversational web Ask)** — `pages/4_Ask.py` threads `Context` through `session_state` and
      calls `ask.converse` (not `answer`), so **pronouns + the existing why/next/what-about follow-ups** work
      in the web chat. The first turn is unchanged (converse with no context == answer); a build answer's
      "Use this squad →" bridge still works.
- [ ] **No drift** — analytics decide, LLM narrates, every turn still verified (ADR-037); existing **636**
      stay green; ruff clean.
- [ ] Docs: ADR-080 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-247 | **Pronoun resolution** — `_resolve_pronoun` in `_fresh`: a pronoun → the last turn's sole subject, then route. ADR-080. | High | ✅ Done | ~½ session |
| US-248 | **Conversational web Ask** — thread `Context` via `session_state` + use `converse`, so pronouns + follow-ups work in the web chat. | Medium | ⬜ To do | ~½ session |

---

### 🧭 Design sketch

**US-247 (ADR-080).** In `ask.py`: `_PRONOUNS = {"he","him","his","she","her","they","them","their"}`;
`_resolve_pronoun(question, context)` → if `context and context.decision` and `len(subjects) == 1` and a
pronoun token is present, `re.sub(r"\\b(he|him|his|…)\\b", repl, question, flags=I)` where `repl` returns
`"{antecedent}'s"` for his/their else `antecedent`. Call it as the first line of `_fresh` (context-less
`answer` is unaffected). Chained pronouns work because the new context's subject updates each turn.

**US-248.** `pages/4_Ask.py`: init `st.session_state.chat_context = None`; in `_ask`, open a `Storage`, call
`result, ctx = ask.converse(question, st.session_state.chat_context, store=store, active_squad=_active)`,
close the store, save `ctx`, append to history + stash `built_squad`. (converse with `context=None` on the
first turn == today's `answer`.) `history` replay unchanged.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `_resolve_pronoun` rewrites "is he worth it?" → "is <player> worth it?" after a
   single-subject turn, leaves it alone with 2+ subjects or no pronoun, and possessives → `name's`; a
   `converse` sequence (captain → "is he worth the money?") routes to `worth` for the pick; the web Ask
   threads context so a follow-up ("why?") re-narrates and a pronoun resolves. Existing **636** stay green.
2. **Manual smoke** — CLI `chat`: "is Haaland worth it?" → "compare him to Isak" → a Haaland-vs-Isak compare;
   web Ask: same, plus "why?" after a pick.
3. **Docs updated** — ADR-080 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-247 (pronoun resolution, ADR-080).** `ask.py`: a pure `_resolve_pronoun(question, context)` rewrites a
pronoun (`he·him·his·she·her·they·them·their`, whole-word/case-insensitive; possessives → `name's`) → the
last turn's **sole** subject, wired as the first line of `_fresh` — so it fires in `converse`/`chat` and is a
**no-op for the context-less one-shot `answer`**. Resolves only when there's exactly one antecedent (2+
subjects / no pronoun / no context → unchanged). Substitutes the player's *name* (never assigns a pronoun).
Smoke: "is he worth captaining?" → "is Haaland worth captaining?"; "what are his fixtures?" → "…Haaland's…";
a real converse chain worth(Haaland) → "compare him to Isak" → the **compare** intent. +3 tests (rewrite +
possessive; ambiguous/no-pronoun/no-context no-ops; the converse chain). ruff clean, full suite **639** green.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
