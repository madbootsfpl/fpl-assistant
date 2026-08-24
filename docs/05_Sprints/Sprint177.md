# Sprint 177: Player DNA was drawing a fingerprint out of missing data (ADR-126 follow-up)

**Dates:** 2026-08-24
**Status:** ✅ Complete. 1147 → 1155 tests, ruff clean. Owner-reported from the live app.

> **Owner (live on Cloud):** "player dna is not correct, just getting Team Attack stat, for all players".

---

### 🐛 What was happening

Two faults compounding, and the report described the symptom exactly.

**1. Nothing to rank against.** `player_dna` ranks a player against same-position peers with ≥ `MIN_MINUTES`
(450 — five matches). One gameweek in, the maximum anyone has played is 90, so the pool is **empty** and every
per-player percentile comes back `None`:

```
Haaland (FWD)
   Goal Threat   0.74   pct=None      Consistency  90.0   pct=None
   Creativity    0.02   pct=None      Value        0.13   pct=None
   Set Pieces    9.0    pct=None      Bonus Potl   0.0    pct=None
   FPL Output    2.0    pct=None      Team Attack  2.24   pct=85   ← the only survivor
```

Team Attack survived alone because it ranks across **team** xG totals, which carry no minutes gate.

**2. `None` was drawn as zero.** `radar_svg` plotted `frac = (ax.percentile or 0) / 100`, so every unranked axis
landed at the centre of the chart. Seven vertices collapsed to the origin and the polygon became a single spike
out to Team Attack — a shape assembled almost entirely from absent data, rendered as though it were a
measurement.

The second fault is the more serious one: the first is a data gap, the second turns a data gap into a confident
false statement. It is the same `None`-reads-as-zero shape as this morning's trend chart, where a 14-point haul
and a 2-point one both drew on the chart floor.

---

### 🔧 What shipped

**The pool falls back to last season** — the ADR-126 pattern, third surface. `player_dna_this_or_last` ranks the
player against last season's pool when this season's is empty, *including the target*, so a full-season value is
compared against full-season peers rather than one gameweek against thirty-eight. It retires itself once the
pool fills (~GW5), and a caption names the season.

```
Haaland (FWD) — 2025/26, pool 33          Gabriel (DEF) — 2025/26, pool 111
   Goal Threat   0.78  pct=100               Goal Threat   0.10  pct=88
   Creativity    0.08  pct=79                Creativity    0.06  pct=62
   Set Pieces    9.00  pct=100               Set Pieces    0.00  pct=87
   FPL Output    7.28  pct=91                FPL Output    6.84  pct=100
```

**Bonus Potential is dropped when falling back**, because FPL does not keep ICT index in a player's season
history. An axis every player scores 0 on would rank them all identically and read as real; seven honest axes
beat eight with a fabricated one. Price, ownership and set-piece duty keep coming from the **live** row for the
same reason they do on the boards — you pay today's price, and it is today's penalty taker you want.

**The radar refuses to lie.** Fewer than three ranked axes now renders "Not enough games played to rank this
player yet" instead of a shape. A lone unranked axis among ranked ones sits at mid-radius with a hollow dashed
vertex — absent evidence reads as unknown, never as the worst score in the pool.

---

### ✅ Definition of Done

- **Automated:** 1147 → **1155 tests**, green, ruff clean. 5 on the fallback (the empty-pool precondition, the
  fallback itself, the dropped axis, self-retirement once this season can rank, and the honest unranked state
  for a player with no last-season row) and 3 on the renderer (refusing to draw from missing data, drawing once
  enough axes are ranked, and the hollow mid-radius vertex).
- **Manual smoke:** the real Players ▸ Card page through `AppTest` — one radar, seven labelled axes, no
  placeholder, no hollow dots, every chip carrying a percentile rather than a dash, and the season caption
  present.
- **Docs:** this sprint doc, ADR-126 follow-ups, PROJECT_STATUS.

---

### 📝 Lessons

**`or 0` is how a missing value becomes a confident wrong one.** Twice in one day — the trend chart floor and
this radar. `(x or 0)` reads as a harmless default and is actually a claim: *this player scored zero here*. The
honest default for "we don't know" is to not draw the thing.

**A gate on the peer pool fails differently from a gate on a row.** The three stat boards showed *nothing* when
their 900-minute gate bit, which was at least visibly empty. Player DNA's 450-minute gate emptied the
*comparison set* instead, so the card still rendered — confidently, and wrong. Degrading to blank is a nuisance;
degrading to plausible is a bug you only find when a user tells you.

**Six dormant-data bugs in two days, all the same root.** The season rollover reset every cumulative stat, and
each gate, flag and default that had never seen a fresh season fired for the first time. Preseason green tests
proved less than they appeared to.

---

### 🔭 Found, not fixed (needs its own gate)

**`_percentile` ranks ties at the top.** It counts peers "at or below", so in a pool where almost everyone
scores zero, a zero lands in the 90s — A.Becker, a goalkeeper, shows **Goal Threat 96th percentile on a raw
0.00**, and Set Pieces 100th. This is pre-existing (ADR-118) and was merely invisible while every percentile was
`None`; it would have appeared at GW5 regardless. The standard fix is a **midrank** percentile —
`(below + 0.5 × equal) / n` — which puts an all-tied pool at 50 instead of 100. That changes every percentile in
both Player DNA and Team DNA, so it wants an ADR rather than riding along with a different fix.
