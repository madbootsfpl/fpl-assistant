# Sprint 004: Custom Fixture Difficulty (Overall)

**Dates:** TBC
**Status:** Planned
**Capacity:** ~3–4 working sessions
**Carried Over:** None (Sprint 003 closed clean — no slips, no roll-over)

---

### ⚠️ Scope note — descoped from Attack/Defence to Overall

Planning check (2026-08-02) found the granular team-strength fields
(`strength_attack_*`, `strength_defence_*`) are **all zero in preseason** — FPL doesn't
publish them until the season is underway. Only `strength_overall_home/away` (1–5) is
populated. So Sprint 004 builds a **custom *overall* FDR** (home/away aware) from that
signal; the **Attack/Defence split is deferred** to a later sprint once the data
populates. (See the memory note `fpl-preseason-strength-data`.)

---

### 🧭 Architecturally, what's new

Sprint 003 *consumed* FPL's coarse 1–5 difficulty as-is. Sprint 004 makes the app
**compute its own** difficulty from `strength_overall_home/away` — data we already
fetch but currently discard.

1. **The `teams` entity grows.** We store `strength_overall_home/away` — the project's
   first *schema-evolution* moment (adding columns to an existing table).
2. **Difficulty becomes ours, and home/away aware.** A team's difficulty facing an
   opponent = the **opponent's overall strength at the venue the opponent plays**:

```
If my team is HOME → opponent is away → difficulty = opponent.strength_overall_away
If my team is AWAY → opponent is home → difficulty = opponent.strength_overall_home
```

The `_view` perspective helper from Sprint 003 is reused. The boundary holds: storage
stores the strengths, analytics computes the rating.

---

### 🎯 Sprint Goal

**Objective:** Compute our **own** fixture difficulty from team overall strengths
(home/away aware), sitting alongside FPL's version for comparison — so we control and
can explain the rating, and have the foundation to extend to Attack/Defence later.

#### Success Criteria
- [x] Custom FDR approach agreed (ADR-005) before feature code
- [x] `strength_overall_home/away` stored (schema evolution handled cleanly)
- [x] Custom difficulty computed correctly, home/away aware
- [x] `fdr --type custom|fpl` works; FPL's FDR remains the default
- [ ] A team's fixtures view can show the custom difficulty per match
- [ ] Tests cover the custom calc, including the home/away perspective
- [ ] **Manual smoke test** run before the sprint is closed (see Definition of Done)

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-013 | Agree custom (overall) FDR approach (ADR-005): formula, home/away, coexistence with FPL FDR, presentation, schema evolution, attack/defence deferral | Critical | ✅ Complete | 0.5 session |
| US-014 | Store `strength_overall_home/away` (extend `Team` + teams table + `from_api`) | High | ✅ Complete | 1 session |
| US-015 | Custom FDR analytics + `fdr --type custom\|fpl` | High | ✅ Complete | 1 session |
| US-016 | Show custom difficulty per match in `fixtures --team` + Handbook update | Medium | Planned | 0.5 session |

#### Technical Tasks & Maintenance
- [x] ADR-005 recorded + added to the ADR index - _Done (US-013)_
- [x] Update Architecture doc: team strength fields + custom FDR - _Done (US-013)_
- [ ] Update `README.md` with the new `fdr --type` usage - _Planned_

---

### ✅ Definition of Done (this sprint)

Carrying the Sprint 003 lesson — *tests verify behaviour, manual testing verifies
experience* — a story isn't done until **all** of the following hold:

1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, and check
   `--help` reveals the feature.
3. **Documentation updated & checked** — as applicable to the story:
   - **Handbook** — a chapter (or badge bump) for any new tool/topic;
   - **Architecture** (`03_Architecture`) — for any change to layers or the data model;
   - **ADR** (`06_Decisions`) + ADR index — for any real decision;
   - **README** — for any new/changed command;
   - **Sprint board + PROJECT_STATUS** — story status and progress.
   (This mirrors the Charter's Documentation Rules: 01_Journal, 03_Architecture,
   04_Roadmap, 06_Decisions.)

A short note — smoke-test result **and** which docs were touched — goes in the session
log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| • Custom **overall** FDR from `strength_overall_*` | • Attack/Defence split → deferred (preseason data) |
| • Home/away weighting | • The xP engine → later |
| • Coexist with FPL's FDR (`--type`) | • Recent-form adjustment |
| • Store `strength_overall_home/away` | • New external data sources |

