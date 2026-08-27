# Architectural Decision Record: A reported departure is a dead slot we know about first

**Decision ID:** ADR-153
**Date:** 2026-08-27
**Status:** ✅ **Accepted — built** (Sprint 208, 2026-08-27). **1456 → 1460 tests, ruff clean.**
**Superseded By / Replaces:** Connects ADR-151's headline events to ADR-136's dead-slot machinery, and fixes
a flag in ADR-146 that asserted ignorance after the cause was available. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on Cloud, minutes after the headline events shipped:

> Correct, Watkins is flagged as expected — however it points to another issue. I have Watkins in my team, we
> have the data that he is to be sold or in process of. However **AI Tips doesn't know that**. It's suggesting
> to start him. Should be recommending a transfer for him.

**Two faults, and the second is the real one.**

**1. The flag asserted ignorance it no longer had.** `gameweek_plan` built its exodus reason as a hardcoded
string — *"167,825 sold him this week — nothing in the data says why"* — while the Romano headline sat in the
same database, already being read by the Risk Monitor and Signals. **The one place the cause was available and
unused.**

**2. Knowing he is leaving changed nothing about the advice.** The plan flagged him, then recommended
**starting** him and transferring out somebody else. FPL still reports `status = 'a'`, so `decision_xp` still
credits Watkins a full horizon of points he will not be here to score.

---

### 🔬 The measurement that decided the design

The obvious approach — ask the model whether a transfer is *out of* the league — means asking it for one more
thing it can get wrong. The data offered a free answer instead. Of the five transfer headlines in the live
seed, exactly one carried a heavy unexplained sell-off:

| player | headline | exodus |
|---|---|---|
| **Watkins** → Al-Hilal | ✓ | **−167,825** |
| Pinnock → Coventry | ✓ | none |
| Disasi → Crystal Palace | ✓ | none |
| Baleba → Man Utd | ✓ | none |
| Hadjam → Brighton | ✓ | none |

The four without one are moves **within or into** the league — the player stays perfectly playable, and the
crowd knows it, which is precisely why nobody is selling. **The exodus is what separates "leaving the football
we can see" from "changed shirts",** and it costs nothing to read.

---

### ✅ Decision

**1. Two independent signals must agree.** `reported_leaving(events, exodus)` requires a transfer headline
**and** a heavy sell-off our own data cannot explain. Neither alone is enough. Conservative on purpose: being
wrong costs a real transfer.

**2. It reaches the advice through ADR-136, not a new path.** A confirmed departure *is* a dead slot — FPL's
`status` simply lags the news by days. So `dead_slots` gains `reported_out`, and the existing `replace_dead`
machinery produces the recommendation, which already flows to `ask`, the CLI and the web. No new surface.

**3. FPL's own status still wins.** The report is a fallback for when the feed is silent, never a replacement
for what it tells us — the same ordering ADR-146 applies to the crowd signal. If FPL says injured, we say
injured.

**4. A reported leaver is measured against zero, not his paper xP.** This is the subtle one. His projected xP
is **fiction**: FPL calls him available, so the recipe credits a full horizon. Comparing a replacement against
that produced *"recovers **−8.6** xP"* on the live squad — a negative recovery, which is not a sentence about
anything. The baseline is now 0, exactly as it already is for a player FPL has marked `u`.

**`decision_xp` is untouched.** Only this slot's arithmetic uses the number that will actually happen — which
is the same thing ADR-136 has always done, reached by a different route.

**5. The wording distinguishes a report from a fact.** *"Watkins is reported to be leaving — per Romano"*, not
*"can't play"*. Naming the source is what lets a reader weigh it and disagree.

### ⚠️ Risks and a known limitation

- **A wrong call costs a transfer.** Hence two signals, and hence the wording being explicitly a report.
- **⚠️ The lineup still starts him.** `best_legal_xi` ranks on `decision_xp`, which still rates Watkins 4.3.
  We recommend replacing him *and* would start him until you do — which is coherent (he is in the squad until
  transferred) but reads oddly. **Zeroing his xP for lineup purposes would be a decision made from a
  headline**, and that is a bigger step than this ADR should take unilaterally. Recorded for the owner rather
  than quietly taken.
- **A gossip headline counts the same as a confirmed one.** *"Al-Hilal closing in"* and *"here we go"* both
  read as `transfer`. The exodus requirement carries most of the weight here; a confidence tier is a possible
  refinement if this ever misfires.

### 🧪 Definition of Done

1. **Tests: +4.** Two signals must agree (with the five-headline table in the docstring); a reported departure
   is a dead slot before FPL says so; FPL's own status still wins; and a reported leaver is measured against
   zero so a recovery can never read as negative.
2. **Manual smoke** — the owner's exact question, end to end.
3. **Docs** — this ADR, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**A signal is only worth what the surfaces do with it.** ADR-151 extracted the Watkins story correctly, stored
it correctly, and displayed it correctly — and the app went on recommending he start. The extraction was
finished; the *feature* was not, because nothing downstream had been taught to act on it.

Worth generalising: **when you add a new fact to the system, list every decision that would change if it were
true.** Here that was two — the flag's wording and the transfer advice — and only the first was obvious,
because it was the one already displaying the fact.
