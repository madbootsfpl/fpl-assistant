# ADR-372 — A window that forgets

**Decision ID:** ADR-372
**Date:** 2026-10-26
**Status:** ✅ **Accepted and built.** ADR-371's **option 2**, chosen by the owner: ship the loosened
in-season guard as a **correctness** change, not an accuracy bid. `in_season_share` now judges the **last 5
completed gameweeks, forgiving 1** — but only once that window is full.
**Superseded By / Replaces:** Replaces [ADR-173](./ADR-173-minutes-you-have-actually-played.md)'s
*"every completed gameweek"* rule. Closes [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md)
option **A**, measured in [ADR-371](./ADR-371-the-ratchet-is-real-and-fixing-it-buys-nothing.md). Keeps
[ADR-125](./ADR-125-in-season-minutes-share.md)'s small-sample objection intact.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 The decision, and what kind of decision it is

ADR-371 measured this candidate and **declined it as an accuracy bid**: +0.18 SE against §B0's +1 SE bar,
dominated by option B which had already declined. The owner shipped it anyway, on ADR-371's own second
option, and the distinction is the whole record here:

> ⭐⭐ **§B0's BAR GOVERNS ACCURACY BIDS. THIS IS NOT ONE.** The claim is not *"this predicts better"* — it
> is that *"every completed gameweek"* is a rule whose failure rate rises monotonically to 100%, and a term
> that answers for 2% of the board has switched itself off. That is a correctness argument, and +0.18 SE
> does not answer it either way.

⭐ What makes that admissible rather than a rationalisation after a disappointing number: **ADR-320 made the
ratchet argument on 2026-09-27, a month before any of these numbers existed.** It is pre-registered by the
ADR that raised it, which is the same test ADR-204 applied to its own clause 2 — *"the reason is independent
of the outcome, which is the only thing that makes it admissible."*

---

### 🔴 First: ADR-371 measured a looser rule than it described

ADR-371 claimed the candidate was *"identical to ADR-173 until the window fills, looser after"*. **It was
not.** The spike used `need = max(1, len(recent) - tolerance)`, which starts forgiving a miss at **two**
completed gameweeks — its own ratchet table shows **106 players "rescued" at GW3**, on a sample of two.

That is precisely [ADR-125](./ADR-125-in-season-minutes-share.md)'s objection, which is still sound and
which ADR-173 exists to honour: *two gameweeks cannot tell a player rested once from one being phased out.*

⭐⭐ **A RULE THAT FORGIVES A MISS OUT OF A SAMPLE OF TWO HAS NOT LOOSENED A GUARD, IT HAS REMOVED ONE.**

⚠️ **And the existing test suite said so before any of this was reasoned out.**
`test_sitting_one_gameweek_out_falls_back_to_history_rather_than_cratering_him` — written for ADR-173 — is a
two-gameweek fixture with one 0, and it fails against the rule ADR-371 measured. ⭐ *A superset change that
breaks a test of the behaviour it claims to preserve is not a superset.*

Fixed by gating the forgiveness on a full window, and **re-measured**, because the rule that ships has to be
the rule that was scored:

```python
need = len(recent) - _FORGIVEN_MISSES if len(recent) >= _WINDOW_GAMEWEEKS else len(recent)
```

---

### 📊 The numbers that were shipped on (`full_only`, 8 gameweeks)

| | board MAE | bias | start call | owned MAE | ρ | xP MAE | hit@20 |
|---|---|---|---|---|---|---|---|
| ADR-173 (before) | 25.7 | +11.5 | 72.4% | 22.0 | 0.617 | 1.26 | 0.19 |
| **last 5, forgive 1** | **25.3** | **+11.4** | **73.0%** | **21.8** | 0.620 | **1.25** | 0.19 |
| *(as ADR-371 measured it)* | *24.7* | *+10.6* | *73.6%* | *21.8* | *0.621* | *1.25* | *0.19* |

**ρ: +0.0837 SE.** Not a gain worth claiming — the point is that **nothing measured gets worse.** That is a
materially different position from option B (which shipped an owned-player regression) and option D (which
made ρ worse), and it is the entire case for shipping.

⭐ **The superset property is visible rather than argued.** Per-round ρ against live:

```
before:  0.520  0.575  0.605  0.594  0.611  0.626  0.693  0.712
after:   0.520  0.575  0.605  0.594  0.611  0.630  0.710  0.718
```

Bit-identical for the first five rounds — the window does not fill until GW6 — and **better in all three
rounds where it acts.** ⚠️ Which is also the honest limit: **three rounds carry the entire result**, and
`last 8, forgive 1/2` scores **+0.0000 SE** because its window never fills in 8 gameweeks.

### ⚠️ Why not the setting that scored better

`last 3, forgive 1` beat it on everything measured (board MAE **24.3**, ρ **+0.13 SE**, start 74.4%),
because a 3-week window fills at GW4 and gets five rounds to act instead of three. **It was not shipped.**

⭐⭐ *"≥ 4 of the last 5" IS ADR-320's OWN PHRASING, WRITTEN A MONTH BEFORE THE DATA EXISTED. "last 3" IS A
VALUE PICKED OFF A CURVE DRAWN ON EIGHT GAMEWEEKS* — ADR-204 was explicit that *"a parameter selected on the
data it is tested on has already spent some of its result"*, and that lesson cost ADR-367 a feature. The
pre-registered setting ships; the flattering one is recorded here and not used.

