# Sprint 230: The signals that live between the boards (ADR-170)

**Dates:** 2026-08-29
**Status:** ✅ Complete — ADR-170. 1578 → 1589 tests, ruff clean.

> **Owner:** *"For Trending I'd like an overview like you did for Scout, as it's a fab way of directing
> people's attention to the more notable items."*

---

### 🔧 What shipped

Trending's four boards each rank one number; the useful signals live **between** them. Three patterns, each
needing two boards at once:

- **In form, still under-owned** — the crowd hasn't caught up. *Hinshelwood: form 8.0 on **2.2%** owned.*
- **A bandwagon forming** — *Cherki: **+113,391** transfers, still 11.9% owned.* Early or late?
- **The template breaking up** — empty this week, so the group doesn't appear.

Unlike Scout, every board has **current** data, so this works today rather than at GW10.

**Two rules, both deliberate.** No new thresholds — all four are calibrated constants from `crowd.py`, and a
test asserts the only tunable this module owns is a display cap. And it says what the crowd is **doing**,
never why: that is Signals' half of the doing-vs-saying axis, and a test asserts the copy never contains
*because · injured · rumour*.

---

### 💡 The lesson

> **When a page has three or more leaderboards, the next feature it needs is probably not a fourth.**

Scout and this were the same complaint — *"several correct tables and nobody reads them"* — and the same fix:
not a better table, but a **reader**. Something that looks across them and names the handful of rows worth
attention, with the evidence attached.

The counterweight is what keeps it honest, and it differed each time. Scout says *worth a look, not worth
points*, because two of its signals are unpriced. This says *what the crowd is doing, not why*, because the
cause belongs to another page. **Same discipline: say exactly as much as the evidence carries, and put the
rest where it is sourced.**

### 🧪 Tests

**+11.** Each pattern's two conditions in both directions; one player reports one pattern; every threshold is
an existing constant; a quiet week says so; the note points at Signals and never guesses; reasons speak in the
crowd's units and never mention xP; safe on empty data. Plus the page: the overview leads, four boards remain,
and no causal word appears in the copy.
