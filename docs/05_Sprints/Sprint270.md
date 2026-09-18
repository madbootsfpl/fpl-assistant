# Sprint 270: A threshold reads the distribution it claims to describe

**Dates:** 2026-09-18
**Status:** ✅ **ADR-210 — 1882 → 1898 tests, ruff clean. 12 mutants, 12 red (2 survived the first sweep).**

---

## Where this sprint came from — and the one that did not happen

The session opened on *"resume madboots"*, and the first answer was **wrong**: ADR-192 (cold-start xMins
inflated to a nailed 1.0) looked like the obvious resume point, because ADR-206 and ADR-209 had both raised
its priority in the preceding days.

It is **date-gated**. ADR-202 already swept it (1.0 → 0.4) and **declined** it — ρ falls monotonically on the
whole board *and* on the 130-player cold-start sub-population — and ADR-204 re-aimed the whole concern at a
better variable, holding both to a pre-registered rule at the **GW8 review, on or after 2026-10-26**.

⭐ **Opening it today would have been running a measurement before its own date and setting a constant off an
n = 1 harm** — precisely what ADR-199 and ADR-183 exist to prevent. *A rule that only binds when it agrees
with you is not a rule* (ADR-204's own sentence, nine days old).

So the sprint went to the one item on the roadmap that was **not waiting on gameweeks and could never be
unblocked by them**: ADR-190's open gate, *"a live percentile for the exodus threshold."*

---

## 🔬 Measured first, and it changed the diagnosis

ADR-190 re-measured `EXODUS_PRESSURE` at GW4, got **−3,901** against the shipped **−8,000**, and recorded:

> *"Two samples 51% apart do not establish a new value — they establish that it varies."*

Right, and one line short. Reading the live board again today:

| read | position in the cycle | p10 | what −8,000 flagged |
|---|---|---|---|
| GW1 calibration (ADR-146) | mid-week | −7,996 | ~10%, *that day* |
| 2026-09-13 (ADR-190) | ~1 day after the GW4 deadline | **−3,901** | **2 of 190** |
| 2026-09-17 (this sprint) | ~5 days in, GW5 deadline imminent | **−14,992** | **50 of 188** |

⭐⭐ **`transfers_in_event` / `transfers_out_event` are a counter that resets at every deadline and fills up
across the week.** `price_pressure` is an **accumulation**, not a level. The two "noisy" samples are two
points on a **ramp**, and the thing that differed between them was the day of the week — which, for a counter
that resets weekly, *was* the measurement.

⭐ **A fixed threshold on an accumulating counter does not encode a severity. It encodes the hour of the week
the calibration happened to run.**

The reader was paying for it: *"An exodus we can't explain"* listed **33 players** on deadline day — a page of
names, which is not news — and about two on the Sunday after a gameweek.

---

## ✅ What was built

### 1. The threshold reads the live board

`EXODUS_PRESSURE` is retired. `EXODUS_PERCENTILE = 10.0` replaces it and the cut is computed on demand.
**The number stops being stable across the week; the fraction it flags becomes stable instead** — which is
what *"the worst tenth"* always claimed.

Three things it needed before a percentile was safe:

* ⭐ **A sign guard.** Every distribution has a bottom tenth, so a bare percentile would report an exodus in a
  week when the whole board was being *bought*, and flag a tenth of the league preseason on flat zeros.
  *The percentile decides how severe; the sign decides whether there is anything to be severe about, and only
  the second one can answer "no".*
* **A population floor** — `MIN_EXODUS_POPULATION = 20`. A tenth of nine players is not a tenth of anything.
* ⚠️ **The right population.** ADR-150's 1% ownership floor now also defines the set the cut is taken over.
  `price_pressure` divides by ownership, so a 0.1%-owned player reads at −500,000 per 1%; let those in and
  they occupy the entire bottom tenth, the cut runs away to an unreachable extreme, and **the flag goes silent
  for the template players it exists to warn about.** *That failure is silent, not loud.*

Where it cannot answer it returns `None` and the flag does not fire — ⭐ deliberately ADR-192's direction,
applied **on purpose** this time: the "no opinion" value is the one that says nothing, not the one that
flags everybody.

### 2. The observer, for the other *now* field

⭐ **ADR-203's table, for the one quantity that was still expiring.** The counters and `selected_by` live on
the mutable `players` row; FPL resets them at each deadline and publishes no history, so every refresh
destroyed the only copy — **which is why ADR-190's own instruction had nothing to run on.**

`player_transfer_flow`, written on every refresh, keyed by the event the counter climbs **toward** (⚠️ not the
one being played), upserted so each event settles on the **last reading before its deadline**.

⭐⭐ **Every row carries `hours_to_deadline`, and that column is the whole point: a value without its position
in the cycle is not a measurement.** It is exactly what ADR-190 lacked, and why it could only say *"it varies."*

---

## 📊 What changed, on the live board

~6 hours before the GW5 deadline:

| | Signals lists | flagged across all players |
|---|---|---|
| fixed −8,000 | **33** | 73 |
| **live worst tenth (−14,992)** | **7** | 11 |

Smoke-tested on the owner's real squad — the flag still reaches `ask`, `analyse`, Health, the Risk Monitor
and Signals: *"Hume (53,752 sold him this week — nothing in the data says why)."*

---

## ⚠️ Stated, not buried

**`EXODUS_PERCENTILE = 10` has no more provenance than −8,000 did.** It is ADR-146's own stated definition
rather than a new claim, and that is the *only* thing that makes it better today. Nothing has validated that
the worst tenth is the right tenth.

📅 **That is what the log is for** — re-asked at the **GW8 review (on or after 2026-10-26)**, when ≥4 events
of end-of-cycle readings exist and like can be compared with like for the first time. ADR-199's rule applies
to the new number exactly as it did to the old one.

---

## 🧪 Guards, and breaking them on purpose

The guards **sweep for the claim** rather than checking the files I thought of (ADR-184): no direct
`crowd_exodus` call anywhere in `src/`, every `exodus_detector` bound to the whole board, the retired constant
unimportable. ⚠️ The last one greps for the constant **in use, not the word** — the name still appears inside
backticks in the comments and ADRs that explain why it went, and deleting that prose would destroy the record
rather than protect it (ADR-178's first anti-pattern). ⭐ *A history of a decision is not a repetition of it.*

**12 mutants, 12 red — but two survived the first sweep, and both were real gaps:**

| mutant | first sweep | why it survived |
|---|---|---|
| delete the `threshold is None` guard | **GREEN ✗** | nothing exercised the path — no test ever built a board too small or too quiet to have a cut point. ⭐ *A guard nothing reaches is not a guard.* |
| ignore the ownership floor inside `exodus_population` | **GREEN ✗** | the only floor test asserted the **list** was filtered, never the **population** the percentile is taken over. ⭐ *Two jobs behind one constant, and only one of them was tested.* |

Both now have tests, and both mutants are red.

---

## ⚠️ A bug caught before it ran

`next_deadline` indexes its rows (`f["event"]`) because every other caller hands it `sqlite3.Row`s. `refresh`
holds `Fixture` **dataclasses**, which are not subscriptable — so the wiring would have raised on the first
real refresh while every dict-based test passed. ⭐ *A fixture that cannot express what the code reads will
confirm a broken mechanism* (6th time this month), so the test uses the dataclass `refresh` actually builds.

`crowd_exodus(player, threshold)` takes its threshold **required** for the same family of reason (ADR-181):
a call site that forgets it **raises**, instead of quietly inheriting a number measured in August.

---

## 💡 The lesson

> **Before concluding that a quantity is noisy, check whether your two samples were taken at the same point in
> whatever cycle it lives in. A measurement of an accumulation is not a measurement of a level.**

And the smaller one, for the third time on this trail: ⭐ *the definition and the number that implements it
are two different things, and only one of them is executable.* `CLEAR` (ADR-190), `TIE_NOISE` (ADR-209) and
now `EXODUS_PRESSURE` were each a comment describing a rule beside a literal that had stopped obeying it.
⭐⭐ **A lesson recorded about one number does not check the others** — ADR-209 wrote that sentence nine days
ago, about a constant three functions away from this one.

---

## 📌 Follow-up for the owner

⏳ **A `refresh` before 17:30Z today writes the first `player_transfer_flow` rows for GW5** (659 players,
~6h from the deadline). After the deadline the counters reset and this week's totals are gone for good —
*the observer has to be in place before the thing it observes.*
