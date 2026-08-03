# Sprint 016: Over/Under-performance (expected vs actual attacking points)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~3 working sessions (a full-stack slice: ingest → storage → analytics → view)
**Carried Over:** None (Sprint 015 closed clean — soccerdata deferred, ADR-016)

---

### 🔎 Verified at planning (per the standing lesson)

The metric was measured on live data before planning:

- **Fields present** in the FPL feed: `goals_scored`, `assists`, `minutes` (alongside the
  `expected_*` we already store).
- **The metric produces real signal:** most over-performing — Semenyo **+38**, Wilson +33,
  B.Fernandes +26 (finishing hot → regression risk); most under-performing — Brooks **−25**,
  Struijk −18 (unlucky → bounce-back).
- **A data-quality find (the "double-check" lesson):** without a minutes gate, Meslier (a GK)
  showed **actual 66, expected 0** — his `goals_scored` was 11 but `minutes` 0 and
  `total_points` 0 (a preseason field-reset glitch). **Gating on `minutes ≥ 900`** removes it
  *and* the small-sample noise — 267 players remain, all sensible.

**No new dependency** — pure FPL-native work (the "lighter model" chosen over soccerdata in
ADR-016). Preseason caveat as ever: last-season numbers, auto-updating on `refresh`.

This sprint is Tony's Sprint 015 pick — the FPL-native lens we chose *instead* of soccerdata.

---

### 🧭 Architecturally, what's new — comparing two things we (nearly) have

Every metric so far *described* players (points, value, xP, xG). This one **compares** two:
what a player's underlying numbers say they *should* have returned, vs what they *did*.

```
expected attacking points = xG · goal_pts[pos] + xA · 3      (we store xG, xA)
actual   attacking points = goals · goal_pts[pos] + assists · 3   (ingest goals, assists)
over/under-performance     = actual − expected
```

`goal_pts` are the FPL rules: **GK/DEF 6, MID 5, FWD 4**; an assist is **3**. It's another
full-stack slice — ingest three fields (`goals_scored`, `assists`, `minutes`) via the same
migration seam as Sprint 014, then a new `overperf` view on top. The **minutes gate** is
part of the metric, not an afterthought: it's what makes the comparison statistically honest.

**Why FPL-native beats soccerdata here (ADR-016 in action):** this needs *no* npXG and *no*
scraping — goals, assists and xG are all in the feed we already fetch, keyed by id. Exactly
the "lighter, decision-relevant" path we chose.

---

### 🎯 Sprint Goal

**Objective:** Add an **over/under-performance** view — expected attacking points (from
xG/xA) vs actual (from goals/assists), minutes-gated — so the user can spot finishing-hot
regression risks and unlucky bounce-back candidates.

