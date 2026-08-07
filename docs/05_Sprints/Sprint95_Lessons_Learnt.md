# Lessons Learned

**Sprint:** Sprint 095 — Set-piece takers & the differential lens

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

See who takes **penalties · corners · free-kicks** for each team, and find **low-ownership set-piece
takers** (a strong differential signal) — a new **Set pieces** view on the Players tab plus a compact flag
on the Pool. Display-only over freshly-ingested fields; no scoring change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Additive schema changes via the migration path** — two new columns into `_MIGRATIONS`, and `get_players`'
  `SELECT p.*` picks them up with no query edit.
- **Reusing an existing lens** instead of inventing a metric — "differential" = set-piece duty *alongside*
  the existing Own% + Val/£m, filterable.

### New Skills Acquired

- The FPL `bootstrap-static` element carries three set-piece order ints (`penalties_order`,
  `corners_and_indirect_freekicks_order`, `direct_freekicks_order`; **1 = first-choice**). Verifying them
  live *before* writing the ADR de-risked the whole sprint.
- A display-only feature that reuses ingested fields (flags, a board, a column) needs **no analytics change**
  and barely ripples — the same shape as the availability/crowd flags.
- `st.column_config.NumberColumn(format="%d")` keeps an order column right-aligned and numerically sortable
  (a pre-formatted string would left-align and sort lexically); `None`/`NaN` renders as a blank cell.

---

# What Went Well ✅

- **Frictionless ingest** — the auto-migration + `SELECT p.*` meant adding two columns touched only the
  model, the upsert list, and `save_players`; no query rewrite.
- **No new metric** — the differential lens fell straight out of Own% + Val/£m + a sortable board.
- **Tiny blast radius** — `decision_xp`/the analytics untouched; the 640 existing tests stayed green.
- **Real data proved the value** — B.Fernandes (pens+FK), Palmer, Isak surface as takers; 10 low-own (≤5%)
  pen takers (Buendía, Wood…) are exactly the differentials the owner asked for.
- 640 → 647 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Which players to list on the board? | 573 rows with mostly-blank set-piece columns is noise | List only players with a set-piece duty (any order present) |
| Is the order int "good" high or low? | 1 = first-choice is non-obvious | Default sort pen-takers-first + a caption/tooltip ("1 = first-choice"); columns stay sortable |
| Val/£m on raw rows | raw `get_players` rows have no `value` | Run through `rank_players(sort_by="value")` to attach it, then filter |
| Columns must format as ints | `Pen`/`Corners`/`FK` weren't in `FORMATS` | Added `%d` — right-aligned, sortable, blank on None |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Additive migration | New columns in `_MIGRATIONS` + `SELECT p.*` = no query change |
| Display-only lens | Reuse ingested fields; the analytics/xP never move |
| `NumberColumn(%d)` | Keeps order columns numeric + sortable; None → blank |
| Differential = a combination | Set-piece duty next to Own% + Val/£m, filterable — not a new score |

---

# Development Lessons 💻

- Verify the upstream data exists (a live fetch) *before* the gate — it turns "will this work?" into "here's
  the sprint".
- Prefer surfacing an existing signal in a new arrangement over adding a scoring input — cheaper, honest, and
  it keeps the grounded xP auditable.
- A display-only feature is safe to ship fast when it reuses ingested fields and the shared filter/formatting.

---

# AI Collaboration Lessons 🤖

- "Set piece & ownership" mapped cleanly to: ingest two ints → a pure flag helper → a board that reuses the
  filter. Naming the reuse (Own% + Val/£m as the differential lens) kept it from sprawling into a new metric.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-081 | **Set-piece takers** — ingest `corners_order` / `freekicks_order` (like the Tier-1 crowd fields); a `set_piece_flags(player)` helper (⚽/🚩/🎯 for the first-choice taker); a Players "Set pieces" view + a Pool flag. Display-only, no scoring change; the differential lens reuses Own% + Val/£m. `refresh` + `reseed` populate real data | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Elite Manager Comparison** (owner intake) — GW1-gated; needs live mini-league data.
- A gated **set-piece xP boost** in `decision_xp` — a possible later *modelling* item (this sprint kept it a
  lens, ADR-081).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.
- Backlog still open (season-timely): AI Chat Assistant (needs a grounded-vs-free-form ADR); Chip Strategy;
  Price Change Predictor; persisted chat context; season countdown / deadline banner; server-side squad
  persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep de-risking gates with a live data check before the ADR — it made this a one-session sprint.

---

# Key Commands Learned

```text
python app.py refresh         # populate the new corners_order / freekicks_order columns
python app.py reseed          # refresh + copy to data/seed.db for the deploy
python -m src.web_streamlit   # Players → Set pieces: pen/corner/FK takers; sort Own% ↑ for differentials
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Set-piece order | An int per duty; **1 = first-choice** taker, higher = backup |
| Differential | A low-owned (≤5%) player — here, a low-owned set-piece taker |
| Display-only lens | A view over ingested fields that never changes the grounded xP |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-081 | The set-piece decision + the "lens, not a score" rationale |
| `src/analytics/crowd.py` (`set_piece_flags`) | The pure, empty-safe duty-flag helper |
| `src/web_streamlit/views/players.py` (`render_set_pieces`) | The board + the Pool "Set" column |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-249 Ingest set-piece orders — `corners_order` / `freekicks_order` + `set_piece_flags`; refresh + reseed (ADR-081)
- US-250 Set pieces view + Pool flag — a filterable takers board (Own% + Val/£m) + a compact Pool flag

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
