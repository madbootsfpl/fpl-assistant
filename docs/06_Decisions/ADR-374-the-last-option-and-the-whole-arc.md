# ADR-374 — The last option, and what the whole arc says

**Decision ID:** ADR-374
**Date:** 2026-10-26
**Status:** ❌ **DECLINED. `FORM_WEIGHT` stays 0.** ADR-320's option **C**, the last unopened one. Peak gain
**+0.05 SE against a +1 SE bar**, MAE rising monotonically from the first step, hit@20 never beating the
baseline. **No production code changed. 3,210 tests (unchanged), ruff clean.**
**Superseded By / Replaces:** Closes [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md)
— **all four options now measured.** Re-affirms [ADR-060](./ADR-060-per-gameweek-history-and-dormant-form-blend.md)'s dormancy on
evidence rather than on absence of it. Runs [ADR-101](./ADR-101-calibration-methodology.md)'s harness.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Nothing was built, because it was already built

ADR-320 described C as *"already built, already tested, dormant by decision"* and that is exactly right:
`form_rate` and `blend_form` have been in `src/analytics/form.py` since ADR-060, wired into `_rate_tier`
behind `config.FORM_WEIGHT = 0.0`, with an invariance test pinning the dormancy.

⭐⭐ **AND THE HARNESS WAS ALSO ALREADY BUILT.** `python -m src.cli calibrate --weight form` exists for
precisely this question — ADR-101 wrote it, `docs/GW1_RUNBOOK.md` documents the flip, and
`config.py`'s own comment says *"at ~GW4+ run `calibrate --weight form` — it backtests + recommends a
value"*. **No spike was written.** ⚠️ This is the sixth time this month a fact or a tool the repo already
held was nearly rebuilt (ADR-370 wrote and deleted a duplicate of ADR-188's dormant weight); the only reason
it did not happen again is that looking first has become the first move.

---

### 📊 The sweep, searched to the end of the domain

| weight | ρ | MAE | hit@20 | vs 0 |
|---|---|---|---|---|
| **0.00** | **0.620** | **1.25** | **0.19** | — |
| 0.05 | 0.621 | 1.26 | 0.17 | +0.03 SE |
| **0.10** | **0.622** | 1.26 | 0.19 | **+0.05 SE** ← peak |
| 0.15 – 0.35 | 0.621 | 1.26–1.27 | 0.18–0.19 | +0.03 SE |
| 0.40 | 0.620 | 1.28 | 0.18 | 0.00 SE |
| 0.50 | 0.619 | 1.29 | 0.16 | −0.03 SE |
| 0.70 | 0.615 | 1.31 | 0.14 | −0.13 SE |
| 1.00 | 0.606 | 1.35 | 0.11 | −0.36 SE |

**1 SE = 0.039. The peak is +0.002.** MAE rises from the very first step and never comes back; hit@20 never
exceeds the baseline's 0.19 at any weight.

### ⭐⭐ Why no finer grid was run, and why that is not ADR-369's mistake

[ADR-369](./ADR-369-the-edge-of-the-grid.md) exists because ADR-367 missed a bar at the **edge** of its grid
and declined to look beyond it — *"a bar missed at the edge of a search is a bar that was never fully
tested."* That lesson is honoured here and then found not to apply:

- The peak is **interior** (0.10), with the curve turning over on **both** sides.
- The domain is searched **to its end** — 0 → 1.0, where 1.0 means *"ignore career history entirely"*.
- ⭐⭐ **THE TOTAL VARIATION OF ρ ACROSS THE WHOLE DOMAIN IS 0.016 — ABOUT 0.4 SE. THE BAR IS 1 SE. NO VALUE
  AT ANY RESOLUTION CAN CLEAR A BAR THAT EXCEEDS THE ENTIRE RANGE OF THE FUNCTION.**

⭐ *A finer grid buys resolution, not altitude.* ADR-369 refined a search whose peak sat where the curve was
still climbing; refining this one would be measuring a flat line more precisely.

---

### ✅ ADR-320's claim about C is the one that survives

ADR-320 said C had *"the biggest single effect on Konsa"* and §2 said his **3.84 per 90 this season has zero
influence on his projection.** Both are correct, and unlike its claims about option A, these hold at GW8:

| player | xP at 0.00 | xP at 0.10 | form pp90 | conf |
|---|---|---|---|---|
| **Konsa** | **2.70** | **3.20** | **8.40** | 1.00 |
| Manzambi | 5.80 | 6.10 | 7.93 | 1.00 |
| Haaland | 6.70 | 6.90 | 8.95 | 1.00 |
| Gibbs-White | 4.00 | 3.80 | 2.60 | 1.00 |
| Palmer | 5.40 | 5.00 | 2.52 | 1.00 |

**220 of 669 players move by ≥ 0.05 xP** — the widest blast radius of the four options, as ADR-320 predicted.
Top-20 churn: **1 out, 1 in.**

⭐⭐ **AND THAT IS THE FINDING.** Konsa's form rate is **8.40 per 90** against a base of 2.98 — the term is not
whispering, it is shouting, and it is shouting the direction the owner's complaint pointed. **The board does
not get better.** A signal that is strong, correctly aimed, and worth +0.05 SE is a signal that is right
about as often as it is wrong.

---

### ⭐⭐⭐ The arc: four fixes, one complaint, and a measured ceiling

ADR-320 began with *"Why is Arsenal's Konsa so low rated?"*. All four of its options are now measured:

| option | what it was | result |
|---|---|---|
| **A** — loosen the in-season minutes guard | the ratchet | ❌ +0.18 SE — **shipped anyway** as a *correctness* fix ([ADR-372](./ADR-372-a-window-that-forgets.md)) |
| **B** — shrinkage blend of minutes | ADR-204's candidate | ❌ +0.9 SE ([ADR-367](./ADR-367-the-gw8-review-phase-1-declined.md)) |
| **C** — the in-season form blend | this ADR | ❌ **+0.05 SE** |
| **D** — a team-strength term for defenders | ADR-188's dormant weight | ❌ ρ declines monotonically ([ADR-370](./ADR-370-option-d-was-already-built-and-it-declines.md)) |

⭐⭐⭐ **EVERY ONE OF THE FOUR MOVES KONSA THE RIGHT WAY, AND NOT ONE OF THEM MAKES THE BOARD BETTER.** D put
him at 3.90 against an actual 3.84; C puts his form at 8.40; A restored his minutes to 1.00. The complaint
was **correct** — and ADR-320's own opening line was more correct still:

> *"⚠️ So **no fix below makes Konsa a premium defender**, and the honest reply to the owner says so before
> it says anything else."*

⭐ *Four independent, correctly-aimed corrections that each fail the same bar is not four failures — it is a
measurement of how much headroom the model has left*, and ADR-202 put a number on that headroom before any
of this started: **perfect minutes is +5.1 SE, of which only +1.5 SE is information** rather than appearance
-point arithmetic. The remaining gains are not in these terms.

---

### 📊 Consequences

**Good:** ADR-320 is closed on evidence, not on effort or opinion. ADR-060's dormancy is now a **measured**
decision rather than an unexamined default — ⭐ *the reason it was dormant was that nobody had measured what
it did to the board, and that reason no longer exists.* Nothing was built.

**Costs / limits:**
- ⚠️ **8 gameweeks.** `form_rate`'s window is 5, so the form term has had roughly three independent reads.
- ⚠️ **Measured on top of ADR-372**, which shipped hours earlier. The baseline ρ is 0.620, not ADR-367's
  0.617. Correct — C would ship on top of A — but it means this number is not comparable to B's and D's
  without saying so.
- 🔴 **A footgun found in the harness, not fixed here.** `calibrate --range "0.5,1.01,0.1"` printed
  *"Recommended FORM_WEIGHT ≈ 0.500"* — the best value **in the range given**, which excluded the baseline
  and is worse than it. ⭐ *A recommendation is relative to the search, and a tool that does not say so can
  recommend a regression.* Worth a one-line fix; it is a CLI change and gets its own gate.
- **ADR-320's §1 — the rate cannot see he changed clubs — remains the only part never addressed by a shipped
  change.** D was the attempt and it declined.

---

### 🔗 Links

- [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md) — the gate, now closed on all four
- [ADR-060](./ADR-060-per-gameweek-history-and-dormant-form-blend.md) — the dormant term, dormant for a measured reason at last
- [ADR-101](./ADR-101-calibration-methodology.md) — the harness that answered this
- [ADR-369](./ADR-369-the-edge-of-the-grid.md) — the grid-edge lesson, honoured and found not to apply
- [ADR-202](./ADR-202-the-minutes-baseline.md) — the ceiling these four were all pushing against
