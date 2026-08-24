# Sprint 174: The cold-start xP rate shrinks by evidence, not value (US-431, ADR-124)

**Dates:** 2026-08-24
**Status:** ✅ Complete — ADR-124. 1115 → 1123 tests, ruff clean. Design verified on the live GW1 board before
the gate; the invariance claim re-verified against it after.

> **Owner:** gated the ADR, then "build it".

---

### 🐛 The bug — one gameweek of data inverted the ranking

```
  1. M.Sangaré      xP=43.4  rate=14.00/GW  mins=75  ep_next=2.0  tier=current
  2. Tzolakis       xP=30.0  rate=10.00/GW  mins=90  ep_next=1.9  tier=current
  3. Emersonn       xP=25.2  rate= 9.00/GW  mins=65  ep_next=1.8  tier=current
  ...
  6. Haaland        xP=17.1  rate= 6.91/GW  mins=90  ep_next=4.0  tier=hist
```

Five players with **one game each** above every established player in the game; Munoz 14th on **27 minutes**.

`player_xp` picks a rate from three tiers. The cold-start branch — no history at all — took
`max(ep_next, points_per_game)` (ADR-104). After one game, `points_per_game` **is** that game's score, so a
14-point opener projects at 14 a week. Preseason it could not misbehave (`ppg` was 0, so `ep_next` always won);
real data is what activated it. Two safeguards no-op for exactly this population — `availability_weight` also
defaults its minutes share to 1.0 without history, so these players took the raw rate *and* a full `w=1.0`
weight against 0.72–0.99 for everyone else.

---

### 💡 The insight — those weren't two tiers, they were two ends of one curve

`fallback_rate` (ADR-040) already solves this for the neighbouring tier, and its docstring already names the
failure: *"projecting raw `points_per_game` lets a one-game cameo … rank like a star."* The cold-start branch
never got it, because with no history there was no career rate to shrink. But **this season's minutes are the
evidence.** And its two extremes are already-agreed behaviour:

| evidence | old rate | |
|---|---|---|
| 0 minutes | `ep_next` | `ppg` is 0, so `max` always picks it — ADR-104 |
| ≥900 minutes | `points_per_game` | a full season's average |

`max()` switches between them on the **value**, which is why one big score flips it on day one. Switching on the
**evidence** turns a discontinuous choice into an interpolation.

---

### 🔧 What shipped

`cold_start_rate` in `analytics/xp.py` — pure, sitting alongside `baseline_rate` and `fallback_rate` and sharing
their shape and their 900-minute bar:

```
c    = min(1, minutes_this_season / 900)
rate = (w × points_per_game) × c  +  ep_next × (1 − c)
```

`w` (the xMins weight) scales the `points_per_game` term **only** — `ep_next` already prices minutes, and ADR-104
is explicit it must not be discounted twice. The two labels `ep_next` and `current` merge into one,
`cold_start`.

**Both endpoints reproduce the old behaviour exactly**, which is the entire safety case — so it was checked
against the live board rather than argued. Replaying the old `max()` rule over the same 604 players: **all 81
zero-evidence players come out bit-for-bit identical**; **31** players' xP actually shifts.

The live board after:

```
   BEFORE                         AFTER
1. M.Sangaré    43.4   →      1. Haaland       17.1
2. Tzolakis     30.0          2. B.Fernandes   16.0
3. Emersonn     25.2          3. Watkins       14.5
...                           ...
6. Haaland      17.1         49. M.Sangaré      9.3
```

It damps without flattening — Slater and Muharemović share a 6.0 ppg but land at 1.50 and 2.58 on their
differing `ep_next` — and converges: a genuine 6.0-ppg signing reaches their real rate by ~game 10, while a
one-game fluke that reverts never spikes.

---

### ✅ Definition of Done

- **Automated:** 1115 → **1123 tests**, all green, ruff clean. 8 new: both endpoints pinned against the old
  behaviour, the one-game damping, the convergence trajectory, the `ep_next`-still-separates-equal-scorers
  property that ruled out the flat prior, the `w`-on-`ppg`-only placement, empty-safety, and the reported
  `minutes_weight`.
- **Manual smoke:** the live 3-GW board — established players back on top, Sangaré 1st → 49th, tiers
  `hist` 352 / `cold_start` 128 / `fallback` 124; the 81/81 invariance replay above.
- **Docs:** ADR-124, this sprint doc, PROJECT_STATUS.

---

### 📝 Lessons

**A dormant branch is untested code with a date on it.** This shipped working and stayed correct for months
because `points_per_game` was 0 all preseason. Nothing broke it — data arriving is what ran it for the first
time. Worth asking of any branch that only fires under conditions we haven't had yet.

**`max()` was standing in for an interpolation.** Choosing the bigger of two estimates *looks* conservative and
is actually the opposite: it systematically picks whichever number is currently most extreme. When two rules
disagree, the question is usually "how much do I trust each?", not "which is bigger?" — and that question has a
continuous answer.

**The fix was already in the codebase, one tier over.** ADR-040 had solved this exact failure and even named the
cameo case. It didn't generalise because the cold-start branch had no career rate to shrink — so the lesson sat
next to the bug for a year. When a neighbouring module has a hard-won damper, check whether the reason it
doesn't apply is essential or incidental.

**The safety case decided the design.** "Both endpoints reproduce today's behaviour exactly" is what made this
buildable on a live decision engine — it turned an unbounded change into a 47-player one, and it was cheap to
verify against real data rather than trust.

---

### 🔭 Still open

- **The xMins minutes share still defaults to 1.0 without history** (`availability_weight`, ADR-038), even though
  in-season minutes could now inform it. It compounds this bug and deliberately stayed out of scope.
- **Season-to-date boards empty until ~GW10** (over/under · DefCon · clean sheets all gate at 900 minutes).
- **`player_history` is 0 rows** — sparklines and W-D-L form dots have nothing to draw, and the ADR-060 form
  blend stays dormant. Needs the throttled `backfill`, which `refresh` does not do.
