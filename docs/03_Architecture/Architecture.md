# Architecture — v0.1 (Draft for Agreement)

**Status:** Draft — pending review
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
| **API client** | Make HTTP requests to the FPL API, return raw JSON | Interpret or store data |
| **Parser / mapper** | Turn raw JSON into simple, explicit Python objects (only the fields we use) | Fetch or persist |
| **Storage (repository)** | Save and load players from SQLite | Know about HTTP or display |
| **Presentation** | Show players as a table (console for now) | Fetch or store |
| **Config** | Endpoints, DB path, constants in one place | Business logic |

Each of these becomes a small module (see §7). The boundaries matter more than the
file names — the point is that the API client knows nothing about SQLite, and the
display knows nothing about HTTP.

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

## 9. Open decisions (need agreement — candidates for ADRs)

These come from the Roadmap and gate later architecture. Provisional stances for
v0.1 are noted, but each deserves a decision record in `docs/06_Decisions/`.

1. **Internal tool vs multi-user product.** *(Roadmap Phase 1)*
   Provisional: **single-user / internal** for now. This is the simplest path and
   fits a learning project. The DB schema already leaves room for multi-manager
   analysis later. → **ADR-001**
2. **UI approach.** Console now; FastAPI + (React/Next.js vs Streamlit/Dash) later.
   Provisional: **console → FastAPI**, UI framework deferred. → **ADR-002**
3. **Caching strategy.** v0.1 uses "fetch once, then read SQLite" with manual
   refresh. TTL-based auto-refresh (and whether Redis is ever needed) is deferred.
4. **Storage engine longevity.** SQLite now; when/whether to move to PostgreSQL.

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
