# Sprint 179: Store the gameweek, not just the season total — and the two DNA follow-ups it unblocked (ADR-128)

**Dates:** 2026-08-24
**Status:** ✅ Complete — ADR-128, closing ADR-118's and ADR-119's tracked GW1 follow-ups. 1170 → 1191 tests.

> **Owner:** "do 1 and 2" — the Player-DNA and Team-DNA GW1 follow-ups.

---

### 🔍 What the investigation changed

Both items were logged as **display** work. Neither was buildable: the season aggregates on `players` are a
**running total** — they know a player has 3 goals, never which weeks — and `player_history` stored **8 of the
41** fields FPL returns per gameweek. No scoreline, so no W-D-L. No per-week stats, so no sparkline. No per-week
`clean_sheets`, so no real clean-sheet rate.

So it wasn't two display tweaks; it was one ingest change with two features on top.

---

### 🔧 What shipped

**The table went 8 columns → 27**, with a `_MIGRATIONS` entry so existing databases upgrade in place — verified
against the live one (8 → 27, all 604 rows preserved, values intact). Then a re-backfill: **609 players, 2051
season rows + 609 per-GW rows**.

**A generous column set, deliberately.** The walk is the expensive part — one API call per player, 609 of them —
not the columns. Adding one later would mean paying that walk again, so everything with a plausible near-term
use came along, including `value`, which the backlog's long-open price-sparkline item needs.

**`analytics/gw_form.py`** (pure): `match_result` · `form_dots` · `stat_series` · `team_form` ·
`team_clean_sheet_rate`.

**Player DNA** gains the team's W-D-L run and a per-stat sparkline grid (Points · BPS · xG · xA · ICT · Minutes).
**Team DNA** gains a form row and the real clean-sheet rate in place of the `def + fix` proxy.

---

### 🪤 The trap it had to design around

FPL writes a per-GW row when a fixture is **scheduled**, not played (ADR-125) — a row of zeros with no
scoreline. **Row presence proves nothing, and neither does `minutes`:** an unused substitute and a player whose
match kicks off tonight both read 0. Everything here judges "played" on the **scoreline being present**.

Not theoretical — on ship day, Chelsea's and Fulham's opener hadn't kicked off:

```
ARS: form=[(1,'W')]  clean-sheet rate=100%     CHE: form=[]  rate=— (keeps the proxy)
LIV: form=[(1,'D')]  clean-sheet rate=0%
MCI: form=[(1,'W')]  clean-sheet rate=0%
```

Without the guard both clubs would have read **0% clean sheets** and a blank form line, as though they had
played and failed.

---

### ✅ Definition of Done

- **Automated:** 1170 → **1191 tests**, green, ruff clean. 12 on `gw_form` (result from either side of the
  scoreline, unplayed fixtures excluded from both dots and series, per-90 dropping minuteless weeks, team form
  from the fullest record, clean-sheet rate from the keeper and ignoring a benched one, None before a team has
  played), 6 on the display helpers, 3 on the Team DNA axis switching.
- **Manual smoke:** both real pages through `AppTest` — Players ▸ Card shows a form dot and no sparklines (one
  gameweek, by design); Fixtures ▸ Team DNA shows a `W` pill and the `actual` clean-sheet sublabel.
- **Docs:** ADR-128, this sprint doc, PROJECT_STATUS, Roadmap (items 1-3 marked done).

---

### 📝 Lessons

**"It's just a display change" is a hypothesis, not a scope.** Two items sat on the roadmap for months as
display work. Ten minutes of looking at the actual payload showed both were blocked on the same ingest gap.
Checking what the data *contains* before estimating would have caught it at planning time.

**When the walk is the cost, take the columns.** 19 extra columns cost nothing; a second 609-call backfill to
add one costs five minutes and a round of API traffic. Breadth is cheap exactly when depth is expensive.

**The same honesty rule, third application.** A sparkline needs two points, a trend card needs two gameweeks, a
radar needs three ranked axes. Each was found the hard way; together they're now a principle in the roadmap:
never render a missing value as a confident zero.

---

### 🔭 Follow-ups

- **Unblocked by the widened table:** the per-season price sparkline (long open in the backlog), rolling
  3-/6-GW form windows, the Tier-3 crowd backtest.
- **`Squad Depth` — done the same day.** ≥1500 minutes is about 17 matches, so for most of a season every club
  reads the same number and the axis says nothing (a flat 50 once ADR-127 stopped ties reading as 100). It now
  falls back to last season's squad while this season cannot separate anyone: MCI 15 (100th) · CHE 14 (92nd) ·
  ARS 13 (76th) · SUN 11 (53rd) · LIV 10 (37th).

  **Scaling the threshold to games played was measured and rejected** — after one gameweek it sorts 20 clubs
  into 5 buckets and still reads 0 for a club yet to kick off. A weak signal that looks like a real one is
  worse than an honest fallback, which is the same call as the boards, the trend card and the radar.
