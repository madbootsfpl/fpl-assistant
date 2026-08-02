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
        │                 Presentation                 │
        │        (print a player table for now)        │
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
