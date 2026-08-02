# Sprint 005: Expected Points (xP v0)

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~3–4 working sessions
**Carried Over:** None (Sprint 004 closed clean)

---

### 🔎 Data verified at planning (per the Sprint 004 lesson)

Checked live `bootstrap-static` before planning:

- **Usable now:** `points_per_game` (400/564), `minutes`, `status`, upcoming fixtures +
  FDR (built in Sprint 004), and FPL's own `ep_next` (527/564) as a comparison baseline.
- **Zero / deferred:** `form` (0/564 — no new-season games), attack/defence strengths
  (0/20 — still preseason).

**On last-season data:** the populated fields (`points_per_game`, `total_points`,
`minutes`) *are* last season's numbers, carried forward in `bootstrap-static`
(minutes ≈ 3330 = a full season). So xP v0's baseline **is** last-season performance,
and it **auto-updates on `refresh`** as the new season plays out — no code change
needed. `form` and the attack/defence split are added when they populate.

---

### 🧭 Architecturally, what's new — the first *cross-domain* metric

Every metric so far lived in one domain: value = players only; FDR = fixtures only.
**xP is the first to combine two** — a player's scoring rate **×** their fixture's
difficulty:

```
xP(player) = points_per_game  ×  fixture_multiplier(next opponent's difficulty)
             └── player domain ──┘   └────────── fixture domain (reuses FDR) ──────┘
```

The analytics layer learns to **join a player to their team's next fixture** — the
first time two analytics threads meet — and it **reuses the FDR** (custom or fpl) from
Sprint 004 as the difficulty input.

---

### 🎯 Sprint Goal

**Objective:** A simple, transparent **expected-points** estimate per player for the
next gameweek — baseline scoring rate adjusted by fixture difficulty — comparable
against FPL's own `ep_next`.

#### The v0 formula (honest heuristic)
```
multiplier = 1 + (3 − difficulty) × 0.10      # diff 1 → 1.20 … diff 3 → 1.00 … diff 5 → 0.80
xP_next    = points_per_game × multiplier      # 0 if the player isn't available (status ≠ 'a')
```

#### Success Criteria
- [x] xP v0 approach agreed (ADR-006) before feature code
- [x] xP inputs stored (`points_per_game`, `status`, `ep_next`) via the migration pattern
- [x] xP computed by joining a player to their team's next fixture difficulty
- [x] `xp` ranks players by expected points; `--type custom|fpl` picks the difficulty
- [x] Output shows our xP alongside FPL's `ep_next` for comparison
- [x] Tests cover the xP calc (multiplier, availability, the player→fixture join)
- [x] **Manual smoke test** run before the sprint is closed (see Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-017 | Agree xP v0 approach (ADR-006): formula, difficulty source, next-GW horizon, availability, deferrals, last-season baseline | Critical | ✅ Complete | 0.5 session |
| US-018 | Store xP inputs — extend `Player` (`points_per_game`, `status`, `ep_next`) via the `ALTER TABLE` migration | High | ✅ Complete | 1 session |
| US-019 | xP analytics — combine ppg × next-fixture difficulty (the cross-domain join) | High | ✅ Complete | 1 session |
| US-020 | `xp` command — rank by expected points (`--type custom\|fpl`), compare vs FPL `ep_next`, + Handbook | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-006 recorded + added to the ADR index - _Done (US-017)_
- [x] Update Architecture doc: player xP fields + xP analytics (cross-domain) - _Done (US-017)_
- [x] Update `README.md` with the `xp` command - _Done (US-020)_

---

### ✅ Definition of Done (this sprint)

Same 3-part DoD that held in Sprint 004 — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Simple xP: ppg × fixture multiplier | Recent form (`form` is 0 preseason) |
| Next single gameweek | Multi-week horizon; double/blank GWs |
| Availability via `status` | Expected-minutes modelling |
| Compare vs FPL `ep_next` | Captain/transfer recommendations |
| Reuse Sprint 004 FDR as difficulty | Attack/Defence FDR (data-blocked) |

**External Dependencies:**
- [ ] `bootstrap-static` `points_per_game`/`status`/`ep_next` (populated; already fetched)
- [ ] Sprint 004 fixtures/FDR (done); Python stdlib only

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| `points_per_game` is prior-season (preseason proxy) | Med | It's the honest baseline available; auto-updates on `refresh` as the season plays |
| Linking player → next fixture (DGW/BGW) | Med | v0 uses the next *single* fixture; note the simplification; DGW/BGW later |
| The multiplier is a heuristic | Med | Keep the constant explicit/config; label it v0; compare against FPL `ep_next` |
| Schema evolution again (players table) | Low | Reuse the US-014 `ALTER TABLE` migration pattern |
| `ep_next` / `points_per_game` are strings in the API | Low | Convert to float at the `from_api` boundary |

---

### 🗝️ Gating decision (US-017 → ADR-006)

Settle before building:
1. **Formula** — `ppg × (1 + (3 − difficulty) × 0.10)`; confirm the constant/shape.
2. **Difficulty source** — reuse `--type custom|fpl` (default?).
3. **Horizon** — next single gameweek for v0.
4. **Availability** — `status != 'a'` → xP 0 (or flag).
5. **Baseline** — record that ppg is last-season data that auto-updates on refresh.

---

### 📝 Session Progress Log

#### Session 1 - 2026-08-02 (US-017: ADR-006 — xP v0 design)
* **Completed:** Recorded ADR-006: xP = `points_per_game × (1 + (3 − difficulty) × 0.10)` (gentle ±20%); difficulty via `--type custom|fpl` (default fpl); next single GW; `status != 'a'` → xP 0; compare vs FPL `ep_next`; baseline is last-season ppg that auto-updates on refresh. Added to ADR index; Architecture §6 gains the player xP columns + a cross-domain note + changelog. US-017 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story).
* **Docs touched:** ADR-006 (new) + index, Architecture §6/changelog, Sprint5 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Data verified at planning, per the Sprint 004 lesson.)
* **Next Steps:** US-018 — store `points_per_game`/`status`/`ep_next` (reuse the migration).

