# Sprint 017: Defensive Contribution (DefCon reliability)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~3 working sessions (a full-stack slice: ingest → storage → analytics → view)
**Carried Over:** None (Sprint 016 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

FPL now scores **Defensive Contribution (DefCon)**: 2 pts/match for clearing a threshold of
defensive actions. A planning probe confirmed the data supports a reliability metric:

- **Fields present** in the FPL feed: `defensive_contribution`, `defensive_contribution_per_90`,
  `clearances_blocks_interceptions`, `tackles`, `recoveries`.
- **The field is position-correct** (verified, so a threshold comparison is valid):
  - **DEF** (Senesi, Gabriel): `defensive_contribution` == **CBIT** (clearances+blocks+
    interceptions+tackles) — recoveries excluded.
  - **MID/FWD** (Anderson, Garner): `defensive_contribution` == **CBIT + recoveries**.
- **Top per-90:** Anderson 13.9 (MID), Garner 12.1 (MID), Senesi 11.5 (DEF) — all clear their
  bar; **no forwards near the top** (confirms Tony's "no FWDs in the value top-20" observation).

**No new dependency** — the FPL feed we already fetch. Preseason caveat as ever (last-season
totals, auto-updating on refresh). This sprint is **Tony's Sprint 016 idea** — a defensive
analog to `overperf`.

---

### 🧭 Architecturally, what's new — a margin vs a threshold

`overperf` compared actual to *expected*. There's no "expected DefCon", but there's a natural
reference: the **threshold** a player must clear to earn the 2 points. So the analog is a
**margin**:

```
threshold[pos]:  DEF = 10 CBIT/match;  MID = FWD = 12 (CBIT + recoveries)/match  (GK: n/a)
margin = defensive_contribution_per_90 − threshold[pos]
```

- **Positive margin** → on average clears the bar → a reliable DefCon-point earner.
- **The larger the margin, the more reliably** they clear it game to game.

Same full-stack seam as Sprints 14/16 — ingest the fields, then a `defcon` view — and the
same **minutes gate** for statistical honesty. **GK are excluded** (not DefCon-eligible;
they score via saves/clean sheets).

**Why a single ranked list, not two ends (unlike `overperf`):** a defensive "under-performer"
isn't meaningful — a forward with a low DefCon count isn't *failing* at anything, it's just
not his job. The useful output is the *ranked assets*: who reliably banks DefCon points.

---

### 🎯 Sprint Goal

**Objective:** Add a `defcon` view — rank players by how comfortably they clear their
position's Defensive Contribution threshold (`per-90 − threshold`), minutes-gated — so the
user can find reliable DefCon-point earners (the defenders and defensive mids now dominating
value).

#### Success Criteria
- [x] Approach agreed (**ADR-018**) before feature code
- [x] `Player.from_api` parses `defensive_contribution`, `defensive_contribution_per_90`,
      `clearances_blocks_interceptions`, `tackles`, `recoveries`
- [x] `refresh` stores them; a schema **migration** adds the columns to existing DBs
- [x] A `defcon` view ranks players by margin (per-90 − threshold), minutes-gated, `--pos`/`--limit`
- [x] Thresholds are correct (DEF 10, MID/FWD 12) and **GK are excluded**
- [x] The view shows per-90, the threshold, and the margin _(components stored; headline shown)_
- [x] Honest caveats stated: a per-90 average ≠ a per-match guarantee; last-season; GK n/a
- [x] Existing views/objectives unchanged; a `refresh` re-run stays idempotent
- [x] Tests cover parsing, the migration, the margin/threshold maths, GK exclusion, the view
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-053 | Agree the approach (**ADR-018**): the margin = per-90 − threshold formula, thresholds (DEF 10, MID/FWD 12, GK excluded), the minutes gate, ingest the five fields, the `defcon` view, the caveats — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-054 | Ingest & store: `Player.from_api` gains the five DefCon fields; `storage` migration + save + `get_players`. Tests (parse + migration) | High | ✅ Complete | 1 session |
| US-055 | The metric + the `defcon` view: an analytics function (margin vs threshold, minutes-gated, GK excluded) + a ranked view. Tests + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-018 recorded + added to the ADR index — _US-053_
- [ ] Update Architecture doc (players gain the DefCon columns; data model + changelog) — _US-054_
- [ ] Update `README.md` + `--help` with `defcon` — _US-055_
- [ ] Handbook — a short section on Defensive Contribution (the rules, the caveats) — _US-055_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for sixteen sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| DefCon reliability: per-90 vs the position threshold | Exact DefCon *points* earned (needs per-match data) |
| Ingest the five DefCon fields | GK defensive scoring (saves / clean sheets) |
| A minutes-gated `defcon` ranked view | A squad `--objective` on DefCon |
| The margin + components + honest caveats | Combining DefCon with attacking over/under |

**External Dependencies:**
- [ ] FPL API (already used) + PuLP; **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| A per-90 average ≠ a per-match guarantee | Med | Frame as *reliability* (the bigger the margin, the safer), not exact points — stated |
| Threshold rules wrong / change | Med | Verified the field is position-correct (DEF=CBIT, MID/FWD=CBIT+R); thresholds are named constants; confirm vs FPL's published rules |
| GK slip in with a meaningless margin | Low | GK explicitly excluded (not DefCon-eligible) — a test covers it |
| Small samples / preseason glitch | Low | The same minutes gate as `overperf` (≥ 900) |
| Preseason values are last-season | Low | Same as every FPL number; auto-updates on refresh — stated |

---

### 🗝️ Gating decision (US-053 → ADR-018)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **The metric.** `margin = defensive_contribution_per_90 − threshold[pos]`; positive = a
   reliable earner. Ranked by margin (desc).
2. **Thresholds.** DEF **10** (CBIT); MID/FWD **12** (CBIT + recoveries); **GK excluded**.
   Named constants, confirmable against FPL's rules.
3. **Minutes gate.** `minutes ≥ 900`, as in `overperf` (statistical honesty + glitch guard).
4. **View.** `defcon` ranks players by margin, shows per-90 / threshold / margin + the action
   components, with `--pos` / `--limit`. A single ranked list (defensive "under" isn't meaningful).
5. **Ingest.** The five fields via the model + the generic migration.

**Worked example to verify at the gate:** on real data, `defcon` should top out with Anderson
(MID, 13.9/90, +1.9 over the 12 bar), Garner (+0.1), Senesi (DEF, 11.5/90, +1.5 over the 10
bar) — reliable earners — and show **no forwards** near the top, confirming the metric *and*
Tony's value-table observation before any feature code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-053: ADR-018 — DefCon reliability)
* **Completed:** Recorded **ADR-018**: `margin = defensive_contribution_per_90 −
  threshold[pos]` (DEF 10, MID/FWD 12; **GK excluded**), ranked desc, minutes-gated (≥ 900,
  as `overperf`). A single ranked list (a defensive "under" isn't meaningful). **Pressure-
  tested on real data:** verified FPL's field is **position-correct** (DEF = CBIT, MID/FWD =
  CBIT + recoveries), so the threshold comparison is valid; top reliability Gomes +3.8 /
  Wieffer +2.7 / Anderson +1.9; **0 forwards in the top-20** (confirms Tony's value-table
  observation); only **23 of 248** clear their bar — a scarce, actionable signal. Caveat:
  a per-90 average ≠ a per-match guarantee (reliability, not exact points). Added to the ADR
  index; Architecture §12 changelog. US-053 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the verification.
* **Docs touched:** ADR-018 (new) + index, Architecture changelog, Sprint17 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Data verified position-correct — the key assumption.)
* **Next Steps:** US-054 — ingest & store the five DefCon fields + the migration.

#### Session 2 — 2026-08-03 (US-054: ingest & store the DefCon fields)
* **Completed:** `Player` gained `defcon`/`defcon_per90`/`cbi`/`tackles`/`recoveries` (short
  names mapped from the FPL fields in `from_api`; counts via `raw.get()`, `defcon_per90` via
  `_to_float`). Storage: the five added to `_MIGRATIONS`, `CREATE_PLAYERS`, `UPSERT_PLAYER`,
  and `save_players`; `get_players` unchanged. **4 new tests → 172 total, all green**
  (from_api parse + absent; save/get round-trip; migration). US-054 **complete**.
* **Manual smoke test:** ✅ On the real `data/fpl.db`: opening Storage migrated it (columns
  added); `refresh` populated them — Gomes 15.78/90 (cbi 87 / tk 107 / rec 193), Anderson
  13.91/90, all present.
* **Docs touched:** Architecture §6 data model (players +5 DefCon columns), Sprint17 board,
  PROJECT_STATUS. (README/Handbook come with the view in US-055.)
* **Issues / Blockers:** None.
* **Next Steps:** US-055 — the margin metric + the `defcon` view.

#### Session 3 — 2026-08-03 (US-055: the metric + the `defcon` view)
* **Completed:** New `analytics/defcon.py` — `defcon_reliability(players, min_minutes=900)`
  computes `margin = defcon_per90 − THRESHOLD[pos]` (DEF 10, MID/FWD 12; **GK excluded** via
  `THRESHOLD.get`), minutes-gated, sorted desc (a pure function). `ui/defcon.py` renders the
  ranked list with the reliability caveat. CLI: `defcon` command (`--pos`, `--limit`,
  `--min-minutes`). **+9 tests → 181 total, all green** (threshold-by-position, GK exclusion,
  minutes gate, sort, None-coercion, render + caveat, parse). US-055 **complete** — Sprint 017
  done.
* **Manual smoke test:** ✅ `defcon` → Gomes +3.8 / Wieffer +2.7 / Anderson +1.9 / Senesi
  +1.5 (matches the gate exactly); `--pos DEF` filters to defenders; GKs excluded; caveat
  printed; `--help` shows `--min-minutes`.
* **Docs touched:** README, Handbook Ch20 + new **Ch25 (Defensive Contribution)** + index,
  cli `--help`, Sprint17 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 017 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-053 (ADR-018), US-054 (ingest the five DefCon fields),
  US-055 (the metric + `defcon` view). A defensive counterpart to `overperf`: rank players by
  how reliably they clear their DefCon threshold (`per-90 − threshold`), minutes-gated, GK
  excluded. Tests grew 172 → **181**. **FPL-native, no new dependency.**
* **Carried Forward:** None. Backlog: exact DefCon *points* (per-match data); a defensive
  squad objective; a combined attacking+defensive view.
* **Key Artifacts / Decisions:** ADR-018 (margin/threshold + the position-correct
  verification); `players` +5 DefCon columns; `analytics/defcon.py`; the `defcon` view;
  Handbook Ch25.

#### Retrospective
* **What Went Well?**
  - **Straight from Tony's observation.** "No forwards in the value top-20" → a metric that
    explains and surfaces it. The reflection loop is reliably driving the roadmap.
  - **The load-bearing assumption was verified, not assumed.** Confirming FPL's field is
    position-correct (DEF=CBIT, MID/FWD=CBIT+recoveries) is what made a threshold comparison
    valid — the "double-check" habit catching the thing that mattered most.
  - **A matched pair of lenses.** `overperf` (attacking) + `defcon` (defensive) now give a
    coherent underlying-stats story, both minutes-gated and honest about their limits.
  - The migration seam absorbed a new dimension a *fifth* time; the 3-part DoD held (17th).
* **What Could Be Improved?**
  - We store the action components (CBIT/tackles/recoveries) but the view shows only the
    headline margin — a `--detail` flag could expose them if wanted.
  - Three "underlying stats" views (`xg`, `overperf`, `defcon`) now share a lot of table
    shape; a shared renderer may be worth extracting if a fourth appears.
* **Lessons Learned?**
  - Verify what a third-party field *means* before building on it — position-correctness here
    was the whole ballgame.
  - A good reference point can stand in for "expected" — the threshold gave DefCon a margin,
    just as xG gave attacking a comparison.
  - Reuse a proven pattern (`overperf`'s gate + view shape) to ship a sibling feature fast.
* **Action Items for Next Sprint (018):**
  - [ ] Consider: exact DefCon points (per-match data), a defensive/combined squad objective,
    or another backlog pick — check data first.
  - [ ] Keep probe-at-planning + gate + 3-part DoD.

---

**Proposed follow-on (Sprint 018):** exact DefCon points from per-match data, a combined
attacking+defensive lens, or another backlog pick — data checked first.

**Completion Date:** 2026-08-03
**Final Notes:** A defensive lens to match the attacking one — from Tony's value-table
observation, built on a *verified* position-correct field. Sprint outcome: **Successful** —
3/3 stories, zero roll-over, DoD held.
