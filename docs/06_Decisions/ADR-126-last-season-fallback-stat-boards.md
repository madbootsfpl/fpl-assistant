# Architectural Decision Record: The season-to-date boards fall back to last season until they can answer

**Decision ID:** ADR-126
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved ("build it"), built.** Sprint 176 / US-432. Coverage and output below
are measured on the live data.
**Superseded By / Replaces:** Resolves the option parked on 2026-08-22 (Feedback_Log) when US-430 shipped the
🌱 empty-state note as the stopgap. Extends ADR-017 / ADR-018 / ADR-019 (the three boards) without changing any
of them.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Three of the four stat boards are empty and will stay empty for roughly ten gameweeks:

```
                 rows today
Over / under          0
Clean sheets          0
Defensive Contrib.    0
```

All three gate at `MIN_MINUTES = 900` — about ten matches. That gate is *correct* and hard-won: it is the
Sprint 016 Meslier lesson (ADR-017/018), where a cameo of 20 minutes invented a points-per-90 above 9.0. A
per-90 rate off a tiny sample is not a weak signal, it is a wrong one.

US-430 shipped the honest 🌱 note ("Early season — fills in as games are played") as a stopgap on the assumption
this resolved around GW4-6. It does not: the gate is 900 minutes, so a nailed-on starter first clears it at
**game 10**, and the boards fill gradually over the two or three weeks after. That is ten weeks of three empty
boards, during the exact window new testers are forming a view of whether the tool has anything to say.

Meanwhile we hold the answer. The Sprint 175 backfill populated `player_history_past` with 464 rows for
**2025/26** — and those rows carry far more than points and minutes:

```
season     rows  ≥900 mins   xGI   xGC   DefCon   clean sheets
2025/26     464        272   381   403      368            329
```

#### Decision Drivers
- **Ten weeks is most of the window that matters** — the boards are a browse surface for new users, and they are
  blank exactly when someone is deciding whether to trust the tool.
- **The gate must not move.** Lowering it to fill the boards would make them wrong rather than empty, which is
  strictly worse and undoes a lesson the project already paid for.
- **The data is already local** — backfilled, indexed, and read by `get_history_by_code()` for the xP baseline.

---

### ✅ Proposed Decision

**When a board cannot be answered from this season, answer it from last season — clearly labelled — instead of
showing nothing.**

The three board functions are pure over *player-shaped mappings*, reading only `position`, `minutes`, and a few
stat fields. So last season needs **no change to any of the three analytics modules**: project last season's row
into the same shape and pass it to the same function.

A new pure `analytics/last_season.py`:

```python
last_season_rows(players, history_by_code) -> list[dict]
```

pairing each current player with their most recent `player_history_past` row (`history[-1]` — the table holds
*past* seasons, so that is 2025/26) and mapping the fields the boards read:

| board | fields projected |
|---|---|
| Over / under | `expected_goals → xg`, `expected_assists → xa`, `goals_scored`, `assists`, `minutes` |
| Clean sheets | `expected_goals_conceded → xgc`, `minutes` |
| DefCon | `defensive_contribution × 90 ÷ minutes → defcon_per90`, `minutes` |

Identity fields (`id`, `web_name`, `team`, `position`) come from the **current** row, so a player appears under
the club they play for now — which is the club you are deciding about.

Each `render_*` board computes this season first and falls back only when that comes back empty, swapping the
caption for one that says plainly which season is on screen. The 🌱 note stays for the case where there is no
last-season row either.

#### Measured on the live data

```
                 this season   last season
Over / under               0           272
Clean sheets               0           118
DefCon                     0           253
```

And it produces sense, not noise — the top of the last-season clean-sheet board is the whole Arsenal back line,
which is exactly who it should be:

```
Calafiori  ARS  DEF  xGC/90 0.52     Gabriel  ARS  DEF  xGC/90 0.72
J.Timber   ARS  DEF  xGC/90 0.64     Raya     ARS  GK   xGC/90 0.74
Saliba     ARS  DEF  xGC/90 0.70
```

