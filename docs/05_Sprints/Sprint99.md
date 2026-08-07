# Sprint 099: Redesign the My Squad pitch — an FFH-style green pitch

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a styled HTML/CSS pitch in place of the native card-grid)
**Carried Over:** none

> **Direction (tester feedback):**
> *"Review MySquad graphic, redesign closer to this look on **Fantasy Football Hub**. It does not need to
> mimic, but it looks like a **poor cousin** at the moment."* (An FFH pitch screenshot was attached.)
>
> **Owner steer (this planning):** go for the **full CSS pitch (FFH-style)** — a green football pitch with
> players laid out in formation as kit cards.

---

### 🔎 Verified at planning

- **The current pitch is a native card-grid** (`web_streamlit/pitch.py`, Sprint 062) — `st.container(border)`
  cards in `st.columns` rows. That was a deliberate *"robustness first, no custom CSS"* owner call at the time
  (recorded only in the module docstring — **no formal ADR**), which this sprint revisits.
- **A styled pitch is feasible in this Streamlit** (1.61.1) — verified that `st.markdown(…,
  unsafe_allow_html=True)` **keeps** a `<style>` block + `<div>`/`<img>` (not sanitised away), and the HTML is
  inspectable via `AppTest`'s `.markdown` (so the redesign stays headless-testable).
- **The data is all in hand** — each card already has name · (C) · team · £ · xP · next opponent (H/A) · crowd
  flags · set-piece duty · sub role. **US-255** now resolves every player to a **photo or club-shirt** image,
  so "kits on a pitch" (the FFH look) renders for everyone.
- **The pitch is display-only** — every edit control (swap · reorder ⬆/⬇ · rename · set bench · download) is a
  **separate Streamlit widget rendered after** `render_pitch`, so restyling the graphic **doesn't touch
  interactivity**. Only the pitch's own presentation changes.
- **One test reads pitch content from `st.caption`** (`test_my_squad_pitch_cards_show_set_piece_attributes`) —
  it moves to reading the HTML blob (`.markdown`) after the redesign.

---

### 🎯 Sprint Goal

**Objective:** replace the My Squad card-grid with a **green football pitch** — players laid out by formation
(GK/DEF/MID/FWD) as compact **kit cards** (image · name · xP · £ · opponent · (C) armband · sub badges ·
flags), with a bench strip — a clear visual jump toward the FFH look, theme-aware + responsive, keeping all
the current information and all the edit controls.

#### Success Criteria
- [ ] **US-257 (the pitch + kit cards, ADR-084)** — `render_pitch` emits a single self-contained HTML/CSS
      block: a **green pitch** (gradient + subtle markings) with **formation rows** (GK/DEF/MID/FWD, centered)
      and a **bench strip**; each player a **kit card** — the photo/shirt image, the **name**, an **xP chip**,
      **£m**, and the **next opponent (H/A)**. Names HTML-escaped. Theme-agnostic (readable in light + dark),
      responsive (rows wrap on narrow screens). No JS; display-only.
- [ ] **US-258 (badges, flags & polish)** — the **(C) captain armband**, the **sub badges** (🔁 1st/2nd/3rd/GK,
      priority-ordered), and the **crowd + set-piece flags** on each card; readability/spacing polish; graceful
      when an image is missing. Update the affected test to read the pitch HTML.
- [ ] **No drift** — display-only; the edit controls + analytics unchanged; existing **663** stay green (the
      pitch-content test rewired to `.markdown`); ruff clean.
- [ ] Docs: ADR-084 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 🧭 Design sketch

**US-257 (ADR-084).** Rewrite `pitch.py` to build one HTML string and render it with a single
`st.markdown(html, unsafe_allow_html=True)`:
- A `<style>` block (scoped class names, e.g. `.fpl-pitch …`) — a green `linear-gradient` background + a faint
  centre line/circle (a CSS pseudo-element or an inline SVG data-URI), rounded corners, padding.
