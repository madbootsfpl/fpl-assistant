# Architectural Decision Record: A threshold reads the distribution it claims to describe

**Decision ID:** ADR-210
**Date:** 2026-09-18
**Status:** ✅ **Accepted — built.** Closes the gate [ADR-190](./ADR-190-the-gw4-sitting.md) left open
(*"a live percentile for the exodus threshold, replacing the fixed constant"*) and records the *now* field
[ADR-203](./ADR-203-availability-is-recorded-as-it-passes.md) did not cover.
**1882 → 1898 tests, ruff clean.**
**Superseded By / Replaces:** Retires `EXODUS_PRESSURE` (ADR-146's constant). The ownership floor
([ADR-150](./ADR-150-one-signals-page.md)) is unchanged and now does a second job, stated below.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-146 gave the app its only route to news it cannot read: a heavy sell-off that our own `status` and `news`
leave unexplained. It defined the bar as **the worst tenth** of selling pressure, measured it on live GW1 data,
and shipped the number it got:

```python
EXODUS_PRESSURE = -8_000     # p10 across players owned ≥1%
```

ADR-190 tried to re-measure it at GW4, got **−3,901**, and could not use the result:

> *"`price_pressure` is built from `transfers_in_event` / `transfers_out_event` — **current-event fields**, and
> `player_history` stores no per-round transfer columns. So the app holds *one* week of this quantity at any
> moment. Two samples 51% apart do not establish a new value — they establish that it varies."*

That was right, and it stopped one line short of the mechanism. **It does not vary randomly.**

---

### 🎯 The finding

> ⭐⭐ **`transfers_in_event` / `transfers_out_event` are a counter that resets at every deadline and fills up
> across the week. A fixed threshold on an accumulating counter does not encode a severity — it encodes the
> hour of the week the calibration happened to run.**

Three honest readings of the same quantity:

| read | position in the cycle | p10 | what **−8,000** flagged |
|---|---|---|---|
| GW1 calibration (ADR-146) | mid-week | −7,996 | ~10%, *that day* |
| 2026-09-13 (ADR-190) | ~1 day after the GW4 deadline | **−3,901** | **2 of 190** |
| 2026-09-17 (this ADR) | ~5 days in, GW5 deadline imminent | **−14,992** | **50 of 188** |

The two samples ADR-190 called noise are two points on a ramp. And the consequence was live on the Signals
page: *"An exodus we can't explain"* listed **33 players** on deadline day — a page of names, which is not
news — and would have listed about two on the Sunday after a gameweek.

⭐ **The constant and the definition had come apart, and only the constant was in the code.** ADR-146 wrote
*"the worst tenth"* in a comment and shipped *"−8,000"* in an expression. For as long as those agreed, nothing
distinguished them.

---

### 💡 Options Considered

#### Option 1: Re-calibrate the constant *(rejected)*
What §B0's re-measure rule asks for. It cannot be executed — one reading exists at a time — and even with a
log it would only pick a better *hour*. The next week's ramp is unchanged.

#### Option 2: Normalise the counter by elapsed time *(rejected)*
Divide by hours since the deadline to recover a rate. Assumes transfers accrue **linearly**, and they do not:
volume spikes after team news and again at the deadline. It would trade a wrong constant for a wrong model,
and require the very history we do not have in order to fit it.

#### Option 3: A live percentile *(chosen)*
Compute the cut point from the distribution that exists when the question is asked. Immune to the ramp **by
construction** — not by being calibrated against it, but by re-reading the population every time. The number
stops being stable across the week and the **fraction it flags** becomes stable instead, which is what
*"the worst tenth"* always claimed.

#### Option 4: Do nothing and leave the gate open *(rejected)*
The flag is already wrong in both directions every week, and the cost of waiting is not zero: each gameweek
that passes without a record is a gameweek of this quantity that **cannot be recovered**.

---

### 🎯 Decision

**Two halves. The first fixes the flag; the second makes the question answerable at all.**

#### 1. `exodus_threshold(players)` — the worst tenth of the live board

`EXODUS_PRESSURE` is gone. `EXODUS_PERCENTILE = 10.0` replaces it, and the cut point is computed on demand
from every player above the ownership floor.

⚠️ **Three things the percentile needed before it was safe:**

* **A sign guard.** Every distribution has a bottom tenth, so a bare percentile would report an exodus in a
  week when the whole board was being *bought*, and would flag a tenth of the league preseason when every
  counter is flat zero. ⭐ *The percentile decides how severe; the sign decides whether there is anything to
  be severe about, and only the second one can answer "no".*
* **A population floor.** Below `MIN_EXODUS_POPULATION = 20` there is no distribution to take a tenth of.
* **The right population.** ADR-150's 1% ownership floor now does **two** jobs — it filters the list *and*
  defines the set the cut point is taken over — and they must be the same set. `price_pressure` divides by
  ownership, so a 0.1%-owned player reads at −500,000 per 1%; let those into the population and they occupy
  the entire bottom tenth, the cut runs away to an unreachable extreme, and **the flag goes silent for the
  players it exists to warn about.** ⚠️ *That failure is silent, not loud.*

⭐ **Where it cannot answer, it returns `None` and the flag does not fire** — deliberately the
[ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) direction, applied on purpose this time rather than
by accident: the "no opinion" value is the one that says nothing, not the one that flags everybody.

#### 2. `player_transfer_flow` — recording a *now* field before it expires

⭐ **This is ADR-203's table, for the one other quantity that was still expiring.** `transfers_in_event`,
`transfers_out_event` and `selected_by` live on the single mutable `players` row; FPL resets the counters at
every deadline and publishes no history for them. Written on every `refresh`, one row per player per event:

| column | why |
|---|---|
| `event` | ⚠️ the gameweek the counter is climbing **toward**, not the one being played. Without it the table is readings from different weeks that look like one series. |
| `hours_to_deadline` | ⭐⭐ **the phase, and the whole reason the table exists.** A value without its position in the cycle is not a measurement — that is exactly what ADR-190 had, and why it could only conclude *"it varies"*. |
| `observed_at` | when we **looked**. ADR-203's distinction: never "when it changed". |

One row per player per event, upserted, so each event settles on the **last reading before its deadline** —
the one point in the week comparable across weeks. Intermediate readings are not kept: the live threshold no
longer needs the ramp, and a row per refresh is ~330k a season to describe a curve nothing reads.

---

### ⚖️ Consequences & Trade-offs

**Measured on the live board, 2026-09-17 (≈6h before the GW5 deadline):**

| | Signals lists | flagged across all players |
|---|---|---|
| fixed −8,000 | **33** | 73 |
| **live worst tenth (−14,992)** | **7** | 11 |

Smoke-tested on the owner's real squad: *"Hume (53,752 sold him this week — nothing in the data says why)"* —
the flag still reaches `ask`, `analyse`, Health, the Risk Monitor and Signals.

**Positive:** the flag now means what it says in every week of the season, at any hour. A gate ADR-190 left
open is closed, and the quantity behind it stops being destroyed weekly.

**Negative / limits — stated, not buried:**

* ⚠️⚠️ **`EXODUS_PERCENTILE = 10` has no more provenance than `−8,000` did.** It is ADR-146's own stated
  definition rather than a new claim, and that is the *only* thing that makes it better today. It has never
  been validated against whether the worst tenth is the right tenth.
  📅 **This is what the log is for**: re-ask at the GW8 review (on or after **2026-10-26**), when ≥4 events of
  end-of-cycle readings exist, comparing like with like for the first time. [ADR-199](./ADR-199-a-threshold-needs-a-provenance.md)'s
  rule applies to the new number exactly as it did to the old one.
* The flag now fires on a **relative** bar. In a genuinely quiet week the worst tenth is less alarming than
  the phrase "an exodus" implies — the sign guard only rules out a *net-buying* board, not a dull one.
* **One more table on every refresh** (659 rows). Measured at well under a second.
* ⚠️ The first row can only be written by a refresh that happens **before a deadline**. GW5's is 17:30Z on
  2026-09-18; a refresh after it records GW6 and GW5's totals are gone for good.

---

---

### 📡 Post-ship observation, 2026-09-18 evening — the ramp, caught at both ends in one day

The GW5 deadline (17:30Z) passed before a refresh could capture it, so **GW5's end-of-cycle reading is lost** —
exactly as this ADR said it would be, and the cleanest possible demonstration of why the log exists. FPL reset
the counters at the deadline; the first `player_transfer_flow` rows are **659 players against GW6**, stamped
**517.7 hours** from its deadline (the international break).

That accident produced a **second reading at the opposite end of the cycle, nine hours after the first** — and
it is stronger evidence than anything in the build:

| read (same day) | position in cycle | live threshold | Signals lists | fixed −8,000 lists |
|---|---|---|---|---|
| ~11:00Z | **6 h before** the GW5 deadline | **−14,992** | **7** | **33** |
| ~20:15Z | **3 h after** it, counters reset | **−263** | **8** | **0** |

⭐⭐ **The threshold moved by a factor of 57 in nine hours. The fraction it flags did not move at all.**

That is the whole claim of this ADR, observed rather than argued. And it shows the old constant failing in
**both** directions on the same day's reality: −8,000 would have published a page of 33 names in the
afternoon and then gone **completely silent** in the evening — not because the crowd stopped selling, but
because FPL zeroed a counter.

⚠️ **The lost GW5 row is the cost of the observer arriving one day late**, which is the lesson ADR-203 recorded
and this ADR repeated: *every refresh that runs while the recorder is unwritten is an observation that does
not exist.* GW6's row will be the first complete one.

### 🛠 Implementation & Migration

* **Components Affected:** `analytics/crowd.py` · `analytics/ranking.py` (new `percentile_value`) ·
  `analytics/gameweek.py` · `analytics/squad_risk.py` · `storage.py` · `ingest.py` · `cli.py` · `ask.py` ·
  `web_streamlit/views/squads.py` · `web_streamlit/pages/3_Signals.py` · `web_streamlit/analytics.py`
* **Action Items:**
  - [x] `exodus_threshold` / `exodus_population` / `exodus_detector`; `EXODUS_PRESSURE` removed
  - [x] `crowd_exodus(player, threshold)` — **required**, so a forgotten call site raises (ADR-181)
  - [x] Every call site binds to the **whole board**; `gameweek_plan` / `squad_risk_rows` take `exodus_for`
  - [x] `player_transfer_flow` + `save_transfer_flow` + `transfer_flow`, written from `refresh`
  - [x] `ranking.percentile_value`, with `web_streamlit.analytics._percentile` delegating to it (ADR-123/127 —
        two copies of a rule is how the last one drifted)
  - [x] Guards, and the guards **swept for rather than listed** (ADR-184): no direct `crowd_exodus` call in
        `src/`, every `exodus_detector` bound to `players`, the retired constant unimportable
  - [x] Mutation-tested: **12 mutants, 12 red.** Two survived first time and both were real gaps —
        the `threshold is None` path had no test, and the ownership floor was tested on the *list* but never
        on the *population*
  - [ ] 📅 **GW8 review (on or after 2026-10-26): re-ask `EXODUS_PERCENTILE` against ≥4 events of the log.**

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A constant measured from a distribution is a claim about that distribution, and it keeps the shape of the
> moment it was taken — including the parts of that moment nobody wrote down.**

ADR-190 got within one line of this and stopped at *"it varies"*, because two samples 51% apart look like
noise unless you ask **what else was different between the two readings**. What was different was the day of
the week — and the quantity is a counter that resets weekly, so the day of the week *was* the measurement.

⭐ The general form: **before concluding that a quantity is noisy, check whether your two samples were taken
at the same point in whatever cycle it lives in.** A measurement of an accumulation is not a measurement of a
level.

And the smaller one, which is the third time this trail has recorded a version of it:
⭐ *the definition and the number that implements it are two different things, and only one of them is executable.*
`CLEAR` (ADR-190), `TIE_NOISE` (ADR-209) and now `EXODUS_PRESSURE` were all a comment describing a rule beside
a literal that had stopped obeying it. ⭐⭐ **A lesson recorded about one number does not check the others** —
ADR-209 wrote that sentence nine days ago about a constant three functions away from this one.

---

### 🔗 References & Related Artifacts
- **The gate this closes:** [ADR-190](./ADR-190-the-gw4-sitting.md) — *"a live percentile for the exodus threshold"*
- **The flag itself:** [ADR-146](./ADR-146-the-crowd-knows-what-the-feed-does-not.md) · [ADR-150](./ADR-150-one-signals-page.md) (the ownership floor)
- **The same expiry, the other field:** [ADR-203](./ADR-203-availability-is-recorded-as-it-passes.md) · [ADR-201](./ADR-201-a-season-is-part-of-the-identity.md)
- **A threshold needs a provenance:** [ADR-199](./ADR-199-a-threshold-needs-a-provenance.md) — and the new one still owes its
- **One recipe at every call site:** [ADR-181](./ADR-181-one-recipe-means-every-caller.md)
- **Sweep for the claim, don't list the places:** [ADR-184](./ADR-184-sweep-for-the-claim.md)
- **The same mistake, nine days earlier:** [ADR-209](./ADR-209-the-longer-view-breaks-the-tie.md)
