# Architectural Decision Record: Set the bench order (persist the auto-sub priority)

**Decision ID:** ADR-079
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** refines **ADR-055** (editable session squad) + **ADR-078** (bench order). Makes
`bench_ids` **order** meaningful (= sub priority) and adds a reorder mutation. No analytics change. Triggered
by the deferred half of Sprint 091.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Sprint 091 (ADR-078) *recommends* a bench sub order (outfield by xP). The owner wants to **set** it — persist
a chosen priority + a reorder UI — so the "Bench order (auto-subs)" line reflects what FPL will actually do.

**Verified in code:** `set_bench` currently **discards order** — it rebuilds `bench_ids` in
**squad-position order** (`[i for i in player_ids if i in chosen]`), so a stored priority is meaningless. The
analytics use `bench_ids` as a **set** (`best_legal_xi`, `suggest_transfers`, the XI/bench split), so making
`bench_ids` an **ordered** list is safe for them; `render_pitch` orders by position. The **bench GK is
keeper-only** (it can only replace the starting keeper), so only the **3 outfield subs** are orderable.

#### Decision Drivers
- **Persist a real priority** — the stored order should be the sub priority, editable, in the session +
  download.
- **Honest to the rules** — the GK is a fixed keeper-only slot, not part of the reorder.
- **No analytics change** — the order is a display/edit concern; the analytics keep using the *set*.
- **Keep the recommendation** — one-click "use the xP order" (ADR-078's `bench_order`), then tweak.

---

### ✅ Decision

**1. `bench_ids` order *is* the sub priority (US-243).** `set_bench(squad, bench_ids)` now **preserves** the
given order (`list(bench_ids)`) instead of reordering by squad position. A new pure mutation
`move_bench_sub(squad, player_id, direction, by_id)` swaps an **outfield** sub with its `up`/`down`
neighbour in the priority (bounds-checked, a no-op at the ends); the **bench GK is excluded** (it keeps its
keeper-only slot). Returns a new squad dict (mutations are copy-not-mutate, ADR-055).

**2. My Squad shows + edits the stored order (US-244).** The "🔁 Bench order (auto-subs)" line reads the
**stored** outfield order + the GK (built from `bench_ids`, not owned order). A reorder control (⬆/⬇ per
outfield sub) persists via `move_bench_sub`; a **"Use recommended (xP) order"** button applies
`bench_order`'s ranking via `set_bench`. All mutate `st.session_state` (no server writes); the order rides
in the `squad.json` download.

**3. Only the outfield 3 are ordered; the GK is fixed.** Reordering operates on the outfield bench subset;
the GK slot is separate (keeper-only), matching FPL.

---

### 🔀 Alternatives Considered

- **A separate ordered field (e.g. `bench_order_ids`).** Rejected — `bench_ids` is already a list and the
  analytics use it as a set, so ordering it in place is simpler and back-compatible.
- **1st/2nd/3rd selectboxes for the outfield.** Viable, but ⬆/⬇ per sub is more intuitive and can't produce
  a duplicate/invalid assignment.
- **Order the GK too.** Rejected — a bench GK can only replace the keeper, so its "priority" is meaningless.
- **Auto-apply the xP order (no manual reorder).** Rejected — the owner asked to *set* it; the xP order is
  the one-click default, manual reorder is the point.

---

### 🧭 Consequences

**Positive**
- The bench sub priority is real, editable, and persists (session + download) — the "Bench order" line shows
  what FPL will do.
- No analytics change (they use the set); reuses ADR-078's recommendation as the one-click default.
- Copy-not-mutate mutations keep the editable-squad model consistent (ADR-055).

**Negative / risks (mitigations)**
- **Existing saved squads' `bench_ids` order was arbitrary** → now read as priority; the user reorders (or
  clicks "use recommended"). Harmless — the analytics never used the order.
- **⬆/⬇ is a per-click swap** → each reorders one step + reruns; fine for 3 subs.
- **Still not a per-blank simulator** (ADR-078) → the caption keeps stating the FPL rule.

---

### 📊 Validation

Verified: `set_bench` discarded order; the analytics use `bench_ids` as a set; the GK is keeper-only.
Acceptance: `set_bench` preserves the given order; `move_bench_sub` swaps an outfield sub up/down, leaves the
GK fixed, and is a no-op at the ends; My Squad's ⬆/⬇ reorders the stored priority (persists on rerun + in the
download) and "Use recommended" applies the xP order; the analytics are unchanged; the existing 632 tests
stay green (new tests added).
