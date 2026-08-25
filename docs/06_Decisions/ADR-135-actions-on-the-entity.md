# Architectural Decision Record: Put actions on the entity, to take widgets off the page

**Decision ID:** ADR-135
**Date:** 2026-08-25
**Status:** 🚧 **Proposed — awaiting the owner gate.** Nothing built beyond `spikes/188-actions-on-the-shirt`,
which proved the mechanism and measured what it buys.
**Superseded By / Replaces:** Completes the arc ADR-108 opened (the player-actions panel) and ADR-133 delivered
the input for (tap-the-pitch). Applies the same idiom to the ADR-134 league scan.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

**This is a density change, not an interaction feature.** The owner's framing, and the standard it should be
judged against:

> Reduce as much clutter on each page as possible so it can be embedded in the player / the team / the entity.
> This will reduce the real estate needed and improve the experience on both mobile and desktop. **We are not
> doing this because we can.**

My Squad's density has been a tester complaint twice (US-423 condensed the chrome *above* the pitch). Below the
pitch, measured on the live page with a player selected, **six or seven widgets exist purely to act on one
selected player**: `Select a player` · `⚔️ Boot Battle — pool` · `Club` · `compare with…` · `👑 Make X captain` ·
`🔁 Bring/Take X…` · `Substitute →`. At roughly 76-90px each once labels are counted, that is most of a phone
screen spent on controls for a single player.

ADR-133 shipped the input that makes another arrangement possible — a tap already resolves to a player id.

---

### 🔬 What the spike established

**One tap can carry both the action and the player.** `click_detector` returns the clicked anchor's id as a
**string**, from any anchor in the markup, so `cap:123` encodes both halves. No new dependency.

**One structural constraint, and it is the only real change needed.** HTML forbids `<a>` inside `<a>`, so the
card cannot stay wrapped in a single anchor. The select-anchor and the action anchors must be **siblings**.

**What comes off the page: three to four widgets, ~250-350px** on an 844px screen.

**What cannot come off, and it is the important half.** *You can only tap what is on the pitch.* Boot Battle
exists to compare against players you do **not** own (All · By club), and no shirt-level interaction reaches
them.

---

### ✅ Proposed Decision

**1. The division of labour — the line everything else follows.**

> **The entity owns actions on things you have. The pickers own finding things you don't.**

The pickers therefore do not disappear; they stop being the *default* path and become the **discovery** path. A
design that tries to move everything onto the shirt will re-add a picker somewhere worse.

**2. Actions appear on the *selected* card only — not on all fifteen.**

This is the decision that keeps it a *density* change. Always-visible actions would take widgets off the page
by putting three icons on every one of fifteen cards, trading page height for pitch noise and netting little.
Hover-only would be cleaner at rest but is a **desktop idiom on a surface whose complaints are mobile**, and a
hidden control is one users do not know exists — the lesson from ADR-133's invisible fallback, learned within
an hour of shipping it.

So: **tap a shirt → it becomes the selected card and shows `©` `🔁` `⚔️` inline → tap one.** Same two taps as
today (select, then act), minus the scroll to a widget below the fold, and with **nothing permanent added** to
the pitch.

**3. Two-tap flows must be visibly escapable.** `🔁` and `⚔️` arm an action that needs a second player. The
armed state is shown on the card and in one caption (*"pick who comes off"*), and tapping the armed action
again — or the same shirt — cancels. A flow you can enter and not leave is worse than the picker it replaced.

**4. The same idiom one level up.** The ADR-134 league scan is a row per club with a selectbox beneath it —
structurally identical. A `sel:ARS` anchor on the row replaces that selectbox with a tap, in the same change,
so the app does not end up with a pitch that taps and a table that does not.

**5. The dropdown stays** (ADR-133's rule, unchanged): AppTest drives it, keyboard users need it, and a
component failure must still leave a usable page.

---

### 📏 How this gets judged

Because it is a density change, the acceptance criterion is a **number, not an impression** — and it is
testable, since `AppTest` can count widgets:

| | before | target |
|---|---|---|
| widgets below the pitch serving one selected player | 6-7 | **3** (the discovery pickers only) |
| reclaimed vertical space (est., phone) | — | **250-350px** |
| taps to captain a player | 2 + a scroll | **2, no scroll** |

**A test asserts the widget count does not creep back.** If a later change re-adds a per-player widget below
the pitch, that test fails and the reason gets re-argued rather than forgotten.

---

### 🔀 Alternatives Considered

- **Always-visible actions on every card.** Rejected above: trades page height for pitch noise.
- **Hover-only actions.** Rejected: desktop-only on a mobile-complaint surface, and invisible affordances are
  the mistake ADR-133 just made.
- **A popup menu on tap** (the literal FFH/fplapex idiom). Rejected as the *primary* form: a menu is a third
  surface to lay out, and on a phone it either covers the pitch or needs its own dismissal. Inline actions on
  the selected card get the same result with less machinery. *(Revisit if the inline row proves too cramped on
  the smallest screens.)*
- **Leave it; keep shrinking captions.** Rejected — US-423 already did that, and the complaint recurred. The
  widgets are the real estate.

---

### 🧭 Consequences

**Positive** — attacks the density complaint at its source; no new dependency; two taps instead of two taps
plus a scroll; the idiom generalises to any entity row, which is what the owner asked for; the target is a
number a test can hold.

**Negative / risks (mitigations)** — the selected card gets busier while selected (*mitigation:* it is one card,
only while selected, and it replaces widgets that were bigger); two-tap flows can strand a user
(*mitigation:* decision 3 — visible armed state, tap-again to cancel, and it is the first thing to test); the
pitch markup grows a second anchor per card (*mitigation:* mechanical, spike-verified, and `pitch_html` is
already unit-tested directly since ADR-133); Boot Battle stays a picker, so the page does not go quiet
(*mitigation:* that is the honest division of labour, stated rather than discovered).

---

### 🧾 Status & follow-ups

- **Proposed — needs the owner gate.** Two answers wanted: **(1)** the division of labour in §1 as the
  governing rule, and **(2)** actions-on-selected-card-only rather than always-visible or hover.
- **If accepted:** the sibling-anchor restructure in `_kit_html`; `sel:`/`cap:`/`sub:`/`cmp:` dispatch in
  `tap.py`; the armed-state caption; the same on the league-scan rows; removal of the widgets §📏 names; a
  widget-count test pinning the target; before/after measured and recorded; 3-part DoD.
- **Not this ADR:** reaching off-pitch players from a shirt — it cannot be done, and the design says so.