#### Success Criteria
- [x] Approach agreed (**ADR-017**) before feature code
- [x] `Player.from_api` parses `goals_scored`, `assists`, `minutes`
- [x] `refresh` stores them; a schema **migration** adds the columns to existing DBs
- [x] An `overperf` view ranks players by (actual − expected) attacking points, minutes-gated
- [x] The view shows both ends (over and under), with a minutes/threshold note
- [x] The **minutes threshold** excludes small samples + the Meslier-type glitch
- [x] The **attacking-only** caveat is stated (ignores clean sheets / appearance / bonus)
- [x] Existing views/objectives unchanged; a `refresh` re-run stays idempotent
- [x] Tests cover parsing, the migration, the metric maths, and the view (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-050 | Agree the approach (**ADR-017**): the expected-vs-actual attacking-points formula, `goal_pts` constants, the minutes gate, ingest `goals_scored`/`assists`/`minutes`, the `overperf` view, and the honest caveats — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-051 | Ingest & store: `Player.from_api` gains `goals_scored`/`assists`/`minutes`; `storage` migration + save + `get_players`. Tests (parse + migration) | High | ✅ Complete | 1 session |
| US-052 | The metric + the `overperf` view: an analytics function (expected vs actual attacking points, minutes-gated) + a ranked view (both ends). Tests + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-017 recorded + added to the ADR index — _US-050_
- [ ] Update Architecture doc (players gain goals/assists/minutes; data model + changelog) — _US-051_
- [ ] Update `README.md` + `--help` with `overperf` — _US-052_
- [ ] Handbook — a short section on over/under-performance (what it means, the caveats) — _US-052_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for fifteen sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Expected vs actual **attacking** points | Clean-sheet / appearance / bonus / card points |
| Ingest goals_scored, assists, minutes | npXG / any soccerdata field (deferred, ADR-016) |
| A minutes-gated `overperf` view (both ends) | A squad `--objective` on over/under-performance |
| The over/under diff + the honest caveats | Predicting *next* season (this is a diagnostic lens) |

**External Dependencies:**
- [ ] FPL API (already used) + PuLP; **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Small samples / preseason glitches (Meslier) | Med | **Minutes gate** (≥ ~900) — part of the metric; a test covers a low-minutes exclusion |
| Read as "total" over/under-performance | Med | State the **attacking-only** caveat (no clean sheets/bonus) in the output + docs |
| Defenders look "under-performing" on attack | Low | Same caveat — a DEF's value is clean sheets; the view is an *attacking-returns* lens |
| Regression read as certainty | Low | Frame as a *tendency/flag*, not a guarantee — note it |
| Preseason values are last-season | Low | Same as every FPL number; auto-updates on refresh — stated |

---

### 🗝️ Gating decision (US-050 → ADR-017)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **The formula.** expected = `xG·goal_pts[pos] + xA·3`; actual = `goals·goal_pts[pos] +
   assists·3`; over/under = actual − expected. `goal_pts` = GK/DEF 6, MID 5, FWD 4.
2. **Minutes gate.** Only rank players with `minutes ≥ 900` (~10 matches) — removes noise
   *and* the Meslier glitch. The threshold is a named constant, adjustable.
3. **Scope.** Attacking returns only (goals + assists). Clean sheets / appearance / bonus are
   out — stated plainly so the number isn't over-read.
4. **View.** `overperf` ranks by the diff and shows both ends (top over- and under-performers)
   with the minutes threshold noted.
5. **Ingest.** `goals_scored`, `assists`, `minutes` via the model + the generic migration.

**Worked example to verify at the gate:** on real data, `overperf` tops out with Semenyo
(+38) / B.Fernandes (+26) as over-performers and Brooks (−25) / Struijk (−18) as under, with
Meslier **absent** (minutes gate) — confirming the metric *and* the guard before code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-050: ADR-017 — over/under-performance)
* **Completed:** Recorded **ADR-017**: `over/under = actual − expected` attacking points,
  where expected = `xG·goal_pts + xA·3` and actual = `goals·goal_pts + assists·3`
  (`goal_pts` GK/DEF 6, MID 5, FWD 4; assist 3). A **minutes gate (≥ 900)** is part of the
  metric — it filters small-sample noise *and* the Meslier preseason glitch (goals 11 /
  minutes 0). Attacking-only scope (no clean sheets/bonus), stated as a caveat; a new
  `overperf` view shows both ends. Ingest `goals_scored`/`assists`/`minutes` via the generic
  migration. **Pressure-tested on real data:** over — Semenyo +38 / B.Fernandes +26; under —
  Brooks −25 / Struijk −18; Meslier absent under the gate. Added to the ADR index;
  Architecture §12 changelog. US-050 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the verification.
* **Docs touched:** ADR-017 (new) + index, Architecture changelog, Sprint16 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Data verified; the minutes-gate finding shaped the design.)
* **Next Steps:** US-051 — ingest & store goals_scored / assists / minutes + the migration.

#### Session 2 — 2026-08-03 (US-051: ingest & store goals/assists/minutes)
* **Completed:** `Player` gained `goals_scored`/`assists`/`minutes` (`int|None`); `from_api`
  reads them with `raw.get()` — they're ints in the API, so no `_to_float`. Storage: the
  three added to `_MIGRATIONS["players"]` (INTEGER), `CREATE_PLAYERS`, `UPSERT_PLAYER`, and
  `save_players`; `get_players` unchanged (`SELECT p.*`). **4 new tests → 160 total, all
  green** (from_api parse + absent; save/get round-trip; migration). US-051 **complete**.
* **Manual smoke test:** ✅ On the real `data/fpl.db`: opening Storage migrated it (columns
  added); `refresh` populated them — Haaland 27 goals / 8 assists / 2953 mins; **267 players
  with minutes ≥ 900**, matching the planning probe.
* **Docs touched:** Architecture §6 data model (players +3 columns), Sprint16 board,
  PROJECT_STATUS. (README/Handbook come with the view in US-052.)
* **Issues / Blockers:** None.
* **Next Steps:** US-052 — the over/under-performance metric + the `overperf` view.

#### Session 3 — 2026-08-03 (US-052: the metric + the `overperf` view)
* **Completed:** New `analytics/overperf.py` — `over_under(players, min_minutes=900)`
  computes `expected = xg·goal_pts + xa·3`, `actual = goals·goal_pts + assists·3`, `diff`,
  minutes-gated, sorted desc (`GOAL_POINTS` GK/DEF 6, MID 5, FWD 4; a pure function).
  `ui/overperf.py` renders **both ends** (over / under) with the attacking-only caveat. CLI:
  `overperf` command (`--pos`, `--limit`, `--min-minutes`). **+8 tests → 168 total, all
  green** (maths, minutes-gate exclusion incl. the Meslier glitch, sort, None-coercion,
  render both-ends + caveat, parse). US-052 **complete** — Sprint 016 done.
* **Manual smoke test:** ✅ `overperf` → over: Semenyo +38 / B.Fernandes +26; under: Brooks
  −25 / Struijk −18; `--pos FWD` → Haaland +22; **Meslier absent** (0-minute glitch gated
  out); caveat printed; `--help` shows `--min-minutes`.
* **Docs touched:** README, Handbook Ch20 + Ch24 (over/under-performance section), cli
  `--help`, Sprint16 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 016 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-050 (ADR-017), US-051 (ingest goals/assists/minutes),
  US-052 (the metric + `overperf` view). The first metric that **compares** expected to
  actual — surfacing regression risks and bounce-back candidates, minutes-gated. Tests grew
  160 → **168**. **FPL-native, no new dependency** — the "lighter model" chosen over
  soccerdata (ADR-016).
* **Carried Forward:** None. Backlog: a total-points (not attacking-only) over/under; a
  clean-sheet / defensive lens; recent-form weighting (needs per-gameweek data).
* **Key Artifacts / Decisions:** ADR-017 (formula + minutes gate + attacking-only caveat);
  `players` +3 columns; `analytics/overperf.py`; the `overperf` view.

#### Retrospective
* **What Went Well?**
  - **The lighter model delivered.** Sprint 15 said no to soccerdata; Sprint 16 built the
    FPL-native alternative — no dependency, decision-relevant, and it works (Semenyo +38,
    Brooks −25). ADR-016's argument paid off immediately.
  - **A first: a metric that *compares*.** Every prior metric described a player; this one
    contrasts expected vs actual — a genuinely new kind of insight.
  - **Tony's "double-check" lesson designed the metric.** The planning probe caught the
    Meslier glitch (11 goals, 0 minutes), which turned the minutes gate from a filter into a
    core part of the metric — better *because* we checked.
  - The full-stack seam held a *fourth* time (migration upgraded the live DB); DoD held (16th).
* **What Could Be Improved?**
  - Attacking-only under-serves defenders (their value is clean sheets) — a known limit,
    flagged in the output, and a natural backlog follow-on.
  - The `overperf` view and `xg` view share a lot of shape; if a third similar view appears,
    a shared table renderer might be worth extracting.
* **Lessons Learned?**
  - A verification habit isn't just about correctness — it can *reshape a design* for the
    better (the minutes gate).
  - Comparing two stored metrics is a cheap source of new insight — no new data needed.
  - State a metric's scope in its own output; an "attacking-only" number invites over-reading
    otherwise.
* **Action Items for Next Sprint (017):**
  - [ ] Consider: a total-points over/under, a defensive/clean-sheet lens, or another
    backlog item — check data first, as always.
  - [ ] Keep the probe-at-planning + gate + 3-part DoD.

---

**Proposed follow-on (Sprint 017):** a total-points (not attacking-only) over/under, a
clean-sheet / defensive lens (using xGC), or another backlog pick — data checked first.

**Completion Date:** 2026-08-03
**Final Notes:** The lighter FPL-native model, delivered — the first metric that compares
expected to actual, with a minutes gate that Tony's "double-check" lesson designed. Sprint
outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
