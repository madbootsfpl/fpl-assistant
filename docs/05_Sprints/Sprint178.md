# Sprint 178: Percentiles no longer rank a tie at the top (ADR-127)

**Dates:** 2026-08-24
**Status:** ✅ Complete — ADR-127. 1155 → 1170 tests, ruff clean.

> **Owner:** gated the ADR, chose **formula B** (percentile rank) and **accepted the team-grade drop**.

---

### 🐛 The bug

**A.Becker — a goalkeeper — read *Goal Threat: 96th percentile* on a raw xG/90 of 0.00**, and *Set Pieces: 100th
percentile* on a raw score of 0.

Both ranking functions counted peers **"at or below"** the value, so a tie ranked at the *top* of its tie group.
Nearly every keeper has 0 xG and no set-piece duty, so a 0 counted as beating every other 0. The axis read
*elite* precisely because the player had nothing there.

The same line held a second, quieter fault: it counted the player **themselves**, inflating everyone by `1/n` —
+5 points for the best of twenty and ~+2.5 through the middle.

Both faults were written **twice**, once in `player_dna._percentile` and once in `team_dna._rank`.

---

### 🔧 What shipped

`analytics/ranking.py::percentile_rank` — one function, imported by both. The two local names survive as thin
aliases, so each module still reads in its own vocabulary.

```
rank = below + (equal + 1) / 2         # 1-based average rank across the tie group
pct  = 100 × (rank − 1) / (n − 1)
```

**Formula B over midrank**, because it preserves the **0–100 endpoints**. The insight copy is written as
*"top {100 − pct}%"*, so a formula capping the best at 98 would have the best player in the game reading
*"top 2%"*. B keeps *"top 1%"*.

| | all-tied | best of 20 | worst of 20 |
|---|---|---|---|
| before | **100** ❌ | 100 | 5 |
| after | **50** ✅ | 100 | 0 |

**The shift lands exactly where it should.** On the live card:

```
A.Becker  GK   Goal Threat  96 → 48        Haaland  FWD  Goal Threat  100 → 100
A.Becker  GK   Set Pieces  100 → 50        Saka     MID  Creativity    97 →  96
```

Elites are untouched; the meaningless stops reading as elite.

**Team grades dropped, and that was the accepted outcome.** 9 of 20 teams fell a letter — not from the tie fix
but from removing the self-count inflation. The old grades were simply too generous. Team *ordering* is
unchanged. Distribution now **A 2 · B 4 · C 7 · D 7** (BHA A(84), BRE A(73), LIV B(70), MCI B(69), ARS B(67)).
Re-tuning the 85/72/58/42 thresholds was rejected as fitting the scale to the bug, and stays available if the
skew reads harshly once real data accrues.

---

### ✅ Definition of Done

- **Automated:** 1155 → **1170 tests**, green, ruff clean. 15 new (the fully-tied pool, a zero among mostly
  zeros, a genuine leader untouched, the endpoints, the insight-copy property, tie averaging, inverted axes,
  empty and single-peer pools, out-of-pool values, and a parametrised in-range check) + 4 existing DNA tests
  updated to the new semantics.
- **Manual smoke:** the real Players ▸ Card page — A.Becker's Goal Threat 48 and Set Pieces 50, every axis
  ranked; the live team-grade distribution above.
- **Docs:** ADR-127, this sprint doc, PROJECT_STATUS.

---

### 📝 Lessons

**A default that flatters is harder to spot than one that fails.** `(below + equal)/n` looks like a percentile
and behaves like one everywhere values are distinct. It only misbehaves where they bunch — and it misbehaves
*upward*, which reads as a compliment rather than an error. Nobody reports a player being rated too highly.

**The same rule written twice drifts, and it had already been written twice here.** ADR-123 extracted
`DEADLINE_LEAD` for exactly this reason a day earlier; this was the second instance of the identical pattern.
Worth grepping for others rather than waiting for the third.

**Clamp anything that leaves a formula.** `value` need not be a member of `values` — Player DNA ranks a
below-the-floor target against a floored pool — and on a two-element pool the arithmetic computes −50 before
clamping. The tests caught it; the type hint (`int | None`) would not have.

---

### 🔭 Follow-ups

- **`Squad Depth` is a fully-tied axis right now** — it counts players with ≥1500 minutes, which is 0 for every
  team, so all 20 now read a flat 50. Honest, but it is an ADR-126-shaped problem: a metric that cannot answer
  yet. It was previously masked as 100 for everyone.
- **"Unrank a fully-tied pool"** (return `None` rather than 50) remains available as a refinement if a 50 on a
  meaningless axis proves confusing.
