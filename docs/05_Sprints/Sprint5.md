# Sprint 005: Expected Points (xP v0)

**Dates:** TBC
**Status:** Planned
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
- [ ] xP v0 approach agreed (ADR-006) before feature code
- [ ] xP inputs stored (`points_per_game`, `status`, `ep_next`) via the migration pattern
- [ ] xP computed by joining a player to their team's next fixture difficulty
- [ ] `xp` ranks players by expected points; `--type custom|fpl` picks the difficulty
- [ ] Output shows our xP alongside FPL's `ep_next` for comparison
- [ ] Tests cover the xP calc (multiplier, availability, the player→fixture join)
- [ ] **Manual smoke test** run before the sprint is closed (see Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-017 | Agree xP v0 approach (ADR-006): formula, difficulty source, next-GW horizon, availability, deferrals, last-season baseline | Critical | Planned | 0.5 session |
| US-018 | Store xP inputs — extend `Player` (`points_per_game`, `status`, `ep_next`) via the `ALTER TABLE` migration | High | Planned | 1 session |
| US-019 | xP analytics — combine ppg × next-fixture difficulty (the cross-domain join) | High | Planned | 1 session |
| US-020 | `xp` command — rank by expected points (`--type custom\|fpl`), compare vs FPL `ep_next`, + Handbook | High | Planned | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-006 recorded + added to the ADR index - _Planned_
- [ ] Update Architecture doc: player xP fields + xP analytics (cross-domain) - _Planned_
- [ ] Update `README.md` with the `xp` command - _Planned_

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

#### Session 1 - [Date]
* **Completed:**
* **Manual smoke test:**
* **Docs touched:**
* **Issues / Blockers:**
* **Next Steps:**

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:**
* **Carried Forward:**
* **Key Artifacts / Decisions:**

#### Retrospective
* **What Went Well?**
* **What Could Be Improved?**
* **Lessons Learned:**
* **Action Items for Next Sprint:**

---

**Proposed follow-on (Sprint 006):** richer xP (recent `form` + expected minutes, once
populated), and/or the deferred Attack/Defence FDR split.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
