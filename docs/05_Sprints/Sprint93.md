# Sprint 093: Bench order polish — recommended on Build · sub numbers on the pitch

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (two small extensions of the bench-order feature)
**Carried Over:** none

> **Direction (owner — polish the just-shipped bench order, ADR-078/079):**
> 1. A **freshly-built** squad should start in the **recommended (xP) sub order**.
> 2. Annotate the **My Squad pitch** bench cards with the **sub number** (1st / 2nd / 3rd / GK).

*No new ADR — extends ADR-078 (bench order) / ADR-079 (set the order).*

---

### 🔎 Verified at planning (code)

- **Build's saved bench is in solver order** — `"bench_ids": [p["id"] for p in selected if p["id"] not in xi]`
  — an arbitrary order, so a built squad's auto-sub priority starts unsorted. `bench_order` + `display_xp`
  are **already in `render_build`'s scope**, so ordering it by recommended (xP) is a one-line change.
- **The pitch bench row is ordered by position, unlabeled** — `render_pitch` does
  `sorted(bench, key=_ORDER)` and `_card` shows name/team/xP but **no sub role**. `render_pitch` is called
  **only** from My Squad, so a `bench_roles` param is safe to add.
- **My Squad already computes the priority** — `outfield_subs` (1st/2nd/3rd) + `gk_sub` (from `bench_ids`
  order) exist for the "🔁 Bench order" line; the same map feeds the pitch labels (just computed *before*
  the pitch call).

---

### 🎯 Sprint Goal

**Objective:** a built squad starts with a sensible bench order (recommended xP), and the My Squad pitch
labels each bench card with its sub number — so the auto-sub priority is visible on the pitch, not just in
the line below it. Display/edit only; no analytics change.

#### Success Criteria
- [x] **US-245 (Build → recommended order)** — `render_build`'s saved squad orders `bench_ids` by
      `bench_order(bench, display_xp)` (outfield by xP → 1st/2nd/3rd, then the GK), so *Download* / *Use this
      squad →* start in the recommended priority (still user-reorderable in My Squad).
- [x] **US-246 (pitch sub numbers)** — `render_pitch` accepts a `bench_roles` map (id → "1st"/"2nd"/"3rd"/
      "GK"); the bench row is ordered by that priority and each `_card` shows a **"🔁 1st sub"** (or "GK
      sub") caption. My Squad passes the roles it already computes; the XI cards are unchanged.
- [ ] **No drift** — display-only; the analytics use `bench_ids` as a set (unchanged); existing **634** stay
      green; ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README (no new ADR — extends ADR-078/079).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-245 | **Build → recommended bench order** — order the saved `bench_ids` by `bench_order` (xP) so a built squad starts sensibly. | High | ✅ Done | ~¼ session |
| US-246 | **Sub numbers on the pitch** — `render_pitch` labels bench cards with the sub role (1st/2nd/3rd/GK). | Medium | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

**US-245.** In `render_build`'s squad dict: `"bench_ids": [pl["id"] for _role, pl in bench_order([p for p in
selected if p["id"] not in xi], display_xp)]` — the outfield subs by xP + the GK last. (The rest of the dict
unchanged; still legal, still a full 15.)

**US-246.** `pitch.py`: `_card(..., sub_role=None)` renders `st.caption("🔁 {sub_role} sub")` (or "🔁 GK
sub") when given. `render_pitch(..., bench_roles=None)`: order the bench row by a `_ROLE_ORDER`
(1st<2nd<3rd<GK) when `bench_roles` is present, else by position; pass each card its role. In
`render_my_squad`: compute `bench_ordered`/`outfield_subs`/`gk_sub` + a `bench_roles` map **before** the
`render_pitch` call and pass it (the "🔁 Bench order" line + reorder expander stay after, reusing the vars).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — a built squad's `bench_ids` come out in recommended (xP) order (highest-xP outfield sub
   first, GK last); the My Squad pitch shows a "sub" caption on a bench card (a session squad with a bench).
   Existing **634** stay green.
2. **Manual smoke** — Build → the saved squad's bench is xP-ordered; My Squad pitch bench cards read "1st
   sub / 2nd sub / 3rd sub / GK sub"; reordering (Sprint 092) still updates them.
3. **Docs updated** — PROJECT_STATUS, Architecture, README.

---

### 📝 Session Progress Log

**US-245 (Build → recommended order).** `render_build`'s saved squad dict now orders `bench_ids` via
`bench_order(bench_players, display_xp)` — the outfield subs by xP (highest first) then the GK — so a
*Download* / *Use this squad →* starts in the recommended sub priority (still reorderable in My Squad). A
one-line change (`bench_order`/`display_xp` already in scope); no new ADR. Smoke: a built squad's bench →
MID 18.4 · FWD 17.7 · DEF 16.9 · GK last (outfield xP-desc ✓). +1 test
(`test_build_starts_the_bench_in_recommended_order`). ruff clean, full suite **635** green.

**US-246 (pitch sub numbers).** `pitch.py`: `_card(..., sub_role=None)` renders a **"🔁 1st sub"** / "🔁 GK
sub" caption on a bench card; `render_pitch(..., bench_roles=None)` orders the bench row by priority
(`_ROLE_ORDER`: 1st<2nd<3rd<GK) and labels each card. `render_my_squad` computes the `bench_roles` map (from
the stored order) **before** the pitch call and passes it; the "🔁 Bench order" line + reorder expander stay
below (unchanged). XI cards untouched. Smoke: the pitch bench shows 🔁 1st/2nd/3rd/GK sub in priority order.
+1 test (`test_my_squad_pitch_labels_the_bench_subs`). ruff clean, full suite **636** green.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
