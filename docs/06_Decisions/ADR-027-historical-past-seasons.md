# Architectural Decision Record: Historical past-season data (`history --backfill`)

**Decision ID:** ADR-027
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (first historical data; a second FPL endpoint)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Phase 2 opens with the highest-value item: **historical trend data** to ground xP (and, later,
Phase 3 decision support). A planning probe of the live FPL API settled *what is actually
available* before any design:

- **We are preseason** — 0 of 38 gameweeks finished. So *this* season has **no per-GW history
  yet** (`element-summary` → `history` is empty for everyone); the bootstrap `total_points` is
  **last season's** total carried over.
- The available history is **per-*season*, not per-*gameweek***: `element-summary/{id}/` →
  **`history_past`** gives a rich per-season summary per player (points, minutes, goals, assists,
  clean sheets, goals conceded, xG/xA/xGI/xGC, defensive_contribution, starts, start/end cost),
  keyed by **`element_code`** — the stable cross-season id (the per-season `id` changes yearly).
- It is a **per-player endpoint at scale**: **567** players × 1 call each; players have **4–6**
  past seasons (some young players **0**). Past-season data is **static within a season**.

So "historical trend data" available now = **multi-season summaries**. That is the *ideal* xP input
**preseason** — with no current-season form, a multi-season baseline is the best available signal.
FPL-native, **no new dependency** (consistent with the soccerdata deferral, ADR-016).

#### Decision Drivers
- **Use the best signal available now** — preseason, that's multi-season history.
- **Respect rate limits** — 567 calls is not one bootstrap; don't punish every `refresh`.
- **Keep it simple & FPL-native** — no scrapers, no external historical datasets.

---

### 💡 Decisions

**1. Source: FPL `element-summary/{id}/` → `history_past`.** Per-season summaries, FPL-native. A
**second FPL endpoint** (the first beyond `bootstrap-static`/`fixtures`). Scope this sprint is
**past-season summaries**; per-GW `history` is empty preseason and is **deferred** (same endpoint,
ingest once gameweeks play — see Backlog).

**2. Store keyed by `element_code` (stable across seasons).** A new table `player_history_past`,
**PK (`element_code`, `season_name`)**, via the existing generic-migration pattern. Columns: the
stat fields above. `element_code` is present in the bootstrap (`elements[].code`), so history joins
to the current per-season `id` at read time (verified: Haaland `id=411` ↔ `code=223094`).

**3. A dedicated, throttled `history --backfill` command — not `refresh`.** `refresh` stays one
fast bootstrap call. `history --backfill` fetches `element-summary` for every player, **throttled**
(an inter-call sleep + the `with_retry` helper), **degrades per-player** (one failure skips that
player, never aborts the run), and is **idempotent** (upsert on the PK, so a partial/interrupted
run resumes safely). Run **once per season** — the data is static within a season. `history` gets
its own command home (a later `history <player>` can display a season-by-season trend).

**4. Data-provenance caveat — newer stats read 0 in old seasons.** The probe found
`defensive_contribution` = **0 for 2022/23 and 2023/24** (the FPL stat did not exist yet), then
73/104. **A 0 here means "the stat didn't exist," not "zero actions"** — the same trap as
preseason strengths being 0.

*Extended by a US-077 smoke finding:* the **expected_* fields (xG/xA/xGI/xGC) are also unreliable
in older seasons** — for many players FPL sends a hard `'0.00'` (a string zero, not null) before
~2024/25, even though a marquee player like Haaland happens to have real xG back to 2022/23. The
planning sample (Haaland alone) was misleading; the broad backfill is the truth.

**Consequence for xP enrichment (ADR-028):** rely only on fields **reliably present across all
seasons — `total_points`, `minutes`, `goals_scored`, `assists`** — and treat `xG/xA/xGI/xGC` and
`defensive_contribution` as **recent-seasons-only** (a `0.00`/`0` in an old season = "not tracked",
not a real zero). All fields are still stored faithfully; the caveat is about *consumption*.

**Not in scope:** per-GW `history` ingestion (deferred); external per-GW datasets
(vaastav/scrapers); a first-class xP engine (ADR-028 is a *baseline*, not the full engine).

---

### 🧪 Worked example (pressure-testing — real data, before code)

Haaland's `history_past` as it would be stored (`element_code=223094`):

| Season | pts | mins | xGI | DC | starts |
|---|--:|--:|--:|--:|--:|
| 2022/23 | 272 | 2767 | 31.65 | **0** | 33 |
| 2023/24 | 217 | 2553 | 31.75 | **0** | 29 |
| 2024/25 | 181 | 2736 | 23.94 | 73 | 31 |
| 2025/26 | 239 | 2953 | 28.17 | 104 | 34 |

Confirms: `element_code` joins to the current player; the fields xP needs are populated across all
four seasons; and the DC-zero provenance trap is real (and now designed around).

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the project's first historical data — a multi-season baseline for xP that's robust
  preseason, and the foundation Phase 3 will build on. FPL-native; no new dependency; `refresh`
  stays fast.
* **Negative / Trade-offs:** a full backfill is ~567 throttled calls (~minutes) — but run rarely
  (static data). Per-GW within-season trends aren't available yet (deferred). Historical DC is
  unusable across seasons (caveat).
* **Risks & Mitigations:**
  - *Rate-limiting (429) / slow* → throttled + `with_retry`; idempotent (resumes); out of `refresh`.
  - *0-season players* → store nothing; readers fall back to the current snapshot; never crash.
  - *`element_code` vs `id` confusion* → key on `element_code`; map to `id` at read time.
  - *Misusing a 0 stat as real* → the DC caveat; consume only all-season-present fields.

---

### 🛠 Implementation & Migration
* **Components Affected:** `src/api/client.py` (a `get_element_summary(id)` method); `src/storage.py`
  (`player_history_past` table + generic migration + upsert); `src/cli.py` (`history --backfill`,
  throttled, per-player degrade); Docs (Data Sources, Architecture, Handbook). `refresh` and the
  optimiser are untouched.
* **Action Items:**
  - [x] Record the design + worked example + the DC caveat (US-076)
  - [ ] `element-summary` client + `player_history_past` table + `history --backfill` (US-077)
  - [ ] Enrich xP with a multi-season baseline (US-078, ADR-028)
  - [ ] (Backlog) ingest per-GW `history` once gameweeks play; a `history <player>` trend view

---

### 🔄 Review & Reconsideration
* **Review Date:** Once the season starts (per-GW `history` becomes available) or if a full backfill
  hits rate limits in practice.
* **Triggers for Reconsideration:**
  - [ ] Per-GW trends needed → ingest `history` (same endpoint) into a per-GW table.
  - [ ] Deeper history than FPL offers (>~6 seasons, per-GW past) → revisit an external dataset.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-076 (this), US-077, US-078
- **External Docs:** [ADR-016 (soccerdata — defer, lightweight)](./ADR-016-soccerdata-evaluation.md) · [ADR-006 (xP v0)](./ADR-006-expected-points-v0.md) · [ADR-021 (retry helper)](./ADR-021-importance-scaled-retry.md) · [Sprint 026](../05_Sprints/Sprint26.md)
