# Architecture — v0.1 (Agreed)

**Status:** Agreed
**Version:** 0.1
**Last updated:** 2026-07-31
**Related:** [Project Charter](../00_Project/Project_Charter.md) · [Roadmap](../04_Roadmap/Roadmap.md) · [Sprint 001](../05_Sprints/Sprint1.md)

---

## 1. Purpose of this document

This describes *how* the FPL Assistant is built, so that a future decision can
always be traced back to a reason. It is deliberately small: it covers only what
Sprint 001 needs (fetch → store → display player data), plus enough shape to grow
into the Roadmap's later phases without a rewrite.

It is **not** a final design. Where a decision is not yet made, it is listed in
§9 (Open Decisions) rather than guessed at.

---

## 2. Guiding principles (from the Charter)

- **Keep it simple.** The simplest thing that works, until a real need proves otherwise.
- **Small modules.** Each module does one job and can be read in one sitting.
- **Data flows one way.** External API → local store → analysis → presentation.
- **The official FPL API is the source of truth** for prices, points, and fixtures.
- **Understand before accepting.** Every layer should be explainable end-to-end.

---

## 3. High-level overview

For v0.1 the application is a single Python process with three clear layers:

```
        ┌─────────────────────────────────────────────┐
        │             Presentation (edges)             │
        │  CLI (argparse) · Web: Streamlit (ADR-052,   │
        │  grown) + FastAPI (ADR-050, frozen)          │
        │  — all call the SAME analytics; core is      │
        │    web-free (one-way flow, a test asserts)   │
        └───────────────────┬─────────────────────────┘
                            │ reads
        ┌───────────────────┴─────────────────────────┐
        │                  Storage                     │
        │            (SQLite: local cache)             │
        └───────────────────┬─────────────────────────┘
                            │ writes / reads
        ┌───────────────────┴─────────────────────────┐
        │                Ingestion                     │
        │   (FPL API client → normalise → save)        │
        └───────────────────┬─────────────────────────┘
                            │ HTTP GET
        ┌───────────────────┴─────────────────────────┐
        │        Official FPL API (external)           │
        │      fantasy.premierleague.com/api/...        │
        └─────────────────────────────────────────────┘
```

The golden rule: **data only flows upward.** Presentation never calls the API
directly; it only reads from storage. This keeps the network (slow, rate-limited,
sometimes down) separated from everything that uses the data.

---

## 4. Components (v0.1)

| Component | Responsibility | Does NOT do |
|---|---|---|
| **CLI (interaction)** | Parse the user's command and dispatch to a handler (Sprint 002, `src/cli.py`) | Contain FPL logic itself |
| **API client** | Make HTTP requests to the FPL API, return raw JSON | Interpret or store data |
| **Parser / mapper** | Turn raw JSON into simple, explicit Python objects (only the fields we use) | Fetch or persist |
| **Storage (repository)** | Save and load players from SQLite | Know about HTTP or display |
| **Analytics** | Calculate derived metrics, e.g. Points-per-£m (Sprint 002, `src/analytics/`) | Fetch or store; know about display |
| **Presentation** | Show players as a table (console for now) | Fetch or store |
| **Config** | Endpoints, DB path, constants in one place | Business logic |

Each of these becomes a small module (see §7). The boundaries matter more than the
file names — the point is that the API client knows nothing about SQLite, and the
display knows nothing about HTTP.

**Sprint 002 additions.** The **CLI** sits on top as a thin interaction layer: it
decides *what the user asked for* and calls the layers below, but holds no logic of
its own (see [ADR-003](../06_Decisions/ADR-003-cli-approach.md)). **Analytics** sits
beside presentation: it reads from storage and computes derived numbers (the first
being Points-per-£m), never touching the API or the screen. The golden rule still
holds — only the `refresh` path reaches the network.

**Sprint 007 addition — optimisation.** The squad **optimiser**
(`src/analytics/optimizer.py`, [ADR-008](../06_Decisions/ADR-008-squad-selector.md))
is analytics that *chooses a set* under constraints rather than ranking — the first
feature that makes a decision. It's also the first component with an external
dependency beyond `requests` (**PuLP**, an integer-programming solver), kept sealed
inside that one module so the rest of the code is unaffected.

**Sprint 008 addition — include/exclude.** The optimiser gains forced picks
(`pick = 1`/`0`) so the user can lock players in or out
([ADR-009](../06_Decisions/ADR-009-squad-include-exclude.md)). A small **name-resolver**
turns typed names into player ids, handling the non-unique `web_name` (14 shared) via a
`Name:TEAM` form — input validation at the CLI/optimiser boundary.

**Sprint 009 addition — a second data source (ClubElo).** Until now the app had one
source (FPL). ClubElo (team Elo) is added via its own client + a team-name mapping,
stored as `teams.elo` ([ADR-010](../06_Decisions/ADR-010-clubelo-external-source.md)).
It is **best-effort**: `refresh` still requires FPL, but ClubElo failure is *non-fatal*
— it's logged, the last-known Elo is kept, and every feature still works (**graceful
degradation**). So the golden rule now has two network paths in `refresh` — FPL
(required) and ClubElo (best-effort) — and nowhere else.

---

## 5. Data flow — the Sprint 001 slice

1. **Fetch** — API client `GET`s `/bootstrap-static/` and returns raw JSON.
2. **Map** — parser extracts only the player fields we care about (see §6) into
   plain objects. Unknown/extra FPL fields are ignored, not stored.
3. **Store** — repository writes players into SQLite (upsert, so re-running
   refreshes rather than duplicates).
4. **Read** — presentation loads players from SQLite.
5. **Display** — a basic table is printed (name, team, position, price, points).

Running the app twice should not hit the network twice unnecessarily — after the
first fetch, data is served from SQLite. A manual "refresh" re-runs steps 1–3.
(Automatic scheduled refresh with TTLs is a Roadmap Phase 1 item, **not** v0.1.)

---

## 6. Data model (v0.1)

We store only what we use. The FPL `bootstrap-static` payload is large; mapping a
small explicit subset protects us from schema churn.

**`teams`**

| Column | Type | Source (FPL field) | Notes |
|---|---|---|---|
| `id` | INTEGER PK | `teams[].id` | FPL team id |
| `name` | TEXT | `teams[].name` | e.g. "Arsenal" |
| `short_name` | TEXT | `teams[].short_name` | e.g. "ARS" |
| `strength_overall_home` | INTEGER | `teams[].strength_overall_home` | 1–5 (Sprint 004, [ADR-005](../06_Decisions/ADR-005-custom-fdr.md)) |
| `strength_overall_away` | INTEGER | `teams[].strength_overall_away` | 1–5 (Sprint 004, ADR-005) |

The strength columns are added to an existing `teams` table via a light migration
(`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`), since `CREATE TABLE IF NOT EXISTS`
won't alter a table that already exists. The granular attack/defence strengths are 0
in preseason, so the custom FDR uses overall strength for now (ADR-005).

**`players`**

| Column | Type | Source (FPL field) | Notes |
|---|---|---|---|
| `id` | INTEGER PK | `elements[].id` | FPL element id |
| `first_name` | TEXT | `elements[].first_name` | |
| `second_name` | TEXT | `elements[].second_name` | |
| `web_name` | TEXT | `elements[].web_name` | Display name |
| `team_id` | INTEGER FK → teams.id | `elements[].team` | |
| `position` | TEXT | `elements[].element_type` | Mapped 1–4 → GK/DEF/MID/FWD |
| `price` | REAL | `elements[].now_cost` | Stored as £m (now_cost ÷ 10) |
| `total_points` | INTEGER | `elements[].total_points` | |
| `points_per_game` | REAL | `elements[].points_per_game` | xP baseline; last-season, auto-updates (Sprint 005, [ADR-006](../06_Decisions/ADR-006-expected-points-v0.md)) |
| `status` | TEXT | `elements[].status` | 'a' = available (Sprint 005) |
| `ep_next` | REAL | `elements[].ep_next` | FPL's own expected points, for comparison (Sprint 005) |
| `xg` | REAL | `elements[].expected_goals` | Expected goals; last-season (Sprint 014, [ADR-015](../06_Decisions/ADR-015-expected-goals.md)) |
| `xa` | REAL | `elements[].expected_assists` | Expected assists (Sprint 014) |
| `xgi` | REAL | `elements[].expected_goal_involvements` | xGI = xG + xA; `xg` view + `--objective xgi` (Sprint 014) |
| `xgc` | REAL | `elements[].expected_goals_conceded` | Expected goals conceded; defensive lens (Sprint 014) |
| `goals_scored` | INTEGER | `elements[].goals_scored` | Actual goals; over/under-performance (Sprint 016, [ADR-017](../06_Decisions/ADR-017-over-under-performance.md)) |
| `assists` | INTEGER | `elements[].assists` | Actual assists (Sprint 016) |
| `minutes` | INTEGER | `elements[].minutes` | Minutes played; the ≥ 900 gate for `overperf` (Sprint 016) |
| `defcon` | INTEGER | `elements[].defensive_contribution` | DefCon actions; position-correct (DEF=CBIT, MID/FWD=CBIT+rec) (Sprint 017, [ADR-018](../06_Decisions/ADR-018-defensive-contribution.md)) |
| `defcon_per90` | REAL | `elements[].defensive_contribution_per_90` | Per-90 rate; compared to the position threshold in `defcon` (Sprint 017) |
| `cbi` | INTEGER | `elements[].clearances_blocks_interceptions` | Clearances + blocks + interceptions (Sprint 017) |
| `tackles` | INTEGER | `elements[].tackles` | Tackles (Sprint 017) |
| `recoveries` | INTEGER | `elements[].recoveries` | Ball recoveries (Sprint 017) |
| `chance` | INTEGER | `elements[].chance_of_playing_next_round` | % chance of playing; None = fully fit (Sprint 022, [ADR-023](../06_Decisions/ADR-023-player-availability.md)) |
| `news` | TEXT | `elements[].news` | Injury/suspension detail; availability flag messages (Sprint 022) |

The Sprint 005 columns are added to the existing `players` table via the same light
migration as `teams` (§ADR-005). **Expected Points (xP)** is the first *cross-domain*
metric: it multiplies a player's `points_per_game` by their next fixture's difficulty
(reusing the FDR from ADR-005), so the analytics layer joins the player and fixture
threads for the first time (ADR-006). Sprint 006 extends xP to a **horizon** — the sum
of per-fixture xP over the next N gameweeks (ADR-007) — which captures double gameweeks
(a team playing twice in a gameweek has both fixtures counted).

**`fixtures`** *(Sprint 003 — see [ADR-004](../06_Decisions/ADR-004-fixtures-and-fdr.md))*

| Column | Type | Source (FPL field) | Notes |
|---|---|---|---|
| `id` | INTEGER PK | `fixtures[].id` | Fixture id |
| `event` | INTEGER (nullable) | `fixtures[].event` | Gameweek; null = unscheduled |
| `team_h` | INTEGER FK → teams.id | `fixtures[].team_h` | Home team |
| `team_a` | INTEGER FK → teams.id | `fixtures[].team_a` | Away team |
| `team_h_difficulty` | INTEGER | `fixtures[].team_h_difficulty` | FDR from the home team's view |
| `team_a_difficulty` | INTEGER | `fixtures[].team_a_difficulty` | FDR from the away team's view |
| `finished` | INTEGER (bool) | `fixtures[].finished` | "Upcoming" = not finished |
| `kickoff_time` | TEXT (nullable) | `fixtures[].kickoff_time` | For listing a team's fixtures |

A fixture references **two** teams, so it is stored after teams (and FK enforcement,
now on, guarantees the references are valid). Difficulty is kept per side because FDR
depends on perspective. "Upcoming" is derived from unfinished fixtures ordered by
gameweek — no separate gameweek/events table yet.

**Positions** are stored human-readable (GK/DEF/MID/FWD). The 1–4 → label mapping
lives in config, mapped once at ingestion so the rest of the app never deals with
magic numbers.

**Why SQLite:** zero setup, single file, part of the Python stdlib (`sqlite3`), and
the schema is designed so a later move to PostgreSQL (Roadmap) is a swap of the
storage layer, not a rewrite.

---

## 7. Proposed project structure

Illustrative, kept flat and small. Exact names to be confirmed during US-002/003.

```
fpl-assistant/
├── app.py                  # entry point: wires the slice together
├── requirements.txt
├── fpl/                    # application package
│   ├── __init__.py
│   ├── config.py           # endpoints, DB path, position map
│   ├── api_client.py       # HTTP → raw JSON
│   ├── models.py           # plain Player / Team objects
│   ├── parser.py           # raw JSON → models
│   ├── storage.py          # SQLite read/write (the "repository")
│   └── display.py          # render player table
├── tests/
│   └── test_api_client.py  # first test, against a saved sample response
└── docs/                   # (existing)
```

---

## 8. Technology choices (v0.1)

| Concern | Choice | Reason | Deferred alternative |
|---|---|---|---|
| Language | Python 3.14 | Charter; already set up (Session 1) | — |
| HTTP | `requests` | Simple, well-known, good for learning | `httpx` (async) later |
| Storage | SQLite (`sqlite3`) | Zero-setup, stdlib, single file | PostgreSQL (Roadmap) |
| Testing | `pytest` | Charter goal; readable tests | — |
| Presentation | Console table (plain print) | Smallest thing that proves the slice | FastAPI + web UI |
| Web framework | **Not yet** | Not needed to display data once | FastAPI (Charter/Roadmap) |

**On FastAPI:** the Charter names it and the Roadmap assumes it, but v0.1 does not
need a web server to prove the data pipeline. Introducing it is planned for a later
sprint, once there is data worth serving over HTTP. The layered design above means
the presentation layer can be swapped from "print a table" to "FastAPI endpoint"
without touching ingestion or storage.

---

## 9. Decisions & open questions

These come from the Roadmap and gate later architecture. Items 1–2 are now
**decided** (recorded as ADRs in `docs/06_Decisions/`); items 3–4 remain open.

1. **Internal tool vs multi-user product.** *(Roadmap Phase 1)* — **Decided:**
   **single-user / internal**. Simplest path, fits a learning project; the DB schema
   still leaves room for multi-manager analysis later.
   → [ADR-001](../06_Decisions/ADR-001-single-user-vs-multi-user.md) (Accepted)
2. **UI approach.** — **Decided:** **console now → FastAPI later**, with the web-UI
   framework (React/Next.js vs Streamlit/Dash) deferred to a follow-up ADR.
   → [ADR-002](../06_Decisions/ADR-002-ui-approach.md) (Accepted)
3. **Caching strategy.** *(open)* — v0.1 uses "fetch once, then read SQLite" with
   manual refresh. TTL-based auto-refresh (and whether Redis is ever needed) is deferred.
4. **Storage engine longevity.** *(open)* — SQLite now; when/whether to move to PostgreSQL.

---

## 10. Out of scope for v0.1

To keep the slice honest, the following are explicitly **not** in v0.1 (they map to
later Roadmap phases): analytics (xG/xA, FDR, xP), value/form ranking, transfer or
captain recommendations, user-auth endpoints (`/my-team/`), fixtures and historical
backfill, scheduled refresh, the AI/RAG layer, and optimisation.

---

## 11. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| FPL API schema changes | Med | Map a small explicit field subset; fail loudly on missing fields |
| Rate limiting (429) | Med | Cache to SQLite; tests use a saved sample, not live calls |
| Layer boundaries erode over time | Med | Enforce one-way data flow in reviews; keep modules single-purpose |
| Premature complexity (FastAPI/ORM/Redis too early) | Low | Defer until a real need; v0.1 stays stdlib + `requests` |

---

## 12. Changelog

- **v0.1 (2026-07-31)** — Initial draft for the Sprint 001 foundation slice.
- **v0.1 agreed (2026-07-31)** — Status → Agreed; §9 decisions 1–2 recorded as
  ADR-001 and ADR-002.
- **Sprint 002 (2026-08-01)** — §4 gains two layers: CLI (interaction) and
  Analytics, per ADR-003. One-way data flow unchanged.
- **Sprint 003 (2026-08-01)** — §6 gains the `fixtures` entity (two FKs to teams;
  FK enforcement enabled), per ADR-004. First fixture-based analytics (FDR).
- **Sprint 004 (2026-08-02)** — `teams` gains `strength_overall_home/away` (added by a
  light migration), per ADR-005. Custom overall FDR; Attack/Defence split deferred
  (preseason strengths are zero).
- **Sprint 005 (2026-08-02)** — `players` gains `points_per_game`, `status`, `ep_next`
  (same light migration), per ADR-006. First cross-domain metric: Expected Points (xP)
  = player rate × fixture difficulty. Form/expected-minutes deferred.
- **Sprint 006 (2026-08-02)** — xP extended to a gameweek horizon (sum over the next N
  gameweeks), per ADR-007. No schema change; captures DGW (two fixtures in a gameweek
  both count).
- **Sprint 007 (2026-08-02)** — first optimisation: a squad selector picks the optimal
  XI via integer programming (PuLP), per ADR-008. First dependency beyond `requests`;
  no schema change.
- **Sprint 008 (2026-08-02)** — the squad selector gains include/exclude (forced picks)
  + a name resolver for the non-unique `web_name`, per ADR-009. No new data/dependency.
- **Sprint 009 (2026-08-02)** — first multi-source design: ClubElo (team Elo) added as a
  best-effort second source with graceful degradation, per ADR-010. `teams.elo`;
  Elo-based FDR. No new pip dependency (requests + stdlib csv).
- **Sprint 010 (2026-08-02)** — the squad optimiser's objective becomes pluggable
  (`squad --objective points|value|xp`), per ADR-011. The optimiser maximises any
  per-player score; the objective (reusing value/xP) is computed outside it.
- **Sprint 011 (2026-08-02)** — the optimiser gains the full 15-man squad
  (`squad --full`: 2/5/5/3, £100m, ≤3/club), per ADR-012. No new algorithm — a new
  *caller* of the generic `select_squad` (formation + budget already parameters); the
  bench is the manager's via `--include`. The 15-total is a squad-strength proxy, not a
  weekly score (stated caveat).
- **Sprint 012 (2026-08-02)** — a *declared* bench (`squad --bench`), per ADR-013.
  Benched players are forced in like `--include` but tagged, marked `**`, and sorted to
  the end; `--bench` implies `--full` (cap 4). Knowing the bench yields a starters'
  points subtotal — the honest weekly number that answers ADR-012's caveat. Annotation +
  display; the optimiser's model is unchanged.
- **Sprint 013 (2026-08-02)** — *flexible formations* (`squad --formation`), per ADR-014.
  The XI's position constraints become ranges (DEF 3–5, MID 2–5, FWD 1–3, 11 total);
  `select_squad` gains range/`size` support (exact ints unchanged), and the CLI opts into
  the flexible default (`XI_FLEX`). The chosen shape is shown, as is the bench-implied
  shape in `--full` (shared `formation_str`) — connecting the bench (ADR-013) to the
  formation. Policy at the edge; the solver stays a generic constraint executor.
- **Sprint 014 (2026-08-02)** — *expected goals* (xG/xA/xGI/xGC), per ADR-015. A new data
  dimension from the **FPL API** (FBref rejected — 403 + dependency); `players` gains four
  `expected_*` columns via the generic migration. A new `xg` view ranks by xGI, and
  `--objective xgi` is one new `objective_scores` entry (no solver change — ADR-011). A
  full-stack slice: API → model → storage migration → analytics → view. No new dependency.
- **Sprint 015 (2026-08-03)** — a *spike*, no code: evaluated `soccerdata` and **deferred**
  it (ADR-016). `src/` unchanged; evidence in `spikes/015-soccerdata/`.
- **Sprint 016 (2026-08-03)** — *over/under-performance* (`overperf`), per ADR-017. `players`
  gains `goals_scored`/`assists`/`minutes` via the generic migration; a new view compares
  **expected** attacking points (from xG/xA) to **actual** (from goals/assists), minutes-gated
  (≥ 900) to filter noise + a preseason glitch. Attacking-only (stated caveat). FPL-native,
  no new dependency (the "lighter model" chosen in ADR-016).
