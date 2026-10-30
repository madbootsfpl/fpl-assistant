# ADR-377 — The reading we keep

**Decision ID:** ADR-377
**Date:** 2026-10-30
**Status:** ✅ **Accepted and built** (the capture) — the row now settles on the reading **closest to the
deadline**, explicitly, and the phase is reported on every tick. 📋 **The cadence defect is NOT fixed and
deliberately not chased with more cron.** Plus a measured **corroboration** for ADR-375 from the crowd.
**Superseded By / Replaces:** Hardens [ADR-210](./ADR-210-a-threshold-reads-the-distribution-it-describes.md)'s log and reports what it
was built to protect. Applies [ADR-373](./ADR-373-a-number-that-makes-the-decay-loud.md)'s pattern again.
Supplies independent support for [ADR-375](./ADR-375-the-defence-he-played-behind.md)'s gate.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 🔴 First, a misdiagnosis of mine, corrected

I reported that the crowd capture was *"broken in exactly the way the table was built to prevent"* — 2 events,
GW7–8 missing, phases 420 h and 121 h apart. **That was the wrong database.** I queried local
`data/fpl.db`, which only moves when I run `refresh` by hand; production is Postgres, written by the hourly
Action (ADR-211). ⭐⭐ *A sparse table on a developer's laptop is evidence about the developer's laptop.*

Checked properly against the Actions API: **100 runs, 100 successful.** Nothing is failing.

---

### ⚠️ The real defect, and it is narrower than I claimed

| | measured |
|---|---|
| runs in window (2026-10-13 → 10-30) | 100, all successful |
| gap between runs | **median 3.9 h**, mean 4.1 h, max 7.5 h |
| declared cadence | **hourly** |

`cadence()` has a pre-deadline branch whose comment states the design intent exactly:

> *"ADR-210's transfer counters reset at this deadline, and the reading before it cannot be recovered
> afterwards. **Four chances in the last hour** is the redundancy that makes cron's drift survivable."*

⭐⭐ **THOSE FOUR CHANCES DO NOT EXIST.** `INTERVAL_PRE_DEADLINE` is a 15-minute *policy*, but the policy only
runs when the workflow fires, and the workflow fires every ~3.9 h. At that gap the expected chance of any run
landing inside the final hour is **~26%**. Observed, on the two deadlines that passed inside the window:

| GW | deadline | last run before | phase |
|---|---|---|---|
| 7 | 2026-10-17 10:00 | 09:26 | **0.56 h** |
| 8 | 2026-10-23 17:30 | 12:33 | **4.93 h** |

**A 4.4-hour swing between consecutive gameweeks**, on a counter that resets and climbs all week. That is
precisely the comparability ADR-210 built the table to protect, and ADR-190 is the record of it costing a
measurement. ⭐ *The policy is not wrong; it is unreachable, which is a different bug and needs a different
fix.*

### 🚫 Why this is not fixed with more cron

`data.yml`'s own comment already settles it, with numbers from 2026-09-26: `*/15` fired **6 times in 24
hours** — *"6-7% of what it declared"* — and the conclusion drawn then was *"this changes the documentation,
not the data. GitHub deprioritises scheduled runs on free runners."*

⭐⭐ **ADDING DEADLINE-CLUSTERED CRON LINES WOULD BE ACTING AGAINST A MEASUREMENT THIS REPO ALREADY TOOK.**
Density did not translate into firings at `*/15`; there is no reason it would at a deadline. A fix that the
evidence says will not work is not a fix, and shipping one would make the schedule *look* addressed.

---

### ✅ What was built instead: robustness and visibility

**1 — The row keeps the reading closest to the deadline, explicitly.** The schema comment claimed the row
*"settles on the LAST reading taken before N's deadline"*. It did — but only because later runs happen to be
closer. The upsert was unconditional last-write-wins:

```sql
ON CONFLICT(element_code, event) DO UPDATE SET …
WHERE excluded.hours_to_deadline IS NOT NULL
  AND (player_transfer_flow.hours_to_deadline IS NULL
       OR excluded.hours_to_deadline < player_transfer_flow.hours_to_deadline)
```

⭐ *A guarantee the data happens to satisfy is not a guarantee.* A replayed snapshot, an out-of-order write or
a NULL phase silently replaced the best evidence of the week with worse; now it cannot.

**2 — The phase is reported on every tick** (`crowd_phase`, in the refresh line):

```
Published 669 players, 20 teams, 380 fixtures, 20 Elo, xP board 669 players from GW9, Team DNA 20 teams, crowd GW9 @ 0.6h (ordinary hours).
```

⭐ ADR-210 built the table so readings would be phase-comparable **and nothing reported the phase**. It prints
every tick, not only when bad: the phase is a countdown, so watching it fall is how you know the capture is
alive. ⚠️ *A series whose comparability cannot be seen is one that will be averaged as though it were
comparable.*

---

### ⭐⭐⭐ The unlock: ownership is a stock, the counters are a flow

The phase defect blocks `transfers_in_event` / `transfers_out_event`, because those **reset at each deadline
and accumulate** — a reading at 0.6 h out and one at 4.9 h out measure different fractions of a week.

