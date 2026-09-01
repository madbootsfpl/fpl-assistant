# Architectural Decision Record: A shrink needs something to shrink toward

**Decision ID:** ADR-172
**Date:** 2026-09-01
**Status:** ✅ **Accepted — owner-reported, measured, gated, built** (Sprint 233, 2026-09-01).
**1655 → 1661 tests, ruff clean.**
**Superseded By / Replaces:** Repairs **ADR-124**, whose protection is inert on this season's data. Restores
the intent of **ADR-104**. **Not** ADR-125 — that defers in-season *minutes* to GW4-6; this is the *rate*,
and it is live now. **Changes `decision_xp` for 42 players** (see §Blast radius).
**Deciders / Participants:** Tony Sheridan (Owner, reported it), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner read the week's answer and did not believe it:

> *"Sangaré I think is overrated to score that amount, I'd say 5 and that would be in line with other apps."*

He was right, and the cause is not a tuning question. It is a formula that silently stopped doing anything.

**ADR-124** projects a no-history player by shrinking this season's `points_per_game` toward FPL's own
`ep_next`, in proportion to how many minutes back it:

```
rate = ppg × c + ep_next × (1 − c),    c = min(1, minutes / 900)
```

Sangaré has 165 minutes, so `c = 0.18`: **82% of his rate is supposed to come from the conservative side.**

**But FPL currently publishes `ep_next` equal to `points_per_game`.** Verified against the live
`bootstrap-static` API, not inferred from our copy: **513 of 626 players**. When the two inputs are the same
number, the blend returns it unchanged:

```
9.0 × 0.18  +  9.0 × 0.82  =  9.0        ← the evidence weighting cancels exactly
```

**This is the very failure ADR-124 was written to prevent.** ADR-104 took `max(ep_next, ppg)`; ADR-124
replaced it with a blend *toward* `ep_next` precisely because a switch on the value let one big score
dominate. The blend is the right shape — but it assumed the two inputs were independent, and upstream they
are not. **The bug came back through the input rather than the formula**, which is why no test caught it: the
code does exactly what it says.

---

### 🔬 Blast radius — measured 2026-09-01, GW3

| | |
|---|---|
| players on the cold-start tier | **143** of 626 |
| …whose shrink is **inert** (`ep_next == ppg`, `ppg > 0`) | **42** |
| …in the **top 20 by xP** | **8** |
| …in the **top 3** | **3 of 3** |

The board this produces:

| # | player | xP | tier | actual mins/game |
|---|---|---|---|---|
| 1 | Tzolakis (HUL) | **10.0** | cold, inert | 90 |
| 2 | M.Sangaré (BRE) | **9.9** | cold, inert | 82 |
| 3 | Mendy (HUL) | **8.0** | cold, inert | **60** |
| 4 | Haaland (MCI) | 6.3 | history | 90 |

**Haaland is fourth, behind three players with two games between them.** Further down: Yalcouyé at 4.5 xP on
**38 minutes a game**, Munoz at 5.5 on 58.

**It reaches every ranked surface**, because they all read one `decision_xp` (ADR-041): the captain pick, the
transfer ranking, Scout, the value frontier — and the **Lab optimiser, which maximises xP**, so it will build
squads out of these players.

The owner met it as three separate bad recommendations in one answer. They were one bug:

- **Captain Sangaré (9.9)** — inflated rate.
- **Transfer Raya → Tzolakis (+6.4)** — selling five seasons and xMins 0.96 for a promoted-side keeper with
  two games. The "+6.4" is measuring the inflation.
- **Start Thomas over João Pedro** — Thomas has four history rows, *all with zero minutes*, so he falls
  through to the same tier. The owner agreed with this one on instinct; it is the bug agreeing with him.

---

### ✅ Decision

**When `ep_next` carries no information, do not pretend it does — shrink toward the replacement prior instead.**

```
uninformative  ⇔  ep_next == points_per_game  AND  points_per_game > 0
rate           =  ppg × c + (ep_next if informative else _FALLBACK_PRIOR) × (1 − c)
```

