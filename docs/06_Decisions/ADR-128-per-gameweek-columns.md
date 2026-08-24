# Architectural Decision Record: Store the gameweek, not just the season total

**Decision ID:** ADR-128
**Date:** 2026-08-24
**Status:** ✅ **Accepted — built** (Sprint 179). The enabling change for two follow-ups already agreed in
ADR-118 and ADR-119; recorded as its own ADR because it changes the schema and needs a re-backfill.
**Superseded By / Replaces:** Widens the `player_history` table added by ADR-060.
**Deciders / Participants:** Tony Sheridan (Owner — "do 1 and 2"), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Two follow-ups were tracked as **display** work and turned out to share one blocker.

- **ADR-118 (Player DNA):** real per-stat **sparklines** and **W-D-L form dots**.
- **ADR-119 (Team DNA):** a real **clean-sheet rate** and **team form**, replacing labelled proxies.

Neither could be built. The season aggregates on `players` are a **running total** — they know a player has 3
goals, never which weeks — and `player_history` stored only **8 of the 41 fields** FPL returns per gameweek:

```
stored:     element_code round minutes total_points was_home opponent_team fixture kickoff_time
not stored: goals_scored assists clean_sheets goals_conceded saves bonus bps expected_goals
            expected_assists expected_goal_involvements expected_goals_conceded ict_index
            influence creativity threat defensive_contribution team_h_score team_a_score value …
```

A W-D-L dot needs the **scoreline** (`team_h_score` / `team_a_score`); a sparkline needs the **per-week** stat;
a real clean-sheet rate needs per-week `clean_sheets`. None of it was there.

---

### ✅ Decision

**Widen `player_history` from 8 columns to 27** and re-run the backfill.

**Take a generous column set in one pass.** The expensive part is the walk — one `element-summary` call per
player, 609 of them — not the columns. Adding a column later would mean paying that walk again for one field,
so everything with a plausible near-term use came along: the scoreline, per-week returns (goals, assists, clean
sheets, conceded, saves, bonus, bps), the expected stats (xG, xA, xGI, xGC), the ICT components, defensive
contribution, and `value` (the per-week price, which the backlog's long-open price-sparkline follow-up needs).

**Existing databases upgrade in place.** The `_MIGRATIONS` machinery already exists for exactly this; verified
against the live database — 8 → 27 columns, all 604 rows preserved, existing values intact, new columns null
until the backfill fills them.

**A new pure `analytics/gw_form.py`** reads it: `match_result`, `form_dots`, `stat_series`, `team_form`,
`team_clean_sheet_rate`.

#### The trap this had to design around

FPL writes a per-GW row when a fixture is **scheduled**, not played (ADR-125) — a row of zeros with no
scoreline. So **row presence proves nothing, and neither does `minutes`**: an unused substitute and a player
whose match kicks off tonight both read 0. Everything here judges "played" on the **scoreline being present**,
which only exists once a match has a result.

That is not theoretical. On the day this shipped, Chelsea's and Fulham's opener had not kicked off:

```
ARS: form=[(1, 'W')]  clean-sheet rate=100%      CHE: form=[]  clean-sheet rate=— (keeps the proxy)
LIV: form=[(1, 'D')]  clean-sheet rate=0%
```

Without the guard, both clubs would have read *0% clean sheets* and a blank form line as though they had played
and failed.

#### Two honesty rules carried forward

- **The clean-sheet axis falls back per team**, not globally: a club with results shows `actual`, a club
  without keeps the labelled `def + fix` proxy. One club being ahead of another does not force everyone onto
  the weaker measure, or the stronger one onto a fact it lacks.
- **A sparkline needs two gameweeks.** With one it draws nothing at all, rather than a line through a single
  point. Same rule as the trend card and the DNA radar — this is the third time; it is now a project principle.

---

### 🔀 Alternatives Considered

- **Add only the columns the two features need** (scoreline + `clean_sheets`). Rejected: it saves nothing at
  write time and costs a second 609-call walk the first time anything else wants a per-week number.
- **Derive results from the `fixtures` table** instead of storing the scoreline. Rejected: `fixtures` carries
  no scores, and adding them there would need its own ingest change while still leaving the per-week stats
  missing.
- **Compute weekly values by differencing the season totals.** Rejected: the totals are a snapshot at refresh
  time, not a per-round series — there is nothing to difference against.
- **Ship the display work against the season aggregates.** Rejected: it is the thing that cannot be done. A
  "trend" from a single cumulative number is a straight line by construction.

---

### 🧭 Consequences

**Positive** — both tracked follow-ups become buildable and are built; the widened table also unblocks the
price sparkline, rolling 3-/6-GW form windows, and the crowd backtest without another walk; the migration
upgrades existing databases with no reseed.

**Negative / risks (mitigations)** — `seed.db` grows (381 KB → ~406 KB) (*mitigation:* trivial, and it is the
file the deployed app reads); a re-backfill is needed once (*mitigation:* idempotent, resumable, ~5 minutes,
and already routine); more columns is more surface to keep mapped (*mitigation:* one `from_api` and one upsert,
both covered by tests).

---

### 🧾 Status & follow-ups

- **Built (Sprint 179).** Schema + migration + model + upsert; `analytics/gw_form.py`; the Player DNA card
  gains W-D-L dots and a per-stat sparkline grid; the Team DNA card gains a form row and the real clean-sheet
  rate. 1170 → **1188 tests**.
- **Follow-ups this now unblocks:** the per-season **price sparkline** (backlog, long open); rolling 3-/6-GW
  form windows; the Tier-3 crowd backtest.
- **Follow-up done (same day): `Squad Depth`.** It counts players with ≥1500 minutes — about 17 matches — so
  for most of a season *every* club reads the same number and the axis carries no information (a flat 50 across
  the league once ADR-127 stopped ties reading as 100). It now falls back to last season's squad while this
  season cannot separate anyone, and hands the ranking back the moment it can. Restores real spread: MCI 15
  (100th) · CHE 14 (92nd) · ARS 13 (76th) · SUN 11 (53rd) · LIV 10 (37th).

  **Scaling the threshold to games played was measured and rejected.** After one gameweek it sorts 20 clubs
  into 5 buckets and still reads 0 for a club yet to kick off — a weak signal that *looks* like a real one,
  which is the failure mode this project keeps choosing against. Last season gives 10 distinct values and
  covers every club with history.
