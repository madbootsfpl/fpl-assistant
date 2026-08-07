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
