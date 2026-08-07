# Architectural Decision Record: A styled (CSS) pitch view for My Squad

**Decision ID:** ADR-084
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** revisits the informal Sprint-062 *"native cards, no custom CSS, robustness
first"* pitch decision (recorded only in `web_streamlit/pitch.py`'s docstring — never a formal ADR). This is
the first formal decision on the pitch's presentation. Triggered by tester feedback.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester: *"Review MySquad graphic, redesign closer to the **Fantasy Football Hub** look — it looks like a **poor
cousin** at the moment."* The current My Squad pitch (Sprint 062) is a **native `st.container` card-grid** — a
deliberate "robustness first, no custom CSS" call at the time. It's functional but visually plain: bordered
cards in columns, not a football pitch.

**Verified in code:** this Streamlit (1.61.1) **preserves** a `<style>` block + `<div>`/`<img>` through
`st.markdown(…, unsafe_allow_html=True)` (not sanitised), and the emitted HTML is inspectable via `AppTest`'s
`.markdown` — so a styled pitch is both feasible **and** still headless-testable. The pitch is **display-only**:
every edit control (swap · reorder · rename · set-bench · download) is a *separate* Streamlit widget rendered
after `render_pitch`, so restyling the graphic can't affect interactivity. **US-255** now resolves every
player to a photo-or-club-shirt image, so "kits on a pitch" renders for everyone.

#### Decision Drivers
- **Look the part** — a green football pitch with players in formation (the FFH style), a clear visual jump.
- **Keep every fact** — name · (C) · £ · xP · opponent · crowd/set-piece flags · sub role, all still shown.
- **Don't risk interactivity** — the edit controls stay native widgets; only the (display-only) graphic
  changes.
- **Stay testable + themeable** — one self-contained HTML block, no JS, readable in light + dark, responsive.

---

### ✅ Decision

**Render the My Squad pitch as one self-contained HTML/CSS block** (`render_pitch` →
`st.markdown(html, unsafe_allow_html=True)`), replacing the native card-grid:

**1. The pitch (US-257).** A `<div class="fpl-pitch">` with a **green gradient background** + subtle field
markings, laid out as **formation rows** (GK/DEF/MID/FWD, centered flex rows) plus a **bench strip**. Each
player is a **kit card** (`.kit`): the photo/shirt `<img>`, the **name**, an **xP chip**, and **£m · next
opponent (H/A)**. Every text value is `html.escape`d. Relative units + `flex-wrap` so it reflows on narrow
screens; a pitch-green surface with light cards that read on both Streamlit themes. No JavaScript.

**2. Badges, flags & polish (US-258).** The **(C) captain armband** (a corner badge), the **sub badges**
(🔁 1st/2nd/3rd/GK, from the existing `bench_roles`, priority-ordered), and the **crowd + set-piece flags**
(reusing `crowd_flags`/`set_piece_flags`) on each card; spacing/typography polish; a missing image degrades
cleanly (US-255 gives a shirt).

**3. Display-only, interactivity untouched.** `render_pitch` keeps its signature (`xi, bench, *, captain_id,
xp_by_id, photos, next_opp, bench_roles`); the swap/reorder/rename/download widgets are unchanged. Tests read
the pitch via `AppTest.markdown` (names, xP, flags, badges) instead of `st.caption`.

---

### 🔀 Alternatives Considered

- **Keep polished native cards** (green-tinted, bigger image, xP chip). Rejected (owner steer) — a clear
  improvement but still a card grid, not the FFH pitch the tester asked for.
- **A full SVG / single rendered image of the pitch.** Rejected — maximum fidelity but heavy, and it can't
  interleave the live data cleanly; the HTML/CSS block gets the look with far less complexity.
- **`st.components.v1.html` (an iframe).** Rejected — full HTML control but a fixed-height iframe that can't
  size to content or sit inline with the surrounding Streamlit widgets; `st.markdown` composes better.
- **Client-side interactivity (drag-drop to reorder).** Rejected — needs JS/components; the reorder ⬆/⬇ +
  swap widgets already do this natively. The pitch stays display-only.

---

### 🧭 Consequences

**Positive**
- The My Squad pitch looks like a football pitch (the tester's ask); every fact is retained.
- Display-only + a single contained block → the edit controls and analytics are untouched; still testable
  (via `.markdown`) and theme-aware.
- Reuses US-255's photo-or-shirt images — kits on a pitch, no new data.

**Negative / risks (mitigations)**
- **Custom CSS is less robust than native** (Streamlit could restyle/sanitise in future) → keep it **one
  self-contained block, no JS**, scoped class names, and **display-only** (a visual regression can't break a
  decision or a control). The native controls remain the interactive surface.
- **Readability across themes** → a green pitch with light cards reads on both; colours chosen for contrast,
  not the Streamlit theme variables.
- **Escaping** → every text value is `html.escape`d so a name with `&`/`<`/`'` can't break the markup.

---

### 📊 Validation

Verified: `st.markdown(unsafe_allow_html=True)` keeps the `<style>`/`<div>`/`<img>` (Streamlit 1.61.1) and the
HTML is readable via `AppTest.markdown`. Acceptance: the My Squad pitch renders one HTML block with the
formation rows + every player's **name + xP**; the **set-piece emojis** appear for each owned taker; the
**(C)** armband + **sub badges** appear; the edit controls still work; light + dark both read; existing **663**
tests stay green (the caption-based pitch test rewired to `.markdown`); ruff clean.
