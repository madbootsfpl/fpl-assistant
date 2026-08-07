# Sprint 091: Bench order — the auto-sub priority

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (a pure `bench_order` helper + a My Squad display)
**Carried Over:** none

> **Direction (owner — from the backlog, "Bench order"):**
> Which bench player subs on first? Show/recommend the **auto-sub priority** — if a starter blanks, the
> order your bench comes on in — on My Squad.

---

### 🔎 Verified at planning (code)

- **No auto-sub logic exists yet** — a fresh, small addition. `bench_ids` is stored as a list but **ordered
  by squad position**, not sub priority; `render_pitch` shows the bench ordered by position; nothing surfaces
  "who subs first."
- **The data is on hand** — `render_my_squad` already has the declared `bench` (4 players) + the
  horizon-aware `xp_by_id`. So the recommendation is a pure function over those.
- **The FPL rule (what to model):** when a starter plays 0 minutes, FPL brings on the **first bench player
  (in your set order) that keeps a legal XI**; the **bench GK only ever replaces the starting keeper**. A
  useful *recommendation* is: **outfield subs ranked by xP** (your most valuable bench player first), then
  the **GK sub** separately. (Per-blank formation legality is a runtime detail FPL resolves; the tool
  recommends the priority + notes "the first that keeps a legal XI".)

---

### 🎯 Sprint Goal

**Objective:** My Squad shows a clear **bench order** — 1st / 2nd / 3rd outfield sub (by xP) + the GK sub —
so a manager knows who comes on first if a starter blanks. A pure, tested helper; display-only; no analytics
drift.

#### Success Criteria
- [x] **US-241 (the `bench_order` helper, ADR-078)** — a pure `bench_order(bench, scores)` (analytics):
      outfield bench ranked by `scores` (xP) → `1st`/`2nd`/`3rd`, then the bench GK → `GK` (subs only for the
      keeper). Empty-safe (Row or dict); returns `[(role, player)]`. Unit-tested (order, GK-separate, ties,
      empty).
- [ ] **US-242 (My Squad display)** — under the pitch, a **"Bench order (auto-subs)"** line naming the subs
      in priority with their xP (e.g. *"1st Saka (5.2 xP) · 2nd Diaz (3.1) · 3rd Mitchell (1.4) · GK Sá"*)
      + a one-line explainer ("FPL brings on the first that keeps a legal XI; the bench GK only covers your
      keeper"). Shown when a bench is declared; uses the horizon-aware xP.
- [ ] **No drift** — display-only; `decision_xp`/the analytics otherwise unchanged; existing **629** stay
      green; ruff clean.
- [ ] Docs: ADR-078 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-241 | **`bench_order` helper** — outfield bench by xP (1st/2nd/3rd) + the GK sub, as a pure analytics function. ADR-078. | High | ✅ Done | ~¼ session |
| US-242 | **My Squad bench-order line** — show the recommended sub priority + an auto-sub explainer under the pitch. | Medium | ⬜ To do | ~¼ session |

---

### 🧭 Design sketch

**US-241 (ADR-078).** `src/analytics/optimizer.py` (next to `best_legal_xi`): `bench_order(bench, scores)` →
`[(role, player)]` where role is `"1st"/"2nd"/"3rd"` for the outfield bench sorted by `scores` desc, then
`("GK", keeper)` for the bench GK. Empty-safe; exported from `src.analytics`.

**US-242.** In `render_my_squad`, after the pitch: `order = bench_order(bench, xp_by_id)`; if it's non-empty,
`st.caption("**Bench order** (auto-subs): " + " · ".join(f"{role} {p['web_name']} "
f"({round(xp_by_id.get(p['id'],0),1)} xP)" ...) + " — FPL brings on the first that keeps a legal XI; the "
"bench GK only covers your keeper.")`.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `bench_order` ranks the outfield bench by xP (`1st` = highest), puts the GK last as
   `GK`, is empty-safe and tie-stable; My Squad shows a "Bench order" caption naming the subs (a session
   squad with a declared bench). Existing **629** stay green.
2. **Manual smoke** — My Squad with a declared bench shows the sub order; the 1st sub is the highest-xP bench
   outfielder; the GK is flagged separately.
3. **Docs updated** — ADR-078 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-241 (the `bench_order` helper, ADR-078).** `src/analytics/optimizer.py::bench_order(bench, scores)` (next
to `best_legal_xi`, exported): the **outfield** bench sorted by `scores` (xP) desc → roles "1st"/"2nd"/"3rd",
then the **bench GK** → "GK" (keeper-only). Returns `[(role, player)]`; empty-safe (Row or dict); tie-stable;
a missing score treated as 0. Smoke: Mid 5.4→1st · Fwd 3.3→2nd · Def 2.1→3rd · GK separate. +2 tests
(ranking + GK-separate; empty/tie/no-scores). ruff clean, full suite **631** green.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