- **Sprint 017 (2026-08-03)** — *Defensive Contribution* (`defcon`), per ADR-018. `players`
  gains five DefCon columns via the generic migration; a new view ranks players by
  `defensive_contribution_per_90 − threshold` (DEF 10, MID/FWD 12; GK excluded), minutes-gated.
  Verified FPL's field is position-correct (DEF=CBIT, MID/FWD=CBIT+recoveries). A defensive
  counterpart to `overperf`; no new dependency.
- **Sprint 018 (2026-08-03)** — *clean-sheet / solidity lens* (`cleansheet`), per ADR-019. A
  **metric + view only, no ingest** — `xGC/90 = xgc × 90 / minutes` (computed from the `xgc`
  stored since Sprint 014; verified == FPL's per-90 field), ranking DEF+GK by best solidity,
  minutes-gated. Completes the defensive picture (DefCon + clean sheets); GKs get a lens. A
  team signal shown per player (stated caveat). No new dependency.
- **Sprint 019 (2026-08-03)** — *ClubElo resilience* (retry-with-backoff), per ADR-020. The
  ClubElo fetch retries transient errors (502/503/504, timeouts, connection) with exponential
  backoff *before* falling back to last-known Elo — so a momentary blip no longer loses the Elo
  refresh. Retry *then* degrade (ADR-010 unchanged); a reusable helper; injectable sleep. No
  new dependency.
- **Sprint 020 (2026-08-03)** — *importance-scaled retry*, per ADR-021. The ADR-020 helper is
  applied to **both** clients: **FPL** (required) retries hard (2, 10s) — a blip no longer kills
  refresh, though exhaustion is still fatal; **ClubElo** (best-effort) fails fast (1 retry, 5s
  timeout) so a sustained outage degrades in ~10s not ~31s. One helper, two policies; the more a
  source matters, the harder we try.
- **Sprint 021 (2026-08-03)** — *validate a legal bench*, per ADR-022. When a full 4-man bench
  is declared, the 11 starters are checked against the `XI_FLEX` legal ranges (reused from
  ADR-014); an illegal bench (e.g. 0 FWD) is **warned**, not blocked. Closes the ADR-014 gap;
  one pure `legal_xi_issues` helper; no new data.
- **Sprint 022 (2026-08-03)** — *player availability*, per ADR-023. `players` gains `chance`
  and `news` via the generic migration (`status` already stored); `squad` excludes unavailable
  players (status i/s/u/n) by default with `--include-unavailable` opt-out, flags doubtful
  picks, and warns on a forced-in injured pick. Availability is a policy at the edge (the CLI
  filters); `select_squad` stays generic. Fixes the optimiser picking an injured player.
- **Sprint 023 (2026-08-03)** — *saved / persistent squad*, per ADR-024. The first **user-state**
  layer: a JSON `SquadStore` (`data/squads.json`, gitignored) stores the user's picks (ids +
  bench), kept **separate from the `data/fpl.db` reference cache** so it survives `refresh`.
  `squad --save/--load`; on load the ids are re-priced and availability re-checked against
  current data, and departed players noted. Store the picks, derive the numbers fresh.
