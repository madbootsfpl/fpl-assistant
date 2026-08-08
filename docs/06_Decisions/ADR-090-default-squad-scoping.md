# Architectural Decision Record: `ask` defaults squad questions to the loaded squad

**Decision ID:** ADR-090
**Date:** 2026-08-10
**Status:** Accepted
**Superseded By / Replaces:** refines the squad-resolution added in **Sprint 066** ("my team" → the session
squad) and the routing in **ADR-047/080**. Routing/semantics only — no analytics change.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

A tester reported: *"`who should I captain from my-team?` returns the same answer regardless of which players I
have — it's picking the best from **all** players, not my squad."*

**Root cause (verified on real data):** `ask._fresh` resolves the natural phrase "my team" → the session
active squad via `re.search(r"\bmy (team|squad|side|xi)\b", question)`. That regex matches **"my team"** (space)
but **not "my-team"** (hyphen) — and the app's own example prompts (`pages/4_Ask.py`) use the **hyphen**
(*"who should I captain from my-team?"*). So clicking a built-in example silently answered **globally**.

Captaincy legitimately has **two** modes: *"who should I captain from my team?"* (scoped) and *"who are the
best captain picks this GW?"* (global, all players — a genuinely useful question). The problem is that a
squad-shaped question fell through to global **silently**, and the fall-through was triggered by a punctuation
mismatch no user would predict.

#### Decision Drivers
- **A loaded squad is a strong signal of intent.** In the web, an active squad is always shown ("Answering
  about your active squad") — a squad question should use *it* by default, not the global pool.
- **Keep the global question first-class.** The owner values "best captain picks this GW" — it must stay
  reachable, on purpose, not by accident.
- **Punctuation must not decide scope.** "my-team" and "my team" must behave identically.
- **No CLI regression.** The CLI `ask` has no session squad; global-by-default must hold there.

---

### ✅ Decision

**When a squad is loaded (`active_squad`) and the question names no known squad and carries no explicit-global
cue, squad-scoped intents default to the loaded squad.** In `ask._fresh`, after `route(...)`:

```python
_EXPLICIT_GLOBAL = re.compile(r"\b(all players|everyone|best overall|from all|any player)\b", re.I)
if not squad and active_squad and active_squad.get("name") and not _EXPLICIT_GLOBAL.search(question):
    squad = active_squad["name"]
```

This single rule:
- **Fixes the hyphen** — no phrase-matching is needed; any bare squad question defaults to the loaded team, so
  "my-team", "my team", "my side", "my players" all scope.
- **Implements "default to the loaded squad"** for the squad-scoped intents (**captain** · transfer · analyse ·
  start/bench · gameweek · chips).
- **Preserves the global mode** — an explicit cue (`all players` / `everyone` / `best overall` / `from all` /
  `any player`) escapes to the global answer (captaincy's only global-capable intent).
- **Leaves the CLI unchanged** — `active_squad` is `None` there, so the rule never fires; `_needs_squad` still
  prompts when no squad is loaded and none is named.

The paired display work (ADR-089 presentation, US-280) makes the two answers **read differently** — a scoped
*"Captain Pick — from squad 'X'"* vs a global *"Best Captain Picks — all players"* + a nudge — so the default is
never silent.

---

### 🔀 Alternatives Considered

- **Just fix the hyphen** (`\bmy[ -](team|squad|…)\b`), keep global-by-default. Rejected as the primary rule —
  it repairs the example prompts but still makes a bare *"who should I captain?"* answer globally with a squad
  loaded, which the owner found counter-intuitive in the web.
- **Always scope to the loaded squad (no global escape).** Rejected — the global "best picks this GW" is a
  question the owner wants to keep.
- **Prompt when ambiguous** ("your squad or all players?"). Rejected for the default path — an extra click on
  the common case; the owner chose a silent default + a clear label instead.

---

### 🧭 Consequences

**Positive**
- The natural, hyphenated example prompts now scope correctly — the reported bug is fixed at the root.
- A loaded squad "just works" across all squad questions in the web, without naming it each time.
- The global question stays reachable via an explicit, discoverable cue.
- Routing-only; the analytics/grounding/verification are untouched.

**Negative / risks (mitigations)**
- **A behaviour change for the web Ask tab** (bare squad questions now scope) → paired with the US-280 reframe +
  nudge so the scope is always visible; the CLI is unaffected.
- **A future non-squad question that a squad intent misreads** (e.g. a stray word) → the rule only fires for
  already-routed squad-scoped intents and only when no known squad name matched, so it can't hijack fixtures/
  rules/compare; a routing test pins the explicit-global escape.

---

### 📊 Validation

Reproduced the bug (hyphen → global) and the working space form before the change. Acceptance: with a squad
loaded, `…from my-team?` and a bare *"who should I captain?"* both scope to it; *"…from all players"* stays
global; the CLI (no active squad) stays global-by-default; existing **713** tests stay green (new scoping tests
added); ruff clean.
