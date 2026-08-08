# Architectural Decision Record: Persist the chat context across CLI runs (local-only)

**Decision ID:** ADR-091
**Date:** 2026-08-11
**Status:** Accepted
**Superseded By / Replaces:** completes the open half of **ADR-047/080** ("persist the chat context across
runs"). Adds a small local user-state file (like the `SquadStore`, ADR-024). No analytics change.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Conversational follow-ups (ADR-047: *why? · next · what-about*) build on the **last turn's `Context`**. Today
that context is **process-local**: the CLI `chat` REPL threads it in memory, the one-shot `ask` is context-free
(`cmd_ask` → `ask.answer`), and the web threads it in `st.session_state`. So *"ask X"* then a separate
*"ask why?"* can't work, and a restarted `chat` forgets the last turn.

**Verified:** a real `Context(intent, squad, question, count, rank, decision)` round-trips via
`dataclasses.asdict` → `json.dumps` (≈1.5 KB; `decision` = detail/headline/facts/subjects/task, all JSON
types). So it can be persisted to a small local file and reloaded.

The **web deploy is multi-user with no server writes** — a guardrail test scans the web edges for `.save(`.
A shared server-side context file would be wrong (cross-user bleed) *and* break that guarantee. So persistence
must be **local, single-user** — the CLI — and the web must keep its per-session `session_state`.

#### Decision Drivers
- **Continuity across runs** — a follow-up should work after the process exits, like a real assistant.
- **Local-only** — the persisted file is single-user CLI state; the multi-user web must never touch it.
- **Honest staleness** — an old "why?" shouldn't resurface a context from hours/days ago.
- **Pure core** — `ask.answer`/`converse` stay context-injectable + side-effect-free; persistence lives at the
  CLI edge, so the web + tests are unaffected.

---

### ✅ Decision

**A small `src/chat_context.py` persists one `Context` to a local, git-ignored JSON file**
(`config.CHAT_CONTEXT_PATH`, default `data/chat_context.json` — already covered by the `data/*.json` ignore):

- `save_context(ctx, *, now)` writes `{"saved_at": <iso>, "context": asdict(ctx)}`.
- `load_context(*, now, ttl=_TTL)` reads it back into a `Context`, returning `None` when the file is absent,
  unreadable, or **older than the TTL** (a light staleness guard).
- `clear_context()` removes the file.
- `now` is injected (a `datetime`) so the TTL is deterministic in tests.

**The CLI edge wires it in**, leaving the pure API untouched:
- `cmd_ask`: `ctx = load_context(); result, new = converse(question, ctx, …); save_context(new)` — a
  follow-up-shaped line uses the last turn, a fresh question overwrites it; a `--forget` clears it.
- `cmd_chat`: seed the REPL with the loaded context, persist after each turn, and a **"forget"** line resets.

**The web is deliberately excluded** — `web_streamlit` never imports `chat_context`; `st.session_state` keeps
per-session memory (no server write). A test asserts the store isn't referenced in the web edge.

---

### 🔀 Alternatives Considered

- **Persist server-side for the web too.** Rejected — multi-user cross-bleed + breaks the read-only guarantee.
- **No TTL (persist forever).** Rejected — a stale "why?" days later would re-explain an ancient, possibly
  wrong, turn; a short TTL keeps follow-ups honest.
- **Make `ask.answer` itself stateful.** Rejected — the pure API is used by the web + tests; keeping
  persistence at the CLI handler preserves purity and avoids surprising callers.
- **A richer transcript / multi-turn history.** Deferred — one last-turn `Context` is all the follow-ups need;
  a full transcript is scope for later.

---

### 🧭 Consequences

**Positive**
- *"ask …"* then *"ask why?"* / *"and the next?"* works across separate commands; a restarted `chat` resumes.
- Local-only + git-ignored; the multi-user web is untouched and stays read-only.
- The TTL keeps a stale follow-up from resurfacing an old turn; `forget` gives explicit control.
- The core stays pure — the persistence is a thin CLI wrapper.

**Negative / risks (mitigations)**
- **A stale or wrong resumed context** → the TTL bounds it; a fresh question overwrites it; `forget` clears it.
- **Serialization drift if `Context`/`decision` gains a non-JSON field** → `save_context` guards with a
  try/except (a failed save is non-fatal — continuity is a nice-to-have, never a crash); a round-trip test pins
  the current shape.
- **Accidental web coupling** → a test asserts `web_streamlit` never imports `chat_context`, and the existing
  `.save(`-scan guardrail still holds (the store's writes live only in the CLI).

---

### 📊 Validation

Verified the `Context` JSON round-trip before building. Acceptance: `save_context`/`load_context` round-trip a
`Context`; a load past the TTL returns `None`; `clear_context` clears; a two-call CLI sequence
(*"who should I captain?"* → *"why?"*) resolves the follow-up via the store; a "forget" resets; the web Ask
still uses `session_state` and never imports the store; existing **716** tests stay green (new tests added);
ruff clean.
