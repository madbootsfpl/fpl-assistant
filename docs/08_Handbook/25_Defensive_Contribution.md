# Chapter 25 — Defensive Contribution (DefCon)

**Badges:** 📖 🧪 💻

---

## Purpose

FPL awards **Defensive Contribution (DefCon)** points — **2 points per match** for clearing
a threshold of defensive actions. It has become a major, and often *cheap*, source of points:
sorting players by value now shows no forwards in the top 20 — the defenders and defensive
midfielders banking DefCon points dominate. The `defcon` view finds the players who reliably
clear the bar.

---

## The rules (and why the field is trustworthy)

| Position | Counts | Threshold / match |
|---|---|---|
| DEF | clearances + blocks + interceptions + tackles (**CBIT**) | **10** |
| MID / FWD | CBIT **+ ball recoveries** | **12** |
| GK | — (they score via saves / clean sheets) | not eligible |

We *verified* (Sprint 017 planning) that FPL's `defensive_contribution` field already applies
these position rules — for defenders it equals CBIT (recoveries excluded); for mids/forwards
it equals CBIT + recoveries. That's the load-bearing check: it means comparing the field to
the threshold is valid, not a guess.

> **Where do the threshold numbers (10 / 12) come from?** *Not* from the FPL API — it doesn't
> expose them (we checked `game_settings`, `game_config` and the position definitions). They
> are **hardcoded constants** in `src/analytics/defcon.py`, transcribed from **FPL's published
> scoring rules**. So the field's *composition* is verified from data, but the two *threshold
> values* are an **assumption to confirm against FPL's official rules** — and to re-check each
> season, since FPL can change them. This is an honest "hand-maintained rule, not fetched
> data" boundary worth remembering.

---

## The metric — a margin vs the threshold

There's no "expected DefCon", but there is a natural reference — the threshold itself:

```
margin = defensive_contribution_per_90 − threshold[pos]
```

- **Positive** → clears the bar on average → a reliable DefCon-point earner.
- **The larger the margin, the more reliably** they clear it game to game.

```bash
python app.py defcon               # most reliable earners (ranked by margin)
python app.py defcon --pos DEF     # defenders only
python app.py defcon --min-minutes 1500
```

```
#  Player     Team  Pos   Mins  DC/90  Thr  Margin
1  Gomes      AVL   MID   2207   15.8   12    +3.8
2  Wieffer    BHA   DEF   1901   12.7   10    +2.7
```

---

## What DC/90 actually means (and its limit)

`DC/90` is FPL's `defensive_contribution_per_90` — **we don't compute it**, we ingest and show
it. FPL derives it as the standard football *per-90* rate:

```
DC/90 = defensive_contribution × 90 ÷ minutes
```

e.g. Gomes: 387 actions in 2207 minutes → 387 × 90 ÷ 2207 = **15.78**.

It's a **rate averaged over 90-minute blocks of pitch time**, *not* over games played:

- `minutes ÷ 90` gives "90-minute equivalents", not appearances. Gomes' 2207 min = **24.5**
  "90s" — close to his **25 starts** only because he plays ~88 min every game. For a
  frequently-subbed player the two diverge (30 cameos of 50 min = 30 games but only ~16.7 "90s").

**Why this is a reliability guide, not a guarantee.** The 2 DefCon points are decided **per
actual match** against a *fixed* threshold (10 / 12 actions *in that match*), while DC/90 is a
**season average**. So:

- A **full-90 player** racks up roughly his DC/90 each match → the margin is a good guide.
- A **subbed player** can have a high DC/90 yet miss the fixed bar in short appearances (less
  pitch time to reach 12 actions in a 60-minute cameo) → a high DC/90 can *overstate* his
  per-match reliability.

Pinning this down exactly (matches actually cleared) would need per-gameweek data — a backlog
item. Until then, read the **margin as a tendency**: bigger is safer, but it's an average.

---

## Design points worth remembering

- **A single ranked list, not two ends** (unlike `overperf`). A defensive "under-performer"
  isn't meaningful — a forward with a low DefCon count isn't *failing*, it isn't his job. The
  useful output is the ranked *assets*.
- **Minutes-gated (≥ 900), like `overperf`.** A per-90 rate off a tiny sample is noise.
- **Reliability, not a guarantee.** A per-90 *average* above the bar isn't a promise of 2
  points *every* match — some games dip below. The margin is a confidence guide; exact DefCon
  points would need per-match data (a backlog item).
- **Scarce signal.** Only ~23 of ~250 minutes-qualified players clear their bar — which is
  exactly why the view is useful: it points at a small, actionable set.

---

## Common Mistakes

- **Reading the margin as guaranteed points.** It's a reliability tendency.
- **Expecting forwards.** By design they rarely clear the 12-action bar — DefCon is a
  defence / defensive-mid signal.
- **Trusting it early season.** Like every FPL number it resets, and the ≥ 900-minute gate
  means it only becomes meaningful ~10 games in.

---

## Related Documents

- [ADR-018 — Defensive Contribution](../06_Decisions/ADR-018-defensive-contribution.md)
- [ADR-017 — Over/under-performance](../06_Decisions/ADR-017-over-under-performance.md) (the attacking counterpart)
- [Chapter 24 — Expected Goals](./24_Expected_Goals.md)
- Code: `src/analytics/defcon.py`, `src/ui/defcon.py`
