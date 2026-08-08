# Sprint 120: Fixtures for planning — target players by run + a "my squad" lens

**Dates:** 2026-08-21
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~½–¾ session (two display lenses on the Fixtures page — no analytics change)
**Carried Over:** none

> **Direction (owner):** *"In addition to what's there, the Fixtures view is needed for **planning a new squad,
> wildcards etc.**"* — i.e. the ticker tells you which **teams** have good runs, but not **which players to buy**
> from them, and it can't focus on **your** squad's teams. Close that gap.

---

### 🔎 Verified at planning (on real data)

- **The Fixtures page today** (`pages/2_Fixtures.py`) is a **teams × gameweeks difficulty ticker** — all 20
  teams as rows (easiest run first), a weeks slider (1–8), each cell the opponent + (H/A), colour-graded
  green→red. It reuses `analytics.fixture_ticker` → `team_fdr` / `team_schedule`. A good *reference*, but it
  stops at the team; a planner still has to guess the players.
- **FPL difficulty is populated preseason.** `team_fdr(fixtures, next_n=5, source="fpl")` ranks all **20** teams
  on real data now — **LIV 2.6** (NEW·NFO·IPS·FUL·BOU) easiest → **FUL 3.6** hardest. So a fixtures→players
  planning view has genuine data to rank on **today** (unlike price/form/momentum, which are 0 until GW1).
- **Players join to the ticker directly.** A player's `team` field is the **short_name** (`Haaland → "MCI"`),
  the same key `team_fdr`/`fixture_ticker` use — so "this team's best players" is a pure lookup, no new mapping.
- **The active squad is reachable off the Squads pages** (`web_streamlit/squads.py::active_squad()`), so a
  "my squad" scope on the ticker can restrict to the teams the user actually owns (with a player-count).
- **No analytics touched** — both stories compose `team_fdr`/`fixture_ticker` with the existing player ranking
  and the session squad; `decision_xp` and the FDR maths are unchanged (display lenses, per ADR-057's rule).

---

### 🎯 Sprint Goal

**Objective:** make the Fixtures page a **planning aid** for a new squad / wildcard — turn "which teams have good
runs" into "**who to buy**", and let you focus the ticker on **your own** teams. Display/lenses only; the FDR +
xP analytics untouched.

#### Success Criteria
- [x] **US-301 (🎯 Target by fixtures)** — below the ticker, for the **top teams by easiest run** over the chosen
      horizon, name each team's **best available players** (ranked by the app's xP), with **price · Own% · Fit** —
      plus a **position filter** (All/GK/DEF/MID/FWD). So a wildcard/new-squad planner sees who rides the best
      runs. Unavailable players (🚑/🚫/⛔) excluded; a clear empty note.
- [x] **US-302 (a "my squad" lens on the ticker)** — a **scope toggle**: **All teams** (current) vs **My squad**
      (the ADR-049 team lens), restricting the ticker rows to the **active squad's teams** with a **player-count**
      column — so you can spot which of *your* teams have hard runs (sell / avoid on a wildcard). A note when no
      squad is loaded.
- [x] **No drift** — display lenses only; `team_fdr`/`fixture_ticker`/`decision_xp` unchanged; the read-only web
      guardrail holds; existing **766** stay green (**771** with +5); ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log, Backlog (US-302 brings the **ADR-049** team
      lens — already in `ask`/`chat` via **ADR-067** — to the web ticker; US-301's ranking metric locked at the
      gate = **`decision_xp`**; a new `analytics/targets.py`, no new ADR — a display composition of the fixtures +
      xP families).

---

### 🧭 Design sketch

**US-301 — Target by fixtures.** Take `team_fdr(upcoming, next_n=weeks)` (already easiest-first); for the top-N
teams (say 6), pull that team's **available** players (`not is_unavailable`), rank by the app's **xP**, and show a
compact block per team: the team badge + its avg difficulty + run, then a small `st.dataframe` of its top
players (Player · £m · Own% · Fit · xP). A `st.segmented_control("Position", ["All","GK","DEF","MID","FWD"])`
(the Sprint-119 pattern) filters the lists. Pure composition — `team_fdr` + the existing player ranking; no
analytics change. *(Gate decision: rank by `decision_xp` (the one xP metric) vs `total_points`/value preseason —
confirm at "start US-301" on real data.)*

