# ADR-380 — A clean sheet he is not there to collect

**Decision ID:** ADR-380
**Date:** 2026-11-21
**Status:** ✅ **Part A built:** the sell guard's doubt is now scaled by expected minutes.
❌ **Part B declined:** ADR-372's fallback cliff is real arithmetic, and **both candidate fixes over-reach
measurably**. The violation is recorded, not corrected.
**From:** the owner, on Konsa and Saliba's return — *"the sentiment around Konsa is 'will he be replaced or
substituted with Saliba being fit again', that will start momentum over the next few days and weeks."*
**Superseded By / Replaces:** Fixes an omission in [ADR-376](./ADR-376-not-on-a-number-we-know-is-biased.md).
Finds and declines to fix a defect in [ADR-372](./ADR-372-a-window-that-forgets.md).
**Deciders / Participants:** Tony Sheridan (Owner, raised it), Claude Code (Implementation)

---

### 📌 How this was found

The owner was not reporting a bug. He was predicting **sentiment**: that the story about Konsa would turn
from *"he is under-rated"* to *"he is about to lose his place"*. Asking what the engine would do in that
world surfaced two defects, neither of which was visible from the direction we had been looking.

⭐⭐ *A forecast of how the complaint would change found two faults that the complaint itself had not.*

---

### ✅ Part A — the guard was blind to minutes, and got **stronger** as a player declined

ADR-376's sell guard withholds a DEF/GK sale when `unpriced_defence` explains it. That figure is a
clean-sheet delta in points per match — **and nothing multiplied it by the chance he is on the pitch.**

| scenario | window share | xMins | doubt **today** | doubt **scaled** |
|---|---|---|---|---|
| plays 90 every week | 1.000 | 90 | **+1.44** | +1.44 |
| 20-minute cameo | 0.844 | 76 | **+1.44** | +1.21 |
| benched once (forgiven) | 0.800 | 72 | **+1.44** | +1.15 |
| benched twice | *refused* | 79 | **+1.44** | — |
| benched three in five | *refused* | 79 | **+1.44** | — |

🔴 **The doubt never moved.** So as Saliba's return cut Konsa's minutes, his xP would fall, the engine would
want to sell him *more*, and the guard would withhold the sale **just as firmly** — at the exact point
selling became correct. ⭐⭐ **A GUARD THAT STRENGTHENS AS ITS SUBJECT GETS WORSE IS NOT CONSERVATIVE, IT IS
STUCK.**

⭐ `decision_xp` already minutes-scales the clean-sheet term it prices (`regime(gw)[1]`), so this was the
same arithmetic failing to reach the one place left out of it.

**Fixed, at no cost:** every `decision_xp` row already carries `minutes_weight`, so both callers hand it
over from a board they already hold. ⚠️ No extra read, so ADR-376's narrowing of ADR-218 stands untouched —
which mattered, because the obvious implementation wanted the per-gameweek history that ADR-376 had
deliberately dropped for growing to ~1.7 MB by May.

⭐ A test pins the **wiring**, not just the arithmetic: *a fix that is a no-op in production is worse than
none, because the unit tests still pass* — the fault `need_doubt` nearly shipped with in ADR-376.

---

### ❌ Part B — ADR-372 took away the ratchet and the cliff moved

ADR-372 replaced *"every completed gameweek"* with a rolling window forgiving one miss. Asked what happens
to a player losing his place:

```
plays every week        share 1.000  ->  xMins 90
benched ONCE in five    share 0.800  ->  xMins 72    (window answers, one miss forgiven)
benched TWICE in five   REFUSED      ->  xMins 79    <-- falls back to history
```

🔴 **The second benching RAISES his expected minutes**, to **0.879 — the share he earned at Aston Villa.**
⭐⭐ *I removed the ratchet and did not notice the cliff had moved rather than gone: the rule no longer gets
stricter every week, but the moment it gives up it reaches for a stale, higher number.*

### 🔴 And both of my fixes for it were wrong, measurably

**Candidate 1 — cap the fallback by the window share.** *"Evidence of decline must never improve a
forecast"* — a monotonicity claim, not a point estimate. It lowered **118 of 167** breachers by a mean of
**44.5 xMins**, worst cases 90 → 0. The reason: a player with no past seasons gets `availability_weight` =
**1.0 by default** (ADR-038), and a two-minute window share then crushes him. ⭐⭐ *That is not fixing a
cliff, it is re-deciding the cold-start default* — ADR-192's proposal, already declined by ADR-202,
arriving by the back door.

