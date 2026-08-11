# Sprint 143: Clearer transfers — My Squad + accept the AI plan

**Dates:** 2026-08-11
**Status:** 📝 Planned — awaiting sign-off (no new ADR; extends ADR-055/046)
**Capacity:** ~½–¾ session (a My Squad transfer polish + one real feature)
**Carried Over:** none

> **Direction (tester → owner):** transfers should be easy from **both** My Squad (in-context) and the Transfer
> page, with **overspend flagged**, and the Transfer page should let you **accept AI-suggested transfers**. Grounding
> revealed **most of this already exists** — so the sprint is *clarify + close three small gaps*, not build-from-zero.
> Owner picked **all four**: rename/clarify · live overspend flag · include-unavailable option · apply the AI plan.

---

### 🔎 Verified at planning (on the code)

- **My Squad already has a free-choice transfer** — the "Swap a player" expander (`views/squads.py:416`, open by
  default): sell one, buy **any same-position** replacement (full list, xP-ranked), a position filter + an
  "Affordable only" toggle, and `apply_transfer` **already warns on overspend** *after* applying.
- **A naming clash we introduced (S142):** the new **"🔁 Substitute"** (lineup) sits right above **"Swap a player"**
  (a transfer) — "swap"/"substitute" read as synonyms. This almost certainly *is* the tester's "add transfers on My
  Squad": it's there, but named confusingly. **Rename → "🔁➡ Transfer in a player"** + a one-liner.
- **The Transfer page already applies a *single* AI swap** (`render_transfer`, the `count==1` branch → "Apply this
  transfer →"). But the **multi-transfer plan** (`count>1` → `suggest_transfer_plan` → `render_transfer_plan`) is
  **display-only — no apply**. That's the one genuine missing feature.
- **The plan's shape is applyable:** each move = `{position, out:{id,price,…}, in:{id,price,…}, gain, bank_after}` —
  so an `apply_transfer_plan(squad, plan, players)` can map every `out.id → in.id` in one pass and do a single
  `squad_15_issues` + cost/overspend check, mirroring `apply_transfer`.
- **FPL honesty:** a transfer is always **same-position** (the 15 are a fixed 2/5/5/3), so "any player" = any
  same-position player. **Points-hits (−4) don't bite preseason** (unlimited free transfers until GW1), so
  "overspend" = the **£100m budget** (a soft flag, never a block — ADR-055).

---

### 🎯 Sprint Goal

**Objective:** make transfers unmistakable and complete — rename My Squad's transfer control (distinct from the new
Substitute), **flag overspend live** as you pick, let you **include flagged players** when planning, and let the
Transfer page **accept a coordinated AI plan** (not just a single swap). Reuses `apply_transfer` /
`suggest_transfer_plan`; no engine change, no server write.

#### Success criteria
- [ ] **US-353 (My Squad transfer — clarity + flag + unavailable)** — rename the "Swap a player" expander to **"🔁➡
      Transfer in a player"** + a one-liner (*Substitute = lineup (XI↔bench) · Transfer = bring in a new player*); a
      **live overspend flag** — as you pick a replacement, show the projected bank / *"£X over £100m"* **before** you
      apply (not only the post-apply warning); an opt-in **"Include injured/suspended"** toggle that adds flagged
      players to the bring-in list (off by default — today they're filtered out).
- [ ] **US-354 (accept the AI plan)** — an **`apply_transfer_plan(squad, plan, players)`** helper (maps each
      `out.id → in.id`; one `squad_15_issues` check; recomputes cost + a soft overspend warning; clears a sold
      captain) + an **"Apply this plan →"** button under the Transfer page's **multi-transfer** suggestion (the
      `count>1` branch), mirroring the single-swap apply (legality error → no change; success → set active + rerun).
- [ ] **No unintended drift** — session-state only (mutates like `apply_transfer` today); the one-xP + read-only
      invariants hold; existing **945** stay green; ruff clean.
- [ ] **Docs** — Help (Substitute vs Transfer; accept-a-plan); PROJECT_STATUS; Architecture; memory.

---

### 🧭 Design sketch

**US-353 (in the My Squad "Transfer in a player" expander):**
- Label → `"🔁➡ Transfer in a player"`; caption: *"🔁 Substitute swaps your lineup (XI↔bench); a Transfer brings in a
  **new** player (sells one of your 15)."*
- `include_flagged = st.checkbox("Include injured/suspended", value=False)` → the candidate filter drops the
  `not is_unavailable(p)` clause when ticked.
- **Live flag:** after `in_choice` is picked, `proj = round(cost - out["price"] + by_id[in_id]["price"], 1)`;
  show `st.caption`/`st.metric` — `f"After this: £{proj:.1f}m · bank £{FPL_BUDGET-proj:.1f}m"` or, if `proj>100`,
  `f"⚠ £{proj-100:.1f}m over the £100m budget"`. Computed each rerun (the selectbox change reruns) — no apply needed.

