# Architectural Decision Record: Per-GW history ingestion + a dormant form blend

**Decision ID:** ADR-060
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** none — the first **Data Hardening** step. Extends the history archive of
ADR-027 (past seasons) into the current season, and the one-xP recipe of ADR-041 with an in-season form term.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The season starts at **GW1 (2026-08-21)**. Two of the highest-value features — *in-season form* and
*per-gameweek trends* — are gated on data that doesn't exist yet: the FPL `element-summary` **`history`**
array (this-season, per-GW) is **empty preseason**, and `players.form` reads **0.0**. The owner's call is to
**front-load** the plumbing now so GW1 is a *switch-flip*, not a scramble — but without changing any of
today's behaviour.

**Verified on real data (2026-08-06, Saka id 12):** `history` = **0 rows**; `history_past` = **8 seasons**
(already ingested, ADR-027); `players.form` = **0.0**. So anything we build must produce **byte-identical
output today** — the existing test suite is the invariance proof.

**Efficiency find:** `backfill_history` already calls `element-summary` **once per player** for
`history_past`. The **same payload carries `history`** — so per-GW ingestion can ride the existing throttled
walk, no second pass.

#### Decision Drivers
- **Dormant until GW1** — no behaviour change now; the season-start flip is a data refresh + one flag.
- **One xP metric (ADR-041)** — form must fold into the *single* `decision_xp` rate, not a parallel path.
- **Honest, minutes-aware form** — a computed rolling **pp90** (owner's call), not FPL's points-per-game
  `form` field (a fixed 30-day window, minutes-blind).
- **Additive, idempotent** — the schema grows the way the rest does (CREATE IF NOT EXISTS + add-missing
  columns; upsert), so an old cache and a fresh one converge.

---

### ✅ Decision

**1. A per-GW `player_history` table (US-196).** A new table, keyed `(element_code, round)` — `element_code`
is the stable id (so form can be looked up by the same `code` the xP baseline uses), `round` is the
gameweek. It's a **current-season working set** (the per-GW `history` payload carries `round` but **no
season name**, so a season key would need a magic constant); a new season simply re-backfills and the upsert
overwrites round-for-round. No FK to `players` (history outlives a player's presence, ADR-027). Columns kept
lean but useful: `minutes`, `total_points`, `was_home`, `opponent_team`, `fixture`, `kickoff_time` (additive
— room to grow). A `PlayerGameweek` model + `from_api(raw, element_code)` mirrors `PlayerSeason` (the per-GW
row has `element`, the season id, not the stable `code`, so the code is passed in from an id→code map).
`save_history` / `get_history` (+ a grouped `get_gw_history_by_code`) mirror the past-season methods.

**2. Ingestion rides the existing walk (US-196).** `backfill_history` **also** maps + stores each player's
`history` (per-GW) alongside `history_past`, from the one `element-summary` call (using an id→code map built
once). **Preseason it stores 0 per-GW rows** (verified) and errors on nothing; at GW1 the same command fills
it. Idempotent (upsert on `(element_code, round)`), per-player degrading (unchanged). The count of per-GW
rows stored is surfaced in the backfill's return + CLI output.

**3. A dormant form blend in the one recipe (US-197).** A pure `form_rate(gw_history)` computes a
**recency-weighted, minutes-aware rolling pp90** over the last **N** gameweeks:
```
form_pp90  = recency-weighted mean of (points·90 / minutes) over the last N GWs with minutes > 0
confidence = min(1, window_minutes / FORM_MIN_MINUTES)      # a cameo must not swing the rate
```
returning `None` when there's no per-GW history. It blends into the existing rate **inside `decision_xp`**
(nowhere else):
```
w    = FORM_WEIGHT × confidence             # FORM_WEIGHT defaults to 0 → dormant
rate = (1 − w) × base_rate + w × form_pp90  # base_rate = today's baseline/fallback/current tier
```
**`FORM_WEIGHT = 0` or `form_pp90 is None` ⇒ `rate = base_rate` exactly** — today's number. Threaded as an
optional `form_by_code` hook into `player_xp` (default `None` → unchanged); assembled in `decision_xp`.

**4. The GW1 flip.** `python app.py history --backfill` (now also per-GW) + set `config.FORM_WEIGHT > 0`.
In-season form then lights up **everywhere at once** (captain / transfer / analyse / squad / `ask`), because
they all share `decision_xp`.

---

### 🔀 Alternatives Considered

- **FPL's `form` field.** Rejected (owner's call): points-per-**game** over a fixed 30-day window,
  minutes-blind — less honest than a computed, minutes-aware rolling pp90. (We already store it for the
  crowd *flags*, ADR-057; that use stays.)
- **A separate in-season xP path.** Rejected — would re-introduce the very inconsistency ADR-041 removed.
  Form belongs *inside* `decision_xp`.
- **Ingest per-GW in a second dedicated walk.** Rejected — wasteful; the `history` array is in the payload
  the past-season walk already fetches.
- **Build only at GW1.** Rejected (owner's call): front-loading the plumbing now, dormant, de-risks the
  season start and lets the design be verified on real data first.
- **Ship the blend live now.** Impossible/meaningless preseason (no per-GW data, `form` 0) — and it would
  change nothing. Dormant-by-default is the honest state.

---

### 🧭 Consequences

**Positive**
- GW1 becomes a **flip** (a refresh + one flag), not a build — the risky season-start work is done and
  tested in the calm of preseason.
- The one-xP invariant (ADR-041) holds — form folds into the single rate; no parallel metric.
- Minutes-aware rolling pp90 is a more honest form signal than FPL's points-per-game.
- Per-GW history also unlocks later trend/rolling views (Backlog) at no extra fetch cost.

**Negative / risks (mitigations)**
- **The live per-GW row shape can't be seen preseason** (`history` empty) → design against the known FPL
  per-GW keys; **additive** schema + idempotent upsert mean an unexpected/extra field costs a one-line
  migration, not a rebuild. Acceptance: it fills at GW1 with **no schema change**.
- **A dormant feature can rot** → an **invariance test** pins "weight 0 (or no history) ⇒ output identical",
  and a **synthetic-history** test proves the blend shifts the rate the intended way — so the path is
  exercised now, not just at GW1.
- **Form weight/window need calibration** → `FORM_WEIGHT` and `N` live in `config`, documented as
  "set/tune at GW1"; the maths is inert until then.

---

### 📊 Validation

Probed live (2026-08-06): `history` empty, `history_past` = 8, `form` = 0.0 — the dormant premise holds.
Acceptance for the sprint: `player_history` stores rows from a fake per-GW payload and **0** from an empty
one (idempotent on re-run); `form_rate` returns the expected recency/minutes-weighted pp90 and `None`
without history; **invariance** — `decision_xp` with `FORM_WEIGHT = 0` (and preseason, no per-GW history)
equals today, pinned by a test; a **synthetic** per-GW history + a non-zero weight shifts a player's rate as
designed; the extended backfill stores **0 per-GW rows preseason without error**; the existing **530** tests
stay green.
