# Sprint 109: Captaincy scopes to *your* squad (+ a clear "best overall")

**Dates:** 2026-08-10 (planned)
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~1 session (a routing fix + display clarity — no analytics change)
**Carried Over:** none

> **Direction (tester feedback):**
> *"`who should I captain from my-team?` returns the same answer regardless of which players I have — it's
> picking the best for that GW from **all** players, not from my squad. (That global question is a great one in
> its own right — but this should scope to my team.)"*

---

### 🔎 Verified at planning (root cause found on real data)

- **`ask` already scopes "my team" → your loaded squad** — via `re.search(r"\bmy (team|squad|side|xi)\b", …)`
  in `_fresh`. That regex matches **"my team"** (space) but **not "my-team"** (hyphen). Reproduced:
  `…from my team?` → *from squad 'RoboTS'* ✅; `…from my-team?` → *all players* ❌; `…from RoboTS?` → scoped ✅.
- **The app's own example prompts use the hyphen** (`pages/4_Ask.py`: *"who should I captain from my-team?"*,
  *"…for my-team?"*). So clicking the built-in example silently answers **globally** — exactly the report.
- **Captaincy has a legitimate global mode** (best picks from all players) — so the fix isn't "always scope";
  it's "**default to your loaded squad**, with an explicit escape to global" (owner steer). An explicit-global
  cue already works cleanly: `\b(all players|everyone|best overall|from all|any player)\b` matches *"from all
  players"* and not the scoped phrasings.
- **The default only affects surfaces that pass an `active_squad`** — i.e. the **web Ask tab**. The CLI `ask`
  has no session squad, so it stays global-by-default (unchanged) — no CLI regression.

---

### 🎯 Sprint Goal

**Objective:** with a squad loaded, captaincy (and the other squad questions) answer about **your** team by
default — the hyphen no longer matters — while the **global** "best captain picks this GW" stays a first-class,
clearly-labelled question you can still ask on purpose. Routing/display only; the analytics are untouched.

#### Success Criteria
- [x] **US-279 (scope to the loaded squad by default)** — (a) the phrase resolver tolerates a hyphen and a few
      synonyms: `\bmy[ -](team|squad|side|players|xi)\b`; (b) **when a squad is loaded** and the question names
      no squad **and** isn't explicitly global, squad-scoped intents (**captain** · transfer · analyse ·
      start/bench · gameweek · chips) **default to the loaded squad**; (c) an **explicit-global** cue
      (`all players` / `everyone` / `best overall` / `from all` / `any player`) forces the global answer. The
      CLI (no `active_squad`) is unchanged.
- [x] **US-280 (make global vs scoped unmistakable)** — (a) the **global** captain answer is **reframed** as
      *"Best Captain Picks — all players"* (a distinct heading, not just a *"all players"* scope line); (b) a
      **nudge** on a global answer — *"Showing all players — load your team (sidebar) or say 'from my team' to
      scope."*; (c) the Ask **example prompts personalise** to the loaded squad's real name (buttons read
      *"…from RoboTS?"*) so clicking one always scopes.
- [x] **No drift** — routing/display only; `captain_picks`/`explain_captain`/the analytics unchanged; the
      grounding still verifies (✓); **716** green (713 → +3: scoping, heading/nudge, personalised examples);
      ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (a short **ADR-090** for the default
      squad-scoping semantics — agreed at the gate).

---

### 🧭 Design sketch

**US-279 — default scoping (the gate writes ADR-090).** In `ask._fresh`, after `route(...)`, replace the
"my team" special-case with a single rule:
```python
_EXPLICIT_GLOBAL = re.compile(r"\b(all players|everyone|best overall|from all|any player)\b", re.I)
if not squad and active_squad and active_squad.get("name") and not _EXPLICIT_GLOBAL.search(question):
    squad = active_squad["name"]          # default squad questions to the loaded team (US-279)
```
This both fixes the hyphen (no phrase-matching needed — any bare squad question defaults) **and** implements
"default to the loaded squad". Captaincy keeps its global mode via the explicit cue. `_needs_squad` still
prompts when **no** squad is loaded and none is named (unchanged). CLI: `active_squad` is `None`, so the rule
never fires — global-by-default holds.

**US-280 — clarity.**
- `render_captain_pick(…, heading="Captain Pick")` gains a `heading` param; `_decide_captain` passes
  **"Best Captain Picks"** + scope *"all players"* for the global case, **"Captain Pick"** + *"from squad 'X'"*
  for the scoped case (so the two questions read differently at a glance).
