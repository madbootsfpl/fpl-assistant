# Sprint 149: The My Squad player-actions panel (ADR-108)

**Dates:** 2026-08-12
**Status:** ✅ Complete — US-365 + US-366 (ADR-108). 972 → 973 tests
**Capacity:** ~1 session (a `render_my_squad` re-layout + docs; helpers reused)
**Carried Over:** none

> **Direction (ADR-108):** consolidate the scattered My Squad player controls into **one inline "player-actions"
> panel** — a single owned-player selection → the **full card** + **👑 Make captain** + **🔁 Substitute**, together,
> on the pitch view. Absorbs the card picker + the Substitute expander; brings captain-setting onto the pitch (no
> tab-hop). Works desktop + phone/tablet (native widgets) and closes the desktop-only-hover mobile gap. **Transfer
> stays separate.** No engine/analytics change — `substitute()` / `set_captain()` / the card renderer are reused.

---

### 🔎 Verified at planning (on the code)

- **The scatter is real** (map): the card picker `"👤 View your player's card"` (`views/squads.py:365`), the 🔁
  Substitute expander (`:390-419`, keys `sub_off`/`sub_on`/`do_sub`), and Set-captain in a *different* sub-tab
  (`render_captain:704`, key `set_captain`) each **re-pick** a player; only the card→sub link exists today
  (`_sub_prefill_for`, `:379-383`).
- **The helpers are pure + reusable from anywhere:** `substitute(squad, off, on, by)` (`web_streamlit/squads.py:140`,
  returns `(new, issues)`) and `set_captain(squad, id)` (`:93`); `render_player_card(...)` (`player_card.py:176`) is
  the full (non-compact) card. So this is a **re-layout of `render_my_squad`**, not new analytics.
- **The pitch stays static** (`pitch.py:126`, one `st.markdown`) — the panel is the interaction, the pitch stays the
  display. The CSS hover popover (`pitch.py:88-92`) remains a desktop bonus.
- **Native widgets tap on mobile** — `st.selectbox` + `st.button` are the panel; the sub/captain selectboxes already
  worked on touch, just scattered.

---

### 🎯 Sprint Goal

On the My Squad pitch view: pick a player once → their **full card** + **Make captain** + **Substitute** appear in one
panel, working on desktop + phone/tablet — with the analytics unchanged and the suite green.

#### Success criteria
- [ ] **US-365 (the panel: selection + card + Make captain)** — replace the standalone `"👤 View your player's card"`
      picker with a single **"Select a player"** selector over the owned squad; on selection render the **full**
      `player_card` in the panel + a **"👑 Make captain"** `st.button` → `set_active_squad(set_captain(squad, id))` +
      `st.rerun()` (the action moved onto the pitch view; the Captain sub-tab's recommendation + its set control stay).
      Tests: selecting a player renders the card; **Make captain** sets `captain_id` (AppTest `set_value` + `click`).
- [ ] **US-366 (fold in Substitute)** — the selected player is the **bring-off**; reveal the **"Bring on"** picker
      (only legal swaps via `substitute()`'s issues) + a **"Substitute →"** confirm → `set_active_squad` + rerun; a
      **benched** selection flips to bring-them-*on*-for-a-starter. **Absorb** the standalone 🔁 Substitute expander;
      **retire** `_sub_prefill_for` (one selection drives it now). Tests: a legal sub applies; only legal bring-ons
      are offered; a benched pick flips the direction.
- [ ] **No drift** — Transfer expander + the Captain recommendation unchanged; **no** analytics/`decision_xp` change;
      ruff clean; the suite green (old picker/expander-label assertions updated to the panel).
- [ ] **Docs** — Help + Home copy (one panel, not "hover / separate substitute"); PROJECT_STATUS; Architecture;
      memory. ADR-108 already written (the gate). Backlog: the deferred **"My Squad v2: tap-the-pitch"** item.

---

### 🧭 Design sketch

`render_my_squad`, after the pitch:

```
─── ⚙ Player actions ───────────────────────────
Select a player ▾   [ Haaland · MCI ]
┌───────────────────────────────────────────────┐
│  [  full player card  ]                        │
│                                                │
│  👑 Make captain            (one click)        │
│  🔁 Substitute →  Bring on ▾  [ Substitute → ] │   (starter → bring-on list; benched → bring-on-for)
└───────────────────────────────────────────────┘
```

- **One selector** (owned players, `"WebName · TEAM"` labels) replaces the card picker; it is the panel's subject.
- **Full card** via `render_player_card` (fixtures + projected xP as today).
- **Make captain**: `st.button` → `set_captain`; disabled/label-noted if already captain.
- **Substitute**: reuse `substitute()` for the legal bring-on list + apply; starter vs bench flips the direction.
- **Removed:** the separate card picker + the Substitute expander + the `_sub_prefill_for` seeding.

**Definition of Done (3-part):** automated tests (panel render + Make-captain + Substitute) + a manual smoke (pick a
player on desktop *and* a narrow viewport → card + both actions work) + docs.

**Out of scope (ADR-108):** Transfer in the panel; the Captain sub-tab; and the **custom JS tap-the-pitch** component
(deferred — its own spike + ADR, post-GW1, feedback-driven).

---

### 📋 Sprint Review

**Delivered — both stories; the golden page's controls are now one panel. 972 → 973 tests; ruff clean.**

- **US-365 (panel: selection + card + Make captain)** — a new **⚙ Player actions** panel: one **"Select a player"**
  selector (replaces the card picker) → the full card + a **👑 Make captain** button (reuses `set_captain`; the
  action moved onto the pitch — no more re-pick + tab-hop to the Captain sub-tab). Built alongside the old Substitute
  expander (kept working, pre-filled off the new selector) so the commit stayed shippable.
- **US-366 (fold in Substitute)** — the selected player is one side of the swap: a **starter** → *"take off — bring
  on"* (legal bench players); a **bench** pick → *"bring on — take off"* (legal starters to drop) + **Substitute →**.
  **Retired** the standalone Substitute expander, the `sub_off`/`sub_on` two-selectbox dance, and the
  `_sub_prefill_for` seed — one selection *is* the pre-fill now. Reuses `substitute()` (still only legal swaps).

**Reused, unchanged:** `substitute()` / `set_captain()` / the card renderer — no analytics/`decision_xp` change.
**Native `selectbox`+`button` → taps on phone/tablet**, giving mobile the full card the desktop-only hover never
could. **Transfer stays its own expander**; the **Captain sub-tab keeps its recommendation** (both call `set_captain`).

**Definition of Done:** ✅ tests (panel render · Make-captain sets `captain_id` · both substitute directions apply) ·
✅ manual smoke (rendered card + captain + substitute on the AppTest page) · ✅ docs (ADR-108 gate; Help step-2 rewrite;
PROJECT_STATUS; Architecture; memory). **Deferred:** the custom JS **tap-the-pitch** component (its own spike + ADR,
post-GW1, feedback-driven — Backlog).

### 🧠 Lessons
*(see `Sprint149_Lessons_Learnt.md`)*
