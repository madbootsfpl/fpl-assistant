# Chapter 23 — External Data & Graceful Degradation

**Badges:** 📖 🧪 💻

---

## Purpose

Some useful data isn't in FPL's own API — team strength, expected goals, and more live
in *other* sources. This chapter is about bringing in a **second data source** safely.
The first one added is **ClubElo** (team Elo ratings).

---

## Why We Use It — and the key idea

FPL's advanced signals are empty in preseason (strengths = 0). ClubElo gives **real
team strength today**, which powers an FDR that works when FPL's can't. But a second
source brings a new responsibility: **it might fail**, and the app must not fall over
when it does.

That's the central lesson — **external sources are best-effort**:

```
refresh:
   FPL      → required   (players, teams, fixtures)
   ClubElo  → best-effort (team Elo)
              if it fails: log it, keep the last-known Elo, carry on
```

The app stays fully usable when a dependency is down. This is called **graceful
degradation**, and it's a pattern you'll want in every system that talks to something
it doesn't control.

---

## Concepts

- **Multi-source:** more than one place data comes from (FPL + ClubElo).
- **Best-effort / graceful degradation:** a non-critical source failing is *non-fatal*
  — logged, skipped, and the last-known value kept.
- **Name matching:** the same team is named differently across sources (FPL "Spurs" vs
  ClubElo "Tottenham"), so you need a mapping — and to **fail loudly** on gaps.
- **Isolation:** keep the new source in its own module so it can't disturb the first.

---

## How it's built (ClubElo)

- `src/api/clubelo.py` — its own client (`EloClient`), error type (`ClubEloError`),
  CSV parse, and a `{ClubElo → FPL}` mapping (14 teams match exactly, 6 are mapped).
- `Storage.save_team_elo()` — updates **only** the `elo` column, kept separate from
  `save_teams` so a refresh can never wipe Elo.
- `ingest._refresh_elo()` — the best-effort step: `ClubEloError` → log + return, Elo
  untouched; unmapped clubs warned but non-blocking.
- `fdr --type elo` — normalises each team's Elo to a 1–5 rank band (strongest → 5) and
  uses the opponent's band as the difficulty (ADR-010).

```python
try:
    elo = parse_english_elo(elo_client.get_elo_csv())
except ClubEloError as exc:
    print("keeping last-known Elo"); return 0   # non-fatal
```

**Proof it degrades gracefully:** with ClubElo simulated down, `refresh` still stored
564 players / 20 teams / 380 fixtures, and the last-known Elo was unchanged.

---

## Common Mistakes

- **Letting a non-critical source crash the app.** Wrap it; a failure is data missing,
  not a fatal error.
- **Silently dropping unmatched names.** Map explicitly and report gaps loudly.
- **Overwriting good data with nulls** on a failed fetch — keep the last-known value.

---

## Best Practices

- Isolate each source in its own module.
- Make external data best-effort; the app's core must work without it.
- Version/record which source data came from (the Roadmap's data-reliability rule).

---

## Lessons Learned

- The hard part of a second source wasn't the fetch — it was **name matching** and
  **graceful degradation** (both flagged at *planning* by checking the source first).
- Resilience is a design choice: separate the Elo write, wrap the fetch, keep last-known.

---

## Related Documents

- [ADR-010 — ClubElo external source](../06_Decisions/ADR-010-clubelo-external-source.md)
- [Architecture §4 (second data source)](../03_Architecture/Architecture.md)
- [Data Sources](../10_Data_Sources/Data_Sources.md)
- Code: `src/api/clubelo.py`, `src/ingest.py`
