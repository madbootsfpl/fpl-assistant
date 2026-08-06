# Sprint 066: Fix — make `ask` see the session active squad (tester bug)

**Dates:** 2026-08-06
**Status:** ✅ Complete (1/1 story; retro done)
**Capacity:** ~1 session (a focused bug fix)
**Carried Over:** None (ends the Sprint-065 hold)

> **Direction (tester feedback, 🔴):** on the web **Ask** tab, "who should I captain from RoboTS" returned
> *"(all players): B.Fernandes"* — B.Fernandes isn't in RoboTS. And "analyse my team" didn't work. **`ask`
> was reading only the server-side saved squads (`SquadStore`), not the squad loaded into the session**
> (build/upload/import, ADR-054/055). On the cloud that's just the demo seed, so a loaded team never
> resolved.

---

### 🔎 Root cause

The web Ask page called `ask.answer(prompt)` with **no squad context**, and every squad load/list inside
`ask` went straight to `SquadStore` (`.load` / `.names`). So the `ask` layer had no awareness of
`st.session_state["squad"]`. On the cloud, a loaded "RoboTS" isn't in the seed → the squad name doesn't
resolve → captain/analyse fall back to the whole market.

---

### ✅ The fix (US-192)

1. **Two resolver helpers** in `ask.py` — `_load_squad(name, active_squad)` (the **session squad wins** on a
   name match, else `SquadStore`) and `_known_squad_names(active_squad)` (saved names **+** the active
   squad's name, so routing resolves it).
2. **Thread an optional `active_squad`** (default `None`, backward-compatible) through
   `answer` / `converse` / `chat_transcript` → `_fresh` / `_apply_followup` → `_dispatch` → the squad-scoped
   deciders (`_decide_captain` · `_squad_xp` [transfer/analyse/start_bench] · `_decide_squad_fixtures`).
3. **"my team" / "my squad"** → the active squad (when one is loaded and no name matched).
4. **The web Ask page** passes `active_squad()` into `ask.answer(...)` and shows *"Answering about your
   active squad: **<name>**"*.

The CLI is unchanged (passes no `active_squad` → `SquadStore`, exactly as before). The engine / `decision_xp`
is untouched — this is purely *which squad the question is about*.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-192 | **`ask` reads the session active squad** — resolver helpers + thread `active_squad`; the web Ask page passes the loaded squad; support "my team". Tests | 🔴 Critical | ✅ Done | 1 session |

---

### ✅ Definition of Done

1. **Tests pass** — `_load_squad`/`_known_squad_names` prefer the active squad; `ask.answer(..., active_squad=)`
   scopes captain to the loaded squad (not "(all players)"); existing `ask` tests stay green (a few
   monkeypatch lambdas updated for the new signature). **517** total green.
2. **Manual smoke done** — with an active squad "ZZTestXI" (not in `SquadStore`), "captain from ZZTestXI" /
   "captain my team" scope to it (Hughes), while without it → "(all players): B.Fernandes".
3. **Docs updated** — Architecture, PROJECT_STATUS, `Feedback_Log.md` (item → done).

---

### 📝 Session Progress Log

- **US-192 ✅** — Fixed. Added `_load_squad` / `_known_squad_names`; threaded an optional `active_squad`
  through the `ask` entry points → deciders (backward-compatible default `None`); "my team" resolves to the
  loaded squad; the web Ask page passes it + shows the active-squad caption. Updated 4 test monkeypatch
  lambdas for the new signature. Tests (+3 → **517**): the two helpers; an end-to-end proof (active squad
  scopes captain; without it → "(all players)"). Smoke confirmed. `ruff` clean. CLI unchanged; xP untouched.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the reported 🔴 bug is fixed: the web Ask tab now answers about *your loaded
team* (captain, analyse, transfer, start/bench, squad-fixtures, and "my team").

**What went well** — a clean seam (two resolver helpers) kept the change small; backward-compatible
`active_squad=None` defaults meant the CLI + most tests were untouched; the fix threads *which squad*, not
new logic, so `decision_xp` stayed put. The Sprint-059 feedback loop worked end-to-end: reported → triaged
(🔴) → fixed same session.

**What to watch** — a few tests monkeypatched internal `ask` functions, so signature changes rippled into
them (updated). If a user names a squad that isn't loaded/saved, captain still silently uses all players —
a nicer "I don't know squad X" message is a small future polish (noted, not done here).

**Lessons captured:** `docs/05_Sprints/Sprint66_Lessons_Learnt.md`.