- A **nudge** line appended to the global answer (only when it's genuinely global) — folded into the scope area
  or a trailing caption — pointing at how to scope.
- `pages/4_Ask.py`: when `_active`, render each example via `example.replace("my-team", _active["name"])` so the
  buttons name the real squad (and always scope when clicked). No active squad → the literal examples (which now
  also work, thanks to the default).

**Deferred:** a hard "load your team first" prompt (owner chose the softer nudge); extending explicit-global
synonyms; a web-native card.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-279 | **Scope to the loaded squad by default** — hyphen/synonym fix + default-to-active-squad with an explicit-global escape (ADR-090). | High | ✅ Done | ~½ session |
| US-280 | **Global vs scoped, unmistakable** — reframe the global "Best Captain Picks", a scope nudge, personalised example prompts. | High | ✅ Done | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `…from my-team?` (hyphen) scopes to the loaded squad; a **bare** *"who should I captain?"*
   with a squad loaded scopes to it; *"…from all players"* stays **global**; the CLI (no active squad) stays
   global-by-default; the global answer reads *"Best Captain Picks"* + the nudge; the example buttons name the
   loaded squad. Existing **713** stay green. No `.save(` / no analytics change (guardrails hold).
2. **Manual smoke** — in the web Ask tab with a squad loaded: the captain example button scopes to your squad;
   *"who should I captain from all players?"* gives the global best picks, clearly headed.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log, ADR-090.

---

### 📝 Session Progress Log

**US-279 — scope to the loaded squad by default.** ✅ Done. **ADR-090** written first (the gate).
- One rule in `ask._fresh` (after `route`): when a squad is loaded, the intent is squad-scoped
  (`_SQUAD_DEFAULT_INTENTS` = captain·transfer·analyse·start_bench·gameweek·chips), no squad was named, and the
  question carries no **explicit-global** cue (`_EXPLICIT_GLOBAL` = `all players|everyone|best overall|from
  all|any player`), scope to the loaded squad. This **replaces** the fragile `\bmy (team|…)\b` phrase-match —
  so the hyphen no longer matters (any bare squad question defaults) **and** a bare "who should I captain?"
  scopes to your team.
- **Gated to squad intents** so a global **fixtures**/compare/worth question isn't scoped (verified: "best
  fixtures next 5" with a squad loaded still returns the league FDR ranking).
- **CLI unchanged** — no `active_squad` there, so the rule never fires; global-by-default holds.
- **Verified on real data:** with a squad loaded — `…from my-team?` → *from squad 'RoboTS'* ✅ (was *all
  players*); bare `…captain?` → *from squad 'RoboTS'* ✅; `…from all players?` → *all players* ✅. No squad
  loaded → *all players* (both) ✅.
- **Tests (+1):** a hermetic scoping test (isolates `SquadStore` to a temp file so ambient saved squads can't
  interfere) covering the hyphen, the bare default, the explicit-global escape, and the CLI-parity global.
  **714** green, ruff clean.

**US-280 — make global vs scoped unmistakable.** ✅ Done.
- **Reframed heading:** `render_captain_pick` gained `heading` + `nudge` params. `_decide_captain` sends the
  **global** answer as **"Best Captain Picks" · all players** and the **scoped** one as **"Captain Pick" · from
  squad 'X'** — so the two questions read differently at a glance (no more silent "all players" line under a
  card that looks identical).
- **Nudge:** the global answer carries a guidance line — *'Showing all players — say "captain from my team"
  (with a squad loaded) to scope to your squad.'* — only on the global path (scoped shows none).
- **Personalised examples:** the Ask example buttons render with the loaded squad's real name
  (`example.replace("my-team", _active["name"])`), so *"…for RoboTS?"* replaces the literal "my-team" and a
  click always scopes. No squad loaded → the literal examples (which now answer globally, correctly).
- **Tests (+2):** a render-level heading/nudge test (global vs scoped); the ADR-090 end-to-end test extended to
  assert the global answer reads "Best Captain Picks" + the nudge while the scoped one reads "Captain Pick"; a
  web test that the example buttons name the loaded squad. **716** green, ruff clean.
- **Manual smoke:** global → "Best Captain Picks · all players" + nudge; scoped → "Captain Pick · from squad
  'RoboTS'"; the web example buttons name RoboTS with a squad loaded.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **713 → 716** (+3: a hermetic scoping test, a
heading/nudge render test, a personalised-examples web test). Ruff clean; CI-parity green. **New ADR-090**
(default squad-scoping semantics). No analytics change — routing + display only; the grounding still verifies.

**Delivered**
- **US-279 — scope to the loaded squad by default (ADR-090).** One rule in `ask._fresh` replaced the fragile
  `\bmy (team|…)\b` phrase-match: with a squad loaded, a squad-scoped question with no named squad and no
  explicit-global cue uses the loaded squad. Fixes the hyphen at the root; a bare question now scopes; the
  global mode stays reachable via an explicit cue. CLI unchanged.
- **US-280 — global vs scoped, unmistakable.** The global answer reframes to "Best Captain Picks · all players"
  + a scope nudge; the scoped one stays "Captain Pick · from squad 'X'"; the Ask example buttons name the
  loaded squad so a click always scopes.

**What went well**
- **The one-line diagnosis was the whole sprint.** Reproducing on real data pinned it to a space-vs-hyphen
  regex mismatch — and that the app's own examples used the hyphen. A precise root cause made the fix small.
- **One rule did two jobs.** Replacing the phrase-match with "default to the loaded squad unless explicitly
  global" fixed the punctuation bug *and* delivered the owner's preferred default in a single, readable check.
- **The gate excluded the danger.** Scoping only the squad-shaped intents (not fixtures/compare) meant a global
  "best fixtures" question stayed global — verified before writing the test.
- **Display made the default honest.** The reframed heading + nudge (US-280) mean the new default is never
  silent — you can always see whether the answer is your squad or all players.

**Watch-outs / follow-ups**
- **A flaky test caught early.** The first end-to-end scoping test was order-sensitive — ambient saved squads
  (`data/squads.json` = RoboTS/TS) leak into routing because `SquadStore`'s default path binds at import. Fixed
  by isolating the store to a temp file in the test. Worth remembering for any `ask`-routing test.
- **The nudge wording is web-leaning** ("with a squad loaded") — fine for the Ask tab; a CLI-only phrasing
  wasn't worth a branch.
- **Deferred:** extending explicit-global synonyms; a hard "load your team first" prompt (owner chose the soft
  nudge); the same default could later help other surfaces.

See `Sprint109_Lessons_Learnt.md` for the detailed retro.
