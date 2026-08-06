# Sprint 078: Team-level squad fixtures (the ADR-049 deferral)

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/1 story)
**Capacity:** ~½ session (a new `fixtures` ask mode — reuses `team_fdr`, no new analytics)
**Carried Over:** the alternative lens deferred at Sprint 049 (ADR-049)

> **Direction (owner):** the team-level squad-fixtures lens deferred at ADR-049 — rank a squad's **teams**
> (with player-counts) by their fixture run, rather than one row per player.

---

### 🔎 Verified at planning (real data)

- Grouping the demo squad's owned players by team, then joining `team_fdr`, gives exactly the lens: the
  **Demo XI = 15 players across 12 teams**, ranked easiest-first by avg FDR with a **player-count** and next
  opponents per team (e.g. `LIV ×1 avgFDR 2.6 → NEW·NFO·IPS`, `CRY ×2 avgFDR 3.0 → EVE·MCI·FUL`).
- It's the **sibling** of the existing player-level `_decide_squad_fixtures` — same inputs, grouped by team
  instead of listed per player. **Reuses `team_fdr`** (no new analytics).
- **Routing cue:** within the squad-scoped branch, a **"teams"/"clubs"/"by team"/"by club"** cue → the
  team-level view; otherwise the player-level view (today's default). A squad's possessive "my team's
  players" won't false-trigger (no `teams`/`by team`).

---

### 🎯 Sprint Goal

**Objective:** answer *"which of \<squad>'s **teams** have the best/worst fixtures?"* — a squad's distinct
teams ranked by their FDR run, with player-counts — grounded + verified, in `ask` **and** `chat` (and so the
web Ask tab), reusing `team_fdr`.

#### Success Criteria
- [x] Approach agreed (**ADR-067**) — a team-level squad-fixtures mode; a **"teams"/"clubs"/"by team"** cue
      routes to it within the squad branch (else player-level); reuses `team_fdr`; grounded (ADR-037)
- [x] **US-214** — `_decide_squad_team_fixtures`: group the squad's owned players by team (count + names),
      join `team_fdr`, rank by avg difficulty (easiest default, hardest on the existing cue); a new
      `render_squad_team_fixtures` renderer (Team · #players · avg FDR · next opponents); routed in
      `_decide_fixtures`; works in `ask` + `chat`
- [x] **Grounded** — every figure/team in the narration traces to the facts (the ✓/⚠ trust line); the
      player-level view + the other fixtures modes are unchanged
- [x] Existing stay green — **584** (+3); ruff clean
- [ ] Docs: ADR-067 + index ✅; Architecture, PROJECT_STATUS, README (an ask example) _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-214 | **Team-level squad fixtures** — "which of \<squad>'s teams have the best fixtures?": group owned players by team + rank by `team_fdr` (with player-counts); a `teams`/`by team` cue routes to it; new renderer; grounded. ADR-067. | High | ✅ Done | ~½ session |

---

### 🧭 Design sketch (to settle in ADR-067)

**Routing (`_decide_fixtures`).** In the `if not match and squad:` branch, choose the view:
```
by_team = any(c in ql for c in ("teams", "clubs", "by team", "by club"))
return (_decide_squad_team_fixtures if by_team else _decide_squad_fixtures)(store, squad, upcoming, …)
```

**Handler (`_decide_squad_team_fixtures`).** Load the squad (session-aware), drop departed ids; group owned
players by `team` → `Counter` (player-count) + names; `fdr = {r["team"]: r for r in team_fdr(upcoming,
next_n=horizon)}`; build a row per distinct team with a valid FDR: `{team, n, players, avg_difficulty,
opponents}`; sort by `avg_difficulty` (reverse on the `hardest` cue). Facts: the ranked teams with counts +
opponents; subjects: the team codes. Degrades (no current players / no FDR) like its sibling.

**Renderer (`ui/fixtures.py` `render_squad_team_fixtures`).** A small fixed-width table: `Team · #Players ·
AvgFDR · Next` (opponents), easiest/hardest-first — mirroring `render_squad_fixtures`'s style via the shared
`_table.py` `Col`/`render_rows` where it fits.

---

### ✅ Definition of Done

1. **Tests pass** — the handler groups + counts + ranks a squad's teams (easiest/hardest); routing sends
   "…teams…" → team-level and "…players…" → player-level; a bad/empty squad degrades; grounding holds.
   Existing **581** stay green; ruff clean.
2. **Manual smoke** — `ask "which of <squad>'s teams have the best fixtures?"` → teams ranked with
   player-counts + opponents + the ✓ trust line; the player-level phrasing still gives the per-player view.
3. **Docs updated** — ADR-067 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

- **US-214 ✅ (gate + build)** — Recorded **ADR-067** (+ index) — implements the ADR-049 deferral. New
  `_decide_squad_team_fixtures` (ask.py): groups the squad's owned players by team (a player-count + names),
  joins `team_fdr`, ranks the distinct teams by avg difficulty (easiest default, hardest on the existing
  cue); grounded facts (teams + counts + opponents), subjects = team codes; degrades like its player-level
  sibling. Routing in `_decide_fixtures`: within the squad branch, a **`teams`/`clubs`/`by team`/`by club`**
  cue → team-level, else the per-player view (a possessive "my team's players" doesn't false-trigger). New
  `render_squad_team_fixtures` (ui/fixtures.py): `Team · #Players · Avg FDR · Next opponents`. Works in
  `ask` + `chat` (and the web Ask tab). Reuses `team_fdr` — no new analytics. Tests (+3 → **584**):
  team-level ranks teams with counts (LIV ×2/BOU ×1), hardest reverses, and routing (`…teams…`→team-level,
  `…players…`→player-level). **Smoke (real DB):** *"which of MyXI's teams have the best fixtures?"* →
  LIV ×1 (2.6) · MCI ×1 (2.8) · **ARS ×2** (3.2) with opponents; the player-level view is unchanged. ruff
  clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the ADR-049 deferral is closed: `ask`/`chat` now answer *"which of \<squad>'s
**teams** have the best/worst fixtures?"* — a squad's distinct teams ranked by their FDR run, with
player-counts — alongside the existing per-player view. Reuses `team_fdr`; no new analytics.

**What went well** — building it as the **sibling** of `_decide_squad_fixtures` (same inputs, grouped by
team) kept it tiny and consistent; the real-data probe at planning confirmed the grouping before a line was
written. The cue-based routing (`teams`/`by team` → team-level) slots into the existing squad branch without
disturbing the other three fixtures modes, and the grounding/verify path came for free.

**What to watch / lessons** — the routing hinges on the plural/`by team` cue so a possessive "my team's
players" stays player-level; a test pins both directions. The team-level view's `subjects` are **team
codes** (not player names), which the grounding verifier handles fine (it gates player-name mentions +
numbers) — worth remembering if the narration prompt ever changes.

**Lessons captured:** `docs/05_Sprints/Sprint78_Lessons_Learnt.md`.
