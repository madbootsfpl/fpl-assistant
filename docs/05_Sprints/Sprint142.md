# Sprint 142: An intuitive substitution on My Squad

**Dates:** 2026-08-11
**Status:** ✅ Complete — US-351 + US-352 (no new ADR; extends ADR-055). 939 → 945 tests
**Capacity:** ~½ session (a small helper + a view control + a picker pre-fill)
**Carried Over:** none

> **Direction (tester → owner):** making a substitution on My Squad is awkward — the only path today is the
> **"Set the bench (pick 4)"** multiselect (re-pick all four), which doesn't match how anyone thinks about a sub
> ("swap *this* starter for *that* bench player"). The tester asked for a **Substitute button on the hover card**.
> Owner's chosen shape: **a dedicated Substitute control** (bring off ↔ bring on) **with the pitch picker
> pre-filling "Bring off"**.

---

### 🔎 Verified at planning (on the code)

- **Today's only sub path is clunky.** `squads.py::render_my_squad` → the **"Set the bench (pick 4)"** expander
  (`set_bench` + a `legal_xi_issues` check). "Swap a player" is a **transfer** (out-of-squad), a different thing.
- **A button on the hover card is impossible** (confirmed, Sprint 139 wall): the pitch + hover cards are one static
  `st.markdown` HTML block, which **cannot call back to Python** — an HTML button there is inert. So the control must
  be **real Streamlit widgets** near the pitch. This is exactly why S139's "click a kit" became the **picker**.
- **The mechanics already exist** — a substitution is `set_bench(new_bench_ids)` where `new_bench = bench − on + off`,
  gated by `legal_xi_issues(new_xi)`. FPL legality: exactly **1 GK** in the XI, formation in {3-4-3…5-4-1} — already
  encoded in `legal_xi_issues`. So a GK only swaps with the bench GK; outfield swaps must keep a legal shape.
- **The picker is already there** — the "👤 View a player's card" selectbox (US-344) returns the chosen player; it
  can seed the Substitute box's "Bring off" default.

---

### 🎯 Sprint Goal

**Objective:** make a substitution a **two-dropdown, one-click** action on My Squad — pick the starter to bring
**off** and the bench player to bring **on** (only legal swaps offered), Substitute → done — and have the existing
**pitch picker pre-fill "Bring off"** so selecting a player on the pitch flows straight into the sub. Reuses
`set_bench` + `legal_xi_issues`; no engine change, no server write.

#### Success criteria
- [ ] **US-351 (the Substitute control)** — a **"🔁 Substitute"** box on My Squad: **Bring off** (a starter) +
      **Bring on** (a bench player), where **only legal swaps are listed** (GK↔GK; outfield swaps that keep a legal
      XI), + a **Substitute →** button. On apply: `set_bench` the new bench, re-check `legal_xi_issues`, `st.rerun`.
      A small **`substitute(squad, off_id, on_id, by_id)`** helper (in `web_streamlit/squads.py`) does the bench
      math + legality so it's unit-testable. The old **"Set the bench (pick 4)"** multiselect stays, tucked **below**
      as the bulk-edit power path.
- [ ] **US-352 (picker pre-fill)** — selecting a player in the **"👤 View a player's card"** picker **pre-fills
      "Bring off"** when that player is a starter (the "both" wiring). No effect for a bench player (they're a
      *bring-on*, surfaced as a caption hint). Purely a default — the dropdowns stay freely changeable.
- [ ] **No unintended drift** — display/session-state only (mutates the bench like `set_bench` today); the one-xP +
      read-only invariants hold; existing **942** stay green; ruff clean.
- [ ] **Docs** — Help (the new sub flow); PROJECT_STATUS; Architecture; memory.

---

### 🧭 Design sketch

**`substitute(squad, off_id, on_id, by_id)`** (pure, in `web_streamlit/squads.py`, mirrors `set_bench`/`move_bench_sub`):
```
new_bench = [i for i in squad["bench_ids"] if i != on_id] + [off_id]   # on comes into XI, off goes to bench
new = set_bench(squad, new_bench)
xi  = [by_id[i] for i in new["player_ids"] if i not in set(new["bench_ids"])]
return new, legal_xi_issues(xi)         # caller shows the issues + doesn't commit an illegal XI
```
**The control** (in `render_my_squad`, replacing the lead role of "pick 4"):
```
off = selectbox("Bring off (from your XI)", xi_players, index=<picked starter if any>)
legal_ons = [b for b in bench if not substitute(squad, off.id, b.id, by_id)[1]]   # only legal swaps
on  = selectbox("Bring on (from your bench)", legal_ons)
if button("Substitute →"):
    new, issues = substitute(squad, off.id, on.id, by_id)
    if issues: st.error(...); else: set_active_squad(new); toast; st.rerun()
```
**Pre-fill:** the picker (`picked`) already runs above; if `picked` is a starter, pass its index as the "Bring off"
default (via `st.session_state`/`index=`). A bench `picked` shows a caption: *"On the bench — pick a starter to bring
off, then choose them under Bring on."*

**Deferred (backlog):** a truly clickable pitch (needs a bespoke component — over-engineered, rejected, ADR-084/S139
reasoning); drag-and-drop; auto-suggest the best legal sub by xP.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-351 | **The Substitute control** — bring off ↔ bring on (legal-only) + `substitute()` helper. | High | ✅ Done | ~⅓ session |
| US-352 | **Picker pre-fill** — the card picker seeds "Bring off". | Med | ✅ Done | ~¼ session |

