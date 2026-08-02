# Sprint 014: Expected Goals — a New Lens (xG / xA / xGI)

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~3 working sessions (a full-stack slice: ingest → storage → analytics → view)
**Carried Over:** None (Sprint 013 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

The backlog item was "FBref xG/xA". A feasibility probe **rejected FBref** and found a far
better source:

- **FBref is blocked here** — `https://fbref.com/...` returns **403**; `soccerdata` isn't
  installed (and would add a heavy scraping dependency + FPL↔FBref name-matching).
- **FPL's own API already carries the data** — every element has 8 expected-* fields:
  `expected_goals`, `expected_assists`, `expected_goal_involvements`,
  `expected_goals_conceded` (+ per-90 variants). Keyed by FPL id — **no new dependency, no
  scraping, no name-matching.**
- **Populated & verifiable:** 564 players, **376 (66%) have xGI > 0**; values are strings
  (`'25.50'` → parse with the model's `_to_float`); **xGI = xG + xA exactly** (Saka
  7.57 + 7.16 = 14.73); xGC populated for GK/DEF (27.56 / 22.01).

Same preseason caveat as every FPL number: these are **last-season totals** that
auto-update on `refresh` once the season starts. **No new data source or dependency** —
the risk that made FBref a spike vanished.

This sprint is Tony's Sprint 013 pick ("the big backlog item — could add significant
value"), re-routed to the safe source the data check found.

---

### 🧭 Architecturally, what's new — a new *data dimension*, through the existing seams

Every sprint since 11 was display/annotation on data we already stored. This one is
different — it brings a **new dimension of data** in, so it's a **full-stack slice** that
exercises the whole flow Tony wanted to understand end-to-end:

```
FPL API → Player model (from_api) → storage (schema migration) → analytics → view/objective
```

Nothing here is novel machinery — each layer already has the seam:
- **Model:** `Player.from_api` gains four fields via the existing `_to_float`.
- **Storage:** the generic `_MIGRATIONS` + `_migrate()` adds columns with
  `ALTER TABLE ADD COLUMN` (the pattern from Sprints 3–4) — old databases upgrade in place.
- **Analytics/CLI:** a new `xg` view ranks by xGI; `--objective xgi` is **a new dict entry
  in `objective_scores`** — exactly what ADR-011 promised ("a 4th objective, not a solver
  change").

So the learning is the *ingest half* of the pipeline (model → migration → store), then two
small, familiar surfaces on top.

---

### 🎯 Sprint Goal

**Objective:** Bring FPL's expected-goals data (xG, xA, xGI, xGC) into the tool — ingest
and store it, rank players by it (an `xg` view), and add `--objective xgi` so the squad
optimiser can chase underlying attacking threat, beside points / value / xp.

#### Success Criteria
- [x] Expected-goals approach agreed (**ADR-015**) before feature code
- [x] `Player.from_api` parses xG / xA / xGI / xGC (strings → floats; missing → None, coerced 0.0 at use)
- [x] `refresh` stores them; a schema **migration** adds the columns to existing DBs
- [x] `xg` view lists players by xGI (with xG / xA / xGC), `--pos` / `--limit` supported
- [x] `squad --objective xgi` optimises on expected goal involvement
- [x] The xGI objective's attacking bias is noted honestly (GK/DEF ≈ 0)
- [x] Existing views/objitves unchanged; a `refresh` re-run is idempotent (upsert)
- [x] Tests cover parsing, the migration, the `xg` view, and the xgi objective (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-044 | Agree the expected-goals approach (**ADR-015**): FBref rejected (403/dependency) for FPL's own fields; ingest xG/xA/xGI/xGC; storage migration; the `xg` view; `--objective xgi` + its honest bias — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-045 | Ingest & store: `Player.from_api` gains xG/xA/xGI/xGC (`_to_float`); `storage` migration + save + `get_players` returns them. Tests (parse + migration) | High | ✅ Complete | 1 session |
| US-046 | Surface: an `xg` ranking view (by xGI; `--pos`/`--limit`) + `--objective xgi` (a new `objective_scores` entry + argparse choice). Tests + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-015 recorded + added to the ADR index — _US-044_
- [ ] Update Architecture doc (players gain expected-* columns; data model + changelog) — _US-045_
- [ ] Update `README.md` + `--help` with `xg` and `--objective xgi` — _US-046_
- [ ] Handbook — a short chapter/section on expected goals (what xG/xA/xGI mean) — _US-046_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for thirteen sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Ingest xG / xA / xGI / xGC from the FPL API | FBref / any external xG source (rejected — 403 + dependency) |
| An `xg` ranking view | A per-90 / minutes-adjusted view (per-90 fields exist; later) |
| `--objective xgi` for the squad | Rebuilding the **xP model** on xG (bigger; a later sprint) |
| A schema migration for old DBs | Historical/gameweek-by-gameweek xG trends |

**External Dependencies:**
- [ ] FPL API (already used) + PuLP; **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Expected fields are strings; blanks for non-players | Low | `_to_float` (already used) → 0.0 on missing/blank; a test covers it |
| Old databases lack the columns | Med | The generic `_migrate()` adds them (`ALTER TABLE ADD COLUMN`); a migration test |
| `--objective xgi` builds an attack-heavy squad (GK/DEF ≈ 0) | Med | **Intended** — it's an attacking lens; note the bias in the ADR + output |
| Preseason values are last-season | Low | Same as every FPL number; auto-updates on refresh — stated, not hidden |
| Scope creep into a full xP-on-xG rebuild | Med | Explicitly out of scope; this sprint *exposes* the data, xP v2 is later |

---

### 🗝️ Gating decision (US-044 → ADR-015)

Settle before building — **pressure-test with a worked example** (per the standing
lesson). Proposed answers (Tony to confirm/redirect):

1. **Source: FPL, not FBref.** FBref is 403-blocked and needs a scraping dependency +
   name-matching; FPL already provides xG/xA/xGI/xGC keyed by id. Record FBref as
   *rejected*, with the reason.
2. **Fields.** Ingest `expected_goals` (xG), `expected_assists` (xA),
   `expected_goal_involvements` (xGI = xG + xA), `expected_goals_conceded` (xGC). Per-90
   variants deferred.
3. **Storage.** A migration adds four REAL columns to `players` via the generic
   `_migrate()`; `save` upserts them; existing DBs upgrade in place.
4. **View.** `xg` ranks by xGI (desc), shows xG / xA / xGI / xGC, with `--pos` and
   `--limit` (mirrors `xp`).
5. **Objective.** `--objective xgi` adds one entry to `objective_scores` returning xGI
   per player — no optimiser change (ADR-011). Its attacking bias is stated.

**Worked example to verify at the gate:** on real data, `xg` should top out with the
known elite involvement (Haaland xGI ≈ 28.2, Saka ≈ 14.7); and `squad --objective xgi`
should return a visibly attack-leaning XI vs `--objective points` — confirming the new
field flows all the way through to a decision *before* the view/objective are written.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-02 (US-044: ADR-015 — expected goals)
* **Completed:** Recorded **ADR-015**: source is the **FPL API**, not FBref (rejected —
  403-blocked + `soccerdata` dependency + FPL↔FBref name-matching, for data FPL already
  gives us by id). Ingest xG/xA/xGI/xGC via the model's `_to_float`; a generic `_migrate()`
  adds four `REAL` columns; a new `xg` view ranks by xGI; `--objective xgi` is one new
  `objective_scores` entry (no solver change — ADR-011). Attacking bias stated.
  **Pressure-tested on real data before writing:** `xg` tops out at Haaland 28.2 /
  B.Fernandes 23.1 / Thiago 22.4; `--objective xgi` vs `points` swapped **9 of 11**
  players (xgi pulls Haaland in). Added to the ADR index; Architecture §12 changelog.
  US-044 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the
  verification — run live against the FPL API + `data/fpl.db`.
* **Docs touched:** ADR-015 (new) + index, Architecture changelog, Sprint14 board.
* **Issues / Blockers:** None. (FBref probed and rejected; FPL fields verified populated.)
* **Next Steps:** US-045 — ingest & store the four fields + the schema migration.

#### Session 2 — 2026-08-02 (US-045: ingest & store xG/xA/xGI/xGC)
* **Completed:** `Player` gained xg/xa/xgi/xgc (`float|None`, default None); `from_api`
  parses them from the `expected_*` fields via `_to_float` (using `raw.get()` → absent =
  None). Storage: the four added to `_MIGRATIONS["players"]`, `CREATE_PLAYERS`,
  `UPSERT_PLAYER` (insert/values/on-conflict), and `save_players`; `get_players` needs no
  change (`SELECT p.*`). **4 new tests → 149 total, all green** (from_api parse + absent;
  save/get round-trip; migration adds the columns to an old players table). US-045
  **complete**.
* **Manual smoke test:** ✅ On the real `data/fpl.db` (which predated the columns): opening
  Storage migrated it (columns added, NULL for old rows); `refresh` then populated them —
  top xGI Haaland 28.17 / B.Fernandes 23.07 / Thiago 22.43, matching the API + ADR-015.
* **Docs touched:** Architecture §6 data model (players +4 expected columns), Sprint14
  board, PROJECT_STATUS. (README/Handbook come with the view in US-046.)
* **Issues / Blockers:** None.
* **Next Steps:** US-046 — the `xg` ranking view + `--objective xgi`.

#### Session 3 — 2026-08-02 (US-046: the `xg` view + `--objective xgi`)
* **Completed:** Two surfaces on the stored data. **`--objective xgi`** is *one* new
  `objective_scores` entry (`{id: xgi or 0.0}`) + `"xgi"` in the `--objective` choices —
  **no solver change**, exactly the ADR-011 promise made three sprints ago. The **`xg`
  view** (`render_xg_table` + `cmd_xg`) ranks players by xGI (None → 0.0), showing xG / xA
  / xGI / xGC with `--pos` / `--limit`. The squad output notes xGI's attacking bias
  (ADR-015). **+7 tests → 156 total, all green.** US-046 **complete** — Sprint 014 done.
* **Manual smoke test:** ✅ `xg` tops at Haaland 28.2 / B.Fernandes 23.1; `xg --pos DEF`
  ranks attacking defenders (O'Reilly 8.8); `squad --objective xgi` leans attacking in
  *both* players and shape (a 3-forward line, via flexible formations) + prints the bias
  note; `--help` shows `xg` and `xgi`.
* **Docs touched:** README, Handbook Ch20 + new **Ch24 (Expected Goals)** + index, cli
  `--help`, Sprint14 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 014 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-044 (ADR-015), US-045 (ingest & store), US-046
  (the `xg` view + `--objective xgi`). Real per-player expected-goals data (xG/xA/xGI/xGC)
  now flows API → model → migration → store → view/objective. Tests grew 145 → **156**.
  **No new dependency** — the risk that made FBref a spike vanished at the planning check.
* **Carried Forward:** None. Backlog: xP v2 built on xG, a per-90 view, a defensive (xGC)
  metric, validate-a-legal-bench, a saved squad, plus season-dependent FPL work.
* **Key Artifacts / Decisions:** ADR-015 (FPL over FBref; four fields; migration; `xg`
  view; `--objective xgi`); the players table +4 columns; `render_xg_table`; Handbook Ch24.

#### Retrospective
* **What Went Well?**
  - **The planning probe changed everything.** FBref is 403-blocked; FPL already carries
    xG/xA by id. The scariest backlog item became the safest sprint — because we *checked
    the source before building the pipeline*.
  - **The ADR-011 promise held, literally.** `--objective xgi` was one dict entry + one
    choices value, zero solver change — the pluggable objective paying off three sprints on.
  - **Every seam already existed** — `_to_float`, the generic `_migrate()`, `SELECT p.*` —
    so a *new data dimension* landed as a full-stack slice with no new machinery. The
    migration groundwork from Sprints 3–4 upgraded the live database untouched.
  - The gate proved the field flows to a decision (9/11 swap) before code; DoD held (14th).
* **What Could Be Improved?**
  - xGC is stored but not yet a metric — a defensive lens is left on the table (backlog).
  - The bigger prize (rebuild xP on xG) was deliberately deferred; the data is now in place
    for it, but it's a real modelling sprint, not a view.
* **Lessons Learned?**
  - The cheapest pipeline is the one you don't build — the source you already have often
    hides the field you want. **Check the source first.**
  - A generic core (pluggable objective, generic migration) turns "a new metric" into a
    small, safe change — proven, not assumed.
  - Store `None`-able, coerce at the read site — old databases carry `NULL` until refreshed.
* **Action Items for Next Sprint (015):**
  - [ ] Consider: xP v2 on xG (the big modelling prize), a defensive xGC metric, a per-90
    view, validate-a-legal-bench, or a saved squad — check data/feasibility first.
  - [ ] Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

**Proposed follow-on (Sprint 015):** rebuild xP on xG (expected points from expected
goals), a defensive (xGC) metric, a per-90 involvement view, or the earlier squad
follow-ons — once the data/feasibility is checked.

**Completion Date:** 2026-08-02
**Final Notes:** The big backlog item — and it landed *safely*, because the planning check
found FPL already serves the data FBref blocks. `--objective xgi` proved the pluggable
objective. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
