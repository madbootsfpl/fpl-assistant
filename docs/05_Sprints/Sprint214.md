# Sprint 214: Two form windows say which way (ADR-159)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-159. 1504 → 1515 tests, ruff clean. Preview approved before commit.

---

### 🔧 What shipped

`form_rate` has always computed one rolling points-per-90. One number cannot say **which way** a player is
going, at any window size. `form_windows` runs it twice — last 3 against last 6 — and reports both rates, the
signed gap, and a direction.

**The data check came first, and it became the design:**

```
distinct PLAYED gameweeks : [1]
players with >=3 played rows : 0
players with >=6 played rows : 0
```

So today the two windows are the *same single match* for everyone, and their gap is exactly 0.0. Reported as
"level", that is a confident flat arrow on no evidence — the mistake this very card already refuses to make
with a line through one point. So `direction` is `None` unless the long window covers **strictly more played
gameweeks** than the short one, and the card says so in words.

That rule keeps earning its place after GW4: a player back from a three-week injury has six rows and three
matches, so the long window holds nothing the short one doesn't. Counting rows gets that wrong; counting
played matches gets it right.

No "significant change" threshold — that needs a distribution of real swings which doesn't exist yet, and
inventing one now is how a constant gets born with no population behind it. One home (the Performance trend
card), and the caption ends **"not in xP"**, because `FORM_WEIGHT` is still 0.

---

### 💡 The lesson

> **When a feature compares two windows, the first question isn't how to compare them — it's when they are the
> same window.**

Six lines of counting turned this sprint from "add a second window" into "add a second window and a rule for
when the two are the same thing", which is the only part with any subtlety in it. Built the other way round,
it would have shipped a level arrow on all 548 players and looked entirely correct doing so.

Early seasons, injury returns and new signings all produce that case, and none of them announce it: the
arithmetic works perfectly and returns zero.

⚠️ Worth recording plainly — **this is the first thing built this session that can't be verified on real
data.** It is tested against synthetic gameweeks; the populated state appears around GW4. That was the
accepted trade for having the machinery ready when `calibrate` clears its guard.

### 🧪 Tests

**+11.** Rising and fading players; one gameweek refusing a direction; windows covering the same matches
refusing one late in a season too; no minutes → no windows; both windows using the same rate; sizes as
arguments. Plus the view: both windows and the gap when there is one; the refusal rendered as words with no
arrow at all; nothing without minutes; and the trend panel degrading to byte-identical output without it.
