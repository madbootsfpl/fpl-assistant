# Sprint 026: Historical Trend Data & Enriched xP (Phase 2 begins)

**Dates:** 2026-08-03
**Status:** ✅ Complete (4/4 stories, retro done)
**Capacity:** ~3–4 working sessions (the first Phase 2 sprint — a real data + modelling sprint)
**Carried Over:** None (Sprint 025 closed Phase 1)

---

### 🔎 Verified at planning (the standing lesson — and it changed the design)

Probed the live FPL API *before* designing. Three findings reshaped the sprint:

1. **We are preseason** — **0 of 38 gameweeks finished**, next is GW1. So *this* season has **no
   per-GW history yet** (`element-summary` → `history` is empty for everyone). The `total_points`
   in the bootstrap (Haaland 239) is **last season's** total carried over.
2. **The available history is per-*season*, not per-*gameweek*.** `element-summary/{id}/` →
   **`history_past`** gives a rich **per-season summary** per player — for Haaland, 4 seasons
   (2022/23→2025/26): `total_points, minutes, goals, assists, clean_sheets, goals_conceded,
   expected_goals/assists/goal_involvements/goals_conceded, defensive_contribution, CBI, tackles,
   recoveries, starts, bonus, bps, ICT, start_cost, end_cost` — keyed by **`element_code`** (the
   stable cross-season id, unlike per-season `id`).
3. **It's a per-player endpoint at scale.** **567** players × 1 call = a ~567-call backfill
   (~3–4 min throttled). Players have **4–6** past seasons; some young players have **0** (handle
   gracefully). Past-season data is **static within a season** → fetch once, not every refresh.

