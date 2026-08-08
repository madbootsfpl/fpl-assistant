# Sprint 119: My Squad edit — a position filter + an "affordable" check

**Dates:** 2026-08-20
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~½ session (two small edit-UI affordances — display only)
**Carried Over:** none

> **Direction (tester feedback):** *"On the My Squad sub-tab, the **Edit** (swap) function should have a filter
> to select GK / DEF / MID / FWD, plus an **affordable** checkbox, when editing your team."*

---

### 🔎 Verified at planning (on real data)

- **The current Swap UI** (`render_my_squad` → the "Swap a player" expander): a **"Replace"** selectbox lists
  **all 15** owned players (sorted by position); the **"With"** candidates are then filtered to the *same
  position* as the picked player, available (`not is_unavailable`), and ranked by xP. So a swap is always
  same-position (as FPL requires) — the tester's **position filter** naturally scopes the **"Replace"** list,
  and the **affordable** check scopes the **"With"** list.
- **The bank is derivable.** `owned` prices sum to the squad's spend; `FPL_BUDGET = 100.0` → **bank =
  100 − spent**. A swap of `out → in` is affordable when `in.price ≤ out.price + bank`.
- **`apply_transfer` already *validates* budget** (`budget=FPL_BUDGET`) — an unaffordable swap is rejected with
  an error today. So the **"affordable" checkbox is a pre-filter** (hide the ones that would be rejected), not
  new enforcement — a UX win, not a rule change.
- **No analytics touched** — both are edit-controls in the My Squad view (ADR-055); the swap engine +
  validation are unchanged.

---

### 🎯 Sprint Goal

**Objective:** editing your team is quicker — filter the swap by **position**, and optionally show only
**affordable** replacements (with your **bank** shown). Display/edit-UI only; the swap validation + analytics
untouched.

#### Success Criteria
- [x] **US-299 (a position filter on the swap)** — a **GK · DEF · MID · FWD** filter (+ **All**) at the top of
      the "Swap a player" expander that scopes the **"Replace"** selectbox to owned players of that position
      (the "With" candidates stay same-position as the picked player). A clear note when you own none of a
      position.
- [x] **US-300 (an "affordable" checkbox)** — an **"Affordable only"** checkbox that filters the **"With"**
      candidates to `price ≤ out.price + bank`, plus a **bank caption** (*"Bank: £X.Xm"*). The swap still
      validates on apply (unchanged); the checkbox just hides what wouldn't fit.
- [x] **No drift** — edit-UI only; `apply_transfer`/`decision_xp`/the analytics unchanged; the session-only edit
      model + read-only web guardrail hold; existing **764** stay green (**766** with +2); ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (extends **ADR-055** (the editable squad) —
      noted; no new ADR).

---

### 🧭 Design sketch

**US-299.** In the "Swap a player" expander, add a **`st.segmented_control("Position", ["All","GK","DEF","MID",
"FWD"], default="All")`**; build the "Replace" options from `owned` filtered by it (`pos == choice`), sorted by
position then name. If the filtered list is empty → a caption (*"No {POS} in your squad."*) and skip the rest.
The "With" candidates already key off the picked player's position, so they follow automatically.

