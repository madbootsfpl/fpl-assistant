# Architectural Decision Record: The My Squad player-actions panel (consolidate card · captain · substitute)

**Decision ID:** ADR-108
**Date:** 2026-08-12
**Status:** Accepted
**Superseded By / Replaces:** **extends ADR-055** (My Squad edit), **ADR-084** (the rich player card, S139), and
**ADR-105** (the My Squad / Squad Lab split). Consolidates controls those sprints added piecemeal (the card picker
S139, the 🔁 Substitute S142, the Set-captain in the Captain tab). **No** analytics/engine/`decision_xp` change — the
`substitute()` / `set_captain()` helpers and the card renderer are reused as-is; this is a UX/IA consolidation of the
pitch view.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

**My Squad is the golden page**, and its player interactions have grown scattered. Picking a player happens in
**three disconnected places**, and captaining one means **leaving the pitch entirely**:

- **"👤 View your player's card"** — a selectbox that opens the full card *(pitch view, `render_my_squad`)*.
- **🔁 Substitute** — a separate expander where you *re-pick* the player to bring off *(same view)*; linked to the
  card picker only one-way via a `_sub_prefill_for` marker.
- **"Set as captain"** — a selectbox where you *re-pick the player again*, over in the **Captain sub-tab**
  (`render_captain`).

So to look at Haaland's card and then captain him, a user picks him twice and switches tabs. **Tester feedback
(2026-08-12, wave 2):** FFH pops a **menu on clicking a player** — *full card · substitute · make captain* — in one
place; the real want underneath is *"open the full card"* rather than cramming detail into the truncated hover.

**The platform wall (S139/142):** our pitch is **one static `st.markdown` HTML block** — it **cannot fire a Python
callback**, so we can't literally click a shirt. But we can collapse the scatter to **one selection → one actions
panel**. And there's a **mobile gap**: the rich card is currently reachable on the pitch only via the **CSS `:hover`
popover**, which **doesn't exist on touch devices** — so phone/tablet users can't get the card at all today.

#### Decision Drivers
- **One player, one place** — a single selection should drive card + captain + substitute; stop re-picking.
- **The full card is the point** — make the rich card the primary way to inspect a player (not the truncated hover).
- **Mobile-first-ish** — a tapped selector → panel works on phone/tablet (native widgets); it *closes the hover gap*.
- **Clean, modern, navigable** (the standing design principle) — a unified panel, not three stacked expanders.
- **Reuse, don't rewrite** — the analytics + `substitute()`/`set_captain()`/card renderer are unchanged.

---

### ✅ Decision

**Add one inline "player-actions" panel to the My Squad pitch view (`render_my_squad`): a single owned-player
selection → the full player card + the actions (Make captain · Substitute) together.**

**1. One selection.** Replace the standalone "👤 View your player's card" picker with a single **"Select a player"**
selector over the owned squad. That selection is the panel's subject — no separate pick for each action.

**2. The full card.** On selection, render the **full** `player_card` (not the compact hover body) directly in the
panel — this is the tester's *"open the full card"*, and on phone/tablet it's the **first** way to see the card at all
(the hover popover is desktop-only and stays as a bonus, not the only path).

**3. The actions, inline.** Below the card, an actions row scoped to the selected player:
- **👑 Make captain** — a one-click `st.button` → `set_captain(squad, id)` (the action **moved into the pitch view**;
  no more tab-hop). The Captain **sub-tab keeps its recommendation card** (the "who *should* I captain" analysis + its
  own set control) — that's a different job (analysis), not a duplicate to remove.