---

### ✅ Definition of Done

1. **Tests** — `substitute()` moves the right players + returns issues for an illegal XI (e.g. subbing the only GK
   for an outfielder → flagged, not committed); a legal outfield swap succeeds; the control lists only legal
   bring-ons (AppTest on the two selectboxes + the button); the picker pre-fills "Bring off". Existing **942** green;
   ruff clean.
2. **Manual smoke** — on My Squad: pick a starter on the picker → it's pre-filled under Bring off → choose a bench
   player → Substitute → the pitch updates; an illegal attempt is refused with a clear message.
3. **Docs** — Help; PROJECT_STATUS; Architecture; memory.

---

### 📝 Session Progress Log

- **US-351 (the Substitute control)** — a **`substitute(squad, off_id, on_id, by_id)`** helper in
  `web_streamlit/squads.py` (copy-not-mutate; `off` → bench taking `on`'s **priority slot**, `on` → XI; the 15 are
  unchanged) returning `(new_squad, issues)` where `issues` is the resulting XI's `legal_xi_issues`. A **"🔁
  Substitute"** expander on My Squad, **right below the pitch + card picker**: **Bring off** (a starter, position-
  sorted) + **Bring on** (a bench player) where **only legal swaps are listed** (`legal_ons` filters bench players
  whose swap returns no issues — so GK↔GK only, and outfield swaps that keep a legal formation) + a **Substitute →**
  button (`set_active_squad` + `st.rerun`; belt-and-braces re-check on apply). The old **"Set the bench (pick 4)"**
  multiselect is relabelled **"Set the whole bench at once (pick 4)"** with a caption pointing to 🔁 Substitute — kept
  as the bulk path. Reuses `set_bench` + `legal_xi_issues`; **session-state only, no engine/server change** (the
  one-xP + read-only invariants hold). **+5 tests:** 4 helper unit tests (legal outfield swap keeps the slot + the 15
  · a legal 3-5-2 formation change · refuses removing the only GK · a legal GK↔GK) + 1 AppTest (the control renders,
  the bench GK isn't offered for an outfield off, a swap updates the session bench). ruff clean. **939 → 944.**
  *(Baseline was 939 — Sprint 141 branding is parked/uncommitted, so it added no tests; the plan's "942" was an
  estimate.)* (US-352 next: the card picker pre-fills "Bring off".)
- **US-352 (picker pre-fill — the "both" wiring)** — the "👤 View a player's card" picker now **seeds** the
  Substitute control: picking a **starter** pre-fills **"Bring off"** to that player; picking a **bench** player
  shows a hint (*"…is on your bench — pick a starter to bring off, then choose them under Bring on"*). **Edge-
  triggered** on a `_sub_prefill_for` session marker (compares the picked id to the last-seen), so it seeds **once
  per pick** and you can still change "Bring off" freely afterwards; the seed writes `st.session_state["sub_off"]`
  before the selectbox is created (a valid option, since a starter is always in the XI). Display/session-state only.
  **+1 AppTest** (picking a starter pre-fills Bring off; picking a bench player shows the hint). ruff clean.
  **944 → 945.**

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Complete — both stories in. My Squad substitutions went from a clunky "re-pick all four" multiselect
to a direct **🔁 Substitute** control (bring off ↔ bring on, **only legal swaps offered**) with the pitch **card
picker pre-filling "Bring off"**. Session-state only — no engine/xP/server change; the one-xP + read-only invariants
hold.

**Shipped**
- **US-351** — `substitute()` helper (`set_bench` + `legal_xi_issues`, returns `(new_squad, issues)`) + the "🔁
  Substitute" control near the pitch (legality-as-filter: only issue-free bring-ons listed). The old "Set the bench
  (pick 4)" multiselect relabelled + kept below as the bulk path. +5 tests.
- **US-352** — the "👤 View a player's card" picker seeds "Bring off" (edge-triggered on `_sub_prefill_for`); a
  benched pick shows a hint. +1 test.

**Tests:** 939 → **945** (+6). ruff clean; CI-parity green.

**What went well:** faithful to the tester's intent within the platform limit; legality-as-filter means the control
can't produce an illegal XI; reused existing helpers (no new rules).

**Constraint navigated (again):** a working button *on* the hover card is impossible — the pitch is one static
`st.markdown` HTML block that can't call back to Python (the Sprint 139 wall). Named it up front, gave the owner the
three shapes that *do* fit, built the chosen one ("both": widgets + the picker bridge).

**Owner follow-up (browser smoke):** pick a starter on the picker → "Bring off" pre-fills → pick a bench player →
Substitute → the pitch + bench update; the only-GK case isn't offered; a benched pick hints.

**Lessons:** `docs/05_Sprints/Sprint142_Lessons_Learnt.md`.

---

### 📌 For Tony — confirm before I gate US-351

1. **No new ADR** — this extends **ADR-055** (My Squad edit) + the S139 picker; it reuses `set_bench` +
   `legal_xi_issues`, no engine/server change. Agree, or want a short ADR on the record? *(My rec: no ADR.)*
2. **Keep the old "Set the bench (pick 4)"** multiselect, tucked **below** the new control (bulk edits / declaring a
   whole bench)? *(My rec: keep it — some edits are faster in bulk; the Substitute box just becomes the lead path.)*
3. This is the **next sprint** (branding stays parked pending art)? *(My rec: yes — it's independent and a real
   tester pain.)*
