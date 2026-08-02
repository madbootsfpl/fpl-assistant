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

A metric can have more than one **source**. `fdr --type fpl|custom` uses either FPL's
published difficulty or our own (the opponent's overall strength at their venue,
ADR-005) — same averaging/ranking machinery, a different input number. Keeping both
lets us compare our rating against FPL's.

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