**What this means:** "historical trend data" available *now* = **multi-season summaries**, not
within-season per-GW trends. That's actually the **ideal xP input preseason** — with zero
current-season form, a multi-season baseline is the best signal we have. FPL-native, **no new
dependency** (fits [[prefers-lightweight-over-data-completeness]] / ADR-016's spirit).

ClubElo re-checked at planning — still down (timeout ~8s).

---

### 🧭 What's new architecturally — a second FPL endpoint + a historical store

Until now the whole app runs off **one** bootstrap call. This sprint adds a **second FPL
endpoint** (`element-summary`, per-player) and the project's **first historical data** — a new
`player_history_past` table, populated by a **dedicated, throttled backfill command** (kept out of
the fast `refresh`, because 567 calls ≠ one). Then xP stops relying only on the current snapshot
and gains a **multi-season baseline** — the enrichment that flows into Phase 3 decision support.

This is a *data + modelling* sprint (unlike Sprint 025's docs, or Sprint 024's refactor): API →
storage (new table + migration) → analytics (xP enrichment) → CLI, with the rate-limit discipline
the original roadmap flagged.

---

### 🎯 Sprint Goal

**Objective:** Ingest FPL **past-season history** (`history_past`, all 567 players, via a throttled
backfill) into a new store, and **enrich xP** with a multi-season baseline so it's robust preseason
— laying the historical foundation Phase 3 will build on. Also stand up **CI/CD** (tests on push).

#### Success Criteria
- [ ] Historical design agreed (**ADR-027**) before code — source, scope, rate-limit strategy, schema
- [ ] A new `player_history_past` table (keyed by `element_code` + `season_name`) + generic migration
- [ ] A **throttled backfill command** fetching `element-summary` for all players, storing past
      seasons; idempotent (safe re-run), degrades on a per-player failure, **not** part of `refresh`
- [ ] xP enrichment agreed (**ADR-028**) + wired in — a multi-season baseline rate, pressure-tested
      on real data (e.g. Haaland 272/217/181/239)
- [ ] Players with 0 past seasons handled gracefully (no crash; fall back to current signal)
- [ ] **CI/CD** — GitHub Actions runs lint + the test suite on push/PR *(the "also in this phase"
      item — may slip to Sprint 027 if the historical work runs long)*
- [ ] Tests for ingestion + storage + the enrichment; **manual smoke test** on live data
- [ ] Docs: ADR-027/028 + index, Architecture changelog, Handbook, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-076 | **Gate.** Historical data design (**ADR-027**): source = FPL `element-summary.history_past`; scope = past-season summaries now (per-GW `history` deferred — empty preseason); rate-limit strategy (a throttled, idempotent `history --backfill` command, *not* `refresh`); schema (`player_history_past`, keyed by `element_code`). Pressure-test on real seasons | Critical | ✅ Done | 1 session |
| US-077 | **Ingest past-season history** — a client method for `element-summary/{id}/`; the `player_history_past` table + migration; the throttled backfill command (reuse `with_retry`, inter-call sleep, per-player degrade). Tests + smoke (backfill a handful, verify stored) | High | ✅ Done | 1 session |
| US-078 | **Enrich xP with history** (**ADR-028**) — derive a multi-season, minutes-weighted baseline rate (recency-weighted); blend with current signal (or use it outright preseason). Wire into `xp`; keep the objective generic. Tests + smoke on real data | High | ✅ Done | 1 session |
| US-079 | **CI/CD** — GitHub Actions (lint + `pytest` on push/PR) + pre-commit hooks. Independent of the above; ordered last — **may carry to Sprint 027** | Medium | ✅ Done | 0.5 session |

#### Technical Tasks & Maintenance
- [x] ADR-027 recorded + added to the ADR index — _US-076_
- [x] ADR-028 recorded + added to the ADR index — _US-078_
- [x] Update `docs/10_Data_Sources` (new endpoint) + Architecture changelog — _US-077_
- [x] Update Handbook (Ch 21 — enriching a metric's input; the smoke-caught gate) — _US-078_
- [x] Note the per-GW `history` follow-on in the Backlog (ingest once GWs play) — _US-077_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — ingestion, storage/migration, and the xP enrichment covered; the
   existing 227 stay green.
2. **Manual smoke test done** — backfill real players; confirm past seasons stored; run `xp` and
   sanity-check the enriched numbers against the raw seasons.
3. **Documentation updated & checked** — ADR-027/028 + index, Architecture, Handbook, Data Sources,
   sprint board + PROJECT_STATUS (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Past-season summaries (`history_past`) for all players | Per-GW `history` ingestion (empty preseason — a follow-on) |
| A throttled, idempotent backfill command | Bloating `refresh` with 567 calls |
| A multi-season baseline enriching xP | A full first-class xP engine w/ uncertainty (later Phase 2) |
| CI/CD (tests on push) — may slip to 027 | Web dashboard UI (deferred — near-endpoint value) |
| FPL-native data, no new dependency | External per-GW historical datasets (vaastav/scrapers) |

**External Dependencies:**
- [ ] FPL `element-summary/{id}/` reachable (verified at planning); throttle to respect rate limits.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| 567 calls → rate-limiting (429) / slow | High | A **dedicated throttled backfill** (inter-call sleep + `with_retry`), *not* in `refresh`; idempotent so partial runs resume; run once/season (static data) |
| Preseason: no current-season signal for xP | Med | This is *why* history matters now — the multi-season baseline **is** the signal; blend when current appears |
| Players with 0 past seasons | Med | Handle gracefully — fall back to current snapshot; never crash |
| `element_code` vs per-season `id` confusion | Med | Key history on **`element_code`** (stable across seasons); map to current `id` at read time |
| Over-modelling the xP enrichment | Med | Start simple (minutes-weighted recent-season baseline); ADR-028 gates the method; pressure-test on real players |
| Sprint too big (4 stories, 2 gates) | Med | US-079 (CI/CD) is independent + slippable to 027; historical+xP is the coherent core |

---

### 🗝️ Gating decisions

**US-076 → ADR-027 (historical data).** Proposed (confirm/redirect at "start US-076"):
1. **Source:** FPL `element-summary/{id}/` → `history_past`. FPL-native, no new dependency.
2. **Scope:** past-season **summaries** now. Per-GW `history` is empty preseason → deferred
   (backlog: ingest once GWs play; same endpoint).
3. **Rate limit:** a throttled, idempotent `history --backfill` command (or `refresh --history`);
   **not** the default `refresh`. Upsert keyed by (`element_code`, `season_name`); safe to re-run.
4. **Schema:** `player_history_past` (element_code, season_name, + the ~20 stat fields), via the
   generic migration pattern.

**US-078 → ADR-028 (xP enrichment).** Proposed direction (gated separately, walked on real data):
a **minutes-weighted, recency-weighted multi-season baseline** for a player's scoring rate,
replacing/blending the current single-snapshot rate — most valuable preseason. Kept out of the
generic optimiser (policy at the edge). Pressure-test: does Haaland's 272/217/181/239 (+ minutes)
yield a sensible baseline vs the raw `ep_next`?

---

### 📝 Session Progress Log

- **US-076 (gate) ✅** — Probed the live FPL API at planning: **preseason** (0 GWs, `history`
  empty); the available history is per-**season** `history_past` (rich: pts/mins/goals/xG/xA/xGI/
  xGC/DC/starts/cost), keyed by stable `element_code`; **567** players → a throttled fetch-once
  backfill. Caught the **DC-provenance trap** (`defensive_contribution` = 0 in 2022/23–2023/24
  because the stat didn't exist yet — a 0 ≠ real zero). Recorded **ADR-027**: FPL-native source;
  `player_history_past` keyed by (`element_code`, `season_name`); a throttled/idempotent/per-player-
  degrading `history --backfill` command kept out of `refresh`; per-GW `history` deferred; the DC
  caveat (xP must consume only all-season-present fields). Pressure-tested on Haaland's 4 seasons.
  ClubElo re-checked — still down (timeout).
- **US-077 (ingest) ✅** — Built the full slice: `get_element_summary` (client), a `PlayerSeason`
  model (`from_api`, cost tenths→£m), `player_history_past` table (PK code+season, **no FK**),
  `save_history_past`/`get_history_past`/`get_player_ids`, and `ingest.backfill_history`
  (throttled 0.3s, idempotent, per-player degrade) wired to a `history --backfill [--limit N]`
  command. **6 tests** (model, round-trip, stores-seasons, idempotent, per-player-degrade,
  0-season) → suite **227 → 233**. Smoke: `--limit 5` live → 26 rows in ~2s. **Smoke finding
  (corrected a planning assumption):** historical `expected_*` is unreliable — FPL sends `'0.00'`
  (string zero, not null) for older seasons/most players before ~2024/25 (Haaland was a misleading
  sample). Reliable across all seasons = **points/minutes/goals/assists** only. ADR-027 caveat +
  Data_Sources updated accordingly; feeds US-078's baseline design.
- **US-078 (enrich xP) ✅** — ADR-028: the xP **rate** becomes a multi-season baseline (recency+
  minutes-weighted points/90 over ≤3 seasons; reliable fields only), used outright preseason,
  falling back to current `ppg` without history. Added `players.code` (join key), `baseline_rate`
  analytics, `get_history_by_code`, enriched `player_xp` (rate-in, formula unchanged — policy at
  the edge), and a `Rate` column in `xp` (`*` = baseline) with a "quality when playing" caveat.
  **Live smoke caught a bug the clean-data unit tests missed:** cameo seasons (2 pts/20 mins →
  pp90 90.0) topped the ranking → added the **≥900-min gate** (Sprint 016 Meslier lesson), re-smoked
  clean (top: B.Fernandes/Saka/Haaland, realistic 5–7 rates; `*`/plain correctly reflects backfill
  coverage). **8 tests** (baseline math, gate, fallback, no-code-key) → suite **233 → 242**.
- **US-079 (CI/CD) ✅** — GitHub Actions (`.github/workflows/ci.yml`): `ruff` + `pytest` on every
  push/PR across Python 3.13/3.14 (the offline suite → deterministic CI). Added `ruff.toml` (a
  small stable ruleset — E/F/I; **not** the opinionated DTZ/RUF defaults, since `date.today()` is
  correct here), `.pre-commit-config.yaml` (opt-in local hooks), ruff+pre-commit in requirements,
  a CI badge + Development section in the README, and a CI section in Handbook Ch 11. Ran ruff:
  auto-fixed import-order + one dead import, excluded throwaway `spikes/`; **242 tests + `ruff
  check .` both green locally**. No ADR (straightforward infra). *No behaviour change.*

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All four stories — US-076 (ADR-027), US-077 (ingest history), US-078 (ADR-028,
  enrich xP), US-079 (CI/CD). Phase 2's first sprint: the project's **first historical data**
  (past-season summaries via a throttled `history --backfill`), a **materially better xP** (a
  multi-season baseline rate), and **CI** (ruff + pytest on every push). Tests 227 → **242**; two
  ADRs; **no new dependency**. *The analytics core now stands on multi-season history, and every
  push is checked.*
* **Carried Forward:** None. Per-GW history ingestion is on the Backlog (data doesn't exist until
  GW1); in-season xP blending likewise.
* **Key Artifacts / Decisions:** ADR-027 (FPL `element-summary` history; `element_code` key; the
  throttled/idempotent backfill; the data-provenance caveat); ADR-028 (the multi-season baseline +
  the ≥900-min gate); `player_history_past`, `PlayerSeason`, `baseline_rate`; `ci.yml` + `ruff.toml`.

#### Retrospective
* **What Went Well?**
  - **Verify-at-planning paid off twice.** Probing the live API *before* designing revealed we're
    preseason (no per-GW history) and that history is per-*season* — which reshaped the whole
    sprint away from a wrong "per-GW trends" design.
  - **Then verify-on-real-data caught two more things the clean-data tests couldn't.** (1) The
    Haaland-only planning sample wrongly suggested xG is reliable across seasons; the broad backfill
    showed `'0.00'` for older seasons. (2) The xP smoke showed cameo seasons inventing pp90 = 90 and
    topping the ranking → the ≥900-min gate (the Sprint 016 Meslier lesson, third time it's earned
    its keep). *Real data finds what unit tests can't.*
  - **Enriched a metric without touching its formula** (ADR-028) — only the rate input changed;
    the xP formula, horizon, availability, and the optimiser were untouched. Policy at the edge held.
  - **Rate-limit discipline** — 567 calls became a throttled, idempotent, per-player-degrading
    backfill kept out of the fast `refresh`.
  - **CI right-sized** — a small, stable ruleset that catches real problems without churning correct
    code (`date.today()` left alone). DoD held (26th sprint): tests + live smoke + docs each story.
* **What Could Be Improved?**
  - The **planning sample was too small** (Haaland alone) and gave a false "xG is reliable" read —
    corrected only at ingest. A wider sample at planning would have caught it a story earlier.
  - The sprint was **large** (4 stories, 2 gates) — it held together, but US-079 could have been its
    own sprint.
* **Lessons Learned?**
  - Probe *broadly* at planning — one marquee player isn't a representative sample.
  - Gate small samples everywhere a rate is computed — it's now bitten us in Sprints 016 and 026.
  - Historical data has provenance: a `0.00` in an old season often means "not tracked", not zero.
* **Action Items for Next Sprint (027):**
  - [ ] Pick the next Phase 2 item — richer data (a full 567 backfill in the wild), the web UI, or a
        Phase 3 decision-support feature (captain picks now have a better xP to stand on). Check first.
  - [ ] Once GW1 plays: ingest per-GW `history`; blend the baseline with live form.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 027):** owner to steer — a Phase 3 decision-support feature (captain
suggestions, on the improved xP), the web UI, or hardening the data (full backfill, per-GW once the
season starts).

**Completion Date:** 2026-08-03
**Final Notes:** Phase 2 opened strongly — real historical data, a better xP (the Marmoush
correction is the proof), and CI. Two bugs the unit tests couldn't see were caught by testing on
real data. Sprint outcome: **Successful** — 4/4 stories, zero roll-over, DoD held.