**Candidate 2 — cap only where the history is evidence.** Better: 75 of 167, mean 26.0 xMins. But the names
are **injured players** — Andersen 76 → 2, Zubimendi 79 → 10, Pedro Porro 73 → 9 — whose window share is
near zero because they have been out for weeks. ⚠️ Capping them undoes the exact protection ADR-173 exists
for: *"a player who sat one out… cannot be cratered by a single rest."*

**And then the population at the real boundary killed the premise.** Breachers by appearances in the last
five:

| played | count |
|---|---|
| 0 of 5 | 250 |
| 1 of 5 | 45 |
| 2 of 5 | 64 |
| **3 of 5** (breached by one) | **58**, of which **24** are cliff-eligible |

⭐⭐ **THOSE 24 ARE NOT KONSA-SHAPED, AND NOTHING IN THE DATA IS.** "Played 3 of 5" counts *appearances*, not
full games — Zubimendi played three of the last five and totalled about fifty minutes, which is why the
window says **0.109** and not the 0.6 a 3 × 90 player would give. They are **cameo-returners working back
from injury, where neither number is obviously right.** The motivating example is hypothetical, and the real
population at the boundary looks nothing like it.

**What it would have cost** (8 gameweeks, candidate 2):

| | board ρ | board MAE | hit@20 | breachers ρ | breachers MAE | hit@10 |
|---|---|---|---|---|---|---|
| today | 0.6203 | 1.25 | 0.19 | 0.0905 | 1.39 | 0.15 |
| capped | 0.6211 | **1.22** | 0.19 | **0.0729** | **1.28** | **0.17** |

Board-wide neutral (+0.02 SE on ρ, MAE better). On the population it touches, **ρ falls** while MAE and
hit@10 improve. ⚠️ Mixed, on a ρ of 0.09 — *we can barely rank these players at all*, which is itself the
answer: there is no reliable signal here to improve.

### 📋 So: recorded, not corrected

The monotonicity violation is **real in the arithmetic and absent from the data**. Leaving it is the
smallest honest action. ⭐ *A defect nobody exhibits, whose two candidate fixes both measurably break
players who do exist, is a defect to write down rather than patch.*

**Revisit when a real case appears** — a defender with genuine history, mostly-full recent appearances, then
two absences. ⚠️ Konsa becomes exactly that if Saliba's return benches him outright rather than reducing
him to cameos, so the owner's prediction may yet produce the population this needs.

---

### 🧪 Definition of Done

**1 — Automated tests.** 4 new (3 in `test_cleansheet.py`, 1 in `test_service_endpoints.py`). **4 deliberate
defects, all caught:** scaling removed · a missing weight zeroing the guard · an absent id zeroing the guard
· the service silently passing no weights.

**2 — Manual smoke test.** The scaling verified against the live board: Konsa's doubt 1.44 → 1.15 at a 0.8
weight, → 0.00 at zero. Part B measured in `spikes/380-the-cliff/`, twice, declining both times.

**3 — Docs.** This ADR, ADR-372's cliff recorded, ADR-376's limit closed, index, PROJECT_STATUS.

---

### 📊 Consequences

**Good:** the sell guard now retires itself as a player's minutes fall, instead of digging in. The ADR-372
cliff is documented with the population measured, so the next person meeting it starts from evidence.

**Costs / limits:**
- ⚠️ **The cliff is still there.** A 3 × 90-then-two-absences defender would still see his xMins rise on the
  second absence. Nobody is currently that player.
- ⚠️ Part A makes the guard **weaker**, which is the intent — it will withhold fewer sales, including some
  it was withholding correctly. The guard remains a credibility policy with no measured accuracy basis
  (ADR-375/376).
- ⚠️ `ask`/Streamlit remain unwired to the guard, so they never had the bug and still have no guard.

---

### 🔗 Links

- [ADR-376](./ADR-376-not-on-a-number-we-know-is-biased.md) — the guard this scales
- [ADR-372](./ADR-372-a-window-that-forgets.md) — the window whose cliff this declines to fix
- [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — *cannot be cratered by a single rest*
- [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) · [ADR-202](./ADR-202-the-minutes-baseline.md) — the cold-start demotion candidate 1 reinvented
- `spikes/380-the-cliff/` — `measure.py` · `result-2026-11-21.txt`
