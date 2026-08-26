# Sprint 199: Fixture concentration — the honest version of "player clashes" (ADR-145)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-145. 1398 → 1407 tests, ruff clean. The Roadmap's framing rejected on evidence;
the real quantity underneath it built.

---

### 🔍 The premise didn't survive being checked

*"Player clashes — your own players meeting = point cannibalisation."* Intuitive: your attacker scores, your
defender's clean sheet dies.

**Two measurements killed it.**

**Clashes are universal.** 300 random legal squads, five gameweeks: **100%** had at least one, averaging
**26 clashing pairs**. Narrowed to the XI *and* to defensive-vs-attacker — the only combination that actually
conflicts — still **7.4 per squad**. A warning that fires for everyone every week is wallpaper. (27% of raw
clashes are attacker-vs-attacker, where there is no conflict at all.)

**And a clash costs no expected points.** `decision_xp` already prices each player's own fixture, so summing
them double-counts nothing. A clash changes the **joint** distribution — the outcomes become anti-correlated —
not either marginal. Expected score unchanged; **variance** lower.

Which is not automatically bad: chasing wants variance, protecting a lead wants less of it. Same logic as
league effective ownership (ADR-141). *"Cannibalisation"* is the wrong word for something that is sometimes
exactly what you want.

### 🔧 What shipped instead

**Concentration** — how much of one gameweek's XI projection rides on a single match:

| median | p75 | p90 | max |
|---:|---:|---:|---:|
| **29%** | 34% | 40% | 64% |

Thresholds are those quartiles. Measured on the XI, not the 15 (a benched player was never at risk). The
clash survives as a **qualifier** rather than a warning: players on both sides means their returns partly
cancel, so the week is even *less* spread than the share says.

Both saved squads, six gameweeks: **RoboTS produced no note at all.** TS produced one —

> 🎯 43% of your GW6 rides on LIV v MCI (4 players: Guéhi, Szoboszlai, Virgil, Haaland). You have players on
> **both** sides, so their returns partly cancel.

---

### 💡 The lesson

> **The feature was real; the reason given for it was not.**

There *is* something worth telling a manager about their own players meeting. It just isn't the thing the line
said — not lost points, but a narrower spread of outcomes. Had the roadmap line been implemented as written,
the app would have shipped a warning that fires for every squad every week, about a cost that does not exist,
computed from numbers that already account for it.

The general form, worth carrying: **when a feature request comes with its own explanation, the explanation is
the part to check first.** A wrong premise survives implementation perfectly happily — it produces working
code, passing tests, and a confident sentence that is false. The measurement that catches it takes ten
minutes; the alternative is shipping a plausible lie and defending it later.

Second, smaller: **the discipline is in what it doesn't say.** The naive version fired 100% of the time. This
one is silent for about three-quarters of squad-gameweeks — including, on the day it shipped, one of the two
real squads entirely. A note that appears rarely is one a manager reads.

### 🧪 Tests

**+9.** The match carrying most of a gameweek; **opposed vs same-side** (the distinction the naive framing
misses — two Liverpool players are concentrated but not conflicted, and can both return); the note appearing
only above p75, with the measured distribution in the docstring so the constants explain themselves; heavy
reading more strongly than concentrated; the note naming players, because a bare percentage is not actionable;
a zero-xP gameweek skipped rather than divided by; empty inputs safe; and a page test that any note appearing
names a gameweek, a match and the players.
