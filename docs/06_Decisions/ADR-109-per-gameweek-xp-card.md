# Architectural Decision Record: Per-gameweek xP in the player card

**Decision ID:** ADR-109
**Date:** 2026-08-12
**Status:** Accepted
**Superseded By / Replaces:** **extends ADR-084** (the rich player card) and **ADR-032** (per-GW xP `by_gameweek`).
Display-only — **no** xP math (the data is already computed). Brief by owner's request (the tester supplied an exact
target image).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester (2026-08-12, wave 2 — item A5, with an image): under a shirt on My Squad, show the **per-gameweek points** —
each of the next weeks as its own column with the **xP on top** and the **fixture below** (e.g. Mbeumo: `5.1` HUL (A) ·
`6.2` IPS (H) · `4.5` EVE (A)) — and a **Total** when more than 3 GW are selected. Today the card shows only a single
horizon-total chip; the per-GW split is buried in the Health tab's monospace table.

**The data is free.** `decision_xp` already returns each player's `by_gameweek` (`{event: xP}`) + `gameweeks`, and
`render_my_squad` already materialises `by_gameweek_by_id` (uses it only for the captain bonus, discards the rest).
`team_schedule(upcoming, team)` gives per-fixture `{event, opponent, venue, difficulty}`. Aligning xP to fixture by
**event number** is exact. So A5 is **pure rendering**.

#### Decision Drivers
- **Match the tester's image** — a per-GW row in the card: xP over fixture, per gameweek.
- **One component, both surfaces** — `card_body` drives the pitch **hover popover** *and* the new **⚙ panel card**
  (ADR-108), so one change lands in both (desktop hover + all-device panel).
- **Zero xP risk** — reuse `by_gameweek`; display-only.
- **Clean, not gimmicky** — a tidy row in the roomy card, **not** three numbers crammed onto the tiny kit chip.

---

### ✅ Decision

**Turn the card's fixture row into a per-gameweek row** (in `card_body`, ADR-084): for the next **up-to-3**
gameweeks, a column each showing **xP (bold, top)** + **opponent (venue)** (FDR-tinted, below) — matching the image.
Shows in **both** the hover popover **and** the ⚙ panel card (both call `card_body`).

**No Total column** — the tester's original ask included a Total when horizon >3, but on **previewing it the owner
dropped it** (2026-08-12): the three individual weeks read cleaner and less cluttered, and the **shirt's xP chip
already shows the horizon total**, so no information is lost. The card is always "up to 3 GW columns, no total".

- **Data path:** a shared `fixtures_by_id` builder in `render_my_squad` — per owned player, `team_schedule()`'s
  next-3 fixtures, each with `xp = by_gameweek_by_id[id].get(event)`. Passed into `render_pitch` → `_kit_html` →
  `card_body` (the popover) **and** used for the selected player's panel card.
- **Backward-compatible:** when fixtures carry no `xp` (e.g. the Players "Card" view), `card_body` falls back to
  today's fixture pills + the single Proj-xP chip — unchanged.
- **Not on the kit chip:** the shirt chip stays the single total (the per-GW lives in the card, per the image).

**Two-step build (each shippable):** **US-367** — the per-GW row in `card_body` + wire the **⚙ panel card** (the
all-device path, easy to test); **US-368** — thread `fixtures_by_id` into the **hover popover** (`_kit_html`) so it
shows under every shirt on hover (the exact image).

---

### 🔀 Alternatives Considered

- **On the kit chip** (`2.1·1.8·2.4`). Rejected — three numbers on a small static shirt is cramped (the *clean, not
  gimmicky* bar); the card is the roomy home, and the tester's image is the card, not the chip.
- **A per-GW table below the pitch.** Rejected for A5 — it duplicates the Health tab's breakdown and isn't the
  card-under-the-shirt the tester drew (kept as a possible future if a whole-squad glance is wanted).

---

### 🧭 Consequences

**Positive**
- Matches the tester's image; the per-GW split is where they look (the card), on desktop hover **and** mobile panel.
- Zero xP risk — reuses `by_gameweek`; display-only.
- One `card_body` change serves both surfaces.

**Negative / risks (mitigations)**
- **DGW/BGW alignment** — a team playing twice or not at all in a GW breaks the neat one-fixture-per-column layout.
  *Mitigation:* align by **event number** (exact for the common single-fixture case, always true preseason); a
  double keeps the first fixture, a blank shows the xP with a "—" fixture. Full DGW/BGW polish is a **GW1-era**
  refinement (noted, degrades gracefully — never mislabels).
- **Threading through the pitch** — `_kit_html`/`render_pitch` gain a `fixtures_by_id` param. *Mitigation:* one dict
  built where the data already lives (`render_my_squad`); the pitch just passes it through.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (Sprint 150): **US-367** the per-GW row in `card_body` + the ⚙ panel card; **US-368** the hover
  popover threading. Display-only; docs (Help note; PROJECT_STATUS; Architecture; memory).
- **GW1-era refinement:** proper DGW/BGW handling (two fixtures in a column / a blank) once double/blank gameweeks
  exist in the data.