**US-354 (`web_streamlit/squads.py` + `render_transfer`):**
```
def apply_transfer_plan(squad, plan, players, budget=FPL_BUDGET):
    out_to_in = {m["out"]["id"]: m["in"]["id"] for m in plan}
    new_ids = [out_to_in.get(i, i) for i in squad["player_ids"]]
    issues = squad_15_issues([by_id[i] for i in new_ids if i in by_id])
    if issues: return False, issues, None, None
    ... new_ids/names/bench (out→in) · clear a sold captain · cost + soft over-budget warning ...
```
In `render_transfer`'s `count>1` branch, after `render_transfer_plan`: a **net-cost caption** + **"Apply this plan
→"** → `apply_transfer_plan` → on ok `set_active_squad(new)` + `st.rerun`, else surface the issues.

**Deferred (backlog):** points-hit (−4) modelling of a plan (GW1+, live); a My Squad "apply the best suggested
transfer" shortcut; wildcard/free-hit-aware planning.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-353 | **My Squad transfer — rename + live overspend flag + include-unavailable.** | High | ✅ Done | ~⅓ session |
| US-354 | **Accept the AI transfer plan** — `apply_transfer_plan` + the Transfer-page button. | High | ✅ Done | ~⅓ session |

---

### ✅ Definition of Done

1. **Tests** — the My Squad control reads **"Transfer in a player"** (+ the distinction caption); ticking **Include
   injured/suspended** surfaces a flagged same-position player; an over-budget pick shows the **live** over-flag
   before apply; `apply_transfer_plan` applies N swaps + refuses an illegal result + warns on overspend + clears a
   sold captain; the Transfer page's multi-plan shows **and applies** ("Apply this plan →" updates the session
   squad). Existing **945** green; ruff clean.
2. **Manual smoke** — My Squad: Substitute vs Transfer read as distinct; a pricey buy flags the overspend live; a
   flagged player appears when the toggle's on. Transfer page: a 2-transfer plan applies to the session squad.
3. **Docs** — Help; PROJECT_STATUS; Architecture; memory.

---

### 📝 Session Progress Log

- **US-353 (My Squad transfer — clarity + flag + unavailable)** — the My Squad "Swap a player" expander is renamed
  **"Transfer"** (owner's steer: plain *Transfer*, not "🔁➡ Transfer in a player") with a caption distinguishing it
  from the S142 **🔁 Substitute** (*Substitute swaps your lineup XI↔bench; a Transfer brings in a **new** player —
  sells one of your 15; same-position only, the squad is a fixed 2/5/5/3*). Its selectboxes read **"Transfer out"** /
  **"Bring in"** and the button is **"Transfer →"** (was Replace/With/Swap). A **live overspend flag** — as you pick
  a replacement, a line shows the **projected 15-cost + bank** (*"After this transfer: £X · bank £Y"*), or a
  **⚠ £X over the £100m budget** warning when it would exceed budget — *before* you apply (the post-apply warning
  stays too). An opt-in **"Include injured/suspended"** checkbox adds flagged (🚑/🚫/⛔) same-position players to the
  bring-in list (off by default; drops the `not is_unavailable` filter when ticked). Reuses `apply_transfer`;
  session-state only. **+2 tests** (the control's label/caption + the live projection line · the include-injured
  toggle surfaces a flagged player) + **2 updated** (the renamed "Transfer out"/"Bring in" labels). ruff clean.
  **945 → 947.** (US-354 next: accept a coordinated AI plan on the Transfer page.)
- **US-354 (accept the AI transfer plan)** — a new **`apply_transfer_plan(squad, plan, players)`** in
  `web_streamlit/squads.py` — the N-transfer counterpart of `apply_transfer`: maps every `out.id → in.id` from the
  `suggest_transfer_plan` moves, validates the **whole** result once (`squad_15_issues`), recomputes cost + a soft
  over-budget warning, and clears a captain sold in the plan; returns `(ok, issues, warning, new_squad)`,
  copy-not-mutate, no server write. Wired into `render_transfer`'s **multi-transfer** (`count>1`) branch: below the
  plan table, a **net-spend / +xP caption** + an **"Apply this plan →"** button → applies all transfers at once
  (`set_active_squad` + `st.rerun`; an illegal result surfaces the issues, no change). Previously the coordinated
  plan was **display-only** — only a single suggested swap could be applied. **+5 tests:** 4 helper unit tests
  (applies all moves + updates cost · refuses an illegal result · warns over budget but applies · clears a sold
  captain) + 1 AppTest (the Transfer page's 2-plan **applies** and mutates the session squad). ruff clean.
  **947 → 952.**

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony — confirm before I gate US-353

1. **No new ADR** — extends **ADR-055** (My Squad edit) + **ADR-046** (Transfer); reuses `apply_transfer` /
   `suggest_transfer_plan`, no engine/server change. Agree? *(My rec: no ADR.)*
2. **The label** — **"🔁➡ Transfer in a player"** for the My Squad control (vs the "🔁 Substitute" above)? Or you'd
   prefer plain **"Transfer"**? *(My rec: "🔁➡ Transfer in a player" — explicit, and visually distinct from Substitute.)*
3. **Overspend is a soft flag** (warns, never blocks — prices drift, ADR-055), *not* a points-hit (that's GW1+)?
   *(My rec: yes — budget flag now, hits later.)*
