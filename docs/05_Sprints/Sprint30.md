# Sprint 030: Analyser Enhancements — per-gameweek xP + sort by xP

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~3 working sessions (an analytics extension + wiring)
**Carried Over:** None (Sprint 029 closed clean)

> **Sequence change (owner's call this planning):** the owner's Sprint 29 retro asked for these two
> analyser features, and **Data Hardening's form-blending is blocked until GW1** (2026-08-21, ~2.5
> weeks out — still preseason, 0 GWs). So 030 builds what's *ready and wanted*; **Data Hardening
> moves to a later sprint (at/after GW1)** when per-GW history + form can be built and tested.

---

### 🔎 Verified at planning (the standing lesson — proved the maths first)

Two things checked live before designing:

- **Per-GW xP decomposes the horizon total exactly.** Splitting each player's horizon xP into its
  gameweeks and summing gives back the total: Haaland `{GW1 6.8, GW2 6.8, GW3 7.5, GW4 6.1,
  GW5 7.5}` → **34.7 = `player_xp` total 34.7**; B.Fernandes 34.2; Gabriel 27.8 — all match. A
  **DGW** (two fixtures in a GW) naturally sums to a higher GW value; a **BGW** (no fixture) is 0.
  So per-GW is a faithful breakdown, not a new number.
- **`--sort xp` is trivial** — `analyse_squad` already computes the XI; sorting it by xP instead of
  position is a display option. (The bench is already xP-sorted.)

**Also:** **ClubElo recovered (2026-08-04)** after the 2026-08-03 outage — `refresh` pulls 20 Elo
ratings again and `fdr --type elo` works; the retry-then-degrade design held throughout. No open
issues.

**What this means:** both are small, safe extensions of the xP we already have — the per-GW
breakdown is a reusable analytics addition (usable in `analyse` *and* the `xp` command, closing the
long-standing "xp per-GW" backlog item). FPL-native; no new dependency, no schema change.

---

### 🧭 What's new — xP you can see *week by week*, and rank by

xP has always been a single horizon total. This sprint makes it **legible**: the same total, broken
into its gameweeks, so a manager sees *when* the points land (an easy GW1 vs a tough GW3) — and can
**sort the analyser's XI by xP** to see their strongest and weakest at a glance. Both come from one
reusable per-GW analytics extension; the xP formula (ADR-006/007) is unchanged.

---

### 🎯 Sprint Goal

**Objective:** Extend xP with a **per-gameweek breakdown** (decomposing the horizon total, DGW/BGW
handled) and surface it in `analyse` (and the `xp` command); add **`--sort xp`** to `analyse`.

#### Success Criteria
- [ ] Approach agreed (**ADR-032**) before code — per-GW breakdown decomposes the total; display; sort
- [ ] A reusable per-GW xP capability (analytics) — each player's xP per GW over the horizon; sums to
      the total; DGW = summed, BGW = 0