- `<div class="fpl-pitch">` → one `<div class="row">` per occupied position (GK→FWD), each a flex row of
  `<div class="kit">` cells; then a divider + a `<div class="bench">` strip.
- `<div class="kit">`: `<img src="{photo_or_shirt}">` + `<div class="name">` + `<div class="xp">{xp}</div>` +
  `<div class="meta">£{price} · {opp}</div>`. `html.escape` every text value.
- Relative units + `flex-wrap` so it reflows; a `max-width`; `img` capped. Colours chosen to read on both
  Streamlit themes (a green pitch with light cards).

**US-258.** Add to each kit: the **(C)** armband (a corner badge), the **sub badge** for bench cards
(🔁 1st/2nd/3rd/GK, using the existing `bench_roles`), and the **crowd + set-piece flags** (reuse
`crowd_flags`/`set_piece_flags`). Tidy spacing/typography; ensure a missing image degrades cleanly (US-255
already gives a shirt). Rewire `test_my_squad_pitch_cards_show_set_piece_attributes` to assert the emojis in
the pitch **markdown** (per taker), and add a test that the pitch renders formation rows + names.

**Deferred:** reusing the styled pitch on the **Build** preview (currently a table) — a later consistency win;
any animation/drag-drop (out of scope — Streamlit + no JS).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-257 | **The FFH-style pitch + kit cards** — a green CSS pitch, formation rows + bench, image/name/xP/£/opponent. ADR-084. | High | ⬜ To do | ~⅔ session |
| US-258 | **Badges, flags & polish** — (C) armband · sub badges · crowd/set-piece flags · theme/responsive polish; rewire the pitch test. | High | ⬜ To do | ~⅓ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the My Squad pitch renders one HTML block containing the formation and every player's
   **name + xP** (AppTest `.markdown`); the **set-piece emojis** appear for each owned taker; the **(C)** and
   **sub badges** appear. Existing **663** stay green (the caption-based pitch test rewired to `.markdown`).
2. **Manual smoke** — Squads → My Squad shows a green pitch with the XI in formation + a bench strip; kits/
   photos render (shirt fallback where a photo is missing); the captain shows an armband; subs are numbered;
   flags show; it reads in light **and** dark; it reflows narrow. The swap/reorder/rename/download controls
   still work below.
3. **Docs updated** — ADR-084 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 📝 Session Progress Log

**US-257 — the FFH-style pitch + kit cards (ADR-084).** ✅ Done.
- `pitch.py` rewritten: `render_pitch` emits **one self-contained HTML/CSS block** (`st.markdown(...,
  unsafe_allow_html=True)`) — a **green pitch** (mow-stripe gradient + a faint centre circle, inset white
  border) with **formation rows** (GK/DEF/MID/FWD) + a **bench strip**. Each player is a **kit card** (`.kit`):
  the photo/club-shirt `<img>`, the **name** (+ a gold **(C)**), an **xP chip**, **£m · next opponent (H/A)**,
  and the **crowd + set-piece flags**; bench cards carry their **🔁 sub label**. Every text value is
  `html.escape`d. Relative units + `flex-wrap` (reflows narrow); a green surface + light cards that read on
  both Streamlit themes. No JS; display-only — the edit controls are untouched separate widgets.
- Kept all the info the old card-grid showed (no regression); `render_pitch`'s signature is unchanged.
- **Tests:** rewired the 3 pitch-content tests from `st.caption` → the HTML blob (`AppTest.markdown`): the
  layout test asserts `fpl-pitch` + ≥11 `.kit` cards (no dataframe); the set-piece test counts the ⚽/🚩/🎯
  emojis in the pitch markdown = the squad's total set-piece flags; the bench-subs test finds "🔁 1st/GK sub"
  in the blob. **663** green, ruff clean.
- **Manual smoke (RoboTS + B.Fernandes ©):** a green pitch, 4 formation rows, 15 kit cards, the captain's gold
  (C), 5 set-piece emojis, xP chips — renders without error. (US-258 turns (C)/subs into proper badges + more
  polish.)

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
