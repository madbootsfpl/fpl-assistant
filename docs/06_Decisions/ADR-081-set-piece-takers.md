# Architectural Decision Record: Set-piece takers (ingest + a differential lens)

**Decision ID:** ADR-081
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** new data + display. Adds two ingested fields (like the Tier-1 crowd fields,
ADR-057) and a display helper next to `crowd_flags`/`availability_flag`. No scoring change. Triggered by an
owner feature request.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner request: *"who takes **penalties, corners, and free-kicks** for each team, plus **ownership
combinations** to find high-performing, **low-ownership differential** picks."* Set-piece duty is a strong,
under-surfaced signal — a first-choice penalty taker gets a big expected-points bump, and a *low-owned* one
is a prime differential.

**Verified in code (a live fetch):** `bootstrap-static` elements carry `penalties_order`,
`corners_and_indirect_freekicks_order`, `direct_freekicks_order` — an integer per player (**1 = first
choice**). `penalties_order` + `selected_by` are already ingested; the **corner/FK orders are not** (two new
fields). Storage has an **automatic light migration** (`_migrate` ALTERs missing columns on open), so the
schema addition is low-friction. The **differential lens already exists** (`crowd_flags` 💎 ≤5% owned; the
differential shortlist ADR-061; `value` = xP/£m).

#### Decision Drivers
- **Surface the takers** — pen / corner / FK duty per player, per team.
- **The differential combination** — set-piece duty *alongside* ownership + value, so a low-owned taker
  stands out. Reuse the existing filter/ownership/value, don't invent a metric.
- **Cheap + honest** — ingest the two order ints; display-only; the analytics/xP are unchanged.

---

### ✅ Decision

**1. Ingest two set-piece order fields (US-249).** Add `corners_order` (from
`corners_and_indirect_freekicks_order`) and `freekicks_order` (from `direct_freekicks_order`) to the `Player`
model + `from_api`, and to the storage schema/upsert/`get_players` (the `_migrate` path ALTERs them in). A
`refresh` populates them; a `reseed` carries them to the deployed snapshot. (`penalties_order` already
exists.)

**2. A `set_piece_flags(player)` helper.** In `analytics/crowd.py` (next to `crowd_flags`): a compact list of
duty flags for a **first-choice** taker — `⚽ pens` (penalties_order == 1), `🚩 corners` (corners_order == 1),
`🎯 FK` (freekicks_order == 1). Empty-safe; display-only.

**3. A "Set pieces" view + a Pool flag (US-250).** A new **Set pieces** option on the Players segmented
control: a board of Player · Team · Pos · **Pen/Corners/FK order** · **Own%** · **Val/£m**, through the
shared filter (team/position), sortable — so a user finds **low-ownership takers**; a caption frames the
differential angle. The flag also shows on the **Pool**. Display-only.

---

### 🔀 Alternatives Considered

- **Ingest the `_text` fields** (e.g. "Order: 1"). Rejected — the `_order` ints are cleaner and drive both
  the flags and the board; the text is redundant.
- **A new "set-piece xP boost" in `decision_xp`.** Rejected (this sprint) — that's a scoring change; keep it
  a *display* signal. (Penalty duty already feeds captaincy via `penalty_taker`.) Could be a later, gated
  modelling item.
- **A separate differential score.** Rejected — the differential lens exists (`Own%` + `Val/£m` +
  `crowd_flags` 💎); the board surfaces set-piece duty alongside them, filterable.
- **Only penalties.** Rejected — corners/FKs matter for attacking returns (assists, direct FK goals); the
  owner asked for all three.

---

### 🧭 Consequences

**Positive**
- Set-piece duty is visible per player + per team; a low-owned taker is easy to spot (a real differential
  edge).
- Cheap: two ingested ints + a display helper + a view; reuses the shared filter/ownership/value.
- No scoring change; the analytics/xP are untouched.

**Negative / risks (mitigations)**
- **Needs a refresh to populate** — the migration adds NULL columns; a `refresh` (+ `reseed` for the deploy)
  fills them. Until then the view is empty (honest).
- **Set-piece orders shift in-season** (managers change takers) → it reflects the current snapshot, updated on
  refresh, like the rest of the data.
- **Not a scoring signal (yet)** → framed as a *lens* (like crowd flags); penalty duty still feeds captaincy.

---

### 📊 Validation

Verified (live fetch): the three order fields exist and are reachable (Saka pen 1 · corners 6 · FK 2). Two
of three already ingested; storage auto-migrates. Acceptance: `from_api` maps the corner/FK orders; a storage
round-trip persists them; `set_piece_flags` flags a first-choice taker (and nothing otherwise); the Players
"Set pieces" view renders the order columns + Own%/Val/£m through the shared filter; the Pool shows the flag;
the analytics + existing 640 tests are unchanged (new tests added). A `refresh` + `reseed` populate real data.
