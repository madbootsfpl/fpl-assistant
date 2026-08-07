# Sprint 092: Set the bench order (persist + reorder the auto-sub priority)

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a bench-order model/mutations + a My Squad reorder UI)
**Carried Over:** none

> **Direction (owner — the deferred half of Sprint 091 / ADR-078):**
> Let the user **set** their bench sub priority (persist an ordered bench + a reorder UI), not just see the
> recommended order.

---

### 🔎 Verified at planning (code)

- **`set_bench` discards order today** — it rebuilds `bench_ids` in **squad-position order** (`[i for i in
  player_ids if i in chosen]`), so a stored priority is currently meaningless.
- **The order is free to become the priority** — the analytics use `bench_ids` as a **set** (`best_legal_xi`,
  `suggest_transfers`, the XI/bench split); only the display cares about order. So making `bench_ids` an
  **ordered** list (priority) is safe for the analytics; `render_pitch` still orders by position.
- **Sprint 091 gives the recommendation** — `bench_order(bench, scores)` ranks outfield subs by xP + the GK
  separate. That becomes the **"Use recommended order"** action; the display now shows the **user's set**
  order (what FPL will actually do).
- **Only the 3 outfield subs are orderable** — the **bench GK is keeper-only** (it can't sub for an
  outfielder), so it's a fixed slot, not part of the reorder.
- **The bench built for display is in *owned* order, not `bench_ids` order** (`[p for p in owned if p["id"]
  in bench_ids]`) → build it from `bench_ids` so the stored priority shows.

---

### 🎯 Sprint Goal

**Objective:** a manager can **set** their bench sub priority on My Squad — reorder the 3 outfield subs (⬆/⬇)
or one-click the **recommended (xP)** order — and it **persists** in the session squad + download, driving the
"Bench order (auto-subs)" line. The GK stays keeper-only. Display/edit only; no analytics change.

#### Success Criteria
- [x] **US-243 (the model + mutations, ADR-079)** — `bench_ids` order **is** the sub priority: `set_bench`
      **preserves** the given order (not squad-position); a `move_bench_sub(squad, player_id, direction, by_id)`
      mutation swaps an **outfield** sub with its neighbour (GK excluded, stays fixed). Pure, tested
      (reorder, GK-excluded, edge bounds). Refines ADR-055/078.
- [x] **US-244 (the My Squad reorder UI)** — the "🔁 Bench order" line shows the **stored** order (outfield in
      priority + GK separate); a reorder control (⬆/⬇ per outfield sub) persists via `move_bench_sub`; a
      **"Use recommended (xP) order"** button applies `bench_order`'s ranking. All mutate `session_state`
      (no server writes).
- [ ] **No drift** — the analytics use `bench_ids` as a set (unchanged); existing **632** stay green; ruff
      clean.
- [ ] Docs: ADR-079 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-243 | **Bench-order model + mutations** — `set_bench` preserves order; `move_bench_sub` swaps an outfield sub in priority (GK excluded). ADR-079. | High | ✅ Done | ~½ session |
| US-244 | **My Squad reorder UI** — show the stored order + ⬆/⬇ reorder + a "Use recommended (xP) order" button. | Medium | ✅ Done | ~½ session |

---

### 🧭 Design sketch

**US-243 (ADR-079).** In `web_streamlit/squads.py`: `set_bench(squad, bench_ids)` → `new["bench_ids"] =
list(bench_ids)` (preserve order). New `move_bench_sub(squad, player_id, direction, by_id)`: split
`bench_ids` into outfield (by position via `by_id`) + gk; swap the target with its `up`/`down` neighbour in
the outfield list (bounds-checked, no-op at the ends); `new["bench_ids"] = outfield + gk`. Pure; unit-tested.

