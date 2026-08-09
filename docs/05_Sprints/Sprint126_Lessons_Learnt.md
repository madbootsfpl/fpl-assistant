# Lessons Learned

**Sprint:** Sprint 126 — A gated set-piece xP term (wired-dormant, calibrate at GW1)

**Dates:** 2026-08-27

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add a principled set-piece term to the one `decision_xp` metric — restricted to the rate tier where it doesn't
double-count, **off by default** (an invariance test pins today's numbers), and **auditable** (a grounded reason
when active). A modelling change (not a lens), gated by an ADR; calibrate at GW1.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Read the model before changing it** — planning found the double-counting trap in `player_xp`, not the tests.
- **Wired-dormant** — ship a modelling change at weight 0, pinned by an invariance test; flip + calibrate later.

### New Skills Acquired

- **The baseline already prices the obvious signal.** A player's historical pp90 *includes* their past pens, so
  a blanket set-piece boost double-counts for established takers. The insight became a clean rule: apply the term
  **only when `rate_source != "hist"`** (new signings / role-changers, where the history doesn't capture the
  duty). A subtle modelling bug turned into a one-line, testable guard.
- **A modelling change ≠ a lens.** ADR-057 ("signals never touch `decision_xp`") governs *display* lenses; an xP
  *term* (like form/xMins) legitimately alters the metric. Recording that distinction kept the architecture
  honest and the lens invariance tests untouched.
- **Zero-risk modelling via a dormant knob.** At `SET_PIECE_WEIGHT = 0` the entire suite is byte-identical — the
  change ships with no effect on current picks, and an invariance test guarantees it. The owner flips the weight
  to see it live; GW1 real returns set the magnitude.
- **Keep a metric change auditable.** The term's share of xp is a real number on the row (`set_piece_xp`), and the
  explanation names it ("Penalty taker (+X xP set-piece edge)") — so turning it on never becomes a black box.
- **Verify the guard on real data.** A weight of 0.5 moved 3 fallback-tier takers and 0 of 17 hist-tier — proof
  the tier restriction does exactly what the design claims.

---

# What Went Well ✅

- **Planning caught the double-counting** before a line of code; the tier guard made it a clean rule.
- **Dormant + invariance** → the 794 stayed byte-identical; a big-sounding change shipped with zero risk.
- **Auditable** — `set_piece_xp` on the row + a grounded reason; the change isn't a black box.
- **The lens/xP boundary stayed crisp** — recorded as a modelling term, not a lens.
- 794 → 804 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A boost would double-count | the baseline already includes past pens | Apply only when `rate_source != "hist"` |
| Is this allowed to touch xP? | ADR-057 keeps lenses out of xP | It's a *modelling* term, not a lens — recorded as such |
| How to ship safely | it changes every recommendation | Wired-dormant (weight 0) + an invariance test; calibrate at GW1 |
| Don't make xP a black box | a change to the sacred metric | `set_piece_xp` on the row + a grounded, weight-aware reason |
| A new row field could break tests | strict-dict assertions | Additive field; ran the full suite (nothing regressed) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Double-counting | The baseline prices established signals; boost only where it doesn't |
| Tier-restricted term | `rate_source != "hist"` is a clean, testable "new info only" guard |
| Wired-dormant | Ship a metric change at weight 0, pinned by invariance; calibrate later |
| Modelling vs lens | An xP term legitimately changes `decision_xp`; a lens must not |
| Auditable xP | Expose the term's share as a number + name it in the explanation |

---

# Development Lessons 💻

- Before changing a shared metric, read how its inputs are already assembled — the obvious signal may be priced in.
- Gate a modelling change behind a default-0 weight with an invariance test; it ships with no blast radius.
- Make any change to a trusted number auditable — a real per-item contribution + a grounded reason.

---

# AI Collaboration Lessons 🤖

- A change to `decision_xp` must stay **grounded**: the set-piece contribution is computed (not invented), lives
  on the row as a fact, and the explanation cites the real number — so a narration referencing it verifies ✓.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-096** — a gated, tier-restricted set-piece xP term. `analytics/setpieces.py::set_piece_bonus` (pens >
corners/FK) added to the `player_xp` rate **only on the fallback/current tiers** (no double-counting), gated by
`config.SET_PIECE_WEIGHT` (default 0, wired-dormant — ADR-060 pattern; invariance-pinned). A **modelling** change
(distinct from the ADR-057 lens rule). `set_piece_xp` on the row + a weight-aware explanation reason make it
auditable (ADR-037/089). Calibrate + backtest at GW1._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **GW1 (2026-08-21+): calibrate + backtest `SET_PIECE_WEIGHT`** on real returns — do boosted picks beat the
  unboosted for role-changers? Set the magnitude; revisit the tier guard against observed takers.
- **Deferred:** per-team penalty-rate/conversion modelling; a mid-season duty-change detector; auto-detecting
  "newly the taker" beyond the rate tier.
- Alongside: the **Data Hardening flip** (form + per-GW history) is the other GW1 calibration.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep reading the model's input assembly before adding a term; keep modelling changes dormant + invariance-pinned.

---

# Key Commands Learned

```text
# set config.SET_PIECE_WEIGHT > 0 to activate; a boosted pick's explanation shows "(+X xP set-piece edge)"
python -m pytest tests/test_setpieces.py -q     # the term: bonus, tier guard, invariance, the grounded reason
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Tier-restricted term | A rate adjustment applied only on non-`hist` tiers (avoids double-counting) |
| Wired-dormant | Shipped at weight 0 — a no-op pinned by an invariance test until turned on |
| Modelling change vs lens | An xP-term (allowed to change `decision_xp`) vs a display lens (must not) |
| `set_piece_xp` | The set-piece term's share of a player's xp — a grounded, auditable number |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/setpieces.py` | The pure `set_piece_bonus` |
| `src/analytics/xp.py` (`player_xp`) | The rate assembly + the tier-guarded term + `set_piece_xp` |
| `src/analytics/explain.py` (`_penalty_reason`) | The weight-aware, grounded reason |
| `docs/06_Decisions/ADR-096-…` | The gate + the double-counting rationale |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- ADR-096 A gated, tier-restricted set-piece xP term (design gate)
- US-313 `set_piece_bonus` + `SET_PIECE_WEIGHT` in `player_xp` (non-`hist` tiers); invariance at 0
- US-314 `set_piece_xp` on the row + a weight-aware, grounded explanation reason

**Stories Carried Forward:**

- The GW1 calibration + backtest (set the weight on real returns).

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