- **🔁 Substitute** — the selected player is the **bring-off**; the panel reveals the **"Bring on"** picker (only
  *legal* swaps, via `substitute()`'s issues check) + a **Substitute →** confirm. A **benched** selection flips it
  (bring this player *on* for a starter). The standalone Substitute expander is **absorbed**; the `_sub_prefill_for`
  one-way link is **retired** (one selection now drives it directly).

**4. Transfer stays separate.** Transfer is a heavier flow (budget · filters · bring-in) and was **not** in the
tester's menu — folding it in would bloat the panel. It keeps its own expander / the Transfer sub-tab (unchanged).
*(The pre-existing duplicate manual-transfer inside `render_my_squad` can be revisited later; not this ADR.)*

**5. Native widgets → all devices.** The panel is `st.selectbox` + `st.button` — real form controls that **tap on
phone/tablet and click on desktop** alike. (The substitute + captain selectboxes already worked on mobile; A6 just
unifies them and adds the card path.)

**6. What this is *not*.** Not an engine/analytics change (helpers + card reused). Not literal tap-the-shirt (the
static pitch can't callback — see the deferral). Not a Transfer rework. Not removing the Captain sub-tab's
recommendation.

---

### 🔀 Alternatives Considered

- **A `st.popover` "menu"** (closest to FFH's pop-up). Rejected — a popover can't hold the **full** rich card (it
  opens cramped, defeating the core ask), and every action costs an extra click.
- **Minimal: keep the three expanders, just share one selection.** Rejected — lowest-risk, but the pitch view still
  reads as three stacked expanders; it doesn't deliver the *clean single panel* the principle calls for.
- **Build the custom JS tap-the-shirt component now.** **Deferred** (see below) — the right long-term interaction, but
  a bigger bet that shouldn't gate this win or land in the GW1 crunch.

---

### 🧭 Consequences

**Positive**
- **The golden page gets simpler** — one selection → card + every action; no re-picking, no tab-hop to captain.
- **Mobile gains the card** — a tapped selector → full card closes the desktop-only-hover gap.
- **Reuses everything** — `substitute()`, `set_captain()`, the card renderer, the analytics: all unchanged.
- **A foundation, not a stopgap** — a future tap-the-pitch component reuses **~90%** of this (the whole panel); only
  the selection *input* (dropdown → tap) would change.

**Negative / risks (mitigations)**
- **A real refactor of `render_my_squad`** — the card picker + Substitute expander are restructured into the panel.
  *Mitigation:* the underlying helpers are untouched; it's a re-layout, gated + tested. Tests that assert the old
  picker/expander labels get updated.
- **Two ways to set the captain** (pitch panel + Captain tab). *Mitigation:* intentional — different jobs (inspect a
  player vs read the recommendation); both call the same `set_captain`.
- **Muscle-memory churn** on the golden page. *Mitigation:* it's simpler, not just different; Help/Home copy updated.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (a gated sprint — Sprint 149): the unified panel on `render_my_squad` — one selector → the full
  card + **👑 Make captain** + **🔁 Substitute** (bring-on picker + confirm); absorb the card picker + Substitute
  expander; retire `_sub_prefill_for`. Transfer + the Captain recommendation unchanged. Docs (PROJECT_STATUS,
  Architecture, Help/Home, memory).
- **Deferred by this ADR — "My Squad v2: tap-the-pitch" (a *committed* next, not vague).** A custom **Streamlit
  component** so a **tap on a shirt** returns the player id → opens this same panel. Deferred deliberately: (a) it
  introduces a **front-end build toolchain** into a pure-Python project — an architecture change that can't be
  AppTested, so the golden page loses coverage; (b) **GW1 (2026-08-21) is ~9 days out** — don't destabilise the golden
  page pre-kickoff; (c) it deserves its **own spike + ADR** — *full custom React component* **vs** a *lightweight
  click-detector reusing `pitch.py`'s HTML with per-kit ids* + a **Community-Cloud deploy check** (the spike could
  more than halve the cost). Sequenced for the **post-GW1 settle**, and **feedback-driven** — ship the panel, watch
  the testers; if "I want to tap the shirt" stays the top ask, that's the green light. Captured in `docs/Backlog.md`.
