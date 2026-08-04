# Sprint 036: Fix the `ask analyse` table + assess xMins

**Dates:** 2026-08-04
**Status:** ✅ Complete (2/2 stories, retro done)
**Capacity:** ~1–2 working sessions (a small consistency fix + an assessment)
**Carried Over:** None (Sprint 035 closed clean)

> **Direction (owner's Sprint-35 retro):** (1) *"`ask "analyse TS"` did not produce a table like the
> transfer question… would have liked the breakdown over 5 weeks and who the weakest starters were."*
> (2) A new backlog item — **probabilistic rotation & minutes modelling (xMins)** — *"what do you
> think, and when/where could it fit?"*

---

### 🔎 Verified at planning (the standing lesson)

- **The `analyse --squad` *command* already shows the full table** — XI with per-GW columns
  (GW1…GWN) + weak links + highlights (Sprint 030). The gap is *only* that the `ask` analyse intent
  shows the one-line headline + prose, not that table. So the fix is **reuse**: give the analyse
  decision a structured `detail` = `render_squad_analysis(...)`, exactly as the transfer plan got in
  Sprint 034. Covered by **ADR-036** ("`ask` returns structured detail") — **no new ADR needed**.
- **xMins** is a genuine new feature (assessed below), not a quick fix — this sprint *places* it
  (backlog + roadmap), it doesn't build it.
- ClubElo up (intermittent); still preseason (0 GWs).

---

### 🧭 What's new — consistency in `ask`, and a home for xMins

`ask` learned structured detail for the transfer plan (ADR-036); this brings the **analyse** intent to
the same standard — the exact table (XI, per-GW xP, weak links) above the summary, so *"analyse TS"*
reads like *"which 3 transfers"*. And **xMins** — the recurring "assumes they play" caveat — gets a
proper assessment and a place on the roadmap (a lightweight v0, then a full ML model).

---

### 🎯 Sprint Goal

**Objective:** Make `ask "analyse <squad>"` show the full squad-analysis table (per-GW + weak links)
above its narration — matching the transfer plan. And **assess + place xMins** (a lightweight v0 and
a full ML model) on the backlog/roadmap.

#### Success Criteria
- [ ] `ask "analyse <squad>"` shows the **squad-analysis table** (XI + per-GW xP + weak links) as its
      `detail`, then the narration + the ✓/⚠ trust line
- [ ] Reuses `render_squad_analysis` (no new rendering); under ADR-036 (no new ADR)
- [ ] Existing `ask` intents (captain, transfer, plan) unchanged; existing 312 stay green
- [ ] Tests (the analyse decision carries a `detail`) + live smoke (`ask "analyse TS"`)
- [ ] **xMins assessed and placed** — a lightweight v0 (FPL-native) + a full ML model, with where/when
      each fits — recorded in the Backlog and the Roadmap
- [ ] Docs: Architecture changelog (analyse detail), Handbook/README as needed, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-107 | **`ask "analyse"` structured detail** — the analyse decision carries a `render_squad_analysis` table (per-GW + weak links) shown above the narration (ADR-036 pattern). Tests + smoke | High | ✅ Done | 1 session |
| US-108 | **Assess + place xMins** — record the two-step plan (lightweight v0: `chance%` × historical minutes ratio; full ML: congestion / European / rotation profiles) with where & when each fits, in the Backlog + Roadmap | Medium | ✅ Done | 0.5 session |

#### Technical Tasks & Maintenance
- [ ] Update Architecture changelog (analyse intent gains structured detail) — _US-107_
- [ ] Backlog + Roadmap: xMins v0 (Phase 3) + full ML xMins (later phase, post-GW1) — _US-108_
- [ ] Update PROJECT_STATUS — _US-108_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — the analyse decision carries a `detail`; existing 312 green; no new dependency.
2. **Manual smoke test done** — `ask "analyse TS"` shows the table (per-GW + weak links) + summary + ✓ line.
3. **Documentation updated & checked** — Architecture, Backlog + Roadmap (xMins), sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| `ask "analyse"` structured detail (reuse the table) | *Building* xMins (this sprint places it, doesn't build it) |
| Assessing + roadmapping xMins (v0 + ML) | New rendering / a new ADR |
| Reuse `render_squad_analysis` | Changing the analyse *command* (already has the table) |

**External Dependencies:** None.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| The analyse table is wide in `ask` | Low | Same table the command already shows; default horizon 5; soft cap noted |
| xMins scope creep into this sprint | Med | It's *assessment + placement* only; the build is a future sprint/phase |
| Over-promising xMins v0 | Low | State it's an estimate from chance% + history, not the full ML model |

---

### 🗝️ xMins assessment (US-108 — recorded, not built)

**Value: very high** — rotation/minutes is the biggest FPL variance driver and the recurring "assumes
they play" caveat. **Do it in two steps:**

- **v0 (lightweight, FPL-native, no ML):** expected minutes ≈ `chance_of_playing%` × a historical
  minutes/starts ratio (data we already have). Weight xP by it → separates nailed-on from rotation,
  retires bench-blindness in captain/transfer/analyse. Captures ~most of the decision value. **Fits
  Phase 3**, buildable relatively soon.
- **Full probabilistic xMins (the owner's ML idea):** schedule congestion (hours between kickoffs),
  European-match congestion, historical manager rotation profiles, substitution tendencies → a
  trained model producing per-fixture minutes probabilities. **Needs** in-season per-GW minutes
  (post-GW1), external European-fixture data, and a real ML effort. **A later, dedicated phase**,
  gated on data.

**Placement:** both on the Backlog; v0 as a near-term Phase 3 enhancement, the ML model as a later
phase (post-GW1). It's the highest-value deferred item — worth doing properly, lightweight first.

---

### 📝 Session Progress Log

- **US-107 (`ask "analyse"` structured detail) ✅** — The gap was pure omission: `_decide_analyse`
  discarded the per-GW data `_squad_xp` already hands it and returned a one-line `headline`. Now it
  threads `by_gameweek_by_id` + `gameweeks` into `analyse_squad` and returns
  `detail = render_squad_analysis(...)` — the **exact table the `analyse` command prints** (XI + per-GW
  xP + weak links) — with the one-line headline dropped (the table's header already carries the
  projected XI xP). Same move as the transfer plan (ADR-036); no new ADR, no new dependency.
  **+1 test** (`_decide_analyse` carries a `detail` with `GW1`/`Weakest links`, no `headline`; store
  monkeypatched so it stays offline) → suite **312 → 313**; ruff clean. **Live smoke** (`ask "analyse
  TS"`): now shows the full 5-GW table + named weakest links (Ampadu, Kelleher, Truffert), and the ✓
  trust line still verifies (every named player traces to the table). Architecture changelog updated.
- **US-108 (assess + place xMins) ✅** — Recorded the assessment (owner's Sprint-35 request) as a
  first-class **Backlog** section with the honest two-step recommendation: **v0** (lightweight,
  FPL-native — `chance_of_playing%` × a historical minutes/starts ratio, weight xP by it; near-term
  **Phase 3**, no ML, ~most of the value) and the **full probabilistic ML model** (schedule/European
  congestion, rotation profiles, substitution tendencies → per-fixture minute *probabilities*; needs
  in-season data + external European fixtures → a later **Phase 5**, gated post-GW1). **Roadmap**
  updated to match — the Phase-3 xMins line expanded into v0, a new Phase-5 bullet for the ML model,
  both cross-linked to the Backlog assessment; the terse "expected minutes" Deferred line now points
  at it. Documentation only — no code.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories. **US-107** — `ask "analyse <squad>"` now shows the full squad-analysis
  table (XI + per-GW xP + weak links) above its narration, by reusing `render_squad_analysis` (the
  exact table the `analyse` command prints) as the decision's `detail` — the two retro asks (the 5-GW
  breakout + the *named* weakest starters) in one move. **US-108** — xMins assessed and placed: a
  lightweight FPL-native v0 (Phase 3) and the full probabilistic ML model (Phase 5, post-GW1), on the
  Backlog + Roadmap. Tests 312 → **313**; **no new ADR, no new dependency**.
* **Carried Forward:** None.
* **Key Artifacts / Decisions:** `_decide_analyse` now threads per-GW data + returns a `detail`
  (dropping the one-line headline, like the transfer plan); the xMins two-step assessment
  (Backlog section + Roadmap Phase 3/5 bullets).

#### Retrospective
* **What Went Well?**
  - **The fix was a join, not a rebuild.** The retro gap ("no table like the transfer question") was
    pure omission — `_decide_analyse` was discarding the per-GW data it already held and returning a
    one-liner. Reusing the command's own renderer closed it in a few lines; the ✓ trust line kept
    working untouched (the named weak links all trace to the table). "Reach for a join before a
    rebuild" paid off again.
  - **Consistency as a feature.** `ask`'s intents now behave alike — transfer *and* analyse both show
    the exact table above the narration. One less surprise for the user.
  - **An honest, staged assessment beats a yes/no.** xMins is the highest-value deferred item; splitting
    it into a lightweight FPL-native v0 (most of the value, now-ish) and the full ML model (rigorous,
    post-GW1) gives a real plan and matches the project's "lightweight over completeness" ethos —
    rather than a vague "someday, machine learning".
* **What Could Be Improved?**
  - The `ask "analyse"` table is wide (5 GW columns). It's the same table the command already prints,
    so acceptable — but a future *terse* mode for `ask` (headline + prose only) could be an option.
  - xMins v0 is *assessed*, not built — the "assumes they play" caveat still stands until a later
    sprint picks it up. Deliberate (scope), but the caveat remains live.
* **Lessons Learned?**
  - When two surfaces should agree, wire them to the *same* renderer — don't grow a second one.
  - A good backlog entry is a decision, not a wish: state the two steps, what each needs, and where it
    fits — so "later" is actionable, not vague.
* **Action Items for Next:**
  - [ ] (Backlog) xMins **v0** is now shovel-ready — a candidate near-term Phase 3 sprint.
  - [ ] **Data Hardening** at ~GW1 (2026-08-21); or more Phase 4 / the web UI — owner to steer.
  - [ ] Keep the gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — build **xMins v0** (now assessed and shovel-ready), more
Phase 4, the web UI (Phase 2), or wait for GW1 to do Data Hardening. All live.

**Completion Date:** 2026-08-04
**Final Notes:** A small, honest sprint — one consistency fix (the retro's table gap, closed by reuse)
and one planning decision (xMins, assessed and staged). No new ADR, no new dependency; tests 312 →
313. Sprint outcome: **Successful** — 2/2 stories, zero roll-over, DoD held (36th).
