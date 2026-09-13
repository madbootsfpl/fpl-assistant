# Sprint 247: Price the rebuild (ADR-185)

**Dates:** 2026-09-13
**Status:** ✅ Complete — ADR-185. **1742 → 1746 tests, ruff clean.**
✅ **Owner-verified in the app the same day: *"chips tab does say wildcard"*.**
First of the three gaps from the owner's two-team A/B (ADR-185/186/187).

---

### 🔧 What shipped

`rebuild_value(owned, market, xp, budget=…)` — one solve, ~0.08s — answers *what is a wildcard worth*, and
the advisor now leads with it.

Before, on the owner's squad:

```
Wildcard: GW5–GW7 — your weakest stretch (avg XI 48.8 xP); reset before it · Confidence 42/100 · Low
```

After:

```
Wildcard: worth +99.6 xP — a fresh build beats your squad over this window;
          you keep only 3 of 15; £14.1m of your squad cannot play.
          Your weakest stretch GW5–GW7 (avg XI 48.8 xP) — reset before it · Confidence 95/100 · High
```

**42 → 95**, on a squad that needed rebuilding weeks ago.

The confidence changed because it was measuring the wrong thing. `margin` is *how clearly one window beats
another* — genuinely low when the weeks are close, which they usually are. The decision is not *which week*,
it is *is a rebuild worth it*. **Two different questions were sharing one number.**

The fixture window survives, demoted: it answers a real question, just not the first one.

---

### 💡 The lesson

> **A recommendation that measures only *when* will present itself as an answer to *whether*.**

`chips.py` was never wrong about fixtures. It answered a smaller question than the one on the card, and
nothing in its output said so — the reader supplies the missing half without noticing. The owner did, for
four gameweeks, while 99.6 xP sat on the table.

**And the number is labelled, deliberately.** The rebuild is unconstrained by transfers, which is exactly
right for a chip that lifts that constraint and an overstatement of anything else. Called *"what a wildcard
is worth"* it is precise; called *"how bad your squad is"* it would mislead, because most squads cannot reach
it by any other route.

---

### 🔬 Two guards tested components and not the wiring

Both survived their first mutation, for the same reason:

- The confidence test called **`rebuild_confidence` directly**, so the branch in `explain_chips` that
  *selects* it was never executed. Disabling that branch passed.
- The renderer test passed **`idle_spend` as a literal** in a hand-built dict, so `rebuild_value` never
  computed it. Hard-coding it to `0.0` passed.

> ⭐ **Testing a component is not testing that anything uses it.**

Same shape as ADR-181's *"a test that rebuilds the thing under test is testing the test"*, one level out:
there the substitute was a re-implementation, here a hand-supplied input. Both leave the production path
unexecuted while reading like coverage.

Repaired by driving `explain_chips` end to end — with **near-flat weeks**, so the old fixture margin would
read Low if it were still in charge — and by computing `idle_spend` from data with two deliberately dead
forwards. **Six mutations, all caught**, including a no-op control to prove the harness was live.

---

### 🧪 Tests

**+4.** The wildcard reports what a rebuild is worth · it reads exactly as before without one (the
compatibility contract) · confidence measures the gap, not the fixture margin, **through `explain_chips`** ·
the gain is labelled as the chip's value and the window survives.
