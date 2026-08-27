# Architectural Decision Record: The price journey — the change now, the line later

**Decision ID:** ADR-160
**Date:** 2026-08-27
**Status:** ✅ **Accepted — owner-gated, built** (Sprint 215, 2026-08-27). **1515 → 1525 tests, ruff clean.**
**Superseded By / Replaces:** Delivers the backlog's long-open *"per-season price sparkline"*, unblocked by
ADR-128's `value` column. Complements ADR-092 (which predicts) and ADR-140 (the shared glyph pair).
**No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The app could say where a price is *going* (ADR-092's ▲/▼ pressure flag) and that one moved *this gameweek*
(the crowd's 💰↑/💸↓). It could not say where a price had **been**.

Measured before designing, as with ADR-159 — and this time the data was there, barely:

```
distinct rounds with a `value`      : [1]
players whose price moved since GW0 : 10 of 616
players with a 2-point price series : 9
```

**A discrepancy found while checking units decided the shape of it.** `value` is written when a gameweek is
played; prices move *nightly*. So Watkins reads **£8.0m** in his GW1 row and **£7.9m** on every other surface
in the app. A sparkline built from `value` alone would have ended on the stale figure — a chart visibly
disagreeing with the number printed beside it.

---

### ✅ Decision

**1. `price_series` appends today's live price as the final point.** That is what makes the line agree with the
rest of the app, and — at one played gameweek — it is also the only reason a series exists at all.

**2. An unchanged price yields one point, not a flat pair.** Appending an identical "now" would draw a
dead-level segment implying two observations of the same thing.

**3. `price_move` reads `cost_change_start` straight off FPL.** Exact, and available from day one. **The change
carries this feature now; the line carries it later** — showing only a sparkline would have shipped a blank
strip to 607 of 616 players.

**4. An unmoved price says "unchanged since the season started".** *Nothing has happened* is a real answer to
*what has his price done*, and it is the answer for almost everyone this early.

**5. A double gameweek cannot add a price to itself.** `agg="last"`, the rule ADR-129 wrote **for this exact
column** while building something else. Summing two fixtures in one round would read as a £4.5m rise. Tested.

**6. No new card.** It sits beside the form windows on the trend card, answering the neighbouring question:
not *how is he playing* but *what has the market done about it*. The glyphs are ADR-140's shared pair — plain
triangles so each surface can colour them, green up and red down.

### 🧪 Definition of Done

1. **Tests: +10.** The move read off FPL, and `None` when the field is absent; today's price as the last point
   (the Watkins case, by name); an unmoved price yielding one point; the double-gameweek rule; a player with no
   gameweek rows still reporting his price. Plus the view: the move named with a line when there is one, both
   glyph/colour directions, the unchanged case drawing no line and no arrow, no price → no strip, and the trend
   panel byte-identical without it.
2. **Manual smoke** — a preview from the app's own card, three real players on live data (a faller, a riser,
   the unchanged majority).
3. **Docs** — this ADR, the roadmap item closed, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**Two sources for one fact is usually a smell; here it was the requirement.** `cost_change_start` and the
per-gameweek `value` series measure the same thing at different resolutions and different freshnesses, and
neither alone gives a usable feature: the series is one point long and stale, the scalar has no shape. Using
both — and being explicit about which carries the feature *now* versus *later* — is what made this shippable
at GW1 instead of a placeholder waiting for GW6.

The narrower lesson is worth keeping too: **a chart is a claim about the same numbers the page prints, and it
has to survive being read next to them.** The £8.0m/£7.9m gap existed in the data all along and would not have
shown up in any test — only in a reader noticing that the picture and the label disagreed.
