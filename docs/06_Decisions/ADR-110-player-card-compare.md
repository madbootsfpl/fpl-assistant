# Architectural Decision Record: Compare two players on the card (same-position, winner-highlighted)

**Decision ID:** ADR-110
**Date:** 2026-08-12
**Status:** Accepted
**Superseded By / Replaces:** **extends ADR-084** (the player card). Display-only — reuses the card's stat catalog +
`decision_xp`; **no** new xP math beyond a per-stat winner diff computed from existing values.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester (2026-08-12, wave 2 — item **UX H**, with an image): on the player card, add a **side-by-side comparison of
two players** to help decide between them. Today the Card view shows **one** player.

**Grounding (map):** the Players page's *history* view already has a **"Compare with (optional)"** second picker
(`render_history` + `align_seasons`) — a pattern to mirror. `render_card` already computes `decision_xp` over **all**
players (so a compare target's projected xP is free). But the card's stat rows are **position-specific** (`_stat_rows`'
`order` differs per FWD/MID/DEF/GK, and drops `None` stats), so an **aligned** comparison only works cleanly for two
**same-position** players. There's **no per-stat winner analytics** — `ask`'s compare gives only an overall
higher-xP winner + text — so a per-stat highlight is built from the card's existing stat values.

#### Decision Drivers
- **A real comparison, not two cards** — call out **who wins each stat** so the choice is obvious (the tester's intent).
- **Same-position = aligned** — compare like-for-like; the rows line up and the winner is meaningful.
- **Reuse** — the card's stat catalog + `decision_xp`; mirror the existing "Compare with" picker.
- **Easy search** — a typeable picker (owner ask), scoped to same-position players.
- **Clean, not gimmicky** — a tidy A · stat · B grid with a subtle winner tint; ownership stays neutral.

---

### ✅ Decision

**Add a same-position, winner-highlighted two-player comparison to the Players Card view.** Pick player A, then a
**🔍 "Compare with"** picker (typeable — Streamlit selectboxes filter as you type) scoped to **same-position** players
(A excluded). With a compare target chosen, render a **merged comparison** in place of the single card:

- **Two headers** — each player's photo · Team · Pos · £price · name · **projected xP** (the xP winner tinted) ·
  fixtures (the Card view's FDR pills).
- **Aligned stat rows** — one row per stat in that position's order: **A's value · label · B's value**, with the
  **better value tinted** (a ● / colour). Direction per stat: most **higher-is-better** (points, ppg, goals, xGI, xG,
  xA, DefCon/90, CBI, tackles, recoveries, ICT, value, minutes); **xGC lower-is-better**; **ownership neutral** (no
  "better" — differential vs template is a preference). Ties + a missing value → no highlight (show `—`).

**Implementation shape (display-only):**
- **Expose the stat keys/raw values** — a small refactor so the card's per-stat catalog yields `(key, label, raw,
  formatted)`; `_stat_rows` keeps returning `(label, formatted)`, and the compare uses `raw` for the winner + `key`
  to align two players. Compare **raw numerics**, display **formatted** strings.
- **`compare_card_html(a, b, *, …)`** in `player_card.py` — the two headers + the aligned grid; reuses `CARD_CSS`
  (extended with compare styles). A `render_player_compare(...)` Streamlit wrapper.
- **Wire the Players Card view** — the 🔍 second picker (same-position options); on a pick → `render_player_compare`
  instead of the single card. Both players' xP come from the already-computed `xp` dict; the target's fixtures from
  one more `_card_fixtures(store, b_team)` read (no new xP math).

**Where:** the **Players Card view** (primary). The **⚙ Player-actions panel** "compare with…" (My Squad, pool =
the 15 owned) is a **follow-on**, not this ADR.

**What this is *not*:** not cross-position compare (misaligned — the picker is same-position only); not new analytics
(the winner is a diff of existing values); not a change to the single-card path (unchanged when no compare target).

---

### 🔀 Alternatives Considered

- **Two full cards side by side** (reuse `card_body` twice). Rejected as the primary — works for any two players and
  is cheap, but it's "two cards on screen", not a comparison; no winner cue. (It's the fallback if merged proves
  fiddly.)
- **Cross-position compare.** Rejected — the stat rows don't align; a GK-vs-FWD grid is meaningless. Picker is
  scoped same-position.
- **A free-text search box / custom search component.** Unnecessary — `st.selectbox` already filters as you type; a
  🔍 label makes it discoverable, zero new component.
- **Reuse `ask`'s compare.** Its only structured output is one overall xP winner + a text table — no per-stat
  winners — so not reusable for the grid; we compute the per-stat diff from the card values instead.

---

### 🧭 Consequences

**Positive**
- A genuine decision aid — the better value in each stat is obvious at a glance.
- Reuses the card's catalog + `decision_xp`; the single-card path is untouched.
- The typeable same-position picker keeps it fast and always-aligned.

**Negative / risks (mitigations)**
- **The `(key, label, raw, formatted)` refactor** touches `_stat_rows`. *Mitigation:* keep `_stat_rows`' external
  shape identical (`(label, formatted)`); the raw/key are additive; existing card tests stay green.
- **Missing stats / ties** — same-position players can still differ in which stats are present. *Mitigation:* align
  by **key**, show `—` for a missing side, no highlight on ties/missing.
- **Width on mobile** — two headers + a 3-column grid. *Mitigation:* a compact grid; headers stack / the grid stays
  narrow; smoke on a narrow viewport.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (Sprint 151): **US-369** the compare renderer — expose `(key, raw)` in the catalog, a
  `compare_rows(a, b)` (aligned, per-stat winner via a direction map) + `compare_card_html` / `render_player_compare`,
  with deterministic tests. **US-370** wire the Players Card view — the 🔍 same-position "Compare with" picker → the
  merged compare; a preview for sign-off. Docs (Help; PROJECT_STATUS; Architecture; memory).
- **Follow-on (not this ADR):** the ⚙ panel "compare with…" on My Squad (pool = owned 15).