#### Session 2 - 2026-08-02 (US-018: store xP inputs + generalise migration)
* **Completed:** Extended `Player` (+ `from_api`, with string→float for `points_per_game`/`ep_next`) and the players table with `points_per_game`, `status`, `ep_next`. **Generalised** the migration from `_migrate_teams` to a table-keyed `_migrate()` covering teams *and* players. 4 new tests incl. a players-migration test (61 total); the teams-migration test stayed green. US-018 **complete**.
* **Manual smoke test:** ✅ `refresh` on the real DB populated the columns — ppg (7.0, 6.8…), status ('a'), ep_next (2.0, 4.0…).
* **Docs touched:** Handbook Ch10 (migration now table-generic), Sprint5 board, PROJECT_STATUS. (Architecture §6 covered the columns in US-017.)
* **Issues / Blockers:** None.
* **Next Steps:** US-019 — xP analytics (ppg × next-fixture difficulty, the cross-domain join).

#### Session 3 - 2026-08-02 (US-019: xP analytics — the cross-domain join)
* **Completed:** Added `src/analytics/xp.py` — `player_xp()` joins players to their team's next fixture (via `team_id`), reusing `get_players`, `get_upcoming_fixtures` and the FDR `_view` seam (custom/fpl). xP = ppg × multiplier; 0 if unavailable/no ppg; carries `ep_next`. 7 new tests (68 total). US-019 **complete** — no command yet.
* **Manual smoke test:** ✅ Drove `player_xp` on real data — B.Fernandes (MUN, diff 2) tops our xP at 7.4. Noted: our v0 runs optimistic vs FPL's `ep_next` (last-season ppg, no minutes/form dampening) — expected for v0, and why we show `ep_next` alongside.
* **Docs touched:** Handbook Ch21 (cross-domain metric), Sprint5 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** US-020 — the `xp` command (rank by xP, `--type`, compare vs ep_next) + Handbook.

#### Session 4 - 2026-08-02 (US-020: the xp command)
* **Completed:** Added `ui/xp.py` (`render_xp_table` — xP next to FPL's ep_next + difficulty) and the `xp --type custom|fpl --pos MID --limit N` command (thin handler over `player_xp`, reusing `get_players(position=…)`). Added `xp` to the `--help` examples, Ch20 command list, and README. 5 new tests (73 total). US-020 **complete** — all four Sprint 005 stories done.
* **Manual smoke test:** ✅ `xp --type custom --pos MID --limit 6` ranks midfielders (B.Fernandes 7.4 vs FPL 4.0); `xp` appears in `--help`.
* **Docs touched:** Handbook Ch20, README, cli `--help` examples, Sprint5 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 005 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All four stories — US-017 (ADR-006), US-018 (store xP inputs + generalise the migration), US-019 (xP analytics — the cross-domain join), US-020 (the `xp` command). The **xP engine (v0)** is live: it ranks players by expected points (ppg × fixture difficulty), comparable to FPL's own `ep_next`. Tests grew 57 → 73.
* **Carried Forward:** None. Richer xP (form + expected minutes) and the Attack/Defence FDR split remain deferred — data-dependent, not slipped.
* **Key Artifacts / Decisions:** ADR-006 (xP v0); `src/analytics/xp.py` (first cross-domain metric); a generalised `_migrate()`; commits `38654c1`→`60ffe84`.

#### Retrospective
* **What Went Well?**
  - **The whole sprint was reuse.** xP *composed* five sprints of foundation — `get_players`, `get_upcoming_fixtures`, the FDR `_view` seam, the `--type` source, the migration pattern, the CLI shape. Almost no new domain logic.
  - Data was verified **at planning** (per the Sprint 004 lesson), so the premise held from the start.
  - The DoD (tests → smoke → docs) held for every story again.
  - Generalising the migration (US-018) turned a one-off into a reusable mechanism, safely (teams-migration test stayed green).
  - Showing FPL's `ep_next` beside our xP made the v0's optimism visible and honest.
* **What Could Be Improved?**
  - Our v0 xP runs high vs FPL's `ep_next` (full last-season ppg, no minutes/form dampening) — accurate as a v0, but the gap is a clear signal of what to refine next.
  - The single-GW horizon + "next fixture only" is a simplification worth revisiting (double/blank gameweeks).
* **Lessons Learned?**
  - A well-layered project compounds: by sprint 5, a big feature is mostly *composition* of existing seams.
  - Verifying data at plan time (not execution) prevents mid-sprint pivots.
  - Comparing a home-grown metric against a reference (FPL's `ep_next`) keeps you honest about where it stands.
* **Action Items for Next Sprint (006):**
  - [ ] Refine xP with `form` + expected minutes once the season populates them.
  - [ ] Consider double/blank gameweeks for the xP horizon.
  - [ ] Revisit the deferred Attack/Defence FDR split (data-dependent).
  - [ ] Keep verifying data at plan time + the 3-part DoD.

---

**Proposed follow-on (Sprint 006):** richer xP (recent `form` + expected minutes, once
populated), and/or the deferred Attack/Defence FDR split.

**Completion Date:** 2026-08-02
**Final Notes:** The app crossed from *describing* players to *predicting* them — its first expected-points estimate, built almost entirely by composing earlier sprints. Sprint outcome: **Successful** — 4/4 stories, zero roll-over, DoD held.