**US-302 — My squad lens.** A `st.segmented_control("Show", ["All teams","My squad"], default="All teams")` above
the ticker. On **My squad**, read `active_squad()`, map its `player_ids` → their teams (via the players list),
and filter `fixture_ticker` rows to that set; add a **"Players"** count column (how many you own from each team).
No squad loaded → a caption pointing to Build/Squads. Reuses the existing grid render (the shading path is
unchanged) — just fewer rows + one column.

**Deferred:** a combined "best XI by fixtures" auto-shortlist (that's the Build optimiser's job — link, don't
duplicate); an FDR **source** toggle (fpl/custom/elo) on the page (the ticker fixes `source="fpl"` — a separate
polish); wiring fixture-ease *into* Build's objective (a modelling change, not a lens → Roadmap).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-301 | **🎯 Target by fixtures** — best available players from the easiest-run teams (+ a position filter). | High | ✅ Done | ~½ session |
| US-302 | **A "my squad" lens on the ticker** — scope to your teams + a player-count (ADR-049 lens → web ticker; cf. ADR-067). | High | ✅ Done | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the Fixtures page renders a **Target by fixtures** section listing players from the
   easiest-run teams, filterable by **position**, excluding unavailable players (AppTest); the **scope toggle**
   restricts the ticker to the active squad's teams with a **Players** count, and notes when no squad is loaded.
   Existing **766** stay green. No `.save(` / no analytics change.
2. **Manual smoke** — Fixtures → the top teams (LIV/TOT/MUN today) list their best players; pick **MID** → only
   mids; switch **My squad** → only your teams + counts; a fresh session (no squad) shows the note.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log.

---

### 📝 Session Progress Log

- **US-301 (🎯 Target by fixtures)** — **gate decision:** rank by **`decision_xp`** (the one xP metric, ADR-041),
  confirmed on real data — it differs meaningfully from raw points preseason (e.g. Isak xP 16.9 vs 41 pts, his
  baseline carries over) and keeps the whole app consistent. Added a pure `analytics/targets.py::target_by_fixtures(
  team_ranked, players, xp_by_id, *, position, top_teams=6, per_team=3)` — for the easiest-run teams it takes each
  team's **available** players (unavailable 🚑/🚫/⛔ dropped; a *doubtful* player stays with its Fit), ranks by xP,
  keeps the top `per_team`; exported from `analytics`. Wired into `pages/2_Fixtures.py` below the ticker: a
  **🎯 Target by fixtures** section with a **Position** `st.segmented_control` → a `st.dataframe` (Team · FDR ·
  Next · Player · Pos · £m · Own% · Fit · xP), over the **same weeks window** as the ticker. Pure display
  composition — no analytics change. Smoke: 18 targets (6×3); top teams' best players listed; DEF filter → only
  defenders. +4 tests (3 unit in `tests/test_targets.py` + 1 page AppTest); updated the ticker test (now 2 tables).
  ruff clean. **770** total.
