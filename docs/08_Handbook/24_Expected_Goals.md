# Chapter 24 — Expected Goals (xG / xA / xGI)

**Badges:** 📖 🧪 💻

---

## Purpose

**Expected goals** measures the *quality* of chances, not just the goals scored. It answers
"how many goals/assists *should* a player have, given the chances they had?" — a steadier
signal than raw goals, which are noisy over small samples.

- **xG** (expected goals) — the sum of the scoring probability of each shot a player took.
- **xA** (expected assists) — the same idea for the passes that led to shots.
- **xGI** (expected goal involvements) — **xG + xA**: total attacking threat.
- **xGC** (expected goals conceded) — a team/defence measure carried on each player; a
  rough defensive counterpoint.

---

## Why We Use It — and where the data comes from

The backlog wanted this from **FBref**. A feasibility check (ADR-015) killed that idea and
found a far better source:

- FBref returns **403** here (scraping blocked) and needs a heavy dependency
  (`soccerdata`) plus fragile **name-matching** between FPL and FBref.
- **FPL's own API already carries xG/xA/xGI/xGC**, keyed by player id — no new dependency,
  no scraping, no name-matching.

The lesson (a recurring one): *check the source before you build the pipeline.* The scary
backlog item became a safe one because the data was already in a feed we fetch.

---

## Concepts

- **A rate vs a total:** these are **season totals** (like `total_points`). Preseason they
  are last-season's totals, and they auto-update on `refresh` once the season starts.
- **xGI = xG + xA** exactly — so it's a single headline for attacking involvement.
- **Attacking bias:** goalkeepers and most defenders have xGI ≈ 0. Any ranking or squad
  objective built on xGI therefore leans to attackers — a feature to *state*, not hide.

---

## How it flows through the app (a full-stack slice)

Unlike the display-only features around it, this one added a **new data dimension**, so it
touched every layer — the end-to-end path worth understanding:

```
FPL API  →  Player.from_api (_to_float)  →  storage (schema migration)  →  analytics  →  view / objective
expected_goals, …          xg/xa/xgi/xgc        ALTER TABLE ADD COLUMN         xgi score       xg / --objective xgi
```

Nothing here was new machinery — each layer already had its seam (the model's `_to_float`,
the generic `_migrate()`, the pluggable objective from ADR-011). Adding the objective was
**one dict entry**, exactly as ADR-011 predicted three sprints earlier.

---

## Examples (from this project)

```bash
python app.py xg                       # players ranked by xGI (xG + xA)
python app.py xg --pos DEF --limit 10  # attacking defenders
python app.py squad --objective xgi    # optimise the squad on attacking involvement
```

```
#  Player        Team  Pos    xG    xA   xGI   xGC
1  Haaland       MCI   FWD   25.5   2.7  28.2  38.6
2  B.Fernandes   MUN   MID   10.8  12.3  23.1  44.4
```

`squad --objective xgi` prints a reminder that xGI is attacking, so an all-out-attack XI is
expected, not a bug.

---

## Common Mistakes

- **Treating season totals as current form.** Preseason these are *last* season — the same
  caveat as every FPL number.
- **Reading a defender's low xGI as "bad".** xGI is attacking; defenders are judged more by
  clean sheets / xGC.
- **Reaching for a scraper.** The data is already in the FPL feed — check first.

---

## Best Practices

- Coerce a missing value to 0.0 *at the point of use* (a DB refreshed before this feature
  has `NULL` until the next `refresh`).
- State an objective's bias in the output — honesty as a feature, not a footnote.

---

## Lessons Learned

- The cheapest data pipeline is the one you don't build — the source you already have often
  hides the field you want.
- A generic core (a pluggable objective, a generic migration) turns "a new metric" into a
  small, safe change.

---

## Related Documents

- [ADR-015 — Expected goals](../06_Decisions/ADR-015-expected-goals.md)
- [ADR-011 — Pluggable squad objective](../06_Decisions/ADR-011-squad-objective.md)
- [Chapter 21 — Analytics](./21_Analytics.md) · [Chapter 22 — Optimisation](./22_Optimisation.md)
- Code: `src/models/player.py`, `src/storage.py`, `src/ui/xg.py`, `src/analytics/optimizer.py`
