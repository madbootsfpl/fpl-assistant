# Sprint 145: P0 quick-wins (tester feedback, 2026-08-12)

**Dates:** 2026-08-12
**Status:** 🚧 In progress
**Capacity:** ~½ session (two quick fixes; the data floor is gated separately)
**Carried Over:** none

> **Direction:** the first P0 items from the 2026-08-12 intake. **A3** (transfer filters) + **C1** (captain persists
> on load) are genuine quick fixes and ship here. **B** (the cold-start data floor — new/promoted players at 0)
> **changes `decision_xp`** = the one-xP metric (ADR-041), so it is **NOT** a quick build — it needs a root-cause
> investigation + an **ADR** (→ ADR-104), handled as its own gated story after this bundle.

---

### 🔎 Verified at planning (on the code)

- **A3 (transfer filters):** the My Squad **Transfer** control (`views/squads.py`) already filters the bring-in list
  by **position** (via the out player) + **Affordable only** + **Include injured/suspended** — but the list is still
  long (all same-position players). Add a **Team** filter + a **Max-price** cap on the candidates. Display-only.
- **C1 (captain persist):** `cloud_store.save_squad` stores the **whole squad dict** (incl. `captain_id` if set) and
  `load_squad` returns it verbatim — so the store **does** round-trip the captain. So this is a **timing/UX gap**,
  not a store bug: likely the captain was set *after* the last Save (so the cloud copy has none), and setting a
  captain doesn't re-save. Fix direction: make the captain survive the round-trip in practice — a test to pin it,
  then either auto-save on captain change or a clear "re-save to sync" nudge. Investigate precisely when building.
- **B (data floor):** deferred to its own ADR (changes the core metric).

---

### 🎯 Sprint Goal

Ship the two genuine quick-wins — **Transfer filters** (team + max-price) and **captain-persists-on-load** — and
tee up the cold-start data floor (B) as a gated ADR-104 story.

#### Success criteria
- [ ] **US-356 (transfer filters)** — the Transfer bring-in list gains a **Team** filter + a **Max-price** cap
      (alongside position/affordable/injured); the list narrows accordingly; a test the filters scope it. Display-only.
- [ ] **US-357 (captain persists on load)** — a cloud Save→Load round-trips the `captain_id` in practice; pinned by
      a test; the UX gap (set-after-save) closed (auto-save on captain change and/or a clear nudge).
- [ ] **No drift** — display/session-state only; existing **959** green; ruff clean.
- [ ] **Docs** — PROJECT_STATUS/Architecture; memory.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-356 | **Transfer filters** — team + max-price on the bring-in list. | High | ✅ Done | ~¼ session |
| US-357 | **Captain persists on load** — round-trip + close the set-after-save gap. | High | ✅ Done | ~¼ session |
| — | **B: cold-start data floor** → its own **ADR-104** (changes `decision_xp`) — NOT built here. | High | 🔒 gate next | investigation |

---

### ✅ Definition of Done

1. **Tests** — the transfer bring-in list narrows by team + max-price; the captain round-trips a cloud save/load.
   Existing **959** green; ruff clean.
2. **Manual smoke** — on My Squad → Transfer: pick a team / drop the max price → the list shortens. Save a squad
   with a captain on one device → load on another → the captain is set.
3. **Docs** — PROJECT_STATUS/Architecture; memory.

---

### 📝 Session Progress Log

- **US-356 (transfer filters)** — the My Squad **Transfer** bring-in list gains a **Team** selectbox (All / one
  club) + a **Max price (£m)** slider (0 → the dearest candidate; default = no cap), applied to the same-position
  candidates alongside the existing position / Affordable-only / Include-injured filters — so a long list narrows
  fast. The "no replacements" fallback caption is now filter-aware (points at Team / Max price). Display-only.
  **+1 test** (a Team filter narrows the list to that club + never widens). ruff clean. **959 → 960.** (US-357 next:
  captain persists on load.)
- **US-357 (captain persists on load — auto-sync)** — root-caused: `cloud_store` already stores the **whole squad
  dict** (incl `captain_id`) and returns it verbatim, so the captain persists *if saved* — the gap was **set-after-
  save** (no mechanism to keep a cloud squad in sync after you edit it). Fix: **auto-sync**. A squad becomes
  **linked** to a handle on cloud **Save**/**Load** (`_cloud_linked_handle`); `set_active_squad` now calls a
  best-effort `_autosync` that mirrors the edit back to the cloud when linked + the store is configured — so a
  **captain** (or transfer/bench/sub) change syncs across devices, not just the last manual Save. **Fail-silent**
  (never blocks the edit); **only for cloud-linked squads** (a built/uploaded squad with no handle writes nothing —
  the opt-in server-write invariant holds, ADR-094/054); **Clear** unlinks; the sidebar shows a **🔄 Auto-syncing
  to `<handle>`** line. **+2 tests** (the store round-trips `captain_id`; an edit on a linked squad auto-syncs to
  the handle). ruff clean. **960 → 962.**

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_