---

### 📈 What it does to the live board (GW8, the smoke test)

**The in-season term now answers for 252 of 669 players (37.7%), up from 137 (20.5%)** — the decay reversed,
measured on the real database rather than argued.

| player | old share | new share | xMins | last 5 |
|---|---|---|---|---|
| Konsa | refused | **1.000** | 90 | 90,90,90,90,90 |
| Gibbs-White | refused | 0.800 | 72 | 90,90,90,**0**,90 |
| Manzambi | refused | **0.709** | **64** | 27,71,85,71,65 |
| Onyeka | refused | 0.504 | 45 | 72,90,12,30,23 |
| Cherif | refused | 0.516 | 46 | 30,0,77,59,66 |
| Haaland | 0.985 | 0.976 | 88 | 90,90,79,90,90 |

Three things to read off it:
- **Konsa is the original complaint** (ADR-320) and it is answered — 0.879 from an Aston Villa season
  replaced by the five weeks he has just started at Arsenal.
- **Gibbs-White shows the forgiveness working as designed**: one 0 in the last five is forgiven, and it
  still costs him exactly `1/5` of the share. ⭐ *The window caps what one bad week costs him; it does not
  refund it.*
- **Manzambi is the correction nobody asked for and the most useful one.** He sat at **rank 2–3** on a
  projected full ninety handed to him by the *historical fallback*, having not played one in five weeks.
  ⭐⭐ *The all-or-nothing guard was not conservative about the number — it was conservative about changing
  its mind, and those are opposites at the top of the board.*
- **Haaland barely moves** (0.985 → 0.976): the population that already qualified is not disturbed.

---

### 🧪 Definition of Done

**1 — Automated tests.** 6 new tests in `tests/test_minutes.py`, and **7 deliberate defects, every one
caught:**

| mutant | caught by |
|---|---|
| the window-full gate removed | `test_nothing_is_forgiven_until_the_window_is_full` **+ 2 pre-existing ADR-173 tests** |
| denominator = `len(played)` | the August-miss and the costs-him-a-fifth tests |
| `_FORGIVEN_MISSES = 2` | `test_two_misses_in_the_window_still_refuse_to_answer` |
| `_FORGIVEN_MISSES = 0` | the August-miss and the costs-him-a-fifth tests |
| `_WINDOW_GAMEWEEKS = 6` | 3 tests |
| a 0-minute row counts as played | 3 tests |
| the window reads the earliest rounds | `test_the_forgiven_miss_rolls_out_of_the_window_entirely` |

⭐ **Mutant 1 is caught by the tests ADR-173 wrote**, which is exactly what a real superset change should
do — the old behaviour is still pinned by the old tests, and that is the proof the refusal was kept.

⚠️ **The mutation harness itself mislabelled one row** (it reported mutant 4 failing the wrong test) and the
value had to be echoed back per run to catch it. ⭐ *A mutation harness that reports the wrong thing is worse
than none, because it launders a passing test as a verified one.*

**2 — Manual smoke test.** `python -m src.cli xp` on the live GW8 database; the table above.

**3 — Docs.** This ADR, ADR-371's correction, ADR-173 superseded, ADR-320 closed on A, index, PROJECT_STATUS.

---

### 📊 Consequences

**Good:** the ratchet is gone and the in-season term's reach nearly doubled on live data. ADR-320's original
complaint is answered for Konsa. The correction at the top of the board runs the *useful* direction —
demoting players the historical fallback was promoting on last season's ninety minutes.

**Costs / limits:**
- 🔴 **Blank gameweeks are handled WORSE, and this is the one regression shipped.** Under ADR-173 a missing
  row disqualified a player outright and he kept his historical share. It is now a *forgiven miss* scored
  as a 0 against the available denominator, so a blank costs a nailed starter `1/5` of his share rather than
  nothing. No blanks have landed yet; ADR-173's caveat is unresolved and now has a **second claimant**, and
  the fix is unchanged: *"every completed gameweek"* and *"every gameweek his club played"* are different
  questions and nothing here asks the second.
- ⚠️ **Three rounds carry the whole result** (the window fills at GW6). This will be worth re-reading at
  GW15, when it has had ten.
- ⚠️ **`_WINDOW_GAMEWEEKS` and `_FORGIVEN_MISSES` are now two more unfitted constants.** They were chosen
  by ADR-320's prose, not by a sweep, *deliberately* — but they are parameters and they are not calibrated.
- ~~**ADR-371's option 3 (instrument the decay) was not taken.**~~ ✅ **Taken the same day** —
  [ADR-373](./ADR-373-a-number-that-makes-the-decay-loud.md). Shipping this reset the reach to 37.7% rather
  than making it visible, so nothing would have reported it if it started falling again. ⭐ *A fix applied
  once is not a fix that stays applied* — so the reach is now a line in the Actions log every gameweek, with
  a floor derived from what the rule this replaced had decayed to.
- **C — the dormant form blend — is now the last unopened option on ADR-320.**

---

### 🔗 Links

- [ADR-371](./ADR-371-the-ratchet-is-real-and-fixing-it-buys-nothing.md) — the gate, the measurement, and option 2
- [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — the rule replaced
- [ADR-125](./ADR-125-in-season-minutes-share.md) — the small-sample objection kept intact
- [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md) — option A, now closed
- `spikes/320-rolling-guard/` — `rolling.py` · `rolling_on_points.py` · `who_it_moves.py`
