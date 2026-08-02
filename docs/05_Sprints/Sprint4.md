# Sprint 004: Custom Fixture Difficulty

**Dates:** TBC
**Status:** Planned
**Capacity:** ~3–4 working sessions
**Carried Over:** None (Sprint 003 closed clean — no slips, no roll-over)

---

### 🧭 Architecturally, what's new

Sprint 003 *consumed* FPL's coarse 1–5 difficulty as-is. Sprint 004 makes the app
**compute its own** rating — the first time analytics produces a difficulty from team
strength data we already fetch but currently discard.

1. **The `teams` entity grows.** `bootstrap-static` teams carry
   `strength_attack_home/away` and `strength_defence_home/away`. We fetch these today
   and throw them away. US-014 stores them — the project's first *schema-evolution*
   moment (adding columns to an existing table).
2. **Difficulty becomes directional.** A fixture is no longer one number but two, each
   from the *opponent's* strength at the venue they play:

```
My team's Attack FDR  = opponent's DEFENCE strength (their venue)   → low = easy to score
My team's Defence FDR = opponent's ATTACK strength (their venue)    → low = easy clean sheet
```

The `_view` perspective helper from Sprint 003 is reused and extended. The boundary
holds: storage stores the strengths, analytics computes the rating.

---

### 🎯 Sprint Goal

**Objective:** Replace FPL's coarse 1–5 difficulty with our own **Attack** and
**Defence** FDR, computed from team strengths (home/away aware), so the app can say
*why* a fixture is easy — good for attackers, good for defenders, or both.

#### Success Criteria
- [ ] Custom FDR approach agreed (ADR-005) before feature code
- [ ] Team strength fields are stored (schema evolution handled cleanly)
- [ ] Attack FDR and Defence FDR are computed correctly, home/away aware
- [ ] `fdr --type attack|defence` works; FPL's FDR remains available
- [ ] A team's fixtures view can show the custom difficulty per match
- [ ] Tests cover the custom FDR calc, including the home/away perspective
- [ ] **Manual smoke test** run before the sprint is closed (see Definition of Done)

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-013 | Agree custom FDR approach (ADR-005): definitions, home/away, coexistence with FPL FDR, presentation, schema evolution | Critical | Planned | 0.5 session |
| US-014 | Store team strength fields (extend `Team` + teams table + `from_api`) | High | Planned | 1 session |
| US-015 | Custom Attack & Defence FDR analytics + `fdr --type attack\|defence\|fpl` | High | Planned | 1 session |
| US-016 | Show custom difficulty per match in `fixtures --team` + Handbook update | Medium | Planned | 0.5 session |

#### Technical Tasks & Maintenance
- [ ] ADR-005 recorded + added to the ADR index - _Planned_
- [ ] Update Architecture doc: team strength fields + custom FDR - _Planned_
- [ ] Update `README.md` with the new `fdr --type` usage - _Planned_

---

### ✅ Definition of Done (this sprint)

Carrying the Sprint 003 lesson — *tests verify behaviour, manual testing verifies
experience* — a story isn't done until:

- automated tests pass **and**
- the new capability is **manually smoke-tested** (run the real command, eyeball the
  output, check `--help` reveals it), **and**
- the Handbook is updated for anything new it introduced.

A short manual smoke-test note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| • Custom Attack + Defence FDR from team strengths | • The xP engine → Sprint 005 |
| • Home/away weighting | • Recent-form adjustment to strength → later |
| • Coexist with FPL's FDR (`--type`) | • Player-level expected points |
| • Store team strength fields | • New external data sources |

**External Dependencies:**
- [ ] `bootstrap-static` team `strength_*` fields (already fetched)
- [ ] Sprint 003 fixtures/teams/analytics (done); Python stdlib only

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Schema evolution — teams table gains columns; `CREATE TABLE IF NOT EXISTS` won't alter an existing table | High | The DB is a regenerable cache; decide in ADR-005 between "recreate on schema change" and a light migration (check `pragma table_info`, `ALTER TABLE ADD COLUMN`) |
| Attack/Defence perspective backwards (attack FDR must use opponent's *defence*) | High | Define clearly in ADR-005; a test pins the direction and home/away |
| Raw FPL strengths (~1000–1400) are unintuitive | Med | Decide presentation in ADR-005 (raw vs normalised to a ~1–5 scale) |
| Breaking the existing `fdr` command | Med | FPL FDR stays the default/`--type fpl`; run the full suite |
| Scope drift into xP or form | Med | Hard-limit to strength-based Attack/Defence FDR this sprint |

---

### 🗝️ Gating decision (US-013 → ADR-005)

Settle before building:
1. **Attack/Defence definitions** — attack FDR = opponent defence strength; defence FDR
   = opponent attack strength (home/away aware). Confirm the direction.
2. **Coexistence** — custom FDR added as `fdr --type attack|defence`, with FPL's as
   `--type fpl` (kept for comparison). Recommended over replacing outright.
3. **Presentation** — raw average strength faced vs a normalised ~1–5 scale.
4. **Schema evolution** — how the teams table gains columns without losing the cache.

---

### 📝 Session Progress Log

#### Session 1 - [Date]
* **Completed:**
* **Manual smoke test:**
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

**Proposed follow-on (Sprint 005):** begin the xP engine — now with a custom FDR to build on.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
