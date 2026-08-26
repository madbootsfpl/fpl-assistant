# Sprint 198: The captain margin, calibrated against its own distribution (ADR-144)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-144. 1393 → 1398 tests, ruff clean.

---

### 🔍 Measure first — and the measurement is the feature

The Roadmap wanted *"by a whisker — 0.3 over #2"*. The card already showed the alternatives and their xP, so
the arithmetic was available; **what was missing was any sense of whether the answer was big.**

Across **300 random legal squads** on live data:

| p25 | median | p75 | max |
|---:|---:|---:|---:|
| 0.20 | **0.60** | 1.00 | 2.80 |

…and **44% of squads separate their top two captains by under half a point.**

So the captain call is usually close, and a gold medal plus "Confidence 91/100" was implying a certainty the
numbers mostly do not support.

### 🔧 What shipped

The margin is now stated on **every** card, with a verdict whose thresholds *are the measured quartiles* —
`WHISKER = 0.3` (p25), `CLEAR = 1.0` (p75). That is what makes "a clear pick" mean anything: it is the top
quarter of real leads rather than a round number.

> *"By a whisker — just 0.2 ahead of Haaland. Too close to call; take the one you fancy."*

That closing clause is the feature. A single gameweek's variance dwarfs half a projected point, so a 0.2 lead
is **the model declining to have an opinion** — and saying so is more useful than a false tiebreak.

The old *"Only +0.3 pts ahead of X"* risk bullet was **removed**: with the margin stated always, it was the
same fact told twice, in two places, against two different thresholds. The gap still feeds
`captain_confidence`, which is where it belongs — a narrow lead should lower the confidence, not add a bullet.

---

### 💡 The lesson

**The measurement did not justify the feature; it *was* the feature.**

The plan was a cosmetic line — print the gap. The distribution turned it into something with an opinion:
without knowing that the median lead is 0.6 and that 44% of calls are near-ties, "0.3 ahead" is just a number,
and any threshold for "clear" would have been invented. With the distribution, the same line tells a manager
where this week's call sits among all the calls the model makes.

Worth generalising: **a number is only informative next to its own distribution.** This project keeps
rediscovering that — ADR-138's value frontier needed the price-peer median before "16.9 xP" meant anything,
ADR-141's league EO needed global ownership before 62% meant anything. Same move, third time.

Second, smaller: **it is a decision tool's job to know when it hasn't decided.** Handing the choice back on a
0.2 gap costs nothing and buys the thing that is hardest to earn back — being believed the week the confident
pick blanks.

### 🧪 Tests

**+5.** The thresholds pinned *as the measured quartiles*, with the distribution in the docstring so they
explain themselves; a whisker says too-close-to-call; a clear lead reads as one; no runner-up yields **no**
margin rather than a huge one; and a missing projection is not treated as zero — `or 0` on an unknown being a
mistake this codebase has made before and now tests against by habit.
