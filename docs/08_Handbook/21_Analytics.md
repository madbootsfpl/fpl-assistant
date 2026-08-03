# Chapter 21 — Analytics

**Badges:** 📖 🧪 💻

---

## Purpose

Analytics is where the project *calculates* things, rather than just storing and
showing numbers that came from FPL. The first metric is **Points-per-£m** (value).

---

## Why We Use It — and where it sits in the architecture

Analytics is the first layer that **creates data rather than moving it**. Everything
below it copies FPL's numbers around; analytics turns those into *new* insight. It
**reads from storage, computes, and hands results up to display** — it never touches
the API or the screen.

```
storage (raw rows) → analytics (adds a computed number, ranks) → display
                         ▲ the layer that "thinks"
```

Keeping it in its own layer (`src/analytics/`) means the project's *reasoning* has
one home — as more metrics arrive (form, fixture difficulty, later xP), they all live
together instead of being scattered into queries or formatting code.

---

## Concepts

- **Derived metric:** a number the app computes (points ÷ price), not read from source.
- **Pure function:** numbers in, number out — no side effects; trivial to test.
- **Per-row vs aggregate:** value is per player; fixture difficulty (FDR) is *per team
  across several fixtures* — a summary of a group.
- **Perspective:** the same input can mean different things to different subjects — a
  fixture is easy for one team and hard for its opponent, so each team reads its own side.
- **Undefined results:** some inputs have no sensible answer (divide by zero). Say so
  honestly rather than inventing a value.
- **Cross-domain:** a metric that combines two domains — Expected Points (xP) joins a
  *player's* scoring rate with their *fixture's* difficulty (`points_per_game ×
  multiplier(difficulty)`). The join key is the player's `team_id`.

---

## Examples (from this project)

The value metric in `src/analytics/value.py`:

```python
def points_per_million(total_points, price):
    if total_points is None or not price or price <= 0:
        return None          # undefined — don't invent a number
    return total_points / price
```

Ranking players by value (undefined values sort to the bottom):

```python
enriched.sort(key=lambda d: (d["value"] is not None, d["value"] or 0.0), reverse=True)
```

**The payoff:** sorting by value surfaces cheap high-scorers a points-only list hides
— e.g. a £5.5m defender at 30.0 pts/£m ranking above a £15.5m striker at 15.4.

An *aggregating* metric — Fixture Difficulty (`src/analytics/fdr.py`) — summarises a
group instead of one row. Each fixture is attributed to *both* teams from their own
perspective, then averaged per team over the next N games:

```python
for f in fixtures:
    per_team[f["home"]].append((f["team_h_difficulty"], f["away"]))   # home's view
    per_team[f["away"]].append((f["team_a_difficulty"], f["home"]))   # away's view
# then: average each team's next N, rank easiest-first
```

The boundary from Chapter 10 holds: storage answers "which fixtures are upcoming?";
analytics does the perspective + averaging + ranking.

**Expected Points (xP)** is the first metric to *compose two others*: it multiplies a
player's `points_per_game` by their next fixture's difficulty (reusing FDR's `_view`).
`src/analytics/xp.py` links each player to their team's next fixture via `team_id` —
the first time the player and fixture threads meet. It also carries FPL's own
`ep_next` alongside, so ours can be compared to theirs (ADR-006).

A metric can have more than one **source**. `fdr --type fpl|custom` uses either FPL's
published difficulty or our own (the opponent's overall strength at their venue,
ADR-005) — same averaging/ranking machinery, a different input number. Keeping both
lets us compare our rating against FPL's.

**Enriching a metric's *input*, not its formula (ADR-028).** Sprint 026 improved xP
without touching its formula: instead of the rate being one noisy season's
`points_per_game`, it's a **multi-season baseline** — a recency- and minutes-weighted
points-per-90 over the last ≤3 seasons (from the new past-season history, ADR-027),
falling back to the current season when a player has no history. Two lessons worth
keeping:
- **Gate small samples.** A cameo season (2 pts in 20 mins → pp90 90.0) invents an
  absurd rate. A live smoke test — not the unit tests, which used clean data — caught
  it topping the ranking; the fix was the same ≥900-minute gate the DefCon/over-under
  views use (the Sprint 016 Meslier lesson, again). *Verify metrics on real data.*
- **Use only trustworthy fields.** Older seasons report `0.00` for stats that didn't
  exist yet (xG, DefCon) — a 0 meaning "not tracked", not a real zero. The baseline
  uses only points + minutes, which are reliable across all seasons (ADR-027).
- **Know the boundary.** The baseline is a *"quality when playing"* rate — it doesn't
  model rotation/minutes (that's xMins, a later phase). Stated in the view's footer.

---

## Common Mistakes

- **Dividing by zero / assuming clean data.** Guard undefined inputs; return None.
- **Hiding the metric in SQL or the display.** Then "what counts as value" is smeared
  across layers. Keep it in analytics.
- **Inventing a value for undefined cases** (e.g. 0) — it mixes with real low values.

---

## Best Practices

- Write metrics as pure functions — easy to reason about and test.
- Represent "undefined" explicitly (None → "—", sorted last).
- Analytics reads from storage and returns data; it never fetches or prints.

---

## Lessons Learned

- This is the layer that turns the app from a *viewer* into an *assistant*. Its
  isolation is what will let metrics grow without touching anything else.

---

## Related Documents

- [Architecture v0.1 §4](../03_Architecture/Architecture.md)
- [Chapter 10 — SQLite](./10_SQLite.md) (where the data is read from)
- [Chapter 20 — CLIs](./20_CLIs.md) (how a metric reaches the user)
- Code: `src/analytics/value.py`