- **US-302 (a "my squad" lens on the ticker)** — brings the **ADR-049** team lens (already in `ask`/`chat` via
  **ADR-067**) to the **web ticker**. Added a
  `st.segmented_control("Show", ["All teams","My squad"], default="All teams")` above the ticker in
  `pages/2_Fixtures.py`; on **My squad** it reads `active_squad()`, maps `player_ids → team` via the players
  list (`Counter`), filters the ticker rows to the owned teams, and adds a **"Players"** count column (the
  shading path is unchanged — the count column isn't a GW column so it stays blank). No squad loaded → a caption
  pointing to the Squads tab, and the ticker falls back to all teams (never an empty page). The Target section
  stays all-teams (it's about buying *new* players). Smoke: All teams → 20 rows, no count; My squad (demo
  injected) → 11 owned teams + a Players column summing to 15; no-squad → the note + all-teams fallback. +1 page
  AppTest. ruff clean. **771** total.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ both stories shipped. The Fixtures page is now a **planning aid**, not just a reference:
**🎯 Target by fixtures** turns "which teams have a good run" into "who to buy" (the best available players from
the easiest-run teams, ranked by xP, filterable by position), and a **My squad** ticker lens scopes the grid to
your own teams (with a player-count) so you can spot hard runs to sell/avoid. Display lenses only — `team_fdr`,
`fixture_ticker` and `decision_xp` are untouched.

**Delivered**
- **US-301** — a new pure `analytics/targets.py::target_by_fixtures(...)` (composes `team_fdr` easiest-first with
  the one `decision_xp` metric; unavailable dropped, doubtful kept with its Fit); a **🎯 Target by fixtures**
  section on `pages/2_Fixtures.py` with a **Position** filter. +4 tests (3 unit + 1 page).
- **US-302** — an **All teams / My squad** scope toggle on the ticker (`active_squad()` → `player_ids → team`
  Counter → filter rows + a **Players** count); a no-squad note + all-teams fall-back. Brings the ADR-049 team
  lens (already in `ask`/`chat` via **ADR-067**) to the **web ticker**. +1 page test.

**Gate decision (US-301)** — rank targets by **`decision_xp`** (the one xP metric, ADR-041), confirmed on real
data: it differs meaningfully from raw points preseason (Isak xP 16.9 vs 41 pts — his baseline carries over) and
keeps every recommendation consistent. No new ADR — a display composition of the fixtures + xP families.

**Verified at planning (real data)** — FPL difficulty is populated preseason (`team_fdr` ranks all 20 teams: LIV
2.6 → FUL 3.6), so the shortlist has genuine data now; player `team` = short_name, joining straight to the
ticker; `active_squad()` gives the squad scope. Smoke: 18 targets (6×3), DEF filter → only defenders; My squad →
11 owned teams + a Players column summing to 15; no-squad → the note + fall-back.

**Metrics** — 771 tests (766 → +5), all green · ruff clean · 93 ADRs (no new) · 2 stories, ~¾ session.

**Bonus (found at planning)** — the CLI **Fit column** + the **chance%** on the doubtful flag (an old backlog
bullet) turned out already done (`table`/`xg` carry `fit_flag`; `❓ 75%` via US-236) — marked closed in the
Backlog. A reminder that *verifying the design on real data first* catches "already shipped" before you build it.

**What went well**
- One pure assembler (`target_by_fixtures`) with a thin page edge — unit-testable, no drift, reuses existing xP.
- The two lenses are complementary (buy new vs. hold/sell) and both reuse `team_fdr`/`fixture_ticker` untouched.
- Planning-on-real-data paid off twice: locked the xP metric with evidence, and caught an already-done item.

**Even better if**
- The target shortlist is fixed at top-6 teams × 3 players — no control to widen it (deferred; keeps it scannable).
- No **price/affordability** filter on the targets yet (a natural follow-up — reuse the Sprint-119 bank idea).
- The target ranking ignores **fixture ease within the team's own list** (every player of a team shares the
  team FDR) — fine for a shortlist, but a per-player fixture-weighted xP would be a modelling change (→ Roadmap).

**Deferred / backlog** — a "best XI by fixtures" auto-shortlist (Build's job — link, don't duplicate); an FDR
**source** toggle (fpl/custom/elo) on the page; a price/position-count filter on the targets; wiring fixture-ease
*into* Build's objective (a modelling change, not a lens).

---

### 📌 For Tony

_(sprint-review reflection fields — left blank for you)_

- **Biggest learning this sprint:**
- **One thing to change next sprint:**
- **Does the Target-by-fixtures shortlist help your planning? (1–5):**