#### The caveat that must be on screen

`player_history_past` records what a player did, not who they did it for — and **xGC is a team signal**. A
defender who changed clubs over the summer carries his *old* team's defensive record while displaying his *new*
team's badge. On the clean-sheet board that is actively misleading and the label has to say so.

The other two boards are player-level: a striker's xG and a midfielder's defensive actions travel with him, so
"last season" is the only caveat they need.

---

### 🔀 Alternatives Considered

- **Lower the 900-minute gate early season.** Rejected outright. This is the Meslier bug (ADR-017/018) — the
  boards would fill immediately with per-90 rates extrapolated from single cameos, ranked most-extreme-first,
  which is precisely how a rate board goes wrong. Empty is better than wrong; last season is better than both.
- **Blend last season with this season as the sample grows.** Rejected: two seasons in one number cannot be
  labelled honestly, and a reader cannot tell what they are looking at. One season or the other, named.
- **Wait for a minimum row count before switching to this season** (e.g. only switch at 20+ rows). Rejected as
  a magic constant. This season's board is the truthful answer to "this season" the moment it has one, and it
  fills over two to three weeks as the regulars clear 900.
- **Show both seasons side by side.** Rejected: it doubles a browse surface permanently to serve a condition
  that lasts ten weeks.
- **Keep the 🌱 note.** Rejected — that is the status quo this exists to fix.

---

### 🧭 Consequences

**Positive** — three boards become useful immediately instead of at ~GW10, on data already local; the 900-minute
gate and all three analytics modules are untouched, so the lesson they encode is preserved exactly; the fallback
self-retires board by board as this season's data arrives, with nothing to remember to switch off.

**Negative / risks (mitigations)** — last season is not this season, and squads change (*mitigation:* the label
says which season is on screen, and it is shown only while the alternative is a blank board); a transferred
defender's xGC belongs to his old club (*mitigation:* named explicitly on the clean-sheet board, the only one
where the stat is a team signal); the board visibly shrinks when it switches over, from ~118 last-season rows to
however many players have cleared 900 this season (*mitigation:* honest — those are the players this season can
actually speak to — and it refills within two or three weeks); players new to the Premier League have no
last-season row and are absent from the fallback (*mitigation:* correct, and the same players the 🌱 note
covers).

---

### 🧾 Status & follow-ups

- **Accepted — built (Sprint 176 / US-432).** `analytics/last_season.py` (pure); a `_this_or_last` helper in
  the Players view; the three boards falling back and naming the season in a banner, with the club-change
  caveat on clean sheets; the Players page reading `get_history_by_code()`. 11 tests. 1129 → **1140**, ruff
  clean.
- **One thing the build changed from the plan.** The plan said to take each player's *most recent* stored
  season. On the live data that quietly mixed seasons: 47 players last played in the Premier League in 2024/25,
  so they would have appeared under a banner reading "2025/26" — a true number under a false label, which is
  the single thing this ADR set out to avoid. `last_season_rows` now resolves the most recent season **across
  the pool** and returns only rows from it, so label and data agree by construction rather than by the caller
  being careful. Those 47 players are omitted, which is the honest answer for them.
- **Follow-up done (same day):** the Team DNA card's "key players to target" table had the same 900-minute
  gate, and `team_key_players` is pure over the same shape, so it took the same fallback — a
  `key_players_this_or_last` helper and three more projected fields (`total_points`, `xgi`, `selected_by`).
  Wired into both call sites: Fixtures ▸ 🧬 Team DNA and My Squad ▸ Health ▸ "Your teams". One field is
  deliberately *not* last season's: `selected_by` comes from the live row, because ownership is only ever a
  statement about the present — last season's closing ownership would say nothing about who is differential
  this week, and FPL does not store it. The table's note says "Ownership is current" for that reason.
- **Still not this ADR:** the xG board needs no fallback (no minutes gate, already shows data).
