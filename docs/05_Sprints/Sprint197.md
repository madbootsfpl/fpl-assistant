# Sprint 197: One chip per gameweek (ADR-143)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-143. 1387 → 1393 tests, ruff clean. The Roadmap's sequence *ranking* is declined
on evidence; the legality defect it would have incidentally fixed is built.

---

### 🔍 Two questions, opposite answers

The Roadmap asked to *"rank every valid chip sequence by projected xPts"*. Two things had to hold: sequencing
must **change the answer**, and the change must be **worth something**. Measured across **200 random legal
squads** on live data over 8 gameweeks:

| question | answer |
|---|---|
| Do two chips ever want the same gameweek? | **Yes — 28% of squads** |
| What is resolving it optimally worth? | **0.3 xP median, 1.5 xP worst case** |

**The ranking is declined.** It would change the answer 28% of the time and be worth a third of a point — the
same order as ADR-131's ±3% per-GW noise. That is a precise-looking ordering on numbers that cannot carry one.

Third time a sequence/tree feature has died to a measurement here (ADR-132's transfer path, ADR-131's problem
week, now this), and the reason has been identical each time: **our projections are smooth, and smooth
projections make optimal ordering worthless.** Worth saying out loud, because it is starting to look like a
property of the domain rather than three coincidences.

### 🐛 But the collision is a real defect, and it isn't about points

```
  Triple Captain: GW3 — Watkins (AVL), xP 5.3
  Bench Boost:    GW3 — all 15 project 22.2 xP     ← two chips, one gameweek
```

**FPL forbids it, and the app's own rules base says so** — *"You can play only one chip per gameweek"*
(`fpl_rules`). So `ask` would tell a user chips cannot be stacked while the chip advisor advised stacking
them. **A 28% chance of contradicting your own knowledge base is worth fixing at any point value.**

---

### 🔧 What shipped — and the mistake in the middle of it

Chips are now assigned distinct gameweeks inside `chip_advisor`, so every caller inherits legal advice. The
moved chip says where it came from and what it cost.

**Which chip moves took two attempts, and the first was wrong in an instructive way.** The obvious rule —
*move the chip with the smaller raw margin* — compares margins across chips one paragraph after arguing they
are different currencies. Triple Captain's margin is one player's ceiling; Bench Boost's is a whole-squad
total. **Bench Boost always has the biggest numbers — and its total includes the very spike that made Triple
Captain want that week.** On a crafted squad TC's margin read 24.1 and BB's 29.4 *off the same player*, and
the raw rule moved Triple Captain: exactly backwards.

Fixed with a **relative** gap — the share of its own value a chip gives up by moving. *"Gives up 80% of what
it came for"* means the same thing for all three chips; *"gives up 24.1"* does not.

Re-measured after the fix: **0 of 200 squads illegal**, 57 chips relocated, median cost **0.00 xP**.

---

### 💡 The lesson

> **I made the same category error twice in one function, an hour apart.**

The ADR argues at length that chip values are in incomparable units — so summing them is meaningless — and
then the first implementation *compared* them, which has exactly the same flaw. Writing down why you cannot
add two numbers does not stop you from subtracting them.

The fix is the same either way: **make the quantities dimensionless before they meet.** A share of each
chip's own scale can be compared with any other chip's share; a raw margin cannot be compared with anything.

Smaller one worth keeping: **the feature that got declined and the feature that got built came out of the same
measurement.** Had the 28% number not been checked, the ranking would have been built on top of a defect it
would have hidden — legal advice arrived at for the wrong reason, with no test pinning legality.

### 🧪 Tests

**+6.** No two chips share a gameweek; the least-at-stake chip moves; **the share-not-raw rule pinned with the
exact 24.1-vs-29.4 case that broke the first version**, so nobody re-simplifies it; a moved chip reports where
from and what it cost; an unaffected squad gets no extra noise (~72% of squads); fewer gameweeks than chips
degrades without inventing a week.
