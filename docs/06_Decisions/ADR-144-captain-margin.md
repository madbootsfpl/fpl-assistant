# Architectural Decision Record: The captain margin, calibrated against its own distribution

**Decision ID:** ADR-144
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 198, 2026-08-26). **1393 → 1398 tests, ruff clean.**
**Superseded By / Replaces:** Extends the captain explanation (ADR-089) and **removes** its narrow-lead risk
bullet, which now said the same thing twice. No `decision_xp` change, no change to which player is picked.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The Roadmap line: *"captain margin ('by a whisker — 0.3 over #2', a small polish on the existing captain
confidence)."*

The Captain Pick card already listed alternatives with their xP — `🥇 Salah 5.9 · 🥈 Haaland 5.6` — so a
manager *could* do the subtraction. **What they could not do is tell whether 0.3 is a lot.** And the app gave
no help: a gold medal and a confidence of 91/100 read as certainty regardless of how close the call was.

**So the question was measured before anything was designed.** Across **300 random legal squads** on live
data, the gap between the top pick and the runner-up:

| p25 | median | p75 | max |
|---:|---:|---:|---:|
| 0.20 | **0.60** | 1.00 | 2.80 |

| gap under | share of squads |
|---|---:|
| 0.1 | 7% |
| 0.3 | 28% |
| 0.5 | **44%** |
| 1.0 | 71% |

**The captain call is usually close.** A median lead of 0.6 xP on a next-gameweek projection of 5–7 is around
a tenth of the number — and 44% of squads separate their top two by less than half a point. A medal was
implying a confidence the data mostly does not support.

---

### ✅ Decision

**1. State the margin on every card, not only when it is narrow.** `captain_margin(picks)` returns
`{gap, runner_up, verdict}`, and `margin_line` turns it into one sentence, shown above the alternatives on
both the console card and the web card.

**2. The thresholds are the measured quartiles.** `WHISKER = 0.3`, `CLEAR = 1.0` — p25 and p75 of the real
distribution. That is what makes *"a clear pick"* mean something: it is the **top quarter of actual leads**,
not a number that looked round. Any surface calling 1.5 "clear" is now making a statement about this season's
spread rather than about the author's taste.

**3. A whisker says it is a whisker.**

> *"By a whisker — just 0.2 ahead of Haaland. Too close to call; take the one you fancy."*

The closing clause is the point of the feature. A single gameweek's variance dwarfs half a projected point, so
a 0.2 lead is not a recommendation — **it is the model declining to have an opinion**, and it should say so
rather than let a gold medal imply otherwise. Handing the choice back is more useful than a false tiebreak.

**4. The old narrow-lead risk bullet is removed.** `explain_captain` used to append *"Only +0.3 pts ahead of
X"* below a 0.5 threshold. With the margin now stated always and calibrated, that was **the same fact told a
second time, in a second place, against a different threshold** — one rule written twice, which this project
has watched drift before (ADR-137, ADR-142). The gap still feeds `captain_confidence`, which is where it
belongs: a narrow lead should *lower the confidence*, not add a bullet.

**Not in scope:** changing which player is captained. This ADR describes the decision; it does not make it.

### ⚠️ Risks

- **The thresholds are this season's, and thin.** They come from one gameweek's projections; the spread will
  change as form data arrives (GW4-6, ADR-125). Worth re-measuring then — the constants are named and sit
  beside the measurement that produced them, so re-deriving is a five-minute job rather than an excavation.
- **"Take the one you fancy" is unusual advice from a decision tool.** Deliberate. On a 0.2 gap the honest
  answers are a coin-flip or a personal read, and pretending otherwise is how a tool loses trust the first
  time its confident pick blanks.

### 🧪 Definition of Done

1. **Tests: +5.** The thresholds are pinned *as the measured quartiles*, with the distribution in the
   docstring so the numbers explain themselves; a whisker says too-close-to-call; a clear lead reads as one;
   no runner-up yields **no** margin rather than a huge one; a missing projection is not treated as zero
   (`or 0` on an unknown is a mistake this codebase has made before and now tests against by habit).
2. **Manual smoke** — both real squads through the console card, and the web Captain view.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, a sprint retro.