`_FALLBACK_PRIOR = 2.0` already exists and already means this: it is what `fallback_rate` (ADR-040) shrinks a
thin-evidence player toward. **This ADR adds no new constant** — the tier that could not reach it now does.

**Both ends ADR-124 preserved stay preserved, and the `ppg > 0` guard is what keeps them:**

- **`minutes = 0` → `c = 0` → `rate = ep_next`.** Preseason, `ppg` is 0, so the equality test cannot fire and
  FPL's projection still wins outright. **This is ADR-104, untouched** — and getting it wrong here would
  re-break the case ADR-124 was careful about.
- **`minutes ≥ 900` → `c = 1` → `rate = ppg`.** Full evidence, unchanged either way.

**It self-repairs.** The day FPL publishes a real `ep_next`, the equality stops holding and the shrink goes
back to using it, with no code change and no constant to remember to revert.

**Effect on the players in question:**

| player | now | proposed | Δ |
|---|---|---|---|
| Tzolakis | 10.0 | **3.6** | −6.4 |
| M.Sangaré | 9.9 | **3.6** | −6.3 |
| Mendy | 8.0 | **2.8** | −5.2 |
| Dedić | 6.0 | **2.8** | −3.2 |

The owner's independent estimate for Sangaré was **~5**; shrinking toward the existing prior gives **3.6**,
and toward a 3.0 prior would give 4.5. His judgement brackets the honest answer and the shipped number was
roughly double it — which is the strongest evidence available that the direction is right, since it came from
outside the model.

---

### 🔀 Alternatives Considered

- **Always shrink toward `min(ep_next, prior)`.** Rejected: it would distort the case where `ep_next` is
  genuinely informative *and* legitimately above the prior — punishing FPL for being useful.
- **Ignore `ep_next` entirely for cold starts.** Rejected: it discards the zero-evidence end (`minutes = 0 →
  rate = ep_next`) that ADR-104 established and ADR-124 deliberately kept. Preseason it is the only signal
  there is.
