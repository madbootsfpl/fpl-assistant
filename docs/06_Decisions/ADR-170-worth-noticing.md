# Architectural Decision Record: The signals that live between the boards

**Decision ID:** ADR-170
**Date:** 2026-08-29
**Status:** ✅ **Accepted — owner's idea, built** (Sprint 230, 2026-08-29). **1578 → 1589 tests, ruff clean.**
**Superseded By / Replaces:** Applies ADR-167's shape to Trending. Holds ADR-149/150's doing-vs-saying axis.
**No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> *"For Trending I'd like an overview like you did for Scout in Players, as it's a fab way of directing
> people's attention to the more notable items."*

Trending's four boards — most owned · most transferred in · most transferred out · in form — each rank **one
number**. The useful signals live *between* them: **a player can top none of the four and still be the most
interesting name on the page**.

Unlike Scout, all four boards have **current** data (297 players with form, all 616 with transfer activity),
so this works today rather than at GW10.

---

### ✅ Decision

**Three patterns, each a different action, each needing two boards at once:**

| pattern | rule | what it tells you |
|---|---|---|
| **In form, still under-owned** | `form ≥ FORM_MIN` ∧ `own ≤ DIFFERENTIAL_OWN` | the crowd has not caught up — a differential **with evidence** |
| **A bandwagon forming** | `net ≥ TRENDING_NET` ∧ `own < TEMPLATE_OWN` | whether you are early or late |
| **The template breaking up** | `net ≤ −TRENDING_NET` ∧ `own ≥ TEMPLATE_OWN` | what "safe" now means |

Ordered most-actionable first, and that order is fixed rather than scored: comparing "form" with "transfers"
would need a scale they do not share.

**1. Every threshold already existed.** All four are calibrated constants from `crowd.py`. Inventing a fourth
cut-off to produce a nicer shortlist would be **a number with no population behind it** — the failure this
project has named repeatedly. The only tunable this module owns is a display cap (`per_pattern=4`), and a test
asserts that.

**2. It says what the crowd is DOING, never why.** Trending and Signals are split on exactly that axis
(ADR-149/150). If a sell-off has a headline behind it, Signals' exodus banner owns it; repeating it here would
**put an unsourced guess beside a measured fact** and collapse the distinction the two pages exist on. A test
asserts the copy never contains *because · injured · rumour*.

**3. One player, one pattern.** The shortlist answers *"what should I notice?"* — a name appearing three times
with three framings is a worse answer than appearing once.

**4. An empty group disappears, and an empty week says so.** *"Nothing unusual in the crowd numbers this
gameweek… a quiet week is a finding, not a gap."*

**Live output today:** Hinshelwood (form 8.0 on **2.2%** owned) leading three more under-owned in-form
players, and Cherki at **+113,391 transfers** on 11.9% owned. *The template breaking up* is empty — nobody
widely owned is being dumped at 50k+ net.

### 🧪 Definition of Done

1. **Tests: +11.** Each pattern's two conditions, in both directions (in form but already owned → nothing;
   heavily bought but already template → nothing; sold heavily but nobody owned him → nothing); one player
   reports one pattern; every threshold is an existing constant; a quiet week says so; the note points at
   Signals and never guesses; reasons speak in the crowd's units and never mention xP; safe on empty data.
   Plus the page: the overview leads, all four boards remain, and the copy contains no causal word.
2. **Manual smoke** — a preview from the live pool, sent as a file.
3. **Docs** — this ADR, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**The same shape worked twice, and the reason it did is worth naming.** Scout and this are both *"we have
several correct tables and no one reads them"* — and in both cases the fix was not a better table but a
**reader**: something that looks across them and says which handful of rows deserve attention, with the
evidence attached and no claim beyond what the data supports.

That is now a pattern this codebase has, not a one-off: **when a page has three or more leaderboards, the
next feature it needs is probably not a fourth.**

The counterweight kept it honest here as it did there. Scout's constraint was *worth a look, not worth
points*, because two of its signals are unpriced. This one's is *what the crowd is doing, not why*, because
the cause belongs to a different page. **Both are the same discipline: say exactly as much as the evidence
carries, and put the rest where it is sourced.**
