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