**US-300.** Compute `bank = FPL_BUDGET − sum(p["price"] for p in owned)`; show a **`st.caption(f"Bank:
£{bank:.1f}m")`**. Add **`st.checkbox("Affordable only", value=False)`**; when ticked, filter the candidate list
to `p["price"] <= out["price"] + bank` before ranking. A note when the filter empties the list (*"No affordable
same-position replacements — untick to see all."*). `apply_transfer` still enforces the budget on **Swap →**.

**Deferred:** a price/xP sort toggle on the candidate list; a max-price slider (the affordable check covers the
common case); filtering the transfer/build pickers (this is scoped to My Squad edit per the feedback).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-299 | **Position filter on the swap** — GK/DEF/MID/FWD (+ All) scoping the "Replace" list. | High | ✅ Done | ~¼ session |
| US-300 | **"Affordable only" checkbox** — hide replacements you can't afford; show the bank. | High | ✅ Done | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the My Squad view exposes a **Position** control + an **Affordable only** checkbox in the
   Swap expander (AppTest); selecting a position scopes the "Replace" options to that position; ticking
   "Affordable only" drops candidates above `out.price + bank`; the bank caption shows; a swap still applies +
   validates (the existing swap test stays green). Existing **764** stay green. No `.save(` / no analytics
   change.
2. **Manual smoke** — My Squad → Swap: pick **MID** → only your MIDs in "Replace"; tick **Affordable only** →
   the "With" list drops the too-expensive picks; the bank reads correctly; a swap works.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log.

---

### 📝 Session Progress Log

- **US-299 (position filter on the swap)** — added a `st.segmented_control("Position", ["All","GK","DEF","MID",
  "FWD"], default="All")` at the top of the "Swap a player" expander (`render_my_squad`); the "Replace" options
  now build from `owned` filtered to that position (sorted by position then name), with a *"No {POS} players in
  your squad."* caption when the filter empties. The "With" candidates already key off the picked player's
  position, so they follow. Smoke (AppTest): All → 15 Replace options; GK → the 2 GKs only. +1 test
  (`test_my_squad_swap_position_filter_scopes_the_replace_list`). ruff clean. Edit-UI only — no analytics change.
- **US-300 (an "affordable" checkbox)** — added `bank = FPL_BUDGET − sum(owned prices)` with a `st.caption("Bank:
  £X.Xm")`, plus a `st.checkbox("Affordable only", value=False)`. When ticked, the "With" candidates filter to
  `price ≤ out.price + bank` (a pre-filter — `apply_transfer` still enforces the budget on **Swap →**). A caption
  *"No affordable replacement (≤ £X.Xm) — untick to see all."* when the filter empties a non-empty list. Smoke:
  bank reads £0.0m for the fully-spent demo squad; ticking drops "With" 60 → 42. +1 test
  (`test_my_squad_swap_affordable_only_scopes_candidates_and_shows_bank`). ruff clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ both stories shipped. Editing your team is quicker: the "Swap a player" expander now has a
**Position** filter (All/GK/DEF/MID/FWD) scoping the "Replace" list, a **bank caption**, and an **"Affordable
only"** checkbox scoping the "With" candidates to `price ≤ out.price + bank`. Edit-UI only — the swap engine
(`apply_transfer`), `decision_xp`, and the analytics are untouched; the session-only edit model + read-only web
guardrail hold. Extends **ADR-055**; no new ADR.

**Delivered**
- **US-299** — `st.segmented_control("Position", …)` at the top of the expander (`render_my_squad`); "Replace"
  builds from `owned` filtered by it (sorted position→name); a *"No {POS} players in your squad."* caption when
  empty. +1 test (`test_my_squad_swap_position_filter_scopes_the_replace_list`).
- **US-300** — `bank = FPL_BUDGET − sum(owned prices)` → `st.caption("Bank: £X.Xm")`; a
  `st.checkbox("Affordable only")` filtering the "With" candidates to `price ≤ out.price + bank` (a pre-filter —
  `apply_transfer` still enforces the budget on **Swap →**); a *"No affordable replacement (≤ £X.Xm) — untick to
  see all."* caption when it empties a non-empty list. +1 test
  (`test_my_squad_swap_affordable_only_scopes_candidates_and_shows_bank`).

**Verified at planning (real data)** — the current swap is same-position by design, so the position filter scopes
"Replace" and the affordable check scopes "With"; `FPL_BUDGET = 100.0`, so bank is derivable; `apply_transfer`
already validates budget (the checkbox is a UX pre-filter, not new enforcement). Smoke on the demo squad: All → 15
Replace options, GK → 2; bank £0.0m (fully-spent), "Affordable only" drops "With" 60 → 42.

**Metrics** — 766 tests (764 → +2), all green · ruff clean · 93 ADRs (no new) · 2 stories, ~½ session.

**What went well**
- Reused the existing swap shape end-to-end — no analytics/engine change, so risk stayed in the view.
- The affordable check is a pure display filter over the already-budgeted engine — no double-source-of-truth.

**Even better if**
- The candidate list has no price/xP **sort toggle** or **max-price slider** yet (deferred — the affordable
  check covers the common "what fits" case).
- The transfer/build pickers don't get the same position/affordable filters (out of scope — the feedback was
  My Squad edit).

**Deferred / backlog** — a price/xP sort toggle + a max-price slider on the candidate list; the same filters on
the Transfer/Build pickers.

---

### 📌 For Tony

_(sprint-review reflection fields — left blank for you)_

- **Biggest learning this sprint:**
- **One thing to change next sprint:**
- **Confidence in the swap UX (1–5):**
