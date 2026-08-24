# Sprint 175: The GW1 history backfill, and the two dormant bugs it woke up

**Dates:** 2026-08-24
**Status:** ✅ Complete. 1123 → 1129 tests, ruff clean. A data operation plus the two defects running it exposed.

---

### 📥 The backfill

`player_history` was empty, so the per-GW sparklines, the W-D-L form dots and the ADR-060 form blend all had
nothing to read. `refresh` does not populate it — it needs the throttled `history --backfill`, one
`element-summary` call per player.

```
Backfilling past-season + per-GW history for 604 player(s)…
Stored 2045 season rows + 604 per-GW rows across 604 player(s).
```

604/604, no failures. Copied to the committed `seed.db` (348,160 → 380,928 bytes) so the deployed app gets it —
a **plain copy, not `reseed`**, which would also have re-fetched a fresh FPL snapshot; that is the owner's call,
not a side effect of a backfill.

**xP moved for 5 players, and correctly.** `FORM_WEIGHT` is still 0, so the form blend stayed dormant as
designed. The movement came from the *past-season* half of the walk: Mudryk, Tomiyasu, Hamer, Charles and
Florentino had no stored history and were being treated as cold-start unknowns. They now have real baselines:

```
Mudryk      cold_start 2.00  →      hist 5.41
Tomiyasu    cold_start 1.69  →      hist 4.89
Hamer       cold_start 1.99  →      hist 3.34
Florentino  cold_start 1.50  →      hist 3.60
Charles     cold_start 1.50  →  fallback 2.04
```

Tiers: `hist` 352 → 357, `fallback` 124 → 125, `cold_start` 128 → 122.

---

### 🐛 Two dormant bugs, woken by the same data

Both had been shipped and correct-looking for months. Neither was a regression; both had simply never executed.

**1. `calibrate` crashed on the first real per-GW history.** `backtest.rounds_with_actuals` called `.get()` on
its rows — fine for the dicts every test passes, fatal for the `sqlite3.Row`s the CLI passes, which index but
have no `.get`. It stayed invisible all preseason because `gw_history_by_code` was empty and the loop body never
ran. The backfill executed it for the first time and it raised `AttributeError` — taking out the ADR-101
calibration harness, which is the exact tool needed for the upcoming `FORM_WEIGHT` decision.

Fixed with the row-safe `_get` the other analytics modules already keep, and pinned with tests that pass **real
`sqlite3.Row` objects** — a stand-in dict cannot reproduce this. `calibrate` now answers honestly:
*"Not enough gameweeks yet — have 1, need ≥4."*

**2. The performance-trend chart drew every player as a flatline at zero.** The line normalises to a player's own
min..max, so a single gameweek has no range: `span = (hi - lo) or 1` fell back to 1 and `py()` put the point at
`v == lo` — the chart *floor*. After GW1 every player has exactly one result, so this was not an edge case, it
was everyone. Sangaré's 14 and Haaland's 2 rendered identically, both reading as "scored nothing".

This one was **activated by the backfill**: before it, the honest "Fills in from Gameweek 1" placeholder showed.
Populating the history replaced a truthful placeholder with a misleading chart.

- **One gameweek** now states the score — a big number, "points in GW1", and *"One gameweek is a result, not a
  trend — the line draws from GW2."* No chart, so there is no direction to misread.
- **A flat run** (n ≥ 2, every week the same) now centres vertically instead of flooring. A steady 6-a-week
  return is flat, not zero.
- **A varied run is untouched** — min still floors, max still tops.

---

### ✅ Definition of Done

- **Automated:** 1123 → **1129 tests**, green, ruff clean. 3 pinning the backtest against real `sqlite3.Row`s
  (including the no-leakage walk), 3 pinning the trend states (one-gameweek, flat, varied).
- **Manual smoke:** the backfill run itself (604/604); `calibrate --weight form` returns the ≥4-gameweek guard
  instead of crashing; the trend panel renders distinct output for a 14-point and a 2-point opener.
- **Docs:** this sprint doc, PROJECT_STATUS.

---

### 📝 Lessons

**Three dormant bugs in two days, all the same species.** ADR-123 (a flag that only lies mid-gameweek), ADR-124
(a `max()` that only misbehaves once `points_per_game` is non-zero), and both of today's. None was a regression;
each was code that had never run under real data. Preseason, "the tests pass and the app works" meant less than
it looked like it meant — a whole class of branches was unreachable.

**Empty collections hide type errors.** `for r in rows: r.get(...)` is correct-looking code that cannot fail
while `rows` is always empty. The tests passed dicts and the production caller passed Rows, and nothing forced
the two to agree until data arrived. Where a test substitutes a simpler type for the real one, the substitution
is the thing to distrust.

**Filling a data gap can make the display worse.** The trend card was *more* honest empty than populated: a
placeholder that says "fills in from GW1" tells the truth, while a chart with one point invents a direction.
Worth checking, after any backfill, what was rendering the emptiness — and whether it was doing a better job
than what replaces it.

---

### 🔭 Still open

- **`FORM_WEIGHT` is still 0** — the calibrate harness works again but needs ≥4 gameweeks of returns (~GW4-6).
- **The xMins minutes share still defaults to 1.0 without history** (`availability_weight`, ADR-038) — now that
  in-season minutes are meaningful, this is the sibling of ADR-124 and wants its own gate.
- **Season-to-date boards stay empty until ~GW10** (over/under · DefCon · clean sheets all gate at 900 minutes).
