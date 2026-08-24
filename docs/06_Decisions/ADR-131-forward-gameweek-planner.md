# Architectural Decision Record: A forward planner that leads with what actually varies

**Decision ID:** ADR-131
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved ("build it as described"), built** (Sprint 183). Prototyped on the
live squad, and the prototype changed the feature — see below.
**Superseded By / Replaces:** Extends the per-GW xP toggle (ADR-121) into a multi-gameweek forward view, and
sits beside the Risk Monitor (ADR-130).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The roadmap carries this, from the fplanalyser review:

> **Forward GW planner ("plan not panic")** — per-GW **projected-points-vs-your-average** bars + *"your problem
> week is GW6, 5 weeks out"* narrative + N-hard-fixtures per GW + which players face the hard games.

The Risk Monitor (ADR-130) answers *"who needs attention now?"*. This is the same instinct pointed forward:
*"what's coming, and when should I act?"*

---

### 🔬 What the prototype showed — and why it changes the design

Run against the live squad over the next six gameweeks:

```
  GW   squad xP   hard   blanks
   2       56.8      5        0
   3       55.3      3        0
   4       55.1      7        0
   5       53.5      5        0
   6       57.4      2        0
   7       56.5      2        0

average 55.8 xP/GW · worst is GW5 at 53.5 (−2.3 vs your average)
```

**The xP line is nearly flat, and that is structural, not a data problem.** The fixture multiplier is ±20% at
its extremes (ADR-006), and averaging fifteen players smooths most of that away. The whole six-week range is
3.9 xP on an average of 55.8 — **±3%**. Presenting *"your problem week is GW5, −2.3"* would dress up noise as
a finding, which is the failure this project has spent the week removing everywhere else.

**What does vary is fixture exposure**: the number of your players facing a hard match swings **2 → 7** across
the same six weeks. That is a real, actionable signal, and it is the one the eye should be drawn to.

**And blanks and doubles are the real headline — when they exist.** They are what make a week genuinely
different, because a blanked player scores nothing at all rather than 20% less. Checked against the stored
fixtures: **all 37 upcoming gameweeks currently have exactly 10 fixtures.** FPL publishes a complete schedule
and blanks/doubles only appear later, when cup rounds displace fixtures. So there are none to plan around yet —
which the feature must be able to say, rather than inventing drama.

---

### ✅ Proposed Decision

**Build it, but lead with what varies, and let it say when nothing does.**

**1. The bars are fixture exposure, not xP.** Per gameweek, over a configurable horizon: how many of your
players face a **hard** fixture (difficulty ≥ 4), how many **blank**, how many have a **double**. These move
enough to be worth looking at.

**2. Projected xP is a secondary line, honestly scaled.** Shown per gameweek with the squad's own average as
the reference, and — crucially — **labelled with its range**. A ±3% spread reads as flat, because it is flat.

**3. A "problem week" is only named when one exists.** A gameweek is called out when it is *materially*
different — it contains a blank for one of your players, or a double, or its hard-fixture count is a clear
outlier against the rest of the window. Otherwise the planner says so plainly: *"No standout week in the next
six — your fixtures are even."* **That is a useful answer**, and manufacturing a worst-of-six from noise is
not.

**4. Name the players, not just the count.** For each flagged week, who blanks and who faces the hard games —
the count says there is a problem, the names say what to do about it.

**Reuse only.** `decision_xp`'s `by_gameweek` (ADR-032), `team_schedule` and the FDR difficulties, and the
same blank/double handling that ADR-129's audit confirmed correct. A new pure `analytics/forward_plan.py`; no
new analytics, no `decision_xp` change.

---

### 🔀 Alternatives Considered

- **Lead with the xP bars, as the roadmap line describes.** Rejected on the evidence above: a ±3% spread
  presented as a "problem week" is noise wearing a headline. The roadmap entry was written from a competitor's
  screenshot, not from our numbers; the prototype is what tells us which of the two signals is real.
- **Widen the xP spread by sharpening the fixture multiplier.** Rejected firmly — that changes `decision_xp`,
  the one metric the whole app agrees through (ADR-041), to make a chart look better. Exactly backwards.
- **Wait until blanks and doubles exist.** Tempting, since the headline case is absent today. Rejected: the
  hard-fixture signal is live now, and the structure needs to be in place *before* the first blank rather than
  written in a hurry during it — the same argument that made ADR-129 worth doing early.
- **Extend the existing per-GW toggle instead of a new view.** Rejected: the toggle switches which single
  gameweek the squad page displays; this is a comparison *across* gameweeks, which is a different shape.

---

### 🧭 Consequences

**Positive** — answers "when should I act?" with the signal that actually varies; honest when nothing stands
out, which is itself worth knowing; the blank/double machinery is ready before the first one arrives; pure
reuse, so no new metric to keep calibrated.

**Negative / risks (mitigations)** — the headline case (blanks/doubles) will not appear for months, so early
on the view is mostly the hard-fixture profile (*mitigation:* that profile is real and does vary 2→7; the
copy sets the expectation rather than overselling); a horizon deep into the season leans on fixture difficulty
that FPL revises (*mitigation:* difficulty is FPL's own and refreshes with the data; the view is a lens, not a
projection); "materially different" needs a threshold, and thresholds drift (*mitigation:* blanks and doubles
are structural rather than threshold-based, and the fixture-count outlier test is stated in the code with its
reasoning).

---

### 🧾 Status & follow-ups

- **Accepted and built (Sprint 183).** `analytics/forward_plan.py` (pure) + a **📅 The weeks ahead** card in
  My Squad ▸ Health, beneath the Risk Monitor. 12 new tests. 1224 → **1236**, ruff clean.
- **It picks the right week on the live data, which is the whole test of the design.** The headline names
  **GW4 — 7 players face a hard fixture**, not GW5, which is merely the xP minimum (53.5 against a 55.8
  average). The footnote states the range and adds *"barely moves across these weeks, which is normal"*, so a
  ±3% wobble cannot be read as a forecast.
- **Not this ADR:** acting on it — a transfer targeted at a flagged week is the **multi-GW transfer path
  planner**, its own roadmap item and a much bigger build.
- **Not this ADR:** acting on it — a transfer suggestion targeted at a flagged week is the **multi-GW transfer
  path planner**, which is its own roadmap item and a much bigger build.
