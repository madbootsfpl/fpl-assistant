# Sprint 176: The gated stat boards answer from last season until they can answer from this one (US-432, ADR-126)

**Dates:** 2026-08-24
**Status:** ✅ Complete — ADR-126. 1129 → 1140 tests, ruff clean.

> **Owner:** gated the ADR, then "build it".

---

### 🎯 The problem — ten weeks of blank boards, not four

```
                 rows
Over / under        0
Clean sheets        0
Defensive Contrib.  0
```

All three gate at `MIN_MINUTES = 900`. US-430's 🌱 note shipped on the assumption this cleared around GW4-6; it
does not. 900 minutes is about ten matches, so a nailed-on starter first qualifies at **game 10** and the boards
fill gradually over the following two or three weeks. That is most of the window in which a new tester decides
whether the tool has anything to say.

**The gate itself is not the bug.** It is the Sprint 016 Meslier lesson (ADR-017/018): a 20-minute cameo
invented a points-per-90 above 9.0. A per-90 off a tiny sample is not a weak signal, it is a wrong one, and a
board sorted most-extreme-first puts the wrongest rows on top. Lowering it would have filled the boards with
exactly the nonsense the gate exists to exclude.

What changed is that we now **hold the answer**: Sprint 175's backfill populated `player_history_past` with 464
rows for 2025/26, carrying xG, xA, xGC and DefCon — not just the points and minutes the xP baseline uses.

---

### 🔧 What shipped

**The design cost nothing structurally.** All three board functions are pure over *player-shaped mappings*,
reading only `position`, `minutes` and a few stat fields. So last season needed **no change to any of the three
analytics modules** — project the history row into the same shape and call the same function.

`src/analytics/last_season.py` (pure):

- `last_season_name(history)` → the season label, taken from the data rather than hardcoded, so it cannot drift
  from the numbers beneath it.
- `last_season_rows(players, history)` → each player's row for that season, in `get_players()` shape. Identity
  (`id`, `web_name`, `team`, `position`) comes from the **current** row, so a player appears under the club
  they play for now — the club being decided about.

In the view, a `_this_or_last` helper runs the board's own function on this season and falls back only when that
returns nothing, and `_board` gained a banner naming the season.

```
Over / under     this: 0   →  last: 272 rows
DefCon           this: 0   →  last: 253 rows
Clean sheets     this: 0   →  last: 118 rows
```

Verified through the real page, not just the analytics:

```
📅 Showing 2025/26 — this season's numbers need about 10 matches before a per-90 rate means anything,
   so these are last season's until then. The board switches over on its own as players reach that mark.
   ⚠️ xGC is a team stat, so a player who changed clubs over the summer is showing his old team's defence here.

   Calafiori  ARS  DEF  1697 mins  xGC/90 0.52  🟢 excellent (top 1%)
   J.Timber   ARS  DEF  2452 mins  xGC/90 0.64  🟢 excellent (top 1%)
   Saliba     ARS  DEF  2614 mins  xGC/90 0.70  🟢 excellent (top 2%)
```

The whole Arsenal back line at the top of a defensive board is the sanity check passing.

**The clean-sheet caveat is on screen because it has to be.** `player_history_past` records what a player did
without recording who for, and xGC is a *team* stat — so a summer signing brings his old side's defensive record
under his new side's badge. The other two boards are player-level: a striker's xG and a midfielder's defensive
actions travel with him.

---

### 🔁 The correction during the build

The plan said to take each player's **most recent stored season**. On the live data that quietly mixed seasons —
47 players last appeared in the Premier League in 2024/25, so they would have rendered under a banner reading
"2025/26". A true number under a false label is precisely what this ADR exists to prevent, and the plan walked
straight into it.

`last_season_rows` now resolves the most recent season **across the pool** and returns only rows belonging to
it, so the label and the data agree *by construction* rather than by the caller remembering to be careful. The
47 are omitted — the honest answer for a player who was not in the league.

Caught by comparing the built code's row counts against the numbers measured during the gate: 511 projected
where the investigation had said 464.

---

### ✅ Definition of Done

- **Automated:** 1129 → **1140 tests**, green, ruff clean. 9 on the projection (field mapping, the per-90
  derivation, identity from the current row, the wrong-season skip, no-history, zero-minutes, and the three
  boards consuming it unchanged, plus the 900-minute gate still applying to last season) and 2 AppTests on the
  rendered page (the banner names a season and a table appears; the clean-sheet caveat).
- **Manual smoke:** all three boards rendered through `AppTest` against the live data — 272 / 253 / 118 rows,
  banner present, caveat present on clean sheets only.
- **Docs:** ADR-126, this sprint doc, PROJECT_STATUS.

---

### 📝 Lessons

**"Empty" and "wrong" are not the only options.** The parked decision had been framed as a choice between an
honest blank board and a dishonest lowered gate. The third option — a different, clearly-labelled *source* —
only became available once the backfill landed, and it needed no compromise on either side.

**A label is a claim, and claims need to be true by construction.** Taking "each player's most recent season"
and calling it "last season" was fine for most players and quietly wrong for 47. Making the function resolve one
season for the whole pool means the label cannot be wrong, rather than being right as long as nobody changes
the caller.

**Purity paid a dividend nobody planned for.** The three boards being pure functions over plain mappings is why
last season needed zero analytics changes. That property was chosen for testability years of sprints ago; it
happened to make an unrelated feature nearly free.

---

### 🔭 Follow-ups

- The **Team DNA card's "key players to target"** table has the same 900-minute gate and the same fix available.
- The **xG board** needs no fallback — no minutes gate, and it already shows data.
- The fallback retires itself board by board as players clear 900; nothing to remember to switch off.