**External Dependencies:**
- [ ] `bootstrap-static` team `strength_overall_home/away` (populated; already fetched)
- [ ] Sprint 003 fixtures/teams/analytics (done); Python stdlib only

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Schema evolution — teams table gains columns; `CREATE TABLE IF NOT EXISTS` won't alter an existing table | High | The DB is a regenerable cache; decide in ADR-005 between "recreate on schema change" and a light migration (check `pragma table_info`, `ALTER TABLE ADD COLUMN`) |
| Custom FDR ≈ FPL's FDR (both derive from overall strength) | Med | Frame it as "build your own + compare"; keep FPL's for side-by-side; the learning is the transparent, extendable formula |
| Home/away perspective backwards | Med | Define clearly in ADR-005; a test pins the direction |
| Strength values are 1–5 already (no normalisation needed) | Low | Keep the average on the 1–5 scale; decide any tweak in ADR-005 |
| Attack/Defence data appears mid-sprint | Low | Out of scope here; revisit for the deferred split |

---

### 🗝️ Gating decision (US-013 → ADR-005)

Settle before building:
1. **Formula** — difficulty = opponent's overall strength at the opponent's venue
   (home/away aware). Confirm; decide whether to factor in the team's own strength.
2. **Coexistence** — custom FDR as `fdr --type custom`, with FPL's as `--type fpl`
   (default). Recommended over replacing.
3. **Presentation** — values stay on the 1–5 scale (average shown to 1 dp).
4. **Schema evolution** — how the teams table gains columns without losing the cache.
5. **Deferral** — record that Attack/Defence FDR waits for preseason data to populate.

---

### 📝 Session Progress Log

#### Session 1 - 2026-08-02 (US-013: ADR-005 + preseason data finding)
* **Completed:** Grounding check found attack/defence strengths all zero in preseason → **descoped** the sprint to a custom *overall* FDR (attack/defence split deferred). Recorded ADR-005 (opponent-strength-only formula, home/away aware; `fdr --type custom|fpl`; 1–5 scale; **light `ALTER TABLE` migration** for the new columns). Added to ADR index; updated Architecture §6 + changelog; saved a memory note on the data constraint. US-013 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story).
* **Docs touched:** ADR-005 (new) + index, Architecture §6/changelog, Sprint4 board, PROJECT_STATUS, memory note.
* **Issues / Blockers:** None — the descope was the finding, handled at planning time.
* **Next Steps:** US-014 — store `strength_overall_home/away` (with the light migration).

#### Session 2 - 2026-08-02 (US-014: store team strengths + migration)
* **Completed:** Extended `Team` (+ `from_api`) and the teams table with `strength_overall_home/away`; added a light migration (`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`) so existing caches gain the columns. 3 new tests incl. a migration test on a simulated old DB (49 total). US-014 **complete**.
* **Manual smoke test:** ✅ Ran `refresh` on the real `data/fpl.db` — the teams table went from `[id, name, short_name]` to include the two strength columns, populated with 1–5 values (ARS 4/5, MCI 4/5). No data lost.
* **Docs touched:** Handbook Ch10 (migration concept + example), Sprint4 board, PROJECT_STATUS. (Architecture §6 already covered the columns in US-013.)
* **Issues / Blockers:** None.
* **Next Steps:** US-015 — custom FDR analytics + `fdr --type custom|fpl`.

#### Session 3 - 2026-08-02 (US-015: custom FDR + fdr --type)
* **Completed:** `get_upcoming_fixtures()` now also returns each side's relevant strength; `_view`/`team_fdr` gained a `source` param (fpl|custom); `fdr --type custom|fpl` (default fpl). Custom = opponent's overall strength at their venue (home/away aware). 5 new tests incl. a pinned perspective test + FPL-is-default test (54 total). US-015 **complete**.
* **Manual smoke test:** ✅ `fdr --type custom` vs `--type fpl` differ sensibly — ARS rises to #1 under custom (not in FPL's top 5), Spurs drop out; both in a plausible 2.6–2.8 range.
* **Docs touched:** README (`fdr --type`), Handbook Ch21 (metric sources), Sprint4 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** US-016 — show custom difficulty per match in `fixtures --team` + Handbook.

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

**Proposed follow-on (Sprint 005):** the deferred Attack/Defence FDR split (once
strengths populate), or begin the xP engine.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
