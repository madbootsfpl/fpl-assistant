# Sprint 069: Data Hardening prep — per-GW history + a dormant form blend

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1–2 sessions (a gate + a per-GW ingest + a dormant form-blend in the one xP recipe)
**Carried Over:** none

> **Direction (owner):** front-load the season-start work so **GW1 (2026-08-21)** is a switch-flip, not a
> scramble. Design + wire the two Data-Hardening foundations **now**, verified on real data, but keep them
> **dormant** until there's live per-GW data. Owner's calls: **computed rolling pp90** from per-GW history
> (not FPL's `form` field); **build both this sprint, wired + dormant**, behind a weight-0 flag.

---

### 🔎 Verified at planning (real data — the gate)

Probed the live FPL `element-summary` for Saka (id 12) on 2026-08-06:

- **`history` (this-season per-GW) is EMPTY (0 rows)** preseason — so per-GW ingestion can be **wired now
  but stays dormant**; it fills at GW1. ✔ the core premise.
- **`history_past` = 8 seasons**, already ingested (ADR-027) — untouched by this sprint.
- **`players.form` = 0.0** preseason (already stored, Sprint 060) — so *any* form blend must produce
  **byte-identical outputs today**; the existing tests are the invariance proof.
- **Storage today:** only `player_history_past`; **no per-GW table** → add `player_history` (additive, the
  same "CREATE TABLE IF NOT EXISTS + add-missing-columns" pattern as `players`).
- **Honesty note:** because `history` is empty now, the **live per-GW row shape can't be seen** preseason.
  We design the schema against the known FPL per-GW keys (a superset of `history_past` + fixture context:
  `round`, `opponent_team`, `was_home`, `fixture`, `kickoff_time`, `minutes`, `total_points`, …). Acceptance:
  ingestion fills it at GW1 with **no schema change** (idempotent upsert, additive columns).
- **Efficiency find:** `backfill_history` already calls `element-summary` **once per player** for
  `history_past`. The same payload carries `history` — so per-GW ingestion **rides the same throttled walk**
  (no second pass). Preseason it stores 0 rows; at GW1 it stores per-GW history alongside past seasons.

---

### 🎯 Sprint Goal

**Objective:** lay the two Data-Hardening foundations so GW1 is a flip:
1. **Per-GW history ingestion** — a `player_history` table + per-GW mapping, filled by the *existing*
   throttled `element-summary` walk (empty now, live at GW1).
2. **A dormant form blend in `decision_xp`** — a **computed rolling pp90** from per-GW history blends into
   the one xP rate **behind a weight** that defaults to **0** (dormant), so today's outputs are unchanged.

Both **gated by ADR-060** and proven inert now by an **invariance test**. At GW1: run the backfill and set
the weight → in-season form goes live everywhere at once (one xP recipe, ADR-041).

#### Success Criteria
- [x] Approach agreed (**ADR-060**) — per-GW `player_history` (additive schema, rides the existing walk);
      a rolling-pp90 form blend behind a **weight-0** flag; the dormant-until-GW1 contract explicit;
      the one-xP-metric invariant (ADR-041) preserved
- [x] **US-196** — a `player_history` table + a `PlayerGameweek` model + `save_history`/`get_history…`;
      `backfill_history` also persists per-GW `history` (0 rows preseason, verified); idempotent upsert
- [x] **US-197** — a pure `form_rate` (recency-weighted, minutes-aware rolling pp90 over the last N GWs) +
      an optional `form_by_code` / `form_weight` threaded through `player_xp`/`decision_xp`; **default
      weight 0 → rate unchanged**; `None` form (no per-GW history) → weight 0 for that player
- [x] **Invariance** — with `form_weight = 0` (and/or no per-GW history), `decision_xp` output is
      **identical** to today; a test pins it. A second test with *synthetic* per-GW history + a non-zero
      weight proves the blend shifts the rate the intended way
- [x] **Dormant** — no CLI/web behaviour change now; the weight lives in `config` (0), documented as "set
      at GW1"; every `decision_xp` caller (cli/ask/web) wired → GW1 is a weight-flip only
- [x] Tests green (existing stay green; + the new ingest/form/invariance tests) — **546** (+16)
- [ ] Docs: ADR-060 + index ✅; Architecture, Roadmap (Data Hardening ◑→partly), Backlog, PROJECT_STATUS
      _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-196 | **Per-GW history ingestion** — a `player_history` table + `PlayerGameweek` model; the existing throttled `element-summary` walk also stores `history` (empty now → live at GW1); idempotent. ADR-060. | High | ✅ Done | ~1 session |
| US-197 | **Dormant form blend** — a rolling-pp90 form rate blended into `decision_xp` behind a **weight-0** flag (dormant); preserves the one-xP invariant; invariance + synthetic-blend tests. ADR-060. | High | ✅ Done | ~1 session |

---

### 🧭 Design sketch (to settle in ADR-060)

**Per-GW schema (`player_history`).** Keyed `(element_code, round)` — the per-GW payload has `round` but no
season name, so this is a **current-season working set** (re-backfill overwrites; a season key would need a
magic constant). `element_code` is the stable id (so form is looked up by the same `code` the baseline
uses); `round` is the GW. Columns lean but useful: `minutes`, `total_points`, `was_home`, `opponent_team`,
`fixture`, `kickoff_time` (+ room to grow). No FK to `players` (history outlives presence, ADR-027). The
per-GW row carries `element` (season id), not `code`, so `from_api(raw, element_code)` takes the code from
an id→code map.

**Form rate (rolling pp90).** Mirror `baseline_rate`'s shape but *within* the current season:
```
form_pp90 = recency-weighted mean of (points·90/minutes) over the last N GWs with minutes > 0
confidence = min(1, window_minutes / FORM_MIN_MINUTES)     # a cameo shouldn't swing the rate
```
Returns `None` when no per-GW history exists (→ dormant for that player).

**Blend (in the one recipe).**
```
w    = FORM_WEIGHT × confidence            # FORM_WEIGHT defaults to 0 → dormant
rate = (1 − w) × base_rate + w × form_pp90 # base_rate = today's baseline/fallback/current tier
```
`FORM_WEIGHT = 0` **or** `form_pp90 is None` ⇒ `rate = base_rate` (today's number, exactly). Threaded as an
optional hook into `player_xp`, assembled in `decision_xp` — nowhere else, so the invariant holds.

**GW1 flip:** `python app.py history --backfill` (now also stores per-GW) + set `FORM_WEIGHT` > 0.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — per-GW ingest stores rows from a fake `history` payload and 0 from an empty one
   (idempotent on re-run); `form_rate` computes the expected rolling pp90 (recency + minutes-aware) and is
   `None` without history; **invariance** — `decision_xp` with weight 0 equals today; a synthetic
   history + weight > 0 shifts the rate as designed. Existing **530** stay green.
2. **Manual smoke** — run the (extended) backfill preseason → **0 per-GW rows stored, no error**; a scripted
   synthetic per-GW history + weight > 0 nudges a player's xP; with weight 0, `xp`/`captain`/`squad` output
   is unchanged.
3. **Docs updated** — ADR-060 + index, Architecture, Roadmap, Backlog, PROJECT_STATUS.

---

### 📝 Session Progress Log

- **US-196 ✅ (gate + build)** — Recorded **ADR-060** (+ index). Design refined during build: the per-GW
  `history` payload has `round` but **no season name**, so the table is keyed `(element_code, round)` — a
  **current-season working set** (re-backfill overwrites), avoiding a magic `CURRENT_SEASON` constant (ADR +
  plan updated to match). New `src/models/player_gameweek.py` `PlayerGameweek.from_api(raw, element_code)`
  (the per-GW row carries `element`, the season id, not the stable code — so it's passed in). Storage: a
  `player_history` table + `UPSERT_HISTORY` (upsert on code+round) + `save_history` / `get_history` /
  `count_history` / `get_gw_history_by_code` (grouped, for the form term) + `get_player_codes` (id→code).
  `backfill_history` now **also** maps + stores each player's `history` from the *same* `element-summary`
  call (no second pass), keyed via the id→code map; returns a 4-tuple `(processed, seasons, gameweeks,
  failures)` — CLI output surfaces the per-GW count. Tests (+5 → **535**): the model maps with a passed
  code; the storage round-trip orders by round; the backfill stores per-GW by code, is idempotent, and
  stores **0 rows when `history` is empty** (the preseason case). **Smoke (live API, `--limit 4`):** "Stored
  23 season rows + **0 per-GW rows**" — no error; the table exists + is queryable. Seed: opened `data/seed.db`
  once through `Storage` so it carries the new empty table (re-open is a verified no-op); per-GW is empty
  preseason, so no data to seed. ruff clean. _Cross-cutting docs (Architecture / PROJECT_STATUS / Roadmap)
  batched to the sprint close after US-197._

- **US-197 ✅ (build)** — A pure `src/analytics/form.py`: `form_rate(gw_history)` — a recency- +
  minutes-weighted rolling **pp90** over the last N GWs → `(form_pp90, confidence)`, `(None, 0.0)` when the
  window has no minutes (mirrors `baseline_rate`); `blend_form(base, pp90, conf, weight)` — `rate =
  (1−w)·base + w·form`, inert when `weight` 0 or form `None`. Wired into the **one recipe**: `player_xp`
  gained a precomputed `form_by_code` + `form_weight` (mirroring `baseline_by_code`); `decision_xp` assembles
  `form_by_code` from `gw_history_by_code` and passes `config.FORM_WEIGHT` (**default 0 → dormant**). New
  config `FORM_WEIGHT = 0.0` + `FORM_GAMEWEEKS = 5` (documented "flip at GW1"). **Wired every caller** —
  cli ×3, ask ×4, web ×4 all pass `store.get_gw_history_by_code()` — so GW1 is a *weight-flip only*, no
  further code. Tests (+11 → **546**): `form_rate` (recency/minutes weighting · skips 0-min GWs · `None`
  without minutes · window cap · cameo confidence); `blend_form` (mix · inert when dormant/None); the
  `player_xp` hook (blends at weight > 0 · unchanged at 0); **`decision_xp` invariance** (weight 0 ⇒
  identical) + **activation** (weight 0.5 ⇒ shifts to form). **Smoke (real DB):** dormant → **identical xP
  for every player**; flip `FORM_WEIGHT=0.5` + a synthetic hot run → **Haaland 17.6 → 24.1**, while a player
  with no per-GW form is unchanged. No schema change (US-197 is code + config) → no reseed. ruff clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — both Data-Hardening foundations built, **wired, and dormant**. Preseason output
is provably unchanged (the whole 546-test suite + a real-DB smoke show identical xP for every player), and
GW1 is now a **weight-flip only** (`history --backfill` + raise `FORM_WEIGHT`).

**What went well** — verifying the design on **real data first** paid off twice: the live probe confirmed
`history` is empty preseason (so "wire it dormant" is honest), and it surfaced the *efficiency find* that the
past-season walk's payload already carries per-GW `history` (no second fetch). Folding form into the **one**
`decision_xp` recipe (mirroring how `baseline_by_code` is precomputed and passed) kept the ADR-041 invariant
airtight — the existing suite passing *is* the invariance proof. A design snag (per-GW rows carry no season
name) was caught in build and simplified the schema (`(code, round)`, no magic season constant) rather than
forcing one.

**What to watch** — the **live per-GW row shape is unseen** until GW1 (`history` empty now); the additive
schema + idempotent upsert mean an extra field is a one-line migration, not a rebuild. **`FORM_WEIGHT` +
the window want calibration at GW1** (start small, e.g. 0.3) once real form exists — and the crowd-vs-xP
backtest (Tier 3) is the eventual check that form actually helps. The dormant blend is exercised now by the
activation test + smoke, so it won't rot unnoticed.

**GW1 checklist (2026-08-21):** `python app.py history --backfill` (now also per-GW) → set
`config.FORM_WEIGHT > 0` → verify form nudges xP (captain/transfer/analyse/squad/ask + the web, all at once)
→ calibrate the weight/window.

**Lessons captured:** `docs/05_Sprints/Sprint69_Lessons_Learnt.md`.