**`selected_by` does not reset.** It is a *level*, so a few hours of phase drift barely moves it, and a
week-to-week **difference in ownership** is usable from the data we already hold.

⭐⭐ **SO THE SENTIMENT WORK DOES NOT HAVE TO WAIT FOR THE CADENCE FIX.** The phase defect was the reason to
think it did; it only afflicts one of the two columns.

### 📊 The crowd, used as a validation set rather than an input

It cannot yet be backtested as a *feature* (too few phase-comparable readings). It can be used for free as a
**second opinion on a correction derived independently** — ADR-375 claims `clean_sheet_delta` under-credits
defenders who moved to a better defence; if so, those should be the players the crowd is buying.

ρ(our unpriced defence, ownership change GW6 → GW9), DEF/GK:

| owned ≥ | n | ρ | mean change, under-rated | mean change, rest |
|---|---|---|---|---|
| 0.0% | 290 | **0.021** | +0.167 pp | −0.082 pp |
| 1.0% | 99 | 0.180 | +0.371 pp | −0.321 pp |
| 3.0% | 56 | 0.265 | +0.681 pp | −0.417 pp |
| **5.0%** | 39 | **0.398** | **+1.089 pp** | **−0.786 pp** |

⚠️ **The first run of this returned ρ = 0.021 and I nearly reported "no corroboration".** The flaw was mine:
**ownership change is floor-limited.** A player at 0.0% cannot lose ownership and will not gain any, and the
un-owned tail — Meslier, Igor, Alleyne, all at 0.0% — dominated the correlation with near-zero movement
carrying no information. ⭐⭐ *The crowd has no opinion about a player nobody owns, and reading its silence as
disagreement is a sampling error, not a finding.*

Restricted to players the crowd actually holds an opinion about, **ρ rises monotonically** and the split
widens to ~1.9 pp. Konsa: unpriced **+1.44**, ownership **19.4% → 19.8%** in the weeks the engine was
advising his sale.

🔴 **Reported as support for ADR-375's gate, not as a result.** A monotone rise in ρ with the ownership floor
is also exactly what a **measurement-quality** effect looks like — ownership change is simply measured better
among owned players — and **two readings cannot tell those apart.** n = 39 at the top cut.

---

### 🧪 Definition of Done

**1 — Automated tests.** 8 new (4 in `test_transfer_flow_log.py`, 4 in `test_pipeline.py`). **6 deliberate
defects, all caught:** keeps the furthest reading · a NULL phase overwrites a good one · phase reports the
furthest reading · phase reports the oldest gameweek · phase never printed · last-write-wins restored.
⭐ The keep-closest mutant is also caught by **ADR-210's own** `test_the_row_for_a_gameweek_settles_on_the_
LAST_reading_before_its_deadline`, which is the right kind of overlap.

⚠️ **Three harness notes, all mine and all worth the lines.** Two mutants first came back as false
survivors: one because my `perl` pattern required `))` where the file has `)",`, and one because my test had
**a single row per gameweek, so `min` and `max` were the same number** — fixed by filing a second player at a
worse phase. ⭐⭐ *A test with a one-element sample cannot pin a choice between aggregates.* And the whole
harness reported `NO SUMMARY` for every row because **zsh does not word-split unquoted parameters**, so
`$FILES` reached pytest as one bogus path. ⭐ *An invalid mutant and an uncaught one look identical unless the
harness proves it ran.*

**2 — Manual smoke test.** `crowd_phase` against the live database returns `(9, 121.0)` — which is itself the
instrument working: it says this local reading is 121 h out and therefore worthless.

**3 — Docs.** This ADR, index, PROJECT_STATUS, README counts; `spikes/375-crowd-as-validation/`.

---

### 📊 Consequences

**Good:** the log's central promise is now enforced rather than hoped for, and its usability is visible every
tick. The sentiment line is unblocked on `selected_by` without waiting for anything. ADR-375's gate gained
independent support.

**Costs / limits:**
- 🔴 **The cadence defect is open and now quantified** (median 3.9 h against a declared hourly tick, ~26%
  deadline coverage). It is a platform property on free runners, and the honest options are paying for
  runners, an external trigger, or accepting phase-varying flows and conditioning on `hours_to_deadline`.
- ⚠️ **Keep-closest cannot create a reading that was never taken.** If no run lands in the final hour, the
  best available is still hours out; this stops degradation, not absence.
- ⚠️ The crowd corroboration rests on **two readings and n = 39** at its strongest cut, and cannot separate
  corroboration from a measurement-quality artefact.
- ⚠️ Flow-based sentiment still needs phase-comparable readings. ⭐ *The stock is usable now; the flow is not.*

---

### 🔗 Links

- [ADR-210](./ADR-210-a-threshold-reads-the-distribution-it-describes.md) — the log, and the phase column this reports
- [ADR-375](./ADR-375-the-defence-he-played-behind.md) — the correction the crowd corroborates
- [ADR-373](./ADR-373-a-number-that-makes-the-decay-loud.md) — the same make-it-visible pattern
- [ADR-190](./ADR-190-the-gw4-sitting.md) — what an incomparable series cost last time
- `spikes/375-crowd-as-validation/validate.py`