**US-244.** In `render_my_squad`: build `bench` from `bench_ids` order; the "🔁 Bench order" line reads the
**stored** outfield order + the GK. A small reorder block (in the bench expander or under the line): for each
outfield sub, its name + xP + **⬆ / ⬇** buttons → `set_active_squad(move_bench_sub(...))` + rerun; a **"Use
recommended (xP) order"** button → `set_active_squad(set_bench(squad, [recommended outfield ids] + gk))`
using `bench_order(bench, xp_by_id)`.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `set_bench` preserves the given order; `move_bench_sub` swaps an outfield sub up/down,
   leaves the GK fixed, and is a no-op at the ends; My Squad's ⬆/⬇ reorders the stored priority and the
   "Use recommended" button applies the xP order; the "Bench order" line reflects the stored order. Existing
   **632** stay green.
2. **Manual smoke** — My Squad → move a sub up → it becomes the 1st sub (persists on rerun + in the
   download); "Use recommended" sets the xP order; the GK stays separate.
3. **Docs updated** — ADR-079 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-243 (the model + mutations, ADR-079).** `web_streamlit/squads.py`: `set_bench` now **preserves** the
given order (`list(bench_ids)`) — `bench_ids` order *is* the sub priority. New pure
`move_bench_sub(squad, player_id, direction, by_id)` splits the bench into outfield (by position) + GK, swaps
the target with its up/down neighbour in the outfield priority (bounds-checked, no-op at the ends, no-op for
the GK), and keeps the GK last (keeper-only). Copy-not-mutate (ADR-055). The `set_bench` order change didn't
ripple — the analytics use `bench_ids` as a **set** (633 green proves it). Updated the old
`test_set_bench_keeps_player_id_order` → `test_set_bench_preserves_the_given_order`; +1 `move_bench_sub` test
(reorder · GK-excluded · edge bounds). ruff clean, full suite **633** green.

**US-244 (the My Squad reorder UI).** The "🔁 Bench order" line now reads the **stored** order — built from
`bench_ids` (outfield labelled 1st/2nd/3rd + the GK separate), not the xP sort. A **"Reorder the bench"**
expander shows each outfield sub with **⬆/⬇** buttons (disabled at the ends) → `move_bench_sub` →
`set_active_squad` + rerun, plus a **"↻ Use recommended (xP) order"** button → `set_bench` with
`bench_order`'s xP ranking. All mutate `session_state` (no server writes); the order rides in the download.
Smoke: a non-xP bench shows its stored order; ⬆ the 2nd sub → it becomes 1st and **persists** (`bench_ids[0]`
updated); "Use recommended" applies the xP order. +1 test (`test_my_squad_bench_reorder_persists_and_
recommended_applies`). ruff clean, full suite **634** green.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **632 → 634** (+2); ruff clean; CI-parity green.

**Delivered**
- **US-243 — the model + mutations (ADR-079).** `bench_ids` order *is* the sub priority: `set_bench`
  preserves order; a pure `move_bench_sub` swaps an outfield sub up/down (GK excluded, keeper-only).
- **US-244 — the My Squad reorder UI.** The "🔁 Bench order" line shows the stored order; ⬆/⬇ per outfield
  sub persist a reorder; a "↻ Use recommended (xP) order" button applies the xP ranking.

**What went well**
- **The order was free to carry meaning** — the analytics use `bench_ids` as a *set*, so making it ordered
  broke nothing (the green suite proved it); only the display/edit changed.
- **Honest to the rules** — the GK is excluded from the reorder (keeper-only), so the priority isn't
  misleading.
- **Compounds** — the display uses the horizon-aware xP; the "recommended" button reuses Sprint-091's
  `bench_order`; the edit follows the copy-not-mutate model (ADR-055).

**Watch-outs / follow-ups**
- Existing saved squads' `bench_ids` order was arbitrary → now read as priority; "Use recommended" gives a
  sensible one-click reset. Harmless (the analytics never used the order).
- Possible later: set the bench order **on Build** so a fresh squad starts in the recommended order; annotate
  the pitch bench cards with the sub number.
- The benign `seed.db` byte-touch recurred during manual smokes → restored; pytest leaves it clean.

See `Sprint92_Lessons_Learnt.md` for the detailed retro.
