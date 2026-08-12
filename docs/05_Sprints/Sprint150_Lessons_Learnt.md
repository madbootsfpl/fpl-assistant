# Lessons Learned

**Sprint:** Sprint 150 — Per-gameweek xP in the player card

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Match the tester's image (A5): under a shirt, a **per-gameweek row** in the card — each of the next up-to-3 GWs a
column with **xP on top** + **fixture below** — in the hover popover **and** the ⚙ panel card. Reuse the already-
computed `by_gameweek` (ADR-109) — **display-only, no xP math**.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reuse the data you already compute.** `decision_xp` already returns `by_gameweek` (`{event: xP}`) + `gameweeks`;
  `render_my_squad` already built `by_gameweek_by_id` and threw all but the captain-bonus use away. The whole feature
  was **render markup + threading** — zero new xP math. Grounding the plan on the real code (an Explore pass) turned
  a "new feature" into "surface data we already have".
- **One component, two surfaces.** `card_body` drives both the hover popover *and* the new ⚙ panel card (ADR-108), so
  a single change landed in both — desktop hover + all-device panel — for free.

### New Skills Acquired

- **Align by key, not position.** Per-GW xP is keyed by `event` (gameweek number); fixtures come from
  `team_schedule` with their own `event`. Aligning xP↔fixture by **event number** (not list position) is exact and
  survives the odd ordering — the correct foundation for the DGW/BGW polish later.
- **Preview a visual change before finalising.** Publishing a faithful Artifact (real data, self-contained card CSS,
  photos omitted for the CDN-block) let the owner *see* it and steer — which is exactly what happened.

---

# What Went Well ✅

- **Zero xP risk** — display-only; reused `by_gameweek`; the analytics untouched.
- **The preview earned its keep** — the owner reviewed it and **dropped the Total column** for a cleaner read; caught
  before it shipped, not after.
- **Backward-compatible** — fixtures with no `xp` fall back to today's pills + chip, so the Players "Card" view is
  unchanged.
- **Green throughout** (973 → 976) — deterministic `card_body` unit tests + an AppTest for the popover markup.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A test passed trivially | `player_card_html` prepends `CARD_CSS`, which *names* `.plc-gwrow` — so the class was always "present" | Test against `card_body` (the body **without** the `<style>`) so the class is meaningful |
| Scope changed mid-sprint | The owner dropped the Total after previewing | Removed `total_xp`/`show_total` from `card_body` + `render_my_squad` + `pitch.py` + the dead CSS + the moot test; updated the docs |
| Threading through a static block | The pitch is one `st.markdown`; the popover had no fixtures before | One `fixtures_by_id` dict built where the data lives (`render_my_squad`), passed through `render_pitch` → `_kit_html` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reuse over recompute | Check what the existing call already returns before adding a computation (`by_gameweek` was already there) |
| Testing HTML | Assert on the **body** (`card_body`), not the CSS-bearing full HTML, or class-name asserts pass for free |
| Align by event | Match per-GW xP to fixtures by gameweek **number**, not list index — exact, DGW/BGW-ready |

---

# Development Lessons 💻

- Ground a "new feature" on the real code first — half of A5 was already computed and discarded.
- For a visual change, publish a preview and let the owner steer *before* the retro — it changed the design (no Total).
- When a param is dropped, hunt every caller + the dead CSS + the now-moot test, not just the render site.

---

# AI Collaboration Lessons 🤖

- Display-only: the read-only invariant + every server write are unchanged; no `decision_xp`/analytics change. The
  owner's *clean, not gimmicky* principle drove the Total drop — the card shows the three weeks, the shirt chip keeps
  the total. See [[visual-preview-for-ui-signoff]] (the preview is why the drop happened before shipping) and
  [[prefers-conversation-over-modals]] (the design was steered in conversation over the preview).

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-109 — per-gameweek xP in the player card.** A per-GW row in `card_body` (xP over an FDR-tinted fixture, up to 3
GWs) in the hover popover + the ⚙ panel card; reuses `by_gameweek` aligned by `event`. **No Total column** (owner
steer after preview). DGW/BGW = graceful (align by event); a GW1-era polish.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner smoke (once deployed):** hover a shirt (desktop) → the per-GW row (xP over fixture); open a player in the ⚙
  panel → the same row on mobile.
- **GW1-era refinement:** proper **DGW/BGW** handling (two fixtures in a column / a blank) once double/blank
  gameweeks exist in the data.
- **Still on the 2026-08-12 intake (`docs/Backlog.md`):** the player-card **compare two players** (UX H — pairs
  with the ⚙ panel: "open card → compare with…"). Quick wins done; A5 + A6 shipped.
- **GW1 (2026-08-21, ~9 days):** the dormant-weight calibration remains the data-gated thread (ADR-101); and the
  deferred **tap-the-pitch** JS component (ADR-108), feedback-driven.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Publish a preview Artifact for any card/pitch visual change — cheap, and it catches design calls early.

---

# Key Commands Learned

```text
python -m pytest tests/test_player_card.py -q     # deterministic card_body markup tests (per-GW row, fallback)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Per-GW row | The card's fixture row upgraded to xP-over-fixture columns (ADR-109), up to 3 GWs, no Total |
| `fixtures_by_id` | `{id: [{opp,home,fdr,xp} …≤3]}` — per-player next-3 fixtures + per-GW xP, built once in `render_my_squad` |
| Align by event | Match per-GW xP to its fixture by gameweek number (not list position) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-109-per-gameweek-xp-card.md` | The decision + the Total drop + the DGW/BGW note |
| `src/web_streamlit/player_card.py` (`card_body`) | The per-GW row; the CSS-vs-body test lesson |

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