- **Sprint 026 (2026-08-03)** — *historical past-season data* (Phase 2 begins), per ADR-027. A
  **second FPL endpoint** (`element-summary/{id}/`) and the project's first historical store: a new
  `player_history_past` table (keyed by the stable `element_code`, **no FK** — history outlives a
  player's presence, like ADR-024). Populated by a **throttled, idempotent, per-player-degrading**
  `history --backfill` command (kept out of the one-call `refresh`); a `PlayerSeason` model mirrors
  the `from_api` idiom. Data-provenance caveat confirmed on the live backfill: only
  points/minutes/goals/assists are reliable across all seasons (xG/xA/DC are recent-only). Sets up
  US-078's xP enrichment. Full-stack slice: API → model → storage → ingest → CLI. No new dependency.
  Then (US-078, ADR-028) *xP enrichment*: the scoring **rate** becomes a multi-season baseline
  (recency+minutes-weighted points/90 from history, ≥900-min gated), replacing one noisy season
  preseason and falling back to current `ppg` without history. Only the rate input changed — the xP
  formula, horizon, and optimiser are untouched (policy at the edge); `players` gains a `code` join
  key. A live smoke caught cameo seasons inventing absurd rates → the ≥900-min gate (Sprint 016 lesson).
- **Sprint 027 (2026-08-03)** — *captain suggestions* (**Phase 3 / decision support begins**), per
  ADR-029. The app's first feature that *recommends and explains* rather than ranks: a
  `captain_picks` analytics fn ranks available **outfield** players by next-GW xP (ADR-028) and
  annotates each with opponent, venue, and penalty duty. Reuses availability (ADR-023) and the
  shared renderer (ADR-025 — its first new consumer); `players` gains `penalties_order`.
  Probe-driven policy: **exclude GKs** (a keeper ranked #3 by mean xP — the mean-not-ceiling caveat)
  and **keep doubtful players, flagged** (a new `is_available` seam on `player_xp` so they aren't
  zeroed). Penalties are context, not a score bump (no double-counting). No new dependency.
- **Sprint 028 (2026-08-03)** — *transfer suggestions* (Phase 3, feature 2), per ADR-030. A pure
  `suggest_transfers` analytics fn: for a saved squad, the best legal same-position replacement per
  owned player, ranked by **xP gain over a horizon** — the first feature that respects FPL's
  **transfer rules** (≤3/club, reusing the optimiser's `MAX_PER_CLUB`; budget = sale + `--bank`;
  availability; not-owned). GKs are **included** (a better keeper is a real upgrade — the mirror of
  captaincy's GK *exclusion*); bench players (from the squad's `bench_ids`) are **flagged**, not
  modelled. Composes xP + saved squads; no schema change, no new dependency. (Command + view: US-085.)
- **Sprint 029 (2026-08-04)** — *Team Analyser* (Phase 3 decision-support **capstone**), per ADR-031.
  An `analyse --squad <name>` command that grades a saved squad's health over a horizon: projected
  **XI** xP, value, availability issues, weakest links, club concentration — **indicators, not a
  grade**. A pure `analyse_squad` fn; the XI is the declared bench's complement, else the best legal
  XI via `select_squad` (ADR-008). Almost entirely **composition** — xP (ADR-028) + availability
  (ADR-023) + saved squads (ADR-024) + the optimiser + the shared renderer (ADR-025, its 3rd new
  consumer) — and it **cross-links** the trio (weak link → `transfer`, top XI → `captain`). No schema
  change, no new dependency. Completes captain · transfer · analyse.
- **Sprint 030 (2026-08-04)** — *per-gameweek xP* (analyser enhancements), per ADR-032. `player_xp`
  now groups fixtures **by gameweek** (`_difficulties_by_team_gw`) and returns a `by_gameweek`
  breakdown alongside the total — a **faithful decomposition** (the total is the sum of the unrounded
  per-GW values, so it's byte-for-byte unchanged; DGW = a GW's fixtures summed, BGW = 0). Additive:
  existing consumers/totals untouched. Feeds a per-GW view in `analyse` + `xp` and `analyse --sort xp`
  (US-091), closing the Sprint-006 "xp per-GW" backlog item. No schema change, no new dependency.
- **Sprint 032 (2026-08-04)** — *the `ask` command* (**Phase 4 begins**), per ADR-034 (from the
  ADR-033 spike). The first **language layer** — but it adds words, not intelligence: `ask` routes a
  question by **keyword** (`src/ask.py`; the LLM decides nothing, incl. the route), the analytics
  **decide** and emit **pre-humanised, self-describing facts**, and a local LLM (`src/llm.py`,
  Ollama via stdlib HTTP — no new dependency) **narrates**, forbidden from ranking/computing/
  inventing. Crucially the **LLM is optional**: `narrate` returns `None` when Ollama is absent and
  `ask` degrades to the decision + facts (verified). The narrator is injectable → the flow is
  unit-tested offline; the real model is smoke-only. US-096 wired the `captain` intent; transfer +
  analyse follow (US-097).
- **Sprint 033 (2026-08-04)** — *multi-transfer plan* (deepen Phase 4), per ADR-035. The first
  recommendation over a **sequence**: `suggest_transfer_plan` greedily takes the best legal single
  transfer given the *running* state, up to `count` — **threading the shared bank** (a later move
  spends what an earlier sale freed), updating club counts, and excluding sold/bought players. It
  **reuses `suggest_transfers`** on the evolving state, so it's correct by construction (bank can't
  go negative; no double-buy/re-buy; ≤3/club across the set). Surfaced as `transfer --count N`
  (opt-in; the shortlist is unchanged) and, next, `ask "which N transfers"` (US-100). Greedy (not
  ILP) — explainable; hits deferred. No schema change, no new dependency.
- **Sprint 034 (2026-08-04)** — *per-gameweek transfer-plan table + a structured detail in `ask`*,
  per ADR-036. A **composition** (ADR-035 plan × ADR-032 per-GW xP), no new logic: the plan table
  gains **GW1…GWN columns of the incoming player's** projected xP (US-102), and `ask` returns a
  pre-rendered `detail` table shown above the narration (US-103) — the LLM still narrates only the
  self-describing facts (ADR-034 unchanged). Reuses the shared renderer (ADR-025) + `by_gameweek`;
  the plan engine and `player_xp` are untouched. No new dependency.
- **Sprint 035 (2026-08-04)** — *grounding verification* (deepen Phase 4's trust), per ADR-037.
  Closes the grounding loop: a pure `verify_grounding(text, facts, *, known_names, subjects)` checks
  that every **number** in the LLM's narration appears in the facts, and that any **known FPL player**
  named is a *subject* of the answer (≥4-letter whole-word tokens, so it doesn't cry wolf). `ask` will
  show a **soft ✓/⚠ trust line** (US-106) with the facts/table always present — verification informs,
  never blocks. Makes *"grounded, not a black box"* provable, not just instructed. Pure string work;
  no new dependency; the analytics untouched.
- **Infra changeover (2026-08-12)** — the MADBOOTS brand's own home (ADR-103 follow-through, `docs/MADBOOTS_CHANGEOVER.md`;
  no code/analytics change). GitHub repo transferred `tesheridan/fpl-assistant` → **`madbootsfpl/fpl-assistant`**
  (name kept; git remote updated); Streamlit reconnected + subdomain renamed → **`madboots.streamlit.app`** (a
  per-domain cookie reset — everyone re-enters the code once; cloud squads survive, handle-keyed); the functional
  URL refs updated (`_GITHUB_ISSUE`/`_DEFAULT_ORIGIN`, the README CI badge, tester/setup docs — historical records
  keep the old names, and GitHub redirects the old repo URL); and the **homepage went live on Cloudflare Pages at
  `madboots.com`** (the brand front door + a Launch-the-app CTA). The internal `fpl-assistant` package + the `FPL_*`
  secrets are unchanged. **Access stays in the app** — a static page can't gate a public Streamlit URL (the
  persistence/auth rework, incl. a possible `st.login()`, is the next structural thread).
- **Sprint 146 (2026-08-12)** — *Split the Squads tab → My Squad + Squad Lab* (**ADR-105**, revises ADR-069). The
  single **Squads** page had grown to a **7-way "Tool" switch** (Build defaulting first among six manage-your-team
  tools). **US-359:** split `pages/3_Squads.py` → **`3_My_Squad.py`** (the pitch/edit + a 6-way sub-tab in workflow
  order `My Squad · AI Tips · Captain · Transfer · Chips · Health`, default My Squad; the squad picker + horizon
  here) and a new **`4_Squad_Lab.py`** (the renamed *Build* — `render_build` + a horizon + "Use this squad →").
  Renumbered Ask→Admin (5–10); nav = `Home · Players · Fixtures · My Squad · Squad Lab · Ask · News · Trending ·
  Help · Feedback (· Admin)`. **Reuses `views/squads.py`'s renderers unchanged — IA only, no engine/analytics
  change.** Test-harness: `_squads_view` routes *Build → Squad Lab* else *My Squad* (one helper; the 13 `test_build_*`
  repointed); ~39 page paths renumbered (a direct sed, not a constants refactor); `_TAB_EMOJI`/`test_sidebar_pages`
  + perf/tooltip fixed. **US-360:** the Squad Lab **mascot header** (badge + 🥾 + "Build your squad"), a no-squad My
  Squad **→ Squad Lab** info pointer, and the Home + Help copy rebranded to the two tabs. *(Gotcha: `st.page_link`
  to a page path raises in AppTest bare mode — the pointer is text, not a `page_link`.)* Functional nav labels +
  brand on the page; full MADBOOTS vocabulary deferred (branding-E). +2 tests (964→966).
- **Sprint 145 (2026-08-12)** — *P0 quick-wins (2026-08-12 tester feedback)* (**ADR-104** for the data floor; the
  two quick fixes no new ADR). **US-356:** the My Squad **Transfer** bring-in list gains a **Team** selectbox + a
  **Max-price** slider (alongside position/affordable/injured) so the long same-position list narrows. **US-357
  (captain persists):** root-caused as a *set-after-save* gap — `cloud_store` already round-trips the whole squad
  dict (incl `captain_id`), but nothing synced after an edit. Fix: a squad becomes **linked** to a handle on cloud
  Save/Load (`_cloud_linked_handle`); `set_active_squad` now best-effort **auto-syncs** the edit to the cloud when
  linked + configured, so a captain/transfer/bench change syncs across devices. Fail-silent; **only for
  cloud-linked** squads (no handle → no write; the opt-in server-write invariant holds, ADR-094/054); Clear unlinks;
  a sidebar "🔄 Auto-syncing" line. **ADR-104 / US-358 (cold-start xP floor):** **69 available players** with no FPL
  history projected **0** at GW1 (preseason `points_per_game` 0 → rate 0). In `analytics/xp.py::player_xp`'s last
  rate tier, **`rate = max(points_per_game, ep_next)`** with a new `rate_source="ep_next"` — floor with FPL's own
  expected-points-next-GW (already on the row; honest, no new data); the `ep_next` floor isn't re-scaled by the
  minutes weight (it already prices minutes). **Targeted** — the ≥900-min baseline + shrunk fallback tiers
  (ADR-028/040) are unchanged (established players byte-identical); availability still gates. **Reframe on the
  record:** we do *not* chase FFH — for a player *with* history our number is *above* FPL's own `ep_next`, so FFH is
  the outlier; the genuine defect was only the 0s. A deliberate one-xP change (ADR-041) for the cohort → one
  invariance test updated (+3 ADR-104 tests). +5 tests (959→964).
- **Sprint 144 (2026-08-11)** — *Brand polish — tester feedback* (extends **ADR-103**/**ADR-084**, no new ADR;
  display-only). Three nits on the fresh rebrand. **US-355:** (#1) the My Squad card picker → **"View your player's
  card"** (it's your squad); (#2) fixed the player-card wordmark's **MAD/BOOTS gap** — a US-349 regression where the
  band's brand mark was one `inline-flex` with **three** children (badge · `MAD` · `BOOTS`) so `gap:6px` fell
  *between* MAD and BOOTS — by extracting a shared **`brand.mark_html(badge_px, font_px, purple)`** (the badge +
  wordmark as one lockup with MAD+BOOTS wrapped in a **single** flex child) and using it in the band; (#3) the
  **captain card** (`captain_card.py`) gains the same mark as a `cc-brand` footer (theme-aware) — joining the
  player-card brand family. Branding the *hover* popovers was declined (owner steer — the compact card is slimmed +
  ~15 on the pitch + already under MADBOOTS chrome). +1 test (958→959).
- **Sprint 141 (2026-08-11)** — *MADBOOTS — the rebrand* (**ADR-103**). Rename the product's **user-facing**
  surfaces **FPL Assistant → MADBOOTS** (one word — the two-tone MAD-purple/BOOTS-orange split carries the
  word-break), tagline *Fantasy Football, Calculated.* — folded in as **accents** on the current light/theme-aware
  app (approach B; a dark reskin deferred). **US-348:** a single **`web_streamlit/brand.py`** source of truth
  (`NAME`/`TAGLINE` + a pure `page_config()`), swapping every visible "FPL Assistant" → "MADBOOTS" (all ~10 pages'
  tab titles, the Home header, the beta gate ×2, the player-card band, the feedback subject, the FastAPI title +
  `base.html`) + a **guard test** (no stray old name in `src/`); the two borderline ids flip (`USER_AGENT` →
  `madboots/0.1`, CLI `prog` → `madboots`) — the package/repo + the 14 `FPL_*` secrets **unchanged**. **US-349:** the
  **MB badge** (`assets/madboots-badge.png`, transparent, owner-approved via a real-badge Artifact preview) becomes
  `page_config`'s **`page_icon`** (the favicon on every tab) + the small mark on the Home header (`st.image` + the
  two-tone `wordmark_html()`), the beta gate, and the player-card band (a 64² data URI — the compact pitch popover
  has no band, so no per-kit weight). **US-350:** a quiet **not-affiliated** `DISCLAIMER` footer (Home + gates) + the
  live identity-doc rebrand (README/PRODUCT/Charter/DIRECTION/Testing_Guide/Roadmap; the Journal/sprint-logs/ADRs/
  changelog + the `fpl-assistant` package refs kept as the record). **Display/asset-only** — `brand.py` is pure (no
  Streamlit import); the analytics/decision core, the one-xP metric, and the read-only guardrail are untouched. +6
  tests (952→958). The repo-transfer + `madboots.com` changeover is a **separate bundled backlog item**.
- **Sprint 143 (2026-08-11)** — *Clearer transfers — My Squad + accept the AI plan* (extends **ADR-055** +
  **ADR-046**, no new ADR; from tester feedback). Grounding found ~⅔ already shipped, so *clarify + one feature*.
  **US-353:** My Squad's "Swap a player" expander → **"Transfer"** (owner's steer: plain *Transfer*) with a caption
  distinguishing it from the S142 **🔁 Substitute** (*Substitute = lineup XI↔bench · Transfer = a **new** player,
  sells one of the 15; same-position only*); its widgets read **Transfer out / Bring in / Transfer →**. A **live
  overspend flag** — the projected 15-cost + bank (or a *£X over £100m* warning) computed each rerun, shown **before**
  apply — plus an opt-in **"Include injured/suspended"** toggle (drops the `not is_unavailable` filter). **US-354:**
  a new `apply_transfer_plan(squad, plan, players)` in `web_streamlit/squads.py` (the N-transfer counterpart of
  `apply_transfer` — maps every `out.id → in.id` from the `suggest_transfer_plan` moves, one `squad_15_issues`
  check, recomputes cost + a soft over-budget warning, clears a sold captain; copy-not-mutate) behind an **"Apply
  this plan →"** button on `render_transfer`'s `count>1` branch (the coordinated plan was **display-only**; a single
  swap could already be applied). **Session-state only** (mutates like the existing controls); the one-xP +
  read-only invariants hold. +7 tests (945→952). No engine change.
- **Sprint 142 (2026-08-11)** — *An intuitive substitution on My Squad* (extends **ADR-055** + the S139 picker, no
  new ADR; from tester feedback). Subbing was awkward — the only path was the "Set the bench (pick 4)" multiselect
  (re-pick all four). **US-351:** a `substitute(squad, off_id, on_id, by_id)` helper in `web_streamlit/squads.py`
  (copy-not-mutate; `off` → bench taking `on`'s priority slot, `on` → XI; the 15 unchanged) returning
  `(new_squad, issues)` via `set_bench` + `legal_xi_issues` — and a **"🔁 Substitute"** control on My Squad (below
  the pitch + card picker): **Bring off** (a starter) ↔ **Bring on** (a bench player) where **only legal swaps are
  listed** (the bring-on list is pre-filtered to swaps `legal_xi_issues` clears — so GK↔GK, and outfield swaps that
  keep a legal formation; the apply path re-checks too). The old multiselect is relabelled + kept below as the bulk
  path. **US-352:** the "👤 View a player's card" picker **seeds** the control — a *starter* pick pre-fills "Bring
  off" (edge-triggered on a `_sub_prefill_for` session marker, so once per pick + still user-editable), a *bench*
  pick shows a hint. A working button *on* the hover card is impossible (the pitch is one static `st.markdown` block
  that can't call back to Python — the Sprint 139 wall), so it's real widgets near the pitch + the picker as the
  bridge. **Session-state only** (mutates the bench like the existing controls); the one-xP + read-only invariants
  hold. +6 tests (939→945). No engine change.
- **Sprint 140 (2026-08-10)** — *Tester-feedback polish + a beta waitlist* (**ADR-102**; the polish extends
  ADR-084, no new ADR). **US-345 (polish):** the Players **price filter** max = the highest player price rounded to
  £0.5 (so **Haaland £15.5m** shows, was a stale fixed £15.0); the card band reads **"Last season"** (was the
  misleading "Season 24/25"); Trending shows **🔥 Top discussions first**; Help step 7 leads with **☁ Save/Load**.
  **US-346 (card fit):** the compact card → **4** stats + `.pl-card.compact` overrides + a 250px `.kit-pop`, so the
  pitch hover popover fits without truncation (full card unchanged). **US-347 (the waitlist):**
  `web_streamlit/waitlist.py` — `add(email, reason)` derives a `beta_waitlist` endpoint from `FPL_STORE_URL`'s base
  (reuses `FPL_STORE_KEY`, **no new secret**), cleans the email, and upserts `{email, reason}` with
  `merge-duplicates` (idempotent on the email PK); **best-effort + fail-silent** (a no-op without the store / on a
  bad email; swallows any store failure — never raises or blocks the gate). Wired into `access._registration_gate`'s
  two failure branches: a wrong invite code → `bad_code`, over the cap → `full`. **Off by default** (needs the store
  + `FPL_USER_CAP`) — the **4th** opt-in, secret-gated server write (after squad-save/registration/analytics); the
  read-only invariant now names **four** exceptions. Test upkeep: the shared `_fake_user_store` POST fake made
  **URL-aware** (only a `/beta_users` POST records a user) so a waitlist write no longer pollutes the registration
  test. +7 tests (932→939). Display/store-only; the one-xP invariant holds.
- **Sprint 139 (2026-08-10)** — *A rich player card, in two places* (extends **ADR-084**, no new ADR;
  display-only). **US-342:** `web_streamlit/player_card.py` — a self-contained HTML/CSS card (the pitch/captain
  family): `card_body` (CSS-less) + `player_card_html` (`CARD_CSS` + body) + `render_player_card`; a pure,
  **position-adaptive** `_stat_rows` (FWD/MID → goals/xGI/ICT · DEF → xGC/DefCon-90/CBI/tackles · GK →
  xGC/recoveries; skips missing) + FDR fixture pills + flags (ownership tier · set-pieces · availability · a
  **Projected-xP** chip = our `decision_xp`). A fixed dark surface (reads on both themes); every value
  `html.escape`d; no JS. **US-343:** a Players **"Card"** view (`views/players.py::render_card`) — a filter-scoped
  selectbox → the card + next-3 fixtures (`_card_fixtures`) + a lazy, `timed` `decision_xp` for the xP. **US-344:**
  the My Squad pitch — split `CARD_CSS`/`card_body` so the pitch includes the stylesheet **once** and embeds a
  compact `card_body` per kit as a pure-CSS **hover popover** (`.kit:hover .kit-pop`); a **"View a player's card"**
  picker → the full card (the all-device/touch path — a static markdown pitch can't call back to Python).
  Ships with **our** data; Understat's Key-Passes/Shots-in-Box backlogged (ADR-016), Big Chances (Opta-paid)
  dropped. +12 tests (916→928). No engine change; the one-xP + read-only invariants hold.
- **Sprint 138 (2026-08-09)** — *GW1 Data Hardening: the calibration harness + the runbook (prep)* (**ADR-101**).
  Makes GW1 (2026-08-21) a **switch-flip** for the dormant form/set-piece/DefCon weights — the *tooling*, not the
  values (there's no per-GW data to calibrate against until ~GW4+). **US-340:** `analytics/backtest.py` — **pure +
  read-only**, the **predictor is injected** (so it imports no analytics/config and is synthetic-tested now);
  `pairs()` builds **walk-forward** `(predicted, actual, round)` triples using **only rounds < N** (no leakage);
  metrics `spearman` / `mean_gw_spearman` (primary) / `mae` / `hit_rate`; a weight `sweep()` returning
  `{gws, rows, best}` (best = the smallest value within `_FLAT_EPS` of the top ρ — the overfitting guard;
  `insufficient` below `MIN_GWS=4`). **US-341:** a `python app.py calibrate --weight form|set_piece|defcon` CLI —
  preseason it reports "not enough gameweeks"; at GW4+ it builds a **decision_xp-backed walk-forward** predictor
  (a new `Storage.get_fixtures_by_event`, since `get_upcoming_fixtures` excludes finished; the swept weight via a
  temporary `config` override) and prints a ρ/MAE/hit table + a recommendation. **Recommend-not-flip** — it never
  sets a weight (the owner commits it, `docs/GW1_RUNBOOK.md`). The weights stay 0 (**xP byte-identical**, the
  invariance holds); the engine is untouched. +18 tests (898→916). Real calibration is the data-gated GW1+ flip.
- **Sprint 137 (2026-08-09)** — *Analytics coverage: feature events, perf timers, a gated admin view* (extends
  **ADR-100**, no new ADR). **US-335:** feature events + `error` at the web sites — `analysis_run` (one site in the
  Squads dispatcher), `squad_created` (the "Use this squad →" click), `squad_saved`/`squad_loaded` (in
  `render_cloud_sync` — **no handle/contents**), `feedback_submitted`, and `error` in the cloud/feedback `except`
  blocks; instrument at the **web layer only** (the engine is untouched). **US-336:** perf timers via
  `analytics.timed` on `data_load` (Squads + Players `Storage` reads), `analysis` (the `select_squad` optimiser),
  and `squad_save`/`squad_load` — timing the **compute/IO, not full renders** (a render raises `RerunException`,
  which `timed` would else record as a failure). **US-337:** the **first analytics read** — `recent_events()`
  (best-effort GET, None on failure) + a **pure `summarise()`** (sessions · devices · returning [2+ distinct
  days] · top pages · event counts · success rate · median/P95 per op) behind `pages/9_Admin.py`, gated by
  **`FPL_ADMIN_KEY`** (inert when unset). Reads via the anon key + an **anon SELECT policy** on `events` (the key is
  server-side; events anonymous). **Anonymity pinned** (no handle/message in any payload). +13 tests (885→898).
- **Sprint 136 (2026-08-09)** — *Beta usage & experience analytics — foundation* (**ADR-100**). An **opt-in,
  anonymous, fail-silent** observation layer over the app (never the FPL model). **US-332:**
  `web_streamlit/analytics.py` — `is_enabled()` (`FPL_ANALYTICS` truthy **and** the store configured),
  `session_id()` (per-session `uuid4`), `track(event, *, page, duration_ms, ok, **meta)` (builds the anonymised
  payload on the main thread, POSTs it **fire-and-forget on a daemon thread**, wrapped so **nothing can raise into
  the app**; a hard no-op when off), `timed(op)` (a `perf` event), `boot(page)` (session_started once + page_viewed);
  the `events` endpoint is derived from `FPL_STORE_URL` (**no new secret**); `config.APP_VERSION`. **US-333:**
  generalised `remember.py` to **named cookies** so an anonymous `fpl_anon` returning-user id rides the verified
  component; `anon_id()` **defers-then-mints** (once the cookie settles) so the loading run can't inflate
  unique-users. **US-334:** `analytics.boot("<Name>")` wired into all 9 surfaces + `docs/ANALYTICS.md` + **the
  guardrail** (a raising store never breaks a page; no write when off → byte-identical). The **3rd** opt-in,
  secret-gated server write (after ADR-094/098) — the read-only invariant names three exceptions, each pinned.
  **Anonymous + minimal:** two random ids, small events, **no PII / no click-mouse-screen tracking / no 3rd-party
  service / no full squad**. +18 tests (867→885). Full event coverage + perf timers + a gated admin view = Sprint
  137; **owner smoke pending** (create the table + set the flag).
- **Sprint 135 (2026-08-09)** — *Confirm on Log out + ☁ Save/Load in the Squads sidebar* (extends **ADR-099** /
  **ADR-094**, no new ADR). **US-329:** `access._confirm_logout()` (`@st.dialog`) — the sidebar "Log out" opens a
  confirm (Log out → `logout()` / Cancel → dismiss) so a mis-click can't reset a device; a `_beta_confirming`
  session flag re-calls the dialog each run so it stays interactive (a `st.dialog` isn't re-opened on the next run
  by the opener alone — and AppTest doesn't auto-persist it). **US-331:** the ☁ cross-device Save/Load moved from
  the My Squad body into `squads.render_cloud_sync()`, called by `render_sidebar()` → it renders in the **Squads
  sidebar** on every sub-view. It **Saves the session's active squad** (`active_squad()` — `squad_picker` doesn't
  make a *demo* active, so **Save is disabled with a hint until you have one**); Load/Clear by handle; secret-gated;
  **moved, not duplicated** (fixed widget keys) with a pointer caption in My Squad. No analytics change; the ADR-094
  opt-in, secret-gated single squad-save write is unchanged. +4 tests (864→867).
- **Sprint 134 (2026-08-09)** — *Fix "remember me" persistence* (corrects **ADR-099**, no new ADR; ✅ owner-verified
  on Safari + Chrome). Tester feedback: the cookie didn't survive a refresh on **Safari or Chrome**. Root
  cause = a **cookie-jar mismatch** — `streamlit-cookies-controller` writes `document.cookie` **inside its iframe**,
  but `remember.read()` read via `st.context.cookies` (the cookies sent to the **Streamlit server on the top-level
  request**), so the read never saw the write. **US-330:** `remember.read()` now reads through the **same
  component** (`_controller().get()`, same jar as `write`) + a new `remember.available()`. The component syncs on a
  **rerun**, so `access._maybe_wait_for_cookie()` gives it one run behind a "🔑 Checking your device…" placeholder
  (one-shot via `_beta_cookie_checked`, gated on `available()` → a headless run / blocked cookies never hang, just
  show the gate). Native-read (`_request_cookies`) reverted. +4 tests (860→864; two set `available()=False` for the
  headless path). **AppTest has no browser → the real proof is the owner re-smoke**; if it still fails, the agreed
  escalation is native `st.login()` (Sprint 134 Option 2). Confirm-on-Log-out (US-329) deferred behind the re-smoke.
- **Sprint 133 (2026-08-09)** — *A "Log out" link* (extends **ADR-099**, no new ADR). Let a tester **reset a
  shared device**: a sidebar control clears the "remember me" cookie + the session and re-shows the gate.
  **US-327:** in `access.py` — `gate_active()` (registration or shared-code configured), `logout()` (set
  `_beta_forgotten`, drop `_beta_ok`/`_beta_email`/`_beta_remember`, queue `_beta_clear`, rerun), `_flush_clear()`
  (render `remember.clear()` once on a clean run — the mirror of `_flush_remember`; a `st.rerun()` after the remove
  would discard it), and a `_beta_forgotten` guard in the cookie-restore helpers so a just-logged-out session
  can't be re-admitted from the still-present native-read cookie (it clears from the browser on the next request).
  **US-328:** `_render_account()` — a sidebar caption ("Signed in as {email}" / "Signed in to the beta") + a
  "Log out" button → `logout()`, wired into `require_access` on the passed branch **and** the cookie-admit run
  (else "Log out" wouldn't show until the next rerun after a refresh). **Off by default** — `gate_active()` False
  (the open deploy) → nothing renders (byte-identical; a test pins it). +8 tests (860). Deferred: a confirm, a
  signed token, `st.login()`.
- **Sprint 132 (2026-08-09)** — *A "remember me" cookie for the beta gate* (**ADR-099** — a client-side
  convenience over ADR-087/098, not a new access path). Kill the friction where **every browser refresh
  re-prompts** for the code/email (`st.session_state` is wiped on a full refresh). **US-325:**
  `web_streamlit/remember.py` — a guarded seam: **read** is native (`st.context.cookies` — the request's cookies,
  available on run 1, so restoring never flashes the gate); **write/clear** lazily import a small cookie component
  (`streamlit-cookies-controller`, the one dependency) inside `_controller()`; every call `try/except` → a
  missing/blocked cookie ⇒ `read()` None / `write`/`clear` no-op. **US-326:** `access.require_access` restores a
  remembered session per mode — `_remembered_code` (skip iff the cookie == the **current** `FPL_ACCESS_CODE` — a
  rotation invalidates it) / `_remembered_registration` (skip iff `is_registered(email)` — a **pruned** tester's
  cookie fails); a stale/absent cookie → today's gate. On a fresh pass the value is stashed in `_beta_remember`
  and the gate reruns; the next clean run does `_flush_remember()` → `remember.write(...)` — **deferred** because a
  `st.rerun()` right after a component `set` discards it. Split the shared-code prompt into `_code_gate`. Cookie
  value = *what proves the pass* (email/code); it grants no new access (re-validated each load) and adds no server
  state (the email already lives in `beta_users`). **Off by default** — empty cookies in AppTest/CI → the gate is
  byte-identical (the 4 access tests unchanged). +13 tests (852). `remember.clear()` = plumbing for a later
  "log out"; native `st.login()` = the deferred hard-auth path.
- **Sprint 131 (2026-09-01)** — *A capped email-registration gate* (**ADR-098** — a new access mode; softens the
  "no accounts" stance without the accounts/auth/paid pivot). Control tester numbers before the ramp: a visitor
  enters the **shared invite code + their email** and is admitted up to a **variable `FPL_USER_CAP`**; at the cap →
  a waitlist note (`FPL_SIGNUP_URL`). **US-323:** `web_streamlit/user_store.py` — a `beta_users(email, created_at)`
  table in the **existing Supabase** (endpoint derived from `FPL_STORE_URL`, reusing the key — no new secret):
  `register(email, cap) → "in"|"full"` (idempotent for a known email; capped for a new one), `count`,
  `is_registered`, `clean_email`; best-effort, reuses `cloud_store.store_error`. **US-324:** `access.require_access`
  gains a third mode by precedence — **registration** (cap set + store configured) → **shared-code** → **open**;
  `_registration_gate` = an `st.form` (code + email) → admit / waitlist / surface a store error; the email is
  session-remembered. **Soft** by design (self-declared email, no verification — the code is the anti-abuse lever;
  the cap is a *registered*-not-concurrent load proxy). **The 2nd opt-in, secret-gated server write** (after the
  ADR-094 squad save) — the read-only invariant names two exceptions; **off by default** (unset cap → today's gate,
  invariance-pinned). Native `st.login()` = the deferred hard-auth path. +10 tests (839).
- **Sprint 130 (2026-08-31)** — *Beta-readiness tidy* (docs + a small UX polish; no analytics, no new ADR).
  **Feedback-relay fix (interstitial):** the form was reporting "sent" on any response — now `feedback.relay_result`
  reads FormSubmit/Web3Forms `{success, message}` and shows the real result; and the form sends an
  **`Origin`/`Referer`** header (`FPL_FEEDBACK_ORIGIN`, default the app URL) so FormSubmit accepts the
  **server-side** POST (its anti-abuse rejects origin-less requests — the "web server" error). **US-320:**
  documented the FormSubmit setup end-to-end in `docs/BETA.md` (the `/ajax/` endpoint, the Origin note + the
  secret, the one-time **Activate Form** click, a Troubleshooting `curl`), closing the doc debt. **US-321:**
  `cloud_store.exists(handle)` (a light select) + the ☁ Save now warns **new vs overwrite** ("overwrote the squad
  already saved under that handle") so a shared handle isn't silently clobbered (ADR-094). +5 tests (827).
- **Sprint 129 (2026-08-30)** — *Build the DefCon opposition magnifier* (owner idea; **ADR-097 refined + built**,
  wired-dormant; a modelling change to `decision_xp`, not a lens). **Persistence reviewed:** cross-device squads
  (ADR-094) is done + dormant — owner-activated via the two Supabase secrets; no build. **The refinement:** the
  baseline already includes a player's DefCon points, so rather than add a component, the magnifier **re-weights
  the DefCon share already in the baseline by fixture** — a **delta** `defcon_pts_per_match · (magnifier − 1)`, 0
  at neutral → no double-count. **US-318:** `analytics/defcon_xp.py::defcon_points_per_match` (`2·P(clear)` from
  `defcon_per90` vs `THRESHOLD`; 0 for GK/no-data) + `defcon_magnifier(FDR difficulty)` (band ~0.5–1.5, neutral at
  mid; a clean-sheet proxy — no odds); `DEFCON_P_SCALE`/band = GW1-calibratable constants. **US-319:** a per-GW
  delta in `player_xp` folded into `by_gameweek` (still sums to xp, ADR-032), gated by
  `config.DEFCON_MAGNIFIER_WEIGHT = 0` (invariance-pinned — the 816 stay byte-identical at 0); `defcon_xp` on the
  row + a weight-aware "🛡 DefCon fixture edge" reason. Verified active: a nailed DEF **+1.0 vs a strong opponent /
  −1.0 vs a weak one**. Calibrate + backtest at GW1. +11 tests (822).
- **Sprint 128 (2026-08-29)** — *CLI catch-up* (surfacing only — no new analytics, no new ADR; the CLI/`ask`
  reach parity with web). **US-316:** a **CLI `chips`** command (`cli.py::cmd_chips`, mirrors `cmd_analyse`) —
  load a saved squad → the horizon `decision_xp` (with `by_gameweek`) → `chip_advisor` + `explain_chips` → the
  existing `ui/chips.py::render_chip_advice`; a `chips` subparser; reuses the one `decision_xp` recipe → the CLI
  advice matches `ask`/web by construction. **US-317:** a **`price`** `ask`/`chat` intent — a prediction-specific
  keyword set (placed first so "who's about to rise?"/"price risers" beat rules' "price rise" + trends' "risers")
  + `_decide_price` ranking the pool by `price_pressure` into likely **risers 🔺 / fallers 🔻** (`price_prediction`,
  ADR-092), grounded (facts/subjects/task, ADR-037), a new `ui/price.py::render_price_movers`; **preseason (flat
  net transfers) → a first-class "live at GW1" message**. A **lens** — never `decision_xp`. +6 tests (811).
- **Sprint 127 (2026-08-28)** — *A Gameweeks box-select + the DefCon magnifier design gate* (owner feedback).
  **US-315:** the Squads "Gameweeks ahead" `st.selectbox(range(1,9))` → a `st.segmented_control([1,2,3,4,5,10],
  default=5)` (a box-select including a **10**-GW wildcard window); the horizon flows through the tab unchanged;
  display only. **ADR-097 (design gate, no code):** the owner's **DefCon opposition magnifier** — a **DefCon-xP**
  component (from `defcon_per90` → `P(clear threshold)`; the prerequisite, DefCon isn't in `decision_xp` yet)
  scaled by a **fixture magnifier inverse to a clean-sheet-probability proxy** (FDR/xGC/Elo — **no betting
  odds**), clamped ~0.5–1.5. Records two traps: clean-sheet vs DefCon points move **oppositely** vs opponent
  strength (separate multipliers), and the **transferred-player** baseline reflects the *old* team (a deferred
  team-share adjustment, cf. ADR-096). A modelling change (not a lens); wired-dormant + auditable; **build +
  calibrate at GW1**. Also **answered** the "in-app email" question (the relay already does it; Proton has no
  free SMTP — no build) and logged all three feedback items. +1 test (805).
- **Sprint 126 (2026-08-27)** — *A gated set-piece xP term* (**ADR-096** — a **modelling** change to `decision_xp`,
  not a lens; wired-dormant so today's numbers are unchanged). **US-313:** `analytics/setpieces.py::set_piece_bonus`
  (a per-90 rate bonus: pens `0.30` > corners/FK `0.10` each, #1 duty only) + `config.SET_PIECE_WEIGHT = 0.0`;
  wired into `player_xp` after the form blend, **only when `rate_source != "hist"`** — the trusted baseline
  already prices an established taker's pens, so the boost applies only to fallback/current tiers (new
  signings/role-changers), never double-counting. At weight 0 every xP is byte-identical (invariance test;
  verified on real data — a weight of 0.5 moved only 3 fallback-tier takers, 0 of 17 hist-tier). **US-314:**
  `player_xp` rows carry **`set_piece_xp`** (the term's share of xp; 0 dormant); `captain_picks` passes the weight
  (dormant → no-op); a weight-aware `explain._penalty_reason` shows **"Penalty taker (+X xP set-piece edge)"** when
  active (the number grounds → a narration verifies, ADR-037), the plain lens reason when dormant. Calibrate +
  backtest the weight at GW1. +10 tests (804).
- **Sprint 125 (2026-08-26)** — *History polish* (display-only on the web History view; `player_history`/
  `decision_xp` untouched; extends ADR-027/060/069, no new ADR). **US-311:** `views/players.py::_delta_cell` — the
  season table's **Δ£** shows an up/down cue (`+0.5 🟢` rise / `−0.4 🔴` fall / `0.0` / `—`). **US-312:** a pure
  `analytics/history.py::align_seasons(hist_a, hist_b, *, key="points")` (outer-join on the season label,
  None-fill) + a **"Compare with (optional)"** selectbox → a side-by-side **season table** (Season · *A* · *B*
  points) + a **line chart** overlaying both season-points series (real past-season data now; the per-GW sparkline
  stays GW1-gated). No selection → the single-player view is byte-unchanged. +3 tests (794).
- **Sprint 124 (2026-08-25)** — *Cross-device squads* — **implements ADR-094**; the **first server-side write**
  from the web edge, so the read-only invariant (ADR-053/054) is deliberately revised: *no local DB/squad-file
  writes; the one server write is this opt-in, secret-gated squad save* (a tested exception). **US-309:** a new
  `web_streamlit/cloud_store.py` — `is_configured()` · `save_squad` (Supabase REST upsert:
  `Prefer: resolution=merge-duplicates`, `{handle, data}`) · `load_squad → dict|None` (`?handle=eq.<h>&select=data`)
  · `delete_squad` · `clean_handle` (lower-case `[a-z0-9_-]`, 2–32 — guards the `eq.` filter); config via
  `access.secret` (`FPL_STORE_URL`/`FPL_STORE_KEY`), best-effort via `api.retry.with_retry`. Guardrail: kept the
  `.save(` scan **and** added `test_cloud_store_squad_write_is_secret_gated` (unset secrets → `is_configured()`
  False, no read, `save_squad` refuses before any HTTP). **US-310:** a My-Squad **"☁ Save / Load across devices"**
  expander (`render_my_squad`, shown only when configured) — a handle + Save/Load/Clear (degrade gracefully) + a
  privacy caption; `docs/CLOUD_SQUADS.md` for the owner Supabase setup. **No login** — the handle is the key
  (hobby-beta trade-off); native `st.login()` = the deferred product path (the adapter interface fits it). Off by
  default (no secrets → the feature is hidden + inert). +10 tests (791); no live network (monkeypatched `requests`).
- **Sprint 123 (2026-08-24)** — *Feedback to your inbox* (owner set up **fpl.assistant@proton.me**; display/link
  + payload-field only — no new server write, the read-only guardrail holds; extends **ADR-087**, no new ADR).
  **⚠️ Constraint:** Proton has no free SMTP, so the app can't send mail directly — two free routes instead.
  **US-307:** a pure `web_streamlit/feedback.py::feedback_mailto(email, message, page, version)` (URL-encoded;
  own module so it's importable/unit-testable past the page's numeric prefix) → an always-available **"✉ Email
  your feedback"** `st.link_button` + a **pre-filled** "✉ Email this feedback" on submit when there's no webhook
  (or a POST fails), addressed to `FPL_FEEDBACK_EMAIL` (default fpl.assistant@proton.me); the dev-only GitHub link
  demoted. **US-308:** the webhook POST gains `_subject` (FormSubmit) + `access_key` when `FPL_FEEDBACK_KEY` is
  set (Web3Forms), so the same `requests.post` works with a **form-to-email relay** or the existing Sheet sink;
  `docs/BETA.md` splits the sink into **1A (Sheet)** / **1B (relay → the inbox)** + a why-not-SMTP note. +6 tests
  (781); `tests/test_feedback.py` covers the mailto builder.
- **Sprint 122 (2026-08-23)** — *Foundations for wider testing* (a **decisions/foundations** sprint — two ADR
  gates + two cheap safeguards; no user-facing feature; the read-only guardrail holds — no server writes landed).
  **ADR-094 (design gate, no code):** cross-device squad persistence via a **handle-keyed Supabase store** (no
  login — the handle is the key), a thin swappable `cloud_store` adapter; **revises the read-only invariant**
  (one opt-in, secret-gated squad write); ~£0; **build gated to Sprint 123**. **ADR-095:** the beta-ops decisions
  — a **prod/staging** two-app split (`master`→staging, `main`→prod-for-testers, promote by merge), **public +
  PolyForm Noncommercial** LICENSE, a **mirror backup**, and an external **uptime monitor** (all ~£0, opt-in).
  **US-305:** a `LICENSE` (PolyForm-NC) + a secret-gated `.github/workflows/mirror.yml` (mirror all refs to a 2nd
  remote, inert until `MIRROR_URL` set) + `docs/BACKUP.md`. **US-306:** the **feedback payload** gains
  `page`/`version`/`ts` (`pages/8_Feedback.py`; `_app_version()` via `importlib.metadata`) + a `docs/BETA.md`
  go-live checklist + a `docs/DEPLOY.md` prod/staging section. +1 test (776); 2 ADRs (→ 95).
- **Sprint 121 (2026-08-22)** — *Finish the fixtures planner: a budget cap + value on the targets* (display only;
  extends `analytics/targets.py` + the Fixtures page; reuses ADR-041 xP + ADR-042 value — no new ADR). Both stories
  make **🎯 Target by fixtures** budget-aware. **US-303:** a `max_price` param on `target_by_fixtures` drops
  players over the cap **in the grouping loop, before** the per-team top-K pick (so a cap surfaces the best
  *affordable* name, not a truncation); a `st.slider("Max price", 4.0, 15.5, 15.5)` on the page. **US-304:**
  `sort_by` ("xp"/"value") + `value_by_id` params — the per-team ranking key switches to `value_by_id` when
  sorting by value, and every row carries `value`; the page builds `value_by_id` from `points_per_million(
  total_points, price)` (the app's one **Val/£m**, ADR-042), adds a **Val/£m** column and a
  `st.segmented_control("Sort", ["xP","Val/£m"], default="xP")`. One value definition across the app (no new
  metric); `team_fdr`/`decision_xp`/`points_per_million` unchanged. +4 tests (775).
- **Sprint 120 (2026-08-21)** — *Fixtures for planning: target players by run + a "my squad" lens* (display
  lenses; a new `analytics/targets.py` + **realises ADR-049**; no analytics change — owner feedback: the Fixtures
  view is needed for planning a new squad / wildcard). **US-301:** a pure `analytics.target_by_fixtures(team_ranked,
  players, xp_by_id, *, position, top_teams=6, per_team=3)` — for the easiest-run teams (`team_fdr`, easiest-first)
  it takes each team's **available** players (`is_unavailable` dropped; a *doubtful* player stays with its
  `fit_flag`), ranks by the one **`decision_xp`** metric (ADR-041), keeps the top `per_team`. Wired into
  `pages/2_Fixtures.py` below the ticker as a **🎯 Target by fixtures** section: a **Position** `st.segmented_control`
  → a `st.dataframe` (Team · FDR · Next · Player · Pos · £m · Own% · Fit · xP) over the same weeks window. Turns
  "which teams have a good run" into "who to buy". **US-302:** an **All teams / My squad** scope toggle above the
  ticker — on *My squad* it reads `active_squad()`, maps `player_ids → team` (a `Counter`), filters the ticker rows
  to the owned teams and adds a **"Players"** count column (the shading path unchanged); no squad → a note + a
  fall-back to all teams. Brings the ADR-049 team lens (already in `ask`/`chat` via **ADR-067**) to the **web
  ticker**. Display-only; `team_fdr`/`fixture_ticker`/`decision_xp` unchanged. +5 tests (771).
- **Sprint 119 (2026-08-20)** — *My Squad edit: a position filter + an affordable check* (edit-UI only; extends
  **ADR-055** (the editable squad); no analytics change). Both stories live in `web_streamlit/views/squads.py`'s
  "Swap a player" expander (`render_my_squad`). **US-299:** a `st.segmented_control("Position", ["All","GK","DEF",
  "MID","FWD"], default="All")` at the top scopes the **"Replace"** options to `owned` of that position (sorted by
  position then name), with a *"No {POS} players in your squad."* caption when it empties; the "With" candidates
  already key off the picked player's position, so they follow. **US-300:** `bank = FPL_BUDGET − sum(owned
  prices)` shown as a `st.caption("Bank: £X.Xm")`, plus a `st.checkbox("Affordable only")` that filters the
  **"With"** candidates to `price ≤ out.price + bank` (a *pre-filter* — `apply_transfer` still enforces the budget
  on **Swap →**), with a *"No affordable replacement (≤ £X.Xm) — untick to see all."* caption when the filter
  empties a non-empty list. Edit-UI only (no `apply_transfer`/`decision_xp` change); the session-only edit model +
  read-only web guardrail hold. +2 tests (766).
- **Sprint 118 (2026-08-19)** — *History on the web (+ a price column)* (display only; extends ADR-027/060 +
  ADR-069; no analytics change). **US-297:** `analytics/history.py::player_history` season rows now carry
  `start_cost`/`end_cost` (already £m — the ingest converts tenths) + `change` (`round(end−start,1)`, `None`
  when absent); `ui/history.py::render_player_history` gained a `£m` column (`£start→end`), so the CLI + Ask
  history show a season's price move. **US-298:** a new `web_streamlit/views/players.py::render_history(rows,
  photos, badges)` — a player `st.selectbox` → an on-demand `Storage` read (`get_history_past`/`get_history`) →
  `player_history` → a photo/name header, a native **season `st.dataframe`** (Season · Pts · Mins · Starts ·
  Pts/90 · xGI · xGC · £ start · £ end · Δ£, via the shared `column_config`) + a per-GW `st.line_chart` when
  data exists, else a "fills at GW1" caption; degrades to a "run `history --backfill`" note. Added as a
  **"History"** option on the Players `st.segmented_control`. Native Streamlit (no bespoke CSS, no design
  sign-off — unlike the captain card); display-only, a short-lived read (no server writes). The history feature
  is now complete across CLI · Ask · web. +2 tests (764).
- **Sprint 117 (2026-08-18)** — *A `history <player>` view: past seasons now, per-GW at GW1* (a read-view over
  data we already ingest; extends ADR-027/060 + ADR-037; no analytics change). **US-295:** a pure
  `analytics/history.py::player_history(player, seasons, gameweeks)` → `{player, seasons, gameweeks}` (normalised
  past-season rows with **Pts/90** + this-season per-GW rows; empty-safe — a lens, never xP) + `ui/history.py::
  render_player_history` (a season table + a per-GW trend, or a "fills once the season starts (GW1)" note); the
  CLI `history` command gained a positional `<player>` (`_resolve_player`: exact web_name wins, else a unique
  substring; ambiguous/none → a clear message) → the view, while `history --backfill` still runs the ingest.
  Real past-season data now (`player_history_past`, 2019 rows); the per-GW half lights up at GW1. **US-296:** a
  grounded `history` intent (`_INTENT_KEYWORDS`, after `worth`) + `ask._decide_history` — resolves the named
  player (`_match_players`), renders the view as `detail`, and puts the last season's pts/mins/xGI + the season
  count into `facts` so a narrated number verifies (✓, ADR-037); degrades on ambiguous/absent/no-backfill;
  inherited by the Ask tab + CLI `chat`. +11 tests (762). *(An accidental overwrite of the existing
  `tests/test_history.py` ingestion tests was caught via the suite count + restored; the new view tests live in
  `tests/test_history_view.py`.)*
- **Sprint 116 (2026-08-17)** — *Two feedback fixes + a web-native Captain Pick card* (fixes + display;
  US-294 extends ADR-084 + ADR-089). **US-293:** (a) **pinned `streamlit==1.61.1`** in `requirements.txt` so the
  Community Cloud deploy matches the tested version — the likely fix for "hover-overs stopped working" (the
  ADR-065 `help=` coverage test passes; the pitch CSS is scoped, so no code regression); (b) `cli.py::cmd_reseed`
  now captures + prints `n_elo` (*"…and N Elo ratings (ClubElo)"* / *"kept last-known"*) — `reseed` always
  called ClubElo via `refresh`→`_refresh_elo`, only the printout dropped the count. **US-294:** a new
  `web_streamlit/captain_card.py` (the `pitch.py` pattern) — a pure `captain_card_html(ranked, explanation, *,
  scope, team_names)` + `render_captain_card` that `st.markdown`s one self-contained HTML/CSS block: the 🥇 pick
  (Team·Pos + a projected-xP chip) · a Confidence·Band pill (green/amber/red) · Why (✓) / Risks (⚠) columns ·
  Alternatives (🥈/🥉), theme-neutral (scoped `.cap-card`, rgba-grey neutrals, text inherits), every value
  `html.escape`d, no JS. The web **Captain** view renders it in place of the mono `render_captain_picks` block
  (the rich picks table stays above; the mono renderer stays the CLI surface); reuses `explain_captain` — no
  analytics change. A faithful Artifact preview (both themes) was owner-approved. +5 tests (751).
- **Sprint 115 (2026-08-16)** — *Signal feeds: a media-headlines lens + sharper "talked about"* (owner intake;
  **ADR-093**, display lenses — never xP). Reviewed ~12 external sources; adopted the public, no-auth,
  FPL-relevant **RSS/Atom** feeds and deferred scraping/auth/odds. **US-291:** `api/feeds.py` — a best-effort
  `MediaFeedsClient` (our UA, tight timeout, retry-once, raise → the caller degrades) + a pure
  `parse_feed(xml, limit)` handling **both** RSS `<item>` and Atom `<entry>` with stdlib `ElementTree`
  (**no new dependency**; empty-safe). `web_streamlit/media.py::media_headlines` aggregates `config.MEDIA_FEEDS`
  **per-feed** (a failing/empty feed is skipped). The **News** tab gains an opt-in **Headlines** section —
  button-gated, `st.cache_data(1800)`, grouped by source, links out; **Fantasy Football Scout** + **BBC
  Football** shipped active (YouTube via a documented `MEDIA_FEEDS` slot + `MEDIA_YOUTUBE_URL` — the sandbox
  couldn't resolve a channel-id). **US-292:** `RedditRssClient.get_top_weekly()` (the `top/.rss?t=week` variant,
  `config.REDDIT_TOP_WEEK_URL`) powers a button-gated, cached **"🔥 Top discussions this week"** list beside the
  buzz counter on **Trending**, reusing `parse_feed`. All best-effort (cache + gate + degrade); no server
  writes; **no live network in tests** (fixtures + a fake client). +7 tests (746).
- **Sprint 114 (2026-08-15)** — *Four-tier ownership badges: one ownership language* (tester feedback;
  display/lens, extends ADR-057 + ADR-089; no analytics change). **US-289:** a pure
  `analytics/crowd.py::ownership_tier(player)` → **💎 differential** (≤5%) · **⭐ popular** (5–20%) · **🟦
  template** (20–60%) · **👑 essential** (>60%), via `DIFFERENTIAL_OWN`/`TEMPLATE_OWN`/new `ESSENTIAL_OWN=60`;
  `crowd_flags` swaps its 2-tier 🟦/💎 block for it, so the four tiers propagate to every Trends-column surface
  (Pool · Build · Analyse · My Squad pitch · Captain · Trending) and each player shows exactly one tier (the
  5–20% band was previously unbadged). `CROWD_LEGEND` rewritten to the four tiers; still a **lens** (the
  `decision_xp` invariant holds). **US-290:** `ownership_label(player)` (the tier word) drives a shared
  `explain.py::_ownership_signal(row)` → a **(✓ reason, ⚠ risk)** pair (essential/template → ✓ · differential →
  ⚠ · popular/absent → neither), used by `explain_captain`/`explain_transfer`/`explain_worth`, so the "why"
  speaks the same language as the badges (Haaland reads *"Essential (74% owned)"*). The Trending page + Pool
  inherit the rewritten legend; Help updated. +1 net test (739); the now-unused `TEMPLATE_OWN` import was dropped
  from `explain.py`.
- **Sprint 113 (2026-08-14)** — *A robust Ask scroll + an explained differential shortlist* (tester feedback;
  display/rationale, extends ADR-052 + ADR-042/061; no analytics change). **US-287:** the Ask example-click
  auto-scroll ("worked for some, not all") replaced its single `setTimeout(…, 150ms)` **smooth** scroll with a
  **multi-tick instant** one — `[50,200,450,800].forEach(d => setTimeout(scrollToBottom, d))` — still carrying
  the `/*turn N*/` per-turn token, so it lands reliably after the example expander collapses + late layout and
  Streamlit's scroll-restore can't override it mid-animation. **US-288:** `_decide_shortlist` (differential
  branch) builds a grounded **"Why a differential?"** lead (rank-lever benefit + variance trade-off) and
  `ui/shortlist.py` gained `_pick_signals(row)` (nailed/rotation ~N mins · set-piece duty · in form) + a
  `rationale=` param on `render_shortlist` that prepends the lead + a per-pick *Standout signals* block for the
  top 3. The **plain** shortlist is byte-identical (no rationale); the per-pick signals live in the grounded
  **detail**, not the LLM facts, so the answer still verifies (✓, ADR-037). +1 net test (738).
- **Sprint 112 (2026-08-13)** — *Price Change Predictor (a directional lens, wired dormant → GW1)* (owner
  intake; **ADR-092**, a display/analytics lens — never xP). **US-285:** a pure `analytics/price.py`:
  `price_pressure(player)` = `net_transfers(player) ÷ selected_by%` (signed; `None` when either is absent; **0**
  on flat preseason data), `price_prediction` → rise/fall/stable via module thresholds
  `PRICE_RISE_PRESSURE`/`PRICE_FALL_PRESSURE` (calibrated at GW1), and `price_flag` → 🔺/🔻/"" (a **distinct
  forward-looking** marker, not the retrospective crowd 💰↑/💸↓ which reads `cost_change_event`). Dividing by
  ownership makes players comparable **and** the constant total-manager count cancels for direction + relative
  magnitude, so no `total_players`/ingest/schema change is needed (an absolute "% to change" would need it — a
  GW1 refinement). Reuses `net_transfers`; exported from `analytics`. A `decision_xp` **invariance** test (force
  5M net-in → 🔺 fires) shows xP is identical — the lens never leaks into the recommendations. **US-286:** a
  **Price** column on the Players Pool (`views/players.py`, via `price_flag`) with `PRICE_LEGEND` (tooltip +
  caption) + an honest "live from GW1" note, and a My Squad transfer-timing **nudge** (`views/squads.py`) naming
  owned players predicted to fall (*sell before the change*) / rise (*hold, or buy now*), with a dormant note
  preseason. Display-only; the read-only web guardrail holds. +7 tests (737).
- **Sprint 111 (2026-08-12)** — *Ask tab polish: readable rules, reliable scroll, an explained "worth"* (tester
  feedback; display/explainability, extends ADR-085/052/089/061; no analytics change). **US-283a:** the
  multi-item rules facts (chips · scoring · clean sheets · leagues) are authored with embedded bullet lines;
  `ui/rules.py::render_rules` prints a multi-line fact **verbatim** (a single-concept fact stays one `•`), blank
  line between facts — so a list reads item-per-line. The `fact` keeps the same numbers/names, so `match_rules`
  + the verifier are unchanged (still ✓). **US-283b:** the `4_Ask.py` scroll nudge embeds a **`/*turn N*/`**
  token (`len(history)`) so it's unique per turn — Streamlit re-runs a component only when its inputs change, so
  the static US-275 iframe didn't re-fire on later turns and the example-button path never scrolled (typing used
  `st.chat_input`'s native scroll); now the `scrollTo(bottom)` runs on every answer. **US-284:** a new
  `analytics/explain.py::explain_worth(row, *, value, median, rank, n_peers, xp, horizon)` + a documented
  `worth_confidence` (value-vs-median ratio, then the rank percentile, + a penalty nudge) build a grounded ✓ Why
  / ⚠ Risk (projects N pts · above/below the position median · top-third / mid-pack value · penalty taker ·
  set-pieces · template · premium-price / big-differential) for a value verdict; `_decide_worth` renders
  `detail = verdict + render_explanation(ex) + MODEL_NOTE` (so it explains without Ollama) and puts
  confidence/why/risk into `facts` so a narrated number verifies (ADR-037). Same pattern as captain/transfer;
  the verdict/rank/median engine is unchanged. +4 tests (730).
- **Sprint 110 (2026-08-11)** — *Chat robustness: remembered context + a bigger rules KB* (owner steer;
  **ADR-091** + extends ADR-085; no analytics change). **US-281:** a new `src/chat_context.py`
  (`save_context`/`load_context`/`clear_context`) persists one `Context` ↔ a **local, git-ignored** JSON
  (`config.CHAT_CONTEXT_PATH`) with a **timestamp + 2h TTL** — best-effort (stale/missing/corrupt/shape-drift →
  `None`, never a crash; `now`-injected for deterministic tests). The CLI `cmd_ask` loads → `converse` → saves
  (so *"ask …"* then a separate *"ask why?"* resolves), with `--forget` + a *"forget"/"reset"* word to clear;
  `cmd_chat` seeds the REPL with the saved context and persists each turn. `chat_transcript` gained a `context=`
  seed and now yields `(result, context)` (its one test updated). The pure `ask.answer`/`converse` API is
  unchanged (persistence is a CLI wrapper), and `web_streamlit` **never imports the store** — it keeps
  per-session `st.session_state` (a guardrail test asserts it, anchored on the import/calls, not the
  same-named session_state key). **US-282:** `fpl_rules.py::RULES` grew **13 → 21** (flags · preseason_transfers
  · chip_limits · bench_points · wildcard_timing · leagues · ranking · team_value), `TOPIC_LABELS` to 21, and —
  crucially — the `rules` **routing cues** were extended with specific phrases (`yellow flag`, `two chips`,
  `how many wildcards`, `head to head`, `selling price`, … + `what does`) that win over the squad intents
  without hijacking them, so each new question routes to `rules` and **verifies ✓** from the KB rather than
  falling to free-form. +10 tests (726).
- **Sprint 109 (2026-08-10)** — *Captaincy scopes to your squad by default + a clear "best overall"* (tester
  feedback; **ADR-090**, routing/display only). A tester found *"who should I captain from my-team?"* answered
  from **all** players. Root cause: `ask._fresh` resolved "my team" via `re.search(r"\bmy (team|…)\b")` — which
  matches a **space** but not the **hyphen** the app's own example prompts use. **US-279:** one rule replaces
  the phrase-match — `if not squad and intent in _SQUAD_DEFAULT_INTENTS and active_squad and not
  _EXPLICIT_GLOBAL.search(question): squad = active_squad["name"]` — so with a squad loaded, a squad-scoped
  question with no named squad and no explicit-global cue (`all players|everyone|best overall|from all|any
  player`) **defaults to the loaded squad**. Fixes the hyphen at the root, makes a bare *"who should I
  captain?"* scope to your team, keeps captaincy's global best-picks mode via the explicit cue, and is gated to
  the squad intents (captain·transfer·analyse·start_bench·gameweek·chips) so a global *fixtures*/compare
  question isn't scoped. The CLI has no `active_squad`, so it's global-by-default (unchanged). **US-280:**
  `render_captain_pick` gained `heading` + `nudge` — `_decide_captain` sends the global answer as **"Best
  Captain Picks · all players"** + a scope nudge and the scoped one as **"Captain Pick · from squad 'X'"**, so
  the default is never silent; the Ask example buttons personalise to the loaded squad's name
  (`example.replace("my-team", _active["name"])`). No analytics change; +3 tests (716). A routing test isolates
  `SquadStore` to a temp file (its default path binds at import, so ambient saved squads would otherwise leak).
- **Sprint 108 (2026-08-09)** — *A structured "Captain Pick" answer + a shared Model note* (tester feedback;
  display-only, extends **ADR-089**). **US-277:** the captaincy answer is now the tester's mockup — a new
  `ui/captain.py::render_captain_pick(ranked, explanation, *, scope, team_names)` builds a card: header + scope ·
  🥇 pick (`Team · Pos` via a `short_name→name` map from `get_teams` · `Projected: N pts`) · a clean
  `Confidence: NN/100 (Band)` · Why ✓ / Risks ⚠ · **Alternatives** 🥈🥉 (+xP) · a Model note. The wording lives at
  the single source (`explain_captain`: "Penalty taker", "Set-piece involvement", "Expected ~N mins", "Strong
  fixture vs {OPP}", "Only +{gap} pts ahead of {name}", "Highest projected points" without the redundant number).
  `_decide_captain` renders it, so CLI `ask`/`chat` + the web Ask tab inherit it; the facts still feed the
  verifier (✓). **US-278:** a shared `ui/explain.py::MODEL_NOTE` (the "analytics decide, AI explains" attribution
  + the folded "heuristic, not a probability" caveat) closes **all five** explained answers **once** — captain
  (via the card), transfer + build (appended in `_decide_transfer`/`_decide_build_squad` + the web Build page),
  chips (`render_chip_advice` when confidences) and the gameweek plan (`render_gameweek_plan` when explained,
  once at the foot — never inside the composite). `render_explanation`'s confidence line went clean
  (`NN/100 (Band)`); `explain_transfer` phrasing aligned. The **CLI `captain` + web Captain tab** now render the
  same card — `render_captain_picks` was refactored to **delegate** to `render_captain_pick` (retiring the old
  mono shortlist table + its `ui/_table`/`expected_minutes` machinery; the web keeps its rich photo table above
  the card; Alternatives grow past 🥈🥉 with plain "N." so `captain --limit N` still lists N). No analytics
  change; +5 net tests (713).
- **Sprint 107 (2026-08-08)** — *Ask readability + a "fit" ✅ emoji* (tester feedback; display-only, extends
  **ADR-052/074**). **US-275:** the Ask answer renders with `st.code(answer, language=None, wrap_lines=True)` so
  long narration wraps while the aligned tables / plan / Why-Risk blocks stay readable; after the history
  replays, a `height=1` same-origin `st.iframe` runs `window.parent.scrollTo(…, behavior:'smooth')` in a
  `setTimeout` (wrapped in try/catch → no-ops if ever cross-origin) to bring the newest Q&A into view. **US-276:**
  a new `analytics/crowd.py::fit_flag(player)` = `availability_flag(player) or "✅"` — a fit player now reads **✅**
  instead of a blank cell across the Pool + the stat boards (`views/players.py`) and the CLI `ui/table.py` /
  `ui/xg.py`. Crucially `availability_flag` is **unchanged** (still `""` for a fit player): its emptiness doubles
  as the "is this player a concern?" truthiness test the who's-flagged logic relies on (My Squad's caption, the
  gameweek-plan flags), so a *separate* display helper keeps the Fit column positive **and** that logic intact;
  `AVAILABILITY_LEGEND` now leads with "✅ available". No engine/analytics change; +1 test (Fit-column
  assertions strengthened to expect ✅).
- **Sprint 106 (2026-08-08)** — *Explainability for the AI Tips gameweek plan* (extends **ADR-089**; owner
  request) — the last major decision to get it. **US-273:** `gameweek_plan` runs the captain with `limit=3` and
  returns `captain_ranked` (additive) so the captain explanation has a runner-up. `analytics/explain.py::
  explain_gameweek(plan, players_by_id, xp_by_id, *, horizon)` → `{captain, transfer, lineup, overall}` —
  **reuses** `explain_captain` (on `captain_ranked`) + `explain_transfer` (on the plan's move + the buy's row),
  adds a grounded lineup rationale (*"Start X over Y — higher projected xP: a vs b"*). `ui/gameweek.py::
  render_gameweek_plan(explanation=…)` appends `· Confidence NN/100 · Band` + a compact Why to the captain +
  transfer lines and the lineup line. **US-274:** `gameweek_confidence(captain_conf, n_flags)` (captain-driven,
  −8 per flagged player) + an **overall** `Explanation` (Why = clear captain / a positive-gain upgrade / lineup
  tweaks / no-change; Risk = the flagged players); `render_gameweek_plan` prepends it as a top-of-plan
  Confidence · Why · Risk block, and `_decide_gameweek` puts confidence/why/risk into `facts` so a narrated
  number verifies (ADR-037). `explain_captain`/`explain_gameweek` hardened to tolerate a missing id. Mostly
  reuse — no new heuristics beyond the plan-level confidence; no engine change; the web AI Tips view inherits it
  (routes through `ask.answer`). +2 tests. **Explainability now covers every decision the tester named.**
- **Sprint 105 (2026-08-07)** — *Explainability for squad-build & chips* (extends **ADR-089**; owner request).
  **US-271:** `analytics/explain.py` — `squad_confidence(xi_reliability, spent_fraction)` (documented:
  `100·(0.7·reliability + 0.3·spent)`) + `explain_squad(selected, xp_by_id, weight_by_id, *, budget, xi_ids,
  horizon)` → ✓ (optimised on xP · XI projects N · spent £X of £Y · top picks · a playing bench) + ⚠ (£ unspent
  · rotation-risk starters · doubtful in the 15 · differential-heavy · weak bench). `_decide_build_squad`
  computes it, puts confidence/why/risk into `facts` (narration verifies), prepends `render_explanation` to the
  `detail`; the Build page shows it above the pitch. **US-272:** `chip_advisor` exposes a per-chip **`margin`**
  (a `_gap` helper — how clearly the recommended GW/window beats the next-best: TC/BB by the max, FH/WC by the
  min); `chip_confidence(margin, value)` (a **relative** separation — margin ÷ the chip's own value, so one
  formula spans TC ceilings / BB totals / FH-WC XI-xP; ≥15% → High, near-flat → Low) + `explain_chips(advice)`;
  `ui/chips.py::render_chip_advice(confidences=…)` appends `· Confidence NN/100 · Band` per chip; `_decide_chips`
  wires it in (+ facts). The web Chips view inherits it (it routes through `ask.answer`). Preseason the weeks
  are near-uniform → all chips honestly read **Low**, sharpening in-season. Every confidence + reason is
  computed from the data; no engine change; +5 tests.
- **Sprint 104 (2026-08-07)** — *Explainability in Ask — Why · Risk · Confidence*, per **ADR-089** (US-269/270;
  tester feedback). **US-269:** `analytics/explain.py` (pure) — an `Explanation` (reasons ✓ · risks ⚠ ·
  confidence · band); `captain_confidence(...)` a **documented, transparent** heuristic (`100·(0.45·plays +
  0.40·clearness + 0.15·fixture) + penalty`, clamped 1–99, capped by chance when doubtful — `clearness` = the
  xP lead over the runner-up, so a coin-flip self-tempers); `confidence_band`; `explain_captain(picks,
  players_by_id)` builds the grounded ✓/⚠ from the pick + player rows (xP · penalties · set-pieces · xMins ·
  ownership · fixture · form), gated-zero signals omitted. `ui/explain.py::render_explanation` is the shared
  Confidence·Why·Risk block. `_decide_captain` sets a self-contained `detail` (scope + block) and puts
  confidence/why/risk into `facts` so a narrated number still **verifies** (ADR-037); wired into Ask, the web
  Captain tab, and the CLI `captain`. **US-270:** `transfer_confidence` (scales with the XI-gain margin; capped
  by a doubtful buy) + `explain_transfer(move, in_row)` (✓ +gain to the XI · higher xP · penalties · set-pieces
  · frees cash · template; ⚠ costs £ · selling the out player · doubtful buy · big differential · marginal
  gain), wired into `_decide_transfer`. **Every reason and the number are computed from the data — the LLM only
  phrases them (still verified); an explanation can't be a hallucination.** No engine change; `explain` reads
  the signals a decision already computed; confidence is a heuristic (not a probability), gated signals (form ·
  % of team goals · opponent xGC) light up at GW1. +7 tests.
- **Sprint 103 (2026-08-07)** — *Deadline countdown enhancements* (owner request; all four picked).
  **US-267 (extends ADR-086):** `analytics/deadline.py` — pure `deadline_urgency(time_left)` (calm >24h · today
  <24h · imminent <2h) + `gameweek_context(fixtures, gameweek)` (`{matches, first_kickoff}`, empty-safe).
  `ui/deadline.py::deadline_banner` now **escalates** (⏳ → 🟠 → 🔴, with a *· N matches · first kick-off …*
  clause), and a shared `deadline_line(fixtures, now)` → `(gameweek, deadline, text, urgency)`. Home picks the
  widget by urgency (`st.info`/`warning`/`error`) + a `st.page_link` nudge to Squads when close; Squads a
  compact caption. **US-268, per ADR-088:** `web_streamlit/countdown.py::countdown_html(gw, deadline, now,
  urgency)` — a self-contained HTML/CSS + `setInterval` **Days:Hrs:Mins:Secs** clock (urgency-coloured; cells
  **server-filled** so it's readable without JS; ticks client-side off the embedded deadline ISO, stops at 0);
  `render_countdown` embeds it via **`st.iframe`** (JS-enabled — the modern replacement for the deprecated
  `components.v1.html`). The **first client-side JS** in the app — one self-contained block, no external
  scripts, only our own ISO/int embedded, display-only; the US-267 text line is the no-JS fallback beneath.
  On Home the clock is the hero. All logic is pure + `now`-injected → deterministic tests (the clock's HTML,
  not its JS). No engine change; no server writes. +7 tests.
- **Sprint 102 (2026-08-07)** — *Beta enablement — an opt-in access gate + feedback capture*, per **ADR-087**
  (US-263/264; owner "beta-setup sprint"). **US-263:** `web_streamlit/access.py` — a safe `secret(key, default)`
  (try `st.secrets` → except → `os.environ` → default; `st.secrets` *raises* without a `secrets.toml`, so it's
  read inside try/except) + `require_access()` (a no-op unless **`FPL_ACCESS_CODE`** is set; else a 🔒
  private-beta prompt that `st.stop()`s the page until the code matches, remembering success in
  `st.session_state`, then `st.rerun()`), called right after `st.set_page_config(...)` on **all 8 pages**. A
  *shared* code — no accounts, no server state. **US-264:** a **📣 Feedback** page — an `st.form` that on submit
  POSTs `{message, email, source}` to **`FPL_FEEDBACK_WEBHOOK`** (best-effort, 6s timeout, try/except),
  **degrading to a GitHub-issue link** when the webhook is unset or the POST fails; a **"✋ Join the beta"**
  `link_button` to **`FPL_SIGNUP_URL`** (Home + Feedback, shown only when set) for the founding-tester email
  list; `docs/BETA.md` is the owner runbook (secrets · a Google Apps Script sink · a signup form · recruiting ·
  comps). **All opt-in via secrets, off by default** — the public deploy + CI are unchanged until configured
  (a test pins `secret()` never crashing + the gate open-when-unset / block-then-unlock). The only outbound
  write is the feedback POST to the owner's *own* sink — no user data is persisted on our infra, so the
  read-only guardrail (`no .save(`) still holds. Accounts/DB/payments deferred (DIRECTION §1). +6 tests.
- **Sprint 101 (2026-08-07)** — *Pitch on Build + a season countdown / deadline banner* (owner request).
  **US-261 (pitch on Build; reuses ADR-084):** `views/squads.py::render_build` splits the built 15 into the XI
  (`best_legal_xi`) + bench, orders the bench via `bench_order`, builds a `next_opp` map (`team_schedule`), and
  calls `render_pitch(..., captain_id=None)` **above** the sortable table + `render_squad` block — the picture
  *and* the detail; display-only, no engine change. **US-262, per ADR-086:** a pure
  `analytics/deadline.py::next_deadline(fixtures, now)` derives the next FPL deadline from the stored
  `kickoff_time` — each gameweek's **earliest** kickoff − 90 minutes, returning the first `(gw, deadline)`
  still ahead of `now` (so it **rolls forward** once a gameweek locks); tz-aware, empty-safe. **No `events`
  ingest** — the derivation matches the API's `deadline_time`, and `storage.get_upcoming_fixtures` just adds
  `f.kickoff_time` to its SELECT (additive). `ui/deadline.py::deadline_banner(gw, deadline, now)` formats a
  days/hours countdown + the date in **UK time** (stdlib `zoneinfo`). Shown as a prominent `st.info` on **Home**
  and a compact caption on **Squads**, each passing `datetime.now(timezone.utc)`; `now`-injected so the logic is
  deterministically tested (incl. roll-forward + UK-time). No engine change; no server writes. +7 tests.
- **Sprint 100 (2026-08-07)** — *AI Chat Assistant — a grounded rules KB + a labelled free-form mode*, per
  **ADR-085** (US-259/260; owner intake). **US-259:** `src/fpl_rules.py` — a `RULES` list of **13** authoritative
  `{topic, cues, fact}` entries (scoring · clean sheets/saves · bonus/BPS · Defensive Contribution · chips ·
  transfers/hits · price changes · squad rules · formations · captaincy · auto-subs · deadline · DGW/BGW) +
  a pure `match_rules(question)`. A **`rules`** intent placed **first** in `_INTENT_KEYWORDS` on *question-
  shaped* cues (how does / how do / what is a / how many points / when is the deadline / defensive contribution
  …) that don't collide with the (imperative / squad-scoped) squad commands; `_decide_rules` selects the KB
  facts → narrated + **verified** (✓, ADR-037) via the existing `assemble`/`verify_grounding` path, degrading
  to the raw facts (`ui/rules.py::render_rules`) without a model. Rules come from the **curated KB, not the
  LLM's memory** — which hallucinated chip facts this session (the verifier caught it). **US-260:** a **free-
  form** tail — `assemble` gains a `{"free_form": True}` branch that asks the LLM a *scoped* general question
  (`_free_form_prompt`: rules/tactics only, **never** a specific player/pick) and returns
  `trust={"free_form": True}`; `_trust_line` gains a third state **ℹ "General FPL advice — not checked against
  your data"** (beside ✓/⚠); no model → the `_FALLBACK` help. Both fallbacks funnel here: an unrecognised
  question (`route()==None` → intent `"chat"`) and a rules-shaped question with no curated fact
  (`_decide_rules` no-match). The **Ask** tab + CLI `chat` inherit it (they already call `converse`) — plus two
  rules example prompts + an intro caption naming the three answer types. Grounded squad/player questions +
  `decision_xp` unchanged; no server writes. +9 tests.
- **Sprint 099 (2026-08-07)** — *My Squad pitch redesign (FFH-style)*, per **ADR-084** (US-257/258; tester
  feedback: *"looks like a poor cousin — redesign closer to Fantasy Football Hub"*). **US-257:** `web_streamlit/
  pitch.py::render_pitch` is rewritten to emit **one self-contained HTML/CSS block** via
  `st.markdown(unsafe_allow_html=True)` — a **green pitch** (mow-stripe `repeating-linear-gradient` + a faint
  centre circle, inset border) with **formation rows** (GK/DEF/MID/FWD) + a **bench strip**; each player a
  **kit card** (`_kit_html`): the photo/club-shirt `<img>` (or a 👕 placeholder), the name, an **xP chip**,
  **£m · next opponent (H/A)**, and the **crowd + set-piece flags**. Every text value `html.escape`d; the lines
  are unindented so Markdown doesn't treat the HTML as a code block; relative units + `flex-wrap` reflow it; a
  green surface + light cards read on both Streamlit themes; no JS. **US-258:** the **(C)** captain armband
  (`.c-badge`) and the **sub-number** badge (`.s-badge`, 1/2/3/GK, `title` = the full role) are overlaid on the
  kit via a positioned `.pic` wrapper; a hover-lift (respects `prefers-reduced-motion`) + spacing polish. The
  pitch stays **display-only** — every edit control (swap/reorder/rename/download) is a separate widget, so
  `render_pitch`'s signature is unchanged and interactivity is untouched. Verified Streamlit 1.61.1 keeps the
  `<style>`/`<div>`/`<img>` and the HTML is inspectable via `AppTest.markdown` — the 3 pitch-content tests were
  rewired from `st.caption` to the HTML blob. Replaces the informal Sprint-062 native-card-grid "no custom CSS"
  call. No data/engine change; no server writes. A faithful Artifact preview (real squad + SVG jerseys for the
  CSP-blocked CDN) gave the owner a visual sign-off.
- **Sprint 098 (2026-08-07)** — *Club-shirt image fallback + captain double-points* (tester feedback).
  **US-255 (no ADR — display mechanics):** ~a quarter of players carry a valid photo `code` but the CDN **403s**
  the file, so `web_streamlit/badges.py::photo_url_by_id(players, teams)` now returns the **photo when served,
  else the club shirt** (`shirt_{team_code}[_1]-66.png`, GK variant by position) via a **cached** existence
  sweep `_missing_photo_codes` (threaded HEADs, short timeout) that **degrades to "all present"** on any error;
  `teams` threaded through the Players/Squads/Trending/News pages. The bootstrap `photo` field is `{code}.jpg`
  for everyone (no signal), so an existence check is required — kept in the edge (cached, one first-load sweep)
  and **out of the test suite** via an autouse `conftest.py` fixture that patches the sweep. **US-256, per
  ADR-083:** the My Squad **"Projected XI (N GW)"** summary now adds the captain's **×2 for the next GW only**
  — a pure `web_streamlit/squads.py::captain_bonus(captain_id, xi_ids, by_gameweek_by_id, next_gw)` returns the
  captain's next-GW xP (from `by_gameweek`, ADR-032) when the captain is set **and in the XI** (benched/unset →
  0); `render_my_squad` folds it into the total, reframes "Captain (2×)" to next-GW doubled, and shows a
  **caption** that the ×2 is a one-week thing when horizon > 1 (owner steer). Whole-horizon doubling was
  rejected (captaincy is a weekly decision). Both display-only — `decision_xp`/the engine unchanged; no server
  writes. +4 tests.
- **Sprint 097 (2026-08-07)** — *Set-piece attributes on My Squad* (tester feedback; **no new ADR** — extends
  **ADR-081**, display-only). **US-253:** `web_streamlit/pitch.py::_card` adds a `set_piece_flags` caption line
  (⚽ pens · 🚩 corners · 🎯 FK) beneath the `crowd_flags` (Trends) line — empty-safe, for a first-choice taker
  only; the My Squad pitch cards. **US-254:** a **"Set"** column (`" ".join(set_piece_flags(p))`) next to the
  existing **"Trends"** on the squad tables — `render_build` (the 15 + the formation-preview XI),
  `render_health`, `render_captain` — plus an **"In set"** column beside "In trends" on `render_transfer` (the
  incoming buy). `SET_PIECE_LEGEND` moved from `views/players.py` → `analytics/crowd.py` (next to
  `AVAILABILITY_LEGEND`, exported) so both the Players page and the Squads tables reuse it; `tables.py::
  render_player_table` gained an optional `help=` (threaded to `column_config(..., help=…)`) so the text "Set"
  column carries the legend tooltip. Reuses the Sprint-095 `set_piece_flags` + ingested order fields;
  `decision_xp`/the analytics unchanged; no server writes. +1 test (the pitch caption count equals the squad's
  owned takers) + 2 assertions (Captain "Set"; Transfer "In set").
- **Sprint 096 (2026-08-07)** — *Chip Strategy Guidance*, per **ADR-082** (US-251/252). **US-251:** a pure
  `analytics/chips.py::chip_advisor(owned, by_gameweek_by_id, gameweeks)` reduces the per-GW xP (`by_gameweek`,
  ADR-032) + `best_legal_xi` per GW into a best GW/window per chip — **Triple Captain** = the max single
  starter's ceiling GW · **Bench Boost** = the best all-15 GW (with the bench's share) · **Free Hit** = the
  weakest best-XI GW · **Wildcard** = the weakest rolling 3-GW window (clamped to the horizon). An **assembler**
  (the `gameweek_plan`/ADR-070 shape) — no new analytics, so the chip answer can't diverge from the standalone
  tools. A `chips` `ask`/`chat` intent (`_decide_chips` + `_chips_facts`, reusing `_squad_xp` so the horizon xP
  matches the transfer/analyse/gameweek tools) is narrated + **verified** (✓/⚠, ADR-037); `ui/chips.py::
  render_chip_advice` is the block CLI + web reuse. Routing adds `_INTENT_KEYWORDS["chips"]` **first** with
  distinctive phrases (`chip`/`chips`/`chip strategy`/`which chip`/`triple captain`/`free hit`/`use my bench
  boost`/`use my wildcard`) — **not** bare `bench boost`/`wildcard` (they stay `build_squad` — "build me a
  squad for a bench boost" must build) nor bare `captain`/`bench`; a routing test pins the guard. **US-252:** a
  Squads **"Chips"** view (after AI Tips) — `views/squads.py::render_chips` routes through `ask.answer(active_
  squad=…, horizon=…)` + `render_ask`, horizon-aware, degrading to the block without Ollama. Fixture-run + xP
  based — DGW/BGW timing + mini-league position deferred (in-season / GW1, no `events` table / no DGW preseason
  — verified). Display-only; `decision_xp`/the analytics unchanged; no server writes. +11 tests.
- **Sprint 095 (2026-08-07)** — *Set-piece takers & the differential lens*, per **ADR-081** (US-249/250).
  **US-249 (ingest):** `corners_order` (from `corners_and_indirect_freekicks_order`) + `freekicks_order`
  (from `direct_freekicks_order`) added to the `Player` model + `from_api`, and to storage — the
  `_MIGRATIONS` dict (auto-ALTERed on open), CREATE TABLE, the upsert, and `save_players`; `get_players` picks
  them up unchanged via `SELECT p.*`. A pure, empty-safe `analytics/crowd.py::set_piece_flags(player)` →
  `⚽ pens` · `🚩 corners` · `🎯 FK` for each duty whose order == 1 (the first-choice taker). **US-250 (view):**
  `views/players.py::render_set_pieces` — a `_board` of Player/Team/Pos/Fit + **Pen/Corners/FK** order +
  **Own%/Val/£m**, through the shared filter, sorted pen-takers-first, with a low-ownership **differential**
  caption + per-column tooltips (only players with a set-piece duty are listed); a **"Set pieces"** option on
  the Players segmented control; a compact **"Set"** `set_piece_flags` column on the Pool; `Pen`/`Corners`/`FK`
  → `%d` in `formats.py`. **Display-only** — `decision_xp`/the analytics are unchanged (a lens, like the
  availability/crowd flags); penalty duty already feeds captaincy. `refresh` + `reseed` populated real data
  (573 players, **38** first-choice takers). +7 tests; no server writes.
- **Sprint 094 (2026-08-07)** — *Pronoun-aware chat*, per **ADR-080** (US-247/248; refines ADR-047).
  **US-247:** a pure `_resolve_pronoun(question, context)` rewrites a pronoun (he·him·his·she·her·they·them·
  their, whole-word/case-insensitive; possessives → `name's`) → the last turn's **sole** subject (resolves
  only when there's exactly one antecedent), wired as the first line of `_fresh` — so it fires in
  `converse`/`chat` and is a **no-op for the context-less one-shot `answer`**. It substitutes the player's
  *name* for the pronoun the user typed (never assigns a pronoun). **US-248:** `pages/4_Ask.py` threads a
  `Context` in `st.session_state` and calls `ask.converse` (a `Storage` per turn) instead of `answer`, so the
  web chat gains **pronouns + the existing why/next/what-about follow-ups**; the first turn (context=None) is
  identical to before. Analytics decide, LLM narrates, every turn still verified (ADR-037); no server writes.
  636 → 640 tests.
- **Sprint 093 (2026-08-07)** — *Bench-order polish* (US-245/246; **no new ADR** — extends ADR-078/079).
  **US-245:** `render_build`'s saved squad orders `bench_ids` via `bench_order(bench_players, display_xp)`
  (outfield by xP, GK last), so a *Download* / *Use this squad* starts in the recommended sub priority (still
  reorderable). **US-246:** `pitch.py` — `_card(..., sub_role=None)` renders a "🔁 1st sub" / "🔁 GK sub"
  caption; `render_pitch(..., bench_roles=None)` orders the bench row by priority (`_ROLE_ORDER`) and labels
  each card; `render_my_squad` computes the `bench_roles` map (from the stored order) before the pitch call.
  Display/edit only; the analytics use `bench_ids` as a set. The bench-order feature is now end-to-end (start
  · see · set). 634 → 636 tests.
- **Sprint 092 (2026-08-07)** — *Set the bench order*, per **ADR-079** (US-243/244; refines ADR-055/078). The
  `bench_ids` **order** now means the sub priority. **US-243:** `set_bench` **preserves** the given order
  (was squad-position order); a pure `move_bench_sub(squad, player_id, direction, by_id)` swaps an
  **outfield** sub up/down (bounds-checked, no-op at the ends), excludes the **bench GK** (keeper-only) and
  keeps it last; copy-not-mutate (ADR-055). The change didn't ripple — the analytics use `bench_ids` as a
  **set**. **US-244:** `render_my_squad`'s "🔁 Bench order" line reads the **stored** order (outfield
  1st/2nd/3rd + the GK separate, built from `bench_ids` not owned order); a "Reorder the bench" expander gives
  each outfield sub **⬆/⬇** buttons → `move_bench_sub` → `set_active_squad` + rerun, plus a **"↻ Use
  recommended (xP) order"** button → `set_bench` with `bench_order`'s ranking. Mutates `session_state` (no
  server writes); the order rides in the `squad.json` download. 632 → 634 tests.
- **Sprint 091 (2026-08-07)** — *Bench order — the auto-sub priority*, per **ADR-078** (US-241/242). No
  auto-sub logic existed. **US-241:** a pure `analytics/optimizer.py::bench_order(bench, scores)` (next to
  `best_legal_xi`) → `[(role, player)]`: the **outfield** bench ranked by xP → "1st"/"2nd"/"3rd", then the
  **bench GK** → "GK" (it only ever replaces the starting keeper); empty-safe, tie-stable. **US-242:**
  `render_my_squad` shows a "🔁 Bench order (auto-subs)" caption naming the subs with their (horizon-aware)
  xP + the FPL-rule explainer ("the first that keeps a legal XI; the bench GK only covers your keeper"),
  shown when a bench is declared. A **recommendation** (order by value), not a per-blank simulator;
  display-only, no analytics drift. 629 → 632 tests.
- **Sprint 090 (2026-08-07)** — *A quick-stats summary on the My Squad banner* (US-239/240; **no new ADR** —
  reuses ADR-074/077). `render_my_squad` now renders a `st.columns(5)` metrics row above the pitch —
  **Projected XI ({horizon} GW)** · **Captain (2×)** · **Bench** · **Unavailable** · **Doubtful** — reusing
  the horizon-aware `xp_by_id`, `is_unavailable`, and `captain_id`; the £value / legal-15 banner stays.
  **US-239:** the Projected XI uses the declared XI (if a bench is set) else `best_legal_xi` (same as Health),
  so it's the best **11** and Bench the other 4. **US-240:** a caption names the flagged owned players with
  their `availability_flag` (❓ carries the chance%), or "✓ all 15 available". All display-only, from data
  already on hand; no analytics change; no server writes. 627 → 629 tests.
- **Sprint 089 (2026-08-07)** — *A configurable prediction horizon on the Squads tab*, per **ADR-077**
  (US-237/238). The analytics already took a `horizon` (`decision_xp`/`analyse_squad`); the web Squads views
  hard-used the default 5. **US-237:** a shared `st.selectbox("Gameweeks ahead", 1..8, default 5)` on
  `pages/3_Squads.py`, threaded as a keyword `horizon` into `render_build`/`render_my_squad`/`render_health`/
  `render_transfer` (each → `decision_xp` / `analyse_squad` / the transfer renderers' label). **Captain** is
  next-GW (a one-week decision) with a caption. **US-238:** a backward-compatible `horizon` param on
  `ask.answer` threaded `_fresh → _dispatch → _decide_gameweek → _squad_xp` (default `_HORIZON`, so the CLI /
  Ask tab / other squad decides are unchanged); `render_gameweek_plan(..., horizon=…)` labels the transfer
  window ("over N GW"). Default 5 = unchanged behaviour; no analytics change; no server writes. (A new
  page-level selectbox shifted widget indices → 5 positional test refs re-pointed to select **by label**.)
  625 → 627 tests.
- **Sprint 088 (2026-08-07)** — *UX polish: clickable Ask examples · CLI availability flags · chance% on ❓*
  (US-234/235/236; **no new ADR** — extends US-227 / ADR-074). **US-234:** the Ask page's example prompts are
  now **buttons** — a shared `_ask(question)` helper (answer → `render_ask` → append to history → stash
  `built_squad`) feeds both the chat box and the buttons; clicking runs it + `st.rerun()`
  (`st.chat_input` can't be pre-filled). **US-235:** a last-column **Fit** flag (🚑/🚫/⛔/❓) on
  `ui/table.py` (→ `table`/`search`/`filter`) and `ui/xg.py` (→ `xg`), reusing `availability_flag` — kept
  **last** so an emoji's ~2-cell terminal width can't cascade into the aligned columns (the byte-exact
  substring tests + statusless fixtures needed no changes). **US-236:** `availability_flag` appends the
  chance for a doubtful player (`❓ 75%`), enriching the web Fit column + the new CLI column from one edit.
  Display-only; `decision_xp`/the analytics untouched; no server writes. 622 → 625 tests.
- **Sprint 087 (2026-08-07)** — *"Talked about" — count mentions across a bigger sample*, per **ADR-076**
  (US-232/233, refines ADR-059). A tester saw "1 mention regardless"; a **live fetch** showed the counter is
  fine (it produced 1–4) — the cause is the sample: Reddit's default `.rss` returns only **25 posts**, so
  35/51 players sit at "1". **US-232:** `RedditRssClient.get_subreddit_rss(..., *, limit=config.
  REDDIT_RSS_LIMIT)` appends **`?limit=100`** to the URL (new `config.REDDIT_RSS_LIMIT = 100`), so
  `community_buzz` counts mentions across ~100 posts (the counter is unchanged — it already sums every match
  across every entry; the defaulted `limit` keeps the fake clients / `community_signals` compatible).
  **US-233:** the (now longer) board pages via the shared `paginate(buzz, key="buzz", per_page=30)`, sorted
  by mentions desc. Still a cached, button-gated, degrade-on-failure buzz lens; `decision_xp` untouched; no
  server writes. (Reddit `429`'d during planning — the graceful-degradation path; a live count re-verify is a
  DoD smoke.) 619 → 622 tests.
- **Sprint 086 (2026-08-07)** — *The XI score in the formation preview*, per **ADR-075** (US-230/231). The
  Build page's "🔎 Preview the best XI in a given shape" showed the XI but no total. **US-230:**
  `render_build` now sums the previewed XI's displayed `xP` into a `st.metric("Projected XI — {shape}",
  "{xi_xp} xP")` (free — the shape's `select_squad` solve already runs). **US-231:** a default-off
  **"Compare all formations"** checkbox → `_formation_xi_scores(...)` solves the best XI for each of the 7
  legal shapes and a `st.dataframe` ranks them **Formation · XI xP · Δ vs best** (desc; inline `NumberColumn`
  formatting, ADR-072); an illegal shape → blank. **Gated** because a Streamlit expander body runs even when
  collapsed, so the 7 extra ILP solves fire only on tick. Reuses `select_squad` + the build's
  `scores`/`display_xp`; display-only (the saveable build is still a full 15, ADR-062); no analytics change,
  no server writes. Real spread: 3-5-2 254.1 → 5-4-1 246.0 (8.1 xP). 617 → 619 tests.
- **Sprint 085 (2026-08-07)** — *Availability flags in the player tables*, per **ADR-074** (US-228/229). The
  squad/captain views warned about injuries but the ranking tables didn't. A shared
  `analytics/crowd.py::availability_flag(player)` (next to `crowd_flags`) → **🚑 injured · 🚫 suspended · ⛔
  unavailable · ❓ doubtful** (`""` = available), chosen distinct from the rating circles; a shared
  `AVAILABILITY_LEGEND`. A compact **Fit** column on the **Players Pool** (US-228) and all **four stat
  boards** (US-229): the Pool + xG flag their raw rows directly; the trimmed boards (over/under · DefCon ·
  clean sheets) build a `{(web_name, team): flag}` lookup from the full `players` list each render func
  already receives, so `_board(flag=…)` adds the column/tooltip/legend uniformly — **no analytics change**.
  Reuses ingested `status`/`chance` (ADR-023); display-only; no server writes (60 of 572 flagged preseason).
  613 → 617 tests.
- **Sprint 084 (2026-08-06)** — *Fix the xG rating flaw + rename This week→AI Tips + Ask examples*, per
  **ADR-073** (US-225/226/227). A tester spotted goalkeepers rated "🟢 excellent" on the xG board — xGI is
  ~0 for GKs, 172 players have 0 minutes, and the rating pool was *all shown rows*, so a GK-filtered view
  rated `0.04` as "top 19%". **US-225 (ADR-073, refines ADR-071):** `render_xg` now rates `xGI` only for
  outfield players with ≥900 mins (`_rate_xgi`), against **that** pool; GKs / low-minutes / no-data rows show
  a blank `—`; the column is renamed **"xGI rating"** and moved right after `xGI` (away from `xGC`, the source
  of the "how can 0 be good and 56 be good?" ambiguity). `quality_band`/`rating_cell`, the analytics, and
  Clean sheets are unchanged — only which rows are rated and against what pool. **US-226:** the Squads
  gameweek tab renamed **This week → AI Tips** (label/dispatch/`render_ai_tips`/help/Help copy); the engine
  (ADR-070) is unchanged (the plan content still reads "This week — squad X"). **US-227:** an `st.expander`
  of copy-paste example prompts on the Ask page. 613 tests.
- **Sprint 083 (2026-08-06)** — *Consistent number formatting + a Help refresh*, per **ADR-072** (US-223/224).
  A tester wanted the web tables aligned (`Val/£m` showed `24.2345`; whole prices showed `6`). A shared
  `src/web_streamlit/formats.py` (`FORMATS` label→printf map + `column_config(labels, *, help, images)`)
  formats every Streamlit table via `st.column_config.NumberColumn` — right-aligned + **still numeric/
  sortable** (not pre-rounded strings, which would sort lexically). Policy: money/value/%/form/ICT → **1dp**;
  counts (Pts/Mins) → **integer**; the xG family (xG/xA/xGI/xGC/xGC/90) → **2dp**; signed diffs
  (Diff/Margin/+xP) → **`%+.1f`**. Applied in `views/players.py` (Pool + `_board`, whose `Diff`/`Margin`
  cells move from pre-formatted strings back to raw numbers) and `tables.py` (`render_player_table`, keyed by
  the union of row labels); the dead `_BADGE` constant was removed. **Display-only** — the raw analytics
  values and sort order are untouched; the CLI already aligns via its renderers, so it's unchanged; no server
  writes. **US-224:** the Help guide refreshed to cover This week (the gameweek plan), the 🟢…🔴 quality
  ratings, the table-first Pool, and a "this week" Ask example. 612 tests.
- **Sprint 082 (2026-08-06)** — *Interpretable stat boards + per-tab headers*, per **ADR-071** (US-221/222).
  A **display-only** quality rating answers the tester's "is xGC/90 0.52 good, or just relative?".
  `src/web_streamlit/ratings.py::quality_band(value, pool, *, higher_is_better)` rates a value **relative to
  the players shown** — a quintile (🟢 excellent … 🔴 very poor) + the **percentile** inline ("top N%");
  `rating_cell` formats the cell. `views/players.py` adds a **Rating** column to **Clean sheets** (xGC/90,
  lower=better) and **xG** (xGI, higher=better), computed over the *filtered* board (stable across pages), +
  a legend; all four boards gain clearer captions + per-column `help=` tooltips (`_board` now takes
  `col_help`). **Relative, not fixed** bands — real xGC/90 (median 1.36) makes ChatGPT's fixed table
  mislabel 91/117 defenders "poor"; the two signed boards (over/under, DefCon) keep +/- and get no colour.
  Web-side helper → the analytics core stays pure; no server writes. **US-222:** each tab gains an emoji-led
  title + tagline (👟📅🧩💬📰📈🧭), like Home. 607 tests.
- **Sprint 081 (2026-08-06)** — *An AI gameweek recommendation + refresh clarity + Pool layout*, per
  **ADR-070** (US-218/219/220). **US-220 (the feature):** a grounded **"this week"** plan for a squad —
  captain · lineup · a transfer · flags — as an **assembler**, not new analytics: `src/analytics/gameweek.py`
  `gameweek_plan(owned, market, upcoming, xp_by_id, …)` orchestrates the existing primitives (`captain_picks`
  next-GW · `best_legal_xi` vs the declared bench · one self-funding `suggest_transfers` · `is_unavailable`/
  doubtful flags) → `{captain, lineup, transfer, flags}`. `ask.py` gains a phrase-routed **gameweek** intent
  (`_decide_gameweek` → `detail`/`facts`/`subjects`/`task`), placed **after** the specific intents so
  "captain this week" still routes to captain; it narrates + verifies (✓/⚠, ADR-037). `src/ui/gameweek.py`
  `render_gameweek_plan` is the block; a **Squads → This week** view routes through `ask.answer(active_squad=…)`
  + `render_ask`, degrading to the plan without Ollama. No server writes; captain uses next-GW xP while
  lineup/transfer use the caller's 5-GW xP (the horizon each wants). **US-219:** the freshness caption leads
  with the **player count** + a cloud snapshot note; a one-command **`reseed`** (refresh `fpl.db` → copy to
  `seed.db`; new `config.LIVE_DB_PATH`); DEPLOY/Help split the cloud vs local refresh story. **US-218:**
  `views/players.py::render_pool` renders the table before the top-15 bar. 598 tests.
- **Sprint 080 (2026-08-06)** — *Sidebar consolidation*, per **ADR-069** — the web sidebar went **12 → 7
  tabs** (Players · Fixtures · Squads · Ask · News · Trending · Help). **Players** absorbed Player Stats and
  **Squads** absorbed Build/My Squad/Health/Transfer/Captain, each behind a lazy `st.segmented_control`
  (only the selected view runs — not `st.tabs`, which executes all). View bodies were extracted to a
  `web_streamlit/views/` package (`players.py`, `squads.py`); the consolidated pages load once + dispatch on
  the control (Players: a shared filter; Squads: `render_sidebar` + one shared `squad_picker` for the four
  manage views). ~38 AppTest refs rewired (a `_squads_view` helper; buttons label-filtered) with **every
  prior assertion kept** — no behaviour change. Home + the Help guide updated to the 7-tab nav. 585 tests.
- **Sprint 079 (2026-08-06)** — *A Help tab*, per **ADR-068** — a new static onboarding page
  (`pages/12_Help.py`, placed last → no renumber): a step-by-step guide to building a team with the
  assistant — 7 `st.expander` steps (build → make it yours → check health → improve → research → **ask**
  (copy-paste examples + the ✓/⚠ trust line) → save) + a quick-start + an honest data-freshness/GW1 close.
  No analytics/data dependency (renders before refresh); no input widgets (outside the tooltip test); Home
  gains a pointer. 585 tests.
- **Sprint 078 (2026-08-06)** — *Team-level squad fixtures*, per **ADR-067** — implements the ADR-049
  deferral: a 4th `fixtures` ask/chat mode. `_decide_squad_team_fixtures` groups a squad's owned players by
  team (a player-count + names), joins `team_fdr`, and ranks the distinct teams by avg difficulty (easiest
  default, hardest on the existing cue); a **`teams`/`clubs`/`by team`** cue routes to it within the squad
  branch (else the per-player view; a possessive "my team's players" doesn't false-trigger). A dedicated
  `render_squad_team_fixtures` (Team · #Players · Avg FDR · Next). Reuses `team_fdr` (no new analytics);
  grounded; the other three fixtures modes unchanged. 584 tests.
- **Sprint 077 (2026-08-06)** — *Team-scoped player multiselect* (refines **ADR-064**) — the shared
  `filter_controls` now scopes the **Player** options by the selected **team ∧ position** (empty = all)
  instead of ~570 names; the stored pick is pruned when it falls out of scope. One edit → Players ·
  Player Stats · Trending. `apply` unchanged; no server writes. Smoke: 555 → 28 (ARS) → 15 (ARS ∧ MID).
  581 tests.
- **Sprint 076 (2026-08-06)** — *Tech-debt sweep*, per **ADR-066** — two Backlog items cleared with **no
  behaviour/output change** (65 optimizer + 19 render assertions unchanged). **PuLP** (`optimizer.py`):
  variables → `problem.add_variable(...)`; **kept `PULP_CBC_CMD`** (`COIN_CMD` needs an external CBC —
  "cannot execute cbc" — and would break the read-only Cloud); the blanket `DeprecationWarning` ignore →
  a **targeted** PULP_CBC_CMD filter so other deprecations surface. **Squad renderer** (`ui/squad.py`):
  `render_squad`/`render_loaded_squad` share `_header` + `_BENCH_HEADING`; the `render_rows` fold is
  **closed** (its flat single-space join can't reproduce the mid-table heading, glued `**`/`*` markers, or
  divergent price cells byte-for-byte). Verifying real behaviour re-scoped both items away from the naive
  backlog phrasing. 580 tests.
- **Sprint 075 (2026-08-06)** — *A filter on Trending* (reuses **ADR-064**) — the Trending page gained the
  same **Team · Position · Player** filter as Players & Player Stats: `filter_controls(players,
  key="trending")` once above the four boards, each `apply`-ing it before pagination. The buzz board + the
  GW1-empty note are unchanged. No new analytics/ADR; the filter's `help=` tooltips are inherited (ADR-065),
  so the coverage test stayed green. The third reuse of the shared filter — a few lines. 580 tests.
- **Sprint 074 (2026-08-06)** — *Help tooltips (ⓘ)*, per **ADR-065** — a concise, action-oriented `help=`
  on **every input control** across the web (a Streamlit ⓘ tooltip), added at the shared components
  (`filters` · `paginate` · `squads`) so all pages inherit it, plus each page's own controls; key buttons
  too. `st.tabs` labels + `st.chat_input` take no `help=` → captions cover them. A coverage test
  (`tests/test_help_tooltips.py`, via AppTest `.help`) asserts every input widget on all nine pages carries
  a non-empty tooltip — a standing guarantee against regressions. No behaviour change. 579 tests.
- **Sprint 073 (2026-08-06)** — *Rich filters on Players & Player Stats*, per **ADR-064** — one shared
  `web_streamlit/filters.py`: `filter_controls` (Team · Position · Player multiselects + optional max-price,
  key-namespaced) + a pure `apply` (keep rows matching every non-empty dimension — **AND**; tolerant of
  `sqlite3.Row` and dict). Applied to **Player Stats** (one filter above the four tabs → each analytic
  narrowed before pagination) and **Players** (team + player added to position; max-price kept). The Players
  price-vs-points **scatter is replaced** by a filter-responsive **top-15 horizontal bar** (Altair,
  `y sort="-x"`) of the strongest filtered players by the sort metric. No analytics change; no server
  writes. 578 tests.
- **Sprint 072 (2026-08-06)** — *Player Stats page + pagination*, per **ADR-063** — the CLI's stat views
  come to the web with **no engine change**. A new `pages/2_Player_Stats.py` (sidebar position 2) has tabs
  **Over/under · DefCon · Clean sheets · xG**, each reusing the *same* analytics (`over_under` /
  `defcon_reliability` / `defensive_solidity`; xG = players by `xgi`) → an st.dataframe (team badge + the
  CLI columns), **season-to-date** (last-season carryover preseason). A shared `web_streamlit/paginate.py`
  (`page_labels` pure + `paginate` = a stateless page selectbox) powers see-everything paging: **Players**
  pages through all (no 50-cap) + a **team/position** sort; **Trending's** four boards page past 30. The
  sidebar renumbered (Player Stats 2 → Fixtures 3 … Trending 11). Guardrails caught two regressions (a
  Row-vs-dict crash; ruff F821 on a removed slider's `count`). No server writes. 571 tests.
- **Sprint 071 (2026-08-06)** — *Web build parity + tab reorg*, per **ADR-062** — the web reaches full CLI
  `squad` parity with **no engine change**. **Build Squad** (`pages/3_Build_Squad.py`) exposes the full
  option set as form widgets (include/exclude/declared-bench multiselects · objective · no-xmins · build
  mode · include-unavailable) feeding the *same* `select_squad`/`decision_xp`/`objective_scores` the CLI
  uses; the saveable build stays a full **15** (Download / Use this squad →); formation is a display-only
  best-XI-shape preview (an XI ≠ a 15). The **Ask** edge gained an additive `squad` field on the decision +
  `AskResult`, so a "build me a squad" answer offers **"Use this squad →"** (→ the session squad → My
  Squad). Squad tabs renamed + regrouped via `git mv` (Squads→Squad Health, Build→Build Squad; sidebar
  grouped Build Squad · My Squad · Squad Health); My Squad points to Build Squad (a caption — `st.page_link`
  crashes AppTest). No server writes (guardrail holds). 565 tests.
- **Sprint 070 (2026-08-06)** — *Differentials / value `ask` intent*, per **ADR-061** — two natural-language
  lenses over the unified xP + ownership, grounded + verified (ADR-037), by **reusing** the shortlist, the
  compare matcher, and `DIFFERENTIAL_OWN`. (1) A **differential** filter on the shortlist (`_shortlist_query`
  parses a differential cue; `_decide_shortlist` keeps ≤5%-owned, 0% included; `render_shortlist(show_own=…)`
  adds an **Own%** column — the plain shortlist stays byte-identical). (2) A single-player **`worth`** intent
  (`_decide_worth`): match one player, compute **xP/£m**, rank it among available same-position players, take
  the **position median**, and a tiered fact-derived **verdict**; degrades on ambiguous/absent/flagged.
  Routing precedence: `worth` before transfer ("worth buying" ≠ "buy"), "differentials"→shortlist, "most
  owned"→trends. Preseason-honest (ownership sharpens at GW1). No new data/deps. 556 tests.
- **Sprint 069 (2026-08-06)** — *Data Hardening prep*, per **ADR-060** — the first season-start foundations,
  built **wired but dormant** so **GW1 (2026-08-21)** is a switch-flip. (1) A per-GW `player_history` table
  (`src/models/player_gameweek.py` `PlayerGameweek`, keyed `code+round`; additive/idempotent) filled by the
  **existing** throttled `element-summary` walk — the one call already carries `history` (empty preseason →
  live GW1), so it rides the same pass (keyed via an id→code map). (2) A dormant in-season **form blend**: a
  pure `src/analytics/form.py` (`form_rate` = a recency+minutes-weighted rolling **pp90**; `blend_form`)
  folded into the **one** `decision_xp` recipe (precomputed `form_by_code`, like `baseline_by_code`) behind
  `config.FORM_WEIGHT = 0`. Preseason → xP **unchanged** (an invariance test + a real-DB smoke pin it; the
  whole suite passing is the proof). Every `decision_xp` caller (cli/ask/web) wired → **GW1 = backfill +
  raise the weight**. Not FPL's `form` field (minutes-blind); the one-xP invariant (ADR-041) held. 546 tests.
- **Sprint 068 (2026-08-06)** — *Community Signals*, per **ADR-059** — genuine community "buzz" with **no
  Reddit Developer access / secret**: the public **RSS** feed (the `.json` API 403s). A self-contained
  `src/api/reddit.py` `RedditRssClient` (best-effort, ClubElo pattern) + a pure `src/community.py`
  `community_buzz` (parse Atom + count `web_name` mentions) + `community_signals` (degrade to
  `(None, message)`). Surfaced as a Trending **"💬 Talked about"** board — **button-gated** + `st.cache_data`
  (~30 min), degrading to "unavailable". Buzz (frequency), not sentiment; display-only, xP untouched.
  Cloud-IP may block → degrades. 528 tests green.
- **Sprint 067 (2026-08-06)** — *community "trending"* (no new ADR — executes ADR-057). A pure
  `trending(players, by, limit)` in `analytics/crowd.py` (rank by owned/in/out/form, display-only) powers
  both a new **trends `ask`/`chat` intent** (keywords first so "most transferred" beats the transfer-advice
  intent; grounded; preseason-graceful → "live from GW1") and a **Trending page** (`pages/10_Trending.py` —
  four boards as tabs, photos+badges+flags). Ownership works now; momentum/form light up at GW1. Reddit
  social sentiment recorded as a gated follow-up (US-195, ADR-059, needs a cloud secret). Not xP. 523 tests.
- **Sprint 066 (2026-08-06)** — *fix (tester bug, no ADR)* — the web **Ask** tab ignored the session
  active squad (it resolved squads only via `SquadStore`), so "captain/analyse RoboTS" fell back to "(all
  players)". Added `ask._load_squad` / `_known_squad_names` (the **session squad wins**, else `SquadStore`)
  and threaded an optional `active_squad` (default None → CLI unchanged) through the `ask` entry points →
  deciders; "my team" resolves to the loaded squad; the Ask page passes `active_squad()`. `decision_xp`
  untouched. 517 tests green. *(Ended the Sprint-065 hold.)*
- **Sprint 064 (2026-08-06)** — *Phase 6 Tier 2 (start)*, per **ADR-058** — external/extended signals, two
  **free, no-key** pieces. An FPL official-**news lens**: ingest `scout_news_link` (the source link) +
  reuse the stored `player.news` → a new `pages/9_News.py` (flagged players, most-serious first, a "read
  more" link; degrades to "no current news"). **Import team by manager-ID**: config entry paths +
  `FplClient.get_entry`/`get_entry_picks`, a new pure `src/manager.py` (`picks_to_squad` +
  `fetch_manager_team`, degrade-gracefully like ClubElo, ADR-021) → a sidebar **Import** control that sets
  the session active squad (no server writes; alongside build/upload). Both display/state — `decision_xp`
  untouched. Keyed social (Reddit/X) + pundit NLP deferred. The import's picks are **GW1-gated** (404 until
  the deadline) — built now, live at GW1. 514 tests green.
- **Sprint 063 (2026-08-06)** — *tester-feedback polish* (no ADR) — centred the My Squad pitch-card photos
  via a nested `st.columns([1,2,1])` (robust native, no custom CSS).
- **Sprint 062 (2026-08-06)** — *two UI feature requests* (no ADR — UI over the settled edge). **Fixtures**
  becomes a **fixture ticker**: a new pure `fixture_ticker(fixtures, next_n)` (reuses `team_fdr` /
  `team_schedule`) → a teams × gameweeks grid rendered with a **weeks selector (1–8)** and per-cell
  difficulty colours (green→red) via a pandas Styler. **My Squad** becomes a **formation card-grid**
  (`src/web_streamlit/pitch.py` `render_pitch`) — position rows + bench, each a card (photo · name (+ (C)) ·
  £ · xP · next opponent · crowd flags), replacing the dataframe; robust native `st.columns`/`st.container`
  (owner's call — no custom-CSS pitch). Data-shaping stays in the core (pure + tested); colours/layout at
  the edge. `decision_xp`/engine untouched. 504 tests green.
- **Sprint 061 (2026-08-06)** — *finish Phase 6 Tier-1* — `crowd_flags` extended to Captain (+ a
  template-risk caption) and Transfer (an "In trends" column) reusing the pure helper; the "trends" `ask`
  intent deferred to a GW1-timed sprint (momentum is 0 preseason). Display-only; xP untouched.
- **Sprint 060 (2026-08-06)** — *Phase 6 opener — the crowd lens (Tier 1)*, per **ADR-057**. Crowd &
  sentiment signals as a **complementary lens + flags, never blended into xP** (a test asserts `decision_xp`
  is unchanged). **Ingest** the free FPL Tier-1 fields (`transfers_in/out_event` · `cost_change_*` · `form` ·
  `ict_index`+components · `value_form`) into the `Player` model + storage (`_migrate` adds the columns;
  `seed.db` reseeded so opening it stays a no-op). A pure **`src/analytics/crowd.py`** `crowd_flags` helper
  (empty-safe, tunable thresholds — template ≥20% / differential ≤5% / price sign / trending / in-form)
  surfaced as **Trends** + **Form/ICT** columns on Players and a **Trends** column on Build/Analyse/My Squad.
  Season-gated: momentum/form are 0 preseason, live at GW1. External social + pundit deferred (Tier 2/3).
  499 tests green.
- **Sprint 059 (2026-08-05)** — *pre-tester polish*, two adds before a feedback cycle. **Imagery
  consistency** (no ADR — UI over the settled edge): the player-photo helper moves into the shared
  `badges.py` (`photo_url`/`photo_url_by_id`) + a `web_streamlit/tables.py` `render_player_table`, so
  **Build · Analyse · Transfer · Captain · My Squad** show photo + team-badge tables (augmenting, not
  replacing, their text summaries). **Local refresh + freshness**, per **ADR-056**: a shared
  `web_streamlit/status.py` `render_data_status()` on every tab — a **"Data as of \<date\>"** caption
  (DB mtime) always, plus a **local-only "🔄 Refresh data"** button (reuses `ingest.refresh`), gated by
  `FPL_LOCAL=1` (set by the runner) + a writable non-seed DB. This is the **first web write path**, kept
  narrow: local only, the data cache only; the **cloud stays read-only** (caption only). 487 tests green.
- **Sprint 058 (2026-08-05)** — *an editable session squad*, per ADR-055. The read-only session squad
  (ADR-054) becomes **editable** — still **in `session_state`, no server writes**. Fixed a Build bug (xP/
  xMins rendered 0 — the page now attaches `xp`/`minutes_weight` like the CLI). New generic core validator
  **`squad_15_issues`** (position split vs `SQUAD_15` + ≤3/club; **budget stays a soft edge-side warning**,
  never in the legality list). Edits go through **mutation helpers** in `web_streamlit/squads.py`
  (`rename` · `apply_transfer` · `set_bench` · `set_captain`) — each edits a **copy**, recomputes cost,
  clears a departed captain, and pages never touch the dict inline. Editing happens **where the opportunity
  is**: **Transfer** gains *Apply* (a suggested swap), **Captain** gains *Set as captain* (persisted as
  `captain_id`, shown **(C)** in Analyse + the download; `parse_uploaded` validates it), plus a new
  **My Squad** hub (`pages/8_My_Squad.py`) — the 15 with (C)/cost/legality, rename, manual same-position
  swap (validated), bench, download. `name`/`captain_id` are harmless **superset** keys on the CLI
  `SquadStore` dict. 481 tests green.
- **Sprint 057 (2026-08-05)** — *cloud squads — per-user, no server*, per ADR-054. The deployed app's
  disk is ephemeral + multi-user, so squads move to a **session "active squad"** in `st.session_state`,
  set by **building** (Build → *Download* a `squad.json` + *Use this squad*) or **uploading** one (a
  sidebar `file_uploader`). Persistence is the **user's own file** (the CLI `SquadStore` `{name: squad}`
  shape — interoperable); the web **never writes** server-side (a test scans both edges for `.save(`), so
  the DB/squads stay read-only. A new edge module **`src/web_streamlit/squads.py`** holds the state
  (`active_squad`/`set_active_squad`), a demo+session **`squad_picker`**, upload validation
  (`parse_uploaded` — shape, 11–15 size, ids exist), and the sidebar. A committed **`data/seed_squads.json`**
  demo (+ a `config.SQUADS_PATH` fallback, mirroring `seed.db`) populates the pages on first visit.
  **Analyse · Transfer · Captain** (a new page) run the engine on the squad **dict** (not `ask`-by-name),
  so an uploaded squad works. Core analytics unchanged; 455 tests green.
- **Sprint 056 (2026-08-05)** — *deploy & share*, per ADR-053 — the Streamlit app becomes a public,
  read-only site on **Streamlit Community Cloud** (the owner relaxed the custom domain, so no PaaS /
  Cloudflare / Docker / `$PORT`). Repo-prep: a minimal **`pyproject.toml`** + **`-e .`** in
  `requirements.txt` so `import src` resolves under Community Cloud's `streamlit run` (an editable install
  on the path — no `sys.path` hack); a committed **`data/seed.db`** snapshot (the live `fpl.db` is
  gitignored) with `config.DB_PATH` falling back to it when `fpl.db` is absent; a `.streamlit/config.toml`.
  Security: read-only, no secrets, FPL API public, **Ollama absent → Ask degrades to decision + facts**.
  Going live is owner-executed via `docs/DEPLOY.md`. Core analytics unchanged; 442 tests green.
- **Sprint 055 (2026-08-05)** — *Streamlit visual polish* (no ADR — UI over the settled edge + a
  display-only field). The entrypoint `app.py` → **`Home.py`** (in Streamlit's classic multipage the
  sidebar label is the entrypoint *filename*), the landing lists all six pages; **player photos**
  (`st.column_config.ImageColumn` from the stored player `code`) on Players; **team badges** on Fixtures +
  Players, via a **light `team.code` ingest** (a nullable column + migration, backfilled by `refresh`;
  bootstrap-static `teams[].code`) and an edge helper `src/web_streamlit/badges.py`. Images are fetched by
  the **browser** at render (no new Python dep; a missing one → a broken-thumbnail icon). Core analytics
  unchanged; the two-edge guardrail holds (the badge helper is *edge*).
- **Sprint 054 (2026-08-05)** — *Streamlit polish* (no ADR — UI over the settled edge, ADR-052). The
  `src/web_streamlit/` edge gains **charts** (native `st.bar_chart` — teams by avg FDR on Fixtures; native
  `st.scatter_chart` — price vs points, coloured by position, on Players) and two **interactive decision
  pages** — **Transfer** (`suggest_transfers`, squad + bank/count) and **Build** (`select_squad`, budget +
  archetypes). All reuse the same engines/renderers the CLI does; the core is unchanged, the two-edge
  guardrail holds, FastAPI stays frozen. (US-159 shipped the charts; Transfer/Build are US-160/161.)
- **Sprint 053 (2026-08-05)** — *the Streamlit edge graduated*, per ADR-052 (executing the ADR-051
  decision). The Sprint-052 spike became a real edge, **`src/web_streamlit/`** — **multipage** (`app.py`
  home + `pages/1_Players … 4_Ask.py`, Streamlit's sidebar nav), run via **`python -m src.web_streamlit`**
  (a `__main__.py` that launches `streamlit run` with the project root on `PYTHONPATH`, so the app/page
  files carry **no `sys.path` hack**). Pages reuse the same engine/renderers (`ask.answer` / `rank_players`
  / `team_fdr`); `streamlit` added **web-only** to `requirements.txt`. Now **two web edges over the one
  engine** — Streamlit (grown) + FastAPI (`src/web`, **frozen**, untouched) — with the one-way-flow
  guardrail extended to assert the core imports **neither** (`test_core_never_imports_a_web_edge`). Tested
  per page with Streamlit's `AppTest` (headless); the spike was removed on graduation. Tests 429 → 435.
  Interactivity upgrades (filterable table + chat Ask) + the run/README docs are US-158.
- **Sprint 051 (2026-08-05)** — *a thin web UI (first slice)*, per ADR-050 — realises the web UI deferred
  by ADR-002/003. A **second edge** (`src/web/`) alongside the CLI: a read-only, local-only **FastAPI**
  app (sync handlers) whose routes call the **same** `decision_xp`/`ask.answer`/optimiser and render the
  **existing text renderers wrapped in `<pre>`** (zero new rendering logic). Slice-1 routes: **`/`**
  (players) · **`/fixtures`** (FDR) · **`/ask`** (the flagship — the grounded NL answer with its ✓/⚠ trust
  line, degrading without Ollama like the CLI). The analytics/CLI import **nothing** from `src/web/` — a
  test (`test_core_never_imports_the_web_edge`) asserts the core stays web-free, so one-way flow survives
  the new edge. Run: `python -m src.web` (127.0.0.1:8000). New **web-only** deps (`fastapi`/`uvicorn`/
  `jinja2`, +`httpx` for the test client) — the CLI runs without them. Tests 421 → 427. Later pages +
  HTML polish are US-153 / future.
- **Sprint 049 (2026-08-05)** — *squad-scoped fixtures*, per ADR-049, from the owner (the piece deferred
  from Sprint 048). The `fixtures` intent gains a **third mode**: name a saved squad and
  `_decide_fixtures` ranks **that squad's players** by their team's upcoming FDR (player-level: Player ·
  Team · Avg FDR · Next opponents), easiest default / hardest on a cue — a **join** (player → its team's
  `team_fdr`) **+ a sort**, no new analytics; rendered by a small dedicated `render_squad_fixtures`.
  Precedence in `_decide_fixtures`: a specific **team** → its schedule; else a **saved squad** → the
  squad ranking; else the **league** ranking. A gate-caught bug fixed: **`_squad_name` is now
  possessive-aware** (strips a trailing `'s`, so *"TS's players"* resolves to TS) — a general win for
  every squad-scoped intent. Threads the routed `squad` through the fixtures `_dispatch`, so it works in
  **both `ask` and `chat`**, grounded + verified (ADR-037). Needs a named squad (else league); FPL
  difficulty; per-player xP × fixtures stays `analyse`'s job. No new dependency.
- **Sprint 048 (2026-08-05)** — *a fixtures / FDR `ask` intent*, per ADR-048, from the owner (*more Phase
  4*). Closes the biggest routing gap — every fixtures question fell through before — with **no new
  analytics**: a `fixtures` intent reuses `team_fdr` / `team_schedule` (FPL difficulty) and their
  renderers. Two modes: a **team named** → its schedule (`_match_team` → `team_schedule` →
  `render_team_fixtures`), **no team** → the league **FDR ranking** (`team_fdr` → `render_fdr_table`;
  **easiest** default, **hardest** on a hard/tough/avoid cue). `_match_team` resolves the full name, the
  short code (case-sensitive, so a typed "NEW" matches but the word "new" doesn't) and a small alias set
  (*Tottenham/Spurs*→TOT, *Man Utd*→MUN, *Man City*→MCI, *Forest*→NFO) — and **never guesses** (≥2 teams
  → clarify, none → league mode / a message). "next N" horizon (default 5). Wired through the shared
  `_dispatch`, so it works in **both `ask` and `chat`**, grounded + verified (ADR-037). The routing
  keyword set is placed **last** ("play" is broad); squad-scoped fixtures deferred. No new dependency.
- **Sprint 047 (2026-08-05)** — *conversational `ask`* (mechanics), per ADR-047, from the owner (*more
  Phase 4*). A follow-up can now build on the last turn while the discipline holds — **analytics decide
  every turn**, the LLM only narrates. A `Context` (last intent/squad/decision + a `rank`) carries the
  turn; **`detect_followup`** classifies three families by *subject-less* trigger only (so *"why?"* is a
  follow-up but *"why is Haaland good?"* stays a fresh question): **why** (re-narrate the last decision's
  *same* facts with a deeper task), **next** (re-run the intent at a **rank offset** — captain/transfer
  take the Nth pick, shortlist the next page; the engines already rank), **what-about** (shortlist-only:
  swap the position, *keeping* the price/value constraints via `_swap_position`). **`converse(question,
  context)`** is the per-turn engine (a follow-up on the context, else a fresh question via the shared
  `_dispatch`); the one-shot `answer()` is `converse` with no context; a follow-up with no context yet
  nudges. Grounding (ADR-037) runs every turn. The `chat` REPL that threads the context is US-141. No new
  dependency.
- **Sprint 046 (2026-08-05)** — *XI-aware transfers*, per ADR-046, from the owner (the follow-on to
  bench-aware builds). `suggest_transfers` now ranks single swaps by **XI-gain** = `best_xi_points(owned −
  out + in) − best_xi_points(owned)` — how much a swap lifts your best legal XI — so bench-fodder swaps
  (XI-gain 0) drop out instead of topping with a misleading paper gain. A fast **`best_xi_points(players,
  scores)`** (enumerate the ~7 legal formations, sum top-N per position) gives the XI total in ~O(1) per
  candidate and **matches `best_legal_xi` exactly** (a test pins 235.3 = 235.3; ~750 swaps in 0.02s), so no
  per-candidate ILP. **XI-aware is the default** (`xi_aware=True`); `xi_aware=False` (**`--raw`**, US-138)
  restores the old raw-player-gain ranking. `suggest_transfer_plan` threads `xi_aware` through its greedy
  state. Worked example (a `--weekly` squad, £3 bank): raw tops with *Kusi-Asare → João Pedro **+19.3***
  (bench fodder — its true XI gain is +0.8); XI-aware tops with *Guéhi → Gabriel **+3.0 XI xP***. Legality,
  the greedy dedup (ADR-040) and the `(b)` marker are unchanged. No new dependency.
- **Sprint 045 (2026-08-05)** — *bench-aware squad optimisation*, per ADR-045, from the owner (valuable
  for rotation + Bench Boost). `select_squad(bench_weight=W)` adds a `start[i]` binary per player (a legal
  XI within `XI_FLEX`) and maximises `Σ xp·start + W·xp·(pick−start)`, flagging non-starters `bench` —
  **byte-identical when `W` is None**. **`--weekly`** (`W = 0.1`) builds a strong XI (+7.6 xP) with a
  cheap-but-playing bench (rotation cover); **`--bench-boost`** is the default max-15 (all 15 score) with
  an "all 15 score" note (its arbitrary-XI weight-1.0 form was dropped). `ask "build me a squad for
  rotation / for a bench boost"` picks the mode (`_bench_mode`); `build_squad` moved before `start_bench`
  in routing so "bench boost" isn't caught by "bench". The bench-aware build *designates* its XI (an exact
  breakout, saveable). No new dependency.
- **Sprint 044 (2026-08-05)** — *XI vs bench xP breakout* (a squad-build display completion; no new ADR,
  under ADR-031/041), from the owner's Sprint-43 note. `render_squad` gained an `xi_ids` param: it splits
  the 15 into XI + bench and, under `--objective xp`, prints **`Starting XI (11): projected N xP`** +
  **`Bench (4): projected M xP`** so build iterations compare on the *weekly-relevant* number.
  `cmd_squad` and `_decide_build_squad` auto-derive the XI via `best_legal_xi(selected, xp)` when no bench
  is declared — **display-only** (they don't touch `p["bench"]`, so `--save` is untouched); a declared
  `--bench` drives its own split. `ask "build me a squad"` carries the XI/bench xP in its facts, and the
  task now cites them — which also **fixed the recurring build-narration ⚠** (the LLM stated the grounded
  XI/bench points instead of inventing a cost split). No new dependency.
- **Sprint 043 (2026-08-05)** — *the differential archetype*, per ADR-044, completing ADR-043. Ingested
  **ownership** (`Player.selected_by` ← `selected_by_percent`; a storage column/migration; `refresh`
  populates it — a line-for-line copy of the `chance` field). `select_squad` gained **`min_differentials`**
  — one ILP line (`Σ pick[p] (selected_by ≤ 5%) ≥ N`; the xP objective picks the best qualifiers;
  players without ownership don't count). Surfaced as **`squad --full --differential N`** and wired into
  `build_squad` (the count already parsed) — the "coming soon" note gone. The **≤5%** threshold was
  pinned at the gate (the optimal squad has 2 ≤5% but 6 ≤10%, so ≤10% would be a no-op); a differential
  build tilts off-template at a small xP cost (e.g. −4 xP for +3 differentials). No new dependency.
- **Sprint 042 (2026-08-05)** — *squad archetypes*, per ADR-043, from the owner's multi-faceted build
  request. `select_squad` gained **`band_minimums=[(count, lo, hi), …]`** — one ILP line (`Σ pick[p]
  (lo ≤ price ≤ hi) ≥ count`), byte-identical when absent; `archetype_bands(cheap, premium)` maps counts
  to bands via tunable `LOW_COST_MAX=4.5` / `PREMIUM_MIN=9.0`. Surfaced as **`squad --full --cheap N
  --premium M`** and parsed from NL in `build_squad` (`_archetype_counts` → "3 low-cost … 1 premium");
  an infeasible ask (e.g. ≥6 premiums — only 5 exist) → a clear message, not a crash. The **differential**
  archetype is defined (low ownership) but deferred — `selected_by_percent` isn't ingested yet (Backlog);
  a requested differential returns a "coming soon" note. No new dependency.
- **Sprint 041 (2026-08-05)** — *show what you optimised + a "best players" intent*, per ADR-042 (and
  finishing ADR-041's display). **Part A:** under `--objective xp` (the default) the `squad` table now
  shows **`xMins` + `xP`** columns and a **projected xP total** (not last-season `Pts`) —
  `cmd_squad`/`_decide_build_squad` attach `xp`+`minutes_weight` from `decision_xp`; `render_squad`
  branches on `show_xp`. **Part B:** a seventh `ask` intent — **`shortlist`** (`ask "best <position>
  [under £Xm]"`): `_shortlist_query` parses position + a price cap + a `value` toggle; `_decide_shortlist`
  ranks the available pool by the unified `decision_xp` (or xP/£m for value), top ~8, via a new
  `ui/shortlist.py` table; grounded + verified, with a no-match message. No new dependency.
- **Sprint 040 (2026-08-04)** — *one xP metric + a squad-build intent*, per ADR-041, answering the
  owner's *"why does `transfer` improve my optimal squad?"* Cause: `squad` optimised **`points`**
  (last-season total) while the recommendations rank by **xP**, and even `--objective xp` used a
  *degraded* xP (horizon 1, no baseline/xMins). Fix: **`decision_xp(...)`** — one shared full-xP recipe
  (baseline + fallback + xMins) now used by `squad` (xp objective), `analyse`, `transfer`, and `ask`
  (removing the triplicated assembly); **`xp` is the default `squad` objective** (`--no-xmins` for raw;
  `--objective points` kept), so an xp-optimal squad leaves `transfer` nothing (a test locks it).
  **Phase 4:** `ask "build me a squad [for £X]"` (`_decide_build_squad` + `_squad_budget`) builds the
  optimal 15 on that xP, grounded + verified. Also fixed a latent **grounding-verifier bug** — a `£`
  in the facts was JSON-escaped to `£`, injecting stray digits that wrongly flagged a figure;
  `verify_grounding`/`_build_prompt` now use `ensure_ascii=False`. No new dependency.
- **Sprint 039 (2026-08-04)** — *trust the numbers* (data-quality), per ADR-040, from the owner's
  challenge of three RoboTS outputs. (1) **Sane low-evidence xP** — `fallback_rate` shrinks a no-baseline
  player's career pp90 toward a replacement prior (2.0) by confidence from their **biggest single
  season** (so a cameo like Benitez, or scattered cameos like Enes Ünal, can't project like a star);
  `player_xp` gained a three-tier rate (`hist` → `fallback` → `current`) via an optional
  `history_by_code`, byte-identical without it. (2) **Transfer dedup** — `suggest_transfers` now picks
  disjoint moves (each buy *and* each sell once; a sell whose best target is taken gets its next-best).
  (3) **Consistency** — extracted `best_legal_xi(owned, scores)`, the one primitive `analyse` (no
  bench) and start/bench both call, so they can't diverge; a note makes raw (`--no-xmins`) vs
  xMins legible. No new dependency.
- **Sprint 038 (2026-08-04)** — *two new `ask` intents — start/bench + compare* (**Phase 4 depth**),
  per ADR-039. **start/bench** (`ask "who should I start from <squad>?"`): the best legal XI on
  **xMins-weighted** xP (`select_squad`) diffed against the declared XI → the swap(s) or "already
  optimal" (`_decide_start_bench` + `_lineup_change` + `ui/startbench.py`). **compare**
  (`ask "A or B?"`): a robust name-matcher (`_match_players` — bounded substring, drop-substring
  overlap, ambiguity, not-found) → a side-by-side table (`ui/compare.py`); *the analytics state who's
  higher-xP, the LLM only narrates*. Both carry `subjects`, a structured detail table, and the ✓/⚠
  trust line (ADR-037), and degrade without the LLM. `assemble` gained a soft-`message` short-circuit
  (a specific not-found/ambiguous reply). Pure composition — no new analytics, no new dependency.
- **Sprint 037 (2026-08-04)** — *expected minutes (xMins) v0* (**Phase 3 depth**), per ADR-038. A new
  `analytics/minutes.py` — `chance_factor` × a recency-weighted **minutes share** (minutes-only;
  `starts` proved unreliable pre-2022/23 at planning) → `availability_weight ∈ [0,1]`, with graceful
  fallbacks (no history / no news → nailed-on; injured/suspended → 0). `player_xp` gained an optional
  `minutes_weight` hook (scales the total + per-GW; **byte-identical without it**), and the decision
  edge — `captain`, `transfer`, `analyse`, `ask` — passes it **default-on**, weighting xP by expected
  playing time so rotation risks stop out-ranking nailed-on starters. The weight is **shown as expected
  minutes** (an `xMins` column in captain/analyse; a note on transfer) with a **`--no-xmins`** opt-out;
  the raw `xp` command stays a pure *"assumes they play"* number (**generic core, policy at the edge**).
  The `history --backfill` coverage was broadened 29% → 87% so the signal fires. No new dependency. The
  full probabilistic model (congestion, rotation profiles, in-season minutes) remains Phase 5.
- **Sprint 036 (2026-08-04)** — *`ask "analyse"` gains a structured detail table* (US-107), under
  ADR-036. Pure **reuse/consistency**: `_decide_analyse` now threads the per-GW data into
  `analyse_squad` and renders the same `render_squad_analysis(...)` table the `analyse` command prints
  (XI + per-GW xP + weak links) as the decision's `detail` — so *"analyse TS"* reads like *"which 3
  transfers"* (detail table above the narration, no one-line headline). No new logic, no new ADR, no
  new dependency. (Also this sprint: **xMins** assessed and placed on the Backlog/Roadmap — a
  lightweight FPL-native v0, then a full ML model post-GW1 — US-108.)
- **Sprint 024 (2026-08-03)** — *shared table renderer* (tech-debt closer), per ADR-025. A new
  `ui/_table.py` holds the ranking tables' shared shape once — a `Col` spec
  (header/width/align/`fmt`) + `render_rows(rows, columns, rank=, divider=)`. The seam that keeps
  output **byte-identical**: `fmt` produces the finished cell string (truncation, number format),
  and `render_rows` only pads. **All five** ranking views (`table`, `xg`, `overperf`, `defcon`,
  `cleansheet`) migrated (US-071/072); every existing view test passed **untouched**. A pure
  refactor: the duplicated padding logic (written 5×) is now written once — each view shrank ~12%
  and became a declarative list of columns. (Raw line total is ~flat: the well-documented shared
  module offsets the per-view savings; the win is maintainability — a new view or column is a
  one-line change.) No behaviour change, no dependency.