- **Wait for the GW4-6 calibration sitting** (ADR-125's trigger). Rejected: that gate is about **minutes**,
  and it is a tuning question on terms we have. This is a **live correctness bug** on the most-read surface in
  the app, it is misranking the captain, and three gameweeks of advice is not a rounding error.
- **Lower the 900-minute `c` denominator so evidence accrues faster.** Rejected — it treats the symptom. With
  `ep_next == ppg` the blend returns `ppg` at *every* value of `c`; no denominator fixes a cancelled term.
- **Detect the upstream problem at `refresh` and null the column.** Rejected as the primary fix: it hides a
  fact about the source inside our ingestion, and every consumer would then have to handle a null it did not
  have before. The blend is the right place to decide what it can trust. *(Worth a follow-up: a
  Data-status note when a source field is degenerate.)*

---

### 🧭 Consequences

**Positive** — restores the protection ADR-124 intended; removes three phantom players from the top of every
ranked surface; stops the Lab optimising into them; self-repairs when the source improves; adds no constant
and no new tier.

**Negative / risks (mitigations)** — 42 players move down, some sharply, and one of them might genuinely be a
6-point-a-week player (*mitigation:* that is the trade a shrink exists to make, and the evidence for it is two
games; `c` rises every week they keep it up, so a real signal converges by ~game 10). Equality is a
**heuristic** for "uninformative" and could fire on a coincidence (*mitigation:* on a coincidence the player
is still a low-evidence cold start, so the conservative branch is the right answer anyway — being wrong here
costs accuracy in the direction we already chose). Recommendations will change visibly between gameweeks
(*mitigation:* say so; they were wrong before).

---

### ⏳ Deliberately NOT in this ADR

**The cold-start xMins is forced to 1.0**, so these players are also modelled as nailed 90-minute starters —
Mendy is projected on 60 minutes a game, Yalcouyé on 38. That is a **second, independent over-estimate
stacked on this one**, and it wants its own gate: it interacts with ADR-125's deferred in-season minutes
share, and fixing both at once would leave neither measurable. **Flagged, measured, not built.**

**The mirror-image case is also open.** Calafiori has a sound baseline (5.29 pp90) and projects **2.00**,
because his xMins is **0.43** from last season's injury-hit 1,697 minutes — while `FORM_WEIGHT` is 0 until the
GW4-6 sitting, so nothing can see he has started both games. He is a second Kinsky, and he belongs to
**ADR-125's** gate, not this one.

---

### 🧾 Implementation notes

- One function changes: `cold_start_rate` in `src/analytics/xp.py`. `player_xp`'s tier selection is untouched.
- Tests must pin **the cancellation itself** — `ep_next == ppg` must not return `ppg` — and both preserved
  ends. A test that only checks "Sangaré is lower" would pass on any change that lowers him.
- **Mutation-check the new guard** before trusting it, and check no existing test asserts the inflated value.
- Not a navigation change, so the ADR template's nav checklist is N/A. The index row is not.


---

### 📊 Built — measured after (2026-09-01)

**The top of the board, before → after:**

| # | before | | after |
|---|---|---|---|
| 1 | Tzolakis 10.0 *(cold, inert)* | → | **Haaland 6.3** |
| 2 | M.Sangaré 9.9 *(cold, inert)* | → | B.Fernandes 5.3 |
| 3 | Mendy 8.0 *(cold, inert)* | → | Watkins 5.3 |
| 4 | **Haaland 6.3** | → | Semenyo 5.0 |

**Cold-start-with-inert-shrink players in the top 20: 8 → 0.** The players the owner questioned:
Sangaré **9.9 → 3.6**, Tzolakis **10.0 → 3.6**, Mendy **8.0 → 2.8**, Thomas **3.6 → 1.3**. Raya is unchanged
at 3.6 — so the transfer that read *"+6.4"* is now worth nothing, which is the correct answer.

**The lineup call flips, and that is the interesting one.** Thomas 3.6 → 1.3 while João Pedro is untouched at
3.1, so *"start Thomas over João Pedro"* becomes *"start João Pedro"*. The owner had agreed with the original
on instinct — it was the bug agreeing with him, and the repair disagrees with both.

**End-to-end on the demo squad**, the same answer that exposed this: the transfer was
`Kelleher → Tzolakis (+7.3 XI xP)`; it is now `Senesi → Mukiele (+1.0 · Confidence 58/100 · Medium)`. A
phantom +7.3 became a modest, honestly-hedged +1.0 that agrees with the reported-departure signal already
flagging Senesi.

---

### 🔬 What building it found

**A test fixture had been depending on the bug.** `tests/test_ask.py::_worth_player` builds a MID with
`ep_next = ppg` and **no minutes at all**, then asserts `xp == ppg` so the value ranking has round numbers.
It got that equality from the *cancelled shrink*, not from evidence — and `ppg > 0` with `minutes = 0` cannot
occur in real data, because FPL derives points-per-game **from games played**. The fixture was only plausible
while the bug made it so. Fixed by giving it `minutes=900`, which produces the same numbers for the right
reason; the test is about value ranking, not this tier.

That is a different species from the tests found in Sprint 232 pinning stale *copy*. This one pinned a
**stale model of the data** — and it is the more dangerous kind, because it makes a bug look like the
specification.

**Every guard was mutation-checked**, including the subtle one: dropping the `ppg > 0` half of the test (so
the equality fires on the preseason zero-evidence case) must fail, and does. Reverting the fix outright fails
three tests; shrinking toward the prior unconditionally fails two.

**What is pinned is the cancellation, not the symptom.** `test_a_degenerate_ep_next_does_not_cancel_the_shrink`
asserts the identical-inputs case does **not** return the input, and
`test_the_cancellation_is_broken_at_every_level_of_evidence` asserts the rate actually *slopes* with evidence
— a flat line across `c` is the signature of the shrink cancelling again. A test asserting only *"Sangaré is
lower"* would have passed on any change that lowered him, including a wrong one.
