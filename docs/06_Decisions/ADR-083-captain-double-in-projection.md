# Architectural Decision Record: Captain double-points in the My Squad projection (next-GW only)

**Decision ID:** ADR-083
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** refines the My Squad quick-stats summary (US-239). A **display** calculation —
the grounded engine (`decision_xp`) is unchanged. Triggered by tester feedback.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester: *"MySquad: when I select a captain, the GW xP does **not account for the captain double points**. …
should captain be adjusted for **next gameweek** or **all selected**? Chips have to be next gameweek only. Is
this feasible?"*

**Verified in code:** `render_my_squad` shows **"Projected XI (N GW)"** = the plain best-XI xP sum with **no
captain doubling**, alongside a *separate* **"Captain (2×)"** metric that doubles the captain's **whole-horizon**
xP. So the headline projection never reflects the ×2 the captain actually scores. The next-GW figure is already
available — `decision_xp` returns each player's **`by_gameweek`** (`{gw → xP}`, ADR-032).

**The design question (the tester's).** A captain scores double in **one** gameweek, and captaincy is
**re-chosen every week**. Doubling a *fixed* captain across all N horizon GWs assumes you never change the
armband and that they're the best captain each week — optimistic and unrealistic.

#### Decision Drivers
- **Reflect the ×2** in the headline projection (the tester's core ask).
- **Be honest about the horizon** — captaincy is a weekly decision; don't imply a fixed captain for N weeks.
- **Consistency with chips** — Triple Captain / Bench Boost are single-GW; the owner steered "next GW only".
- **Display-only** — no change to `decision_xp` or any decision engine.

---

### ✅ Decision

**Apply the captain's double for the NEXT gameweek only** (US-256). In `render_my_squad`:
- **Projected XI (N GW)** = `best-XI xP over N GW` **+ the captain's next-GW xP** (one extra copy = the ×2
  bonus), applied **only when a captain is set and is in the projected XI**.
- A **caption states the ×2 counts for the next gameweek only** whenever a multi-GW horizon is selected (owner
  steer) — e.g. *"Captain X is doubled for the next gameweek only (+5.9 xP); the other 4 GWs count once."*
- The **"Captain (2×)"** metric is reframed to the captain's **next-GW** doubled value (consistent), with a
  matching tooltip. A **benched / unset** captain adds **no** bonus (and the caption says the captain is on the
  bench, when applicable).
- The next-GW xP comes from the existing `by_gameweek` (ADR-032); a small pure helper `captain_bonus(...)` is
  unit-tested. `decision_xp`/the engine are untouched.

**Chips** stay on the **Chips** tab (ADR-082), which is next-GW by nature (TC/BB single-GW). No chip toggle is
added to My Squad this sprint.

---

### 🔀 Alternatives Considered

- **Double the captain across all N selected GWs.** Rejected — assumes a fixed captain for the whole horizon
  (you re-pick weekly; the best captain changes with fixtures). Optimistic; overstates the projection.
- **Leave Projected XI undoubled + keep a separate "Captain (2×)" metric.** Rejected — that's the status quo
  the tester flagged as wrong; the headline should reflect the points the squad actually scores.
- **A chip toggle on My Squad** (TC ×3 / BB all-15). Deferred — the Chips tab already models chip GWs; adding a
  toggle here is scope creep.

---

### 🧭 Consequences

**Positive**
- The headline projection now includes the captaincy points, honestly scoped to the one GW it applies to.
- Reuses `by_gameweek` — no engine change, no new metric; a tiny pure helper is testable.
- Consistent with how chips work (next-GW), matching the owner's steer.

**Negative / risks (mitigations)**
- **A mixed-horizon number** (XI over N GW + captain's next-GW bonus) → an explicit caption spells out that the
  ×2 is a one-week thing, so it can't be misread.
- **Benched captain** → no bonus (FPL would auto-sub to the vice); the caption notes it, keeping it honest.

---

### 📊 Validation

Verified (live DB): `by_gameweek` gives the captain's next-GW xP; for RoboTS with B.Fernandes (C), XI over 5 GW
= 236.6, captain next-GW = 5.9 → **242.5** incl. ×2 next-GW (vs the whole-horizon 263.9 we reject). Acceptance:
`captain_bonus` returns the captain's next-GW xP when the captain is in the XI, and **0** when benched/unset;
the My Squad Projected-XI total = `XI + captain_bonus`; the one-GW caption shows when horizon > 1; the engine +
the existing tests are unchanged (new tests added).