- [ ] `analyse --squad <name>` shows per-GW xP for the XI (and total), with **`--sort xp`** (else position)
- [ ] The `xp` command gains a per-GW view (closes the "xp per-GW breakdown" backlog item)
- [ ] Sensible display for the horizon width (columns don't overflow; a cap or compact form if needed)
- [ ] Existing xP totals unchanged (the breakdown is additive — existing tests stay green)
- [ ] Tests (per-GW sums to total, DGW/BGW, sort) + **live smoke** on a real squad
- [ ] Docs: ADR-032 + index, Architecture changelog, Handbook, PROJECT_STATUS; Backlog item closed

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-089 | **Gate.** Per-GW xP design (**ADR-032**): a per-gameweek breakdown that decomposes the horizon total (DGW summed, BGW 0); the display (GW columns + total; width handling); `--sort xp` for `analyse`. Pressure-tested (sums match) | Critical | ✅ Done | 0.5 session |
| US-090 | **Per-GW xP analytics** — a reusable capability returning each player's xP per GW over the horizon (sums to the existing total). Unit-tested (sum, DGW, BGW) | High | ✅ Done | 1 session |
| US-091 | **Wire it in** — `analyse` per-GW view + `--sort xp`; the `xp` command's per-GW view. A view that handles the horizon width. Tests + smoke | High | ✅ Done | 1.5 sessions |

#### Technical Tasks & Maintenance
- [x] ADR-032 recorded + added to the ADR index — _US-089_
- [x] Update Architecture changelog (per-GW xP) — _US-090_
- [x] Update Handbook (Ch 21 — making a metric legible: decompose without changing it) — _US-091_
- [x] Backlog: "xp per-gameweek breakdown" **done**; Data Hardening noted as a post-GW1 sprint — _US-091_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — per-GW sums to the total, DGW/BGW, the sort; existing 271 stay green
   (the breakdown must not change existing xP totals).
2. **Manual smoke test done** — `analyse --squad TS` shows per-GW xP + `--sort xp`; `xp` per-GW reads
   right; the columns don't overflow.
3. **Documentation updated & checked** — ADR-032 + index, Architecture, Handbook, sprint board +
   PROJECT_STATUS; the Backlog item closed (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Per-GW xP breakdown (a faithful decomposition) | Changing the xP formula/total (it's additive only) |
| `analyse` per-GW view + `--sort xp` | Historical per-GW *actuals* (needs GW1 — Data Hardening) |
| The `xp` command's per-GW view | In-season form blending (Data Hardening, at GW1) |
| Compact display for the horizon width | xMins-weighted per-GW (later) |

**External Dependencies:** None beyond stored FPL data.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Per-GW breakdown ≠ the existing total | High | Proven: per-GW sums to the total; a test asserts it; existing totals unchanged |
| Wide tables overflow (large horizon) | Med | GW columns are narrow; cap the per-GW display (e.g. drop a column or note) for big N |
| DGW/BGW mis-handled | Med | A GW's xP = sum of its fixtures (2 for DGW, 0 for BGW) — the natural grouping; unit-tested |
| Confusing "projected per-GW" with "actual" | Low | Label it projected; historical per-GW actuals are Data Hardening (needs GW1) |

---

### 🗝️ Gating decision (US-089 → ADR-032)

Settle before code — pressure-test the maths (done). Proposed (confirm/redirect at "start US-089"):

1. **A faithful decomposition.** Per-GW xP = the player's rate × the sum of fixture multipliers *in
   that gameweek*; summed over the horizon it equals the existing total (proven). Not a new metric —
   the same xP, shown per GW. DGW = the GW's fixtures summed; BGW = 0.
2. **Reusable analytics.** One capability (extend `player_xp` or a sibling fn) that both `analyse`
   and `xp` consume — closing the "xp per-GW breakdown" backlog item in the same stroke.
3. **Display.** GW columns (`GW1 … GWN`) + a total, in `analyse`'s XI/bench and the `xp` table.
   Keep it readable — narrow GW columns; for a large horizon, a compact form or a soft cap.
4. **`--sort xp`.** `analyse` sorts the XI by xP when asked (default stays position, or make xp the
   default — decide at the gate).

**Worked example to verify at the gate:** show Haaland's `{GW1 6.8 … GW5 7.5}` summing to 34.7 in
the real `analyse` output, and `--sort xp` ordering the XI by total.

---

### 📝 Session Progress Log

- **US-089 (gate) ✅** — Recorded **ADR-032**: per-GW xP is a **faithful decomposition** (rate ×
  sum of that GW's fixture multipliers; DGW summed, BGW 0) that sums to the **unchanged** total —
  proven live (Haaland {6.8,6.8,7.5,6.1,7.5}=34.7=`player_xp` total). Additive analytics
  (`by_gameweek` on the result; existing totals untouched); GW columns + total in `analyse`/`xp`;
  per-GW rounded for display, the total authoritative. **Two defaults chosen (flagged for redirect):**
  `--sort xp` is opt-in (default stays `position`); large-horizon width handled by narrow columns
  (soft cap noted, not built). ClubElo confirmed recovered at planning.
- **US-090 (per-GW xP analytics) ✅** — `player_xp` now groups fixtures by GW
  (`_difficulties_by_team_gw`) and returns `by_gameweek` + `gameweeks` alongside the total. The total
  is the sum of the **unrounded** per-GW values → **byte-for-byte unchanged** (all existing xP/analyse/
  captain/transfer tests green). **4 new tests** (sums-to-total, DGW summed, BGW = 0, unavailable
  all-zero) → suite **271 → 275**; ruff clean. Live check: Haaland `{1:6.8,2:6.8,3:7.5,4:6.1,5:7.5}` =
  34.7 = total.
- **US-091 (wire it in) ✅** — `analyse` gained per-GW columns (dynamic `GW1…GWN` + total via the
  shared renderer) and **`--sort xp`** (default stays `position`); `analyse_squad` carries the per-GW
  data + sort. The `xp` command gained **`--by-gameweek`** (a per-GW layout; the default view
  untouched) — closing the Sprint-006 backlog item. **4 tests** (sort-xp, per-GW passthrough, 2
  parser) → suite **275 → 279**; ruff clean. Live smoke: `analyse --squad TS --sort xp` (XI by xP +
  GW cols) and `xp --by-gameweek` both correct. Known display note: per-GW rounded cells can read
  ±0.1 vs the authoritative total (footnoted, ADR-032).

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-089 (ADR-032), US-090 (per-GW xP analytics), US-091 (wire
  into `analyse` + `xp`). The owner's Sprint-29 retro asks are live: **`analyse` shows xP per
  gameweek** and **`--sort xp`**; the `xp` command gained **`--by-gameweek`**, closing the Sprint-006
  "xp per-GW breakdown" backlog item in the same stroke. Tests 271 → **279**; one ADR; **no schema
  change, no new dependency, and the xP total is byte-for-byte unchanged**.
* **Carried Forward:** None. Data Hardening is scheduled as a post-GW1 sprint (Backlog).
* **Key Artifacts / Decisions:** ADR-032 (a faithful decomposition; additive; total authoritative;
  `--sort xp` opt-in); `_difficulties_by_team_gw` + `by_gameweek` on `player_xp`; dynamic GW columns
  in `analyse`/`xp`.

#### Retrospective
* **What Went Well?**
  - **Built exactly what the owner asked for**, from his own retro note — and it also closed a
    four-year-old (Sprint 006) backlog item, because one additive analytics change served both
    `analyse` and `xp`.
  - **Additive, not invasive.** The breakdown is extra keys (`by_gameweek`) on the result; existing
    consumers ignore them and **every existing xP test stayed green** — the proof the total didn't move.
  - **Proved the maths before code.** The planning probe showed per-GW sums to the total exactly, so
    the build was low-risk; a test now asserts it.
  - **Reacted to real conditions at planning** — ClubElo had recovered (housekeeping done) and the
    season hadn't started, so we reordered to build what's *ready and wanted* over what's blocked.
  - DoD held (30th sprint): tests + live smoke + docs.
* **What Could Be Improved?**
  - **The rounding artifact** — per-GW cells are rounded, so a row can read ±0.1 off its total. We
    footnote it (the total is authoritative); honest, but a sharp-eyed user will notice. The
    alternative (fudging the total) was worse.
  - **Wide tables at large horizons** — narrow GW columns cope with the default (5); a soft cap /
    compact form for big N is noted, not built.
* **Lessons Learned?**
  - Decompose a metric to make it legible — but keep it a *faithful* decomposition (sums to the
    same total), added as extra data, not a rewrite.
  - Round for display, keep the total authoritative, and footnote the artifact rather than fake a sum.
  - Plan against live conditions: reordering the sequence for what's buildable (and wanted) beat
    forcing a blocked sprint.
* **Action Items for Next Sprint:**
  - [ ] **Data Hardening** — schedule for ~GW1 (2026-08-21): full 567-player backfill + per-GW
        `history` + in-season xP form blending (the last two need the season started). Check the live
        gameweek state at planning.
  - [ ] Then xMins can retire bench-blindness in captaincy/transfers.
  - [ ] Keep gate + 3-part DoD.

---

**Proposed follow-on:** Data Hardening at/after GW1 (per-GW actuals + form blending become buildable),
with the full history backfill. Owner to steer timing.

**Completion Date:** 2026-08-04
**Final Notes:** Delivered the owner's two analyser asks (per-GW xP + sort) and closed a Sprint-006
backlog item with one additive change — the xP total provably unchanged. A good example of making a
number *legible* without altering it. Sprint outcome: **Successful** — 3/3 stories, zero roll-over,
DoD held.
