# Lessons Learned

**Sprint:** Sprint 151 — Compare two players on the card

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

A **same-position, winner-highlighted** two-player comparison on the Players Card view (UX H, ADR-110): pick A, then a
**🔍 "Compare with"** typeable picker (same-position) → a merged **A · stat · B** grid with the **better value
tinted**. Reuse the card's stat catalog + `decision_xp` — **display-only, no new xP math**.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Refactor for reuse without changing the public shape.** Exposed `(key, label, raw, formatted)` from the card's
  stat catalog (`_stat_catalog`) so the compare can align by **key** and pick a winner from **raw** — while
  `_stat_rows` kept its exact `(label, formatted)` output, so the 12 existing card tests never moved.
- **Mirror an existing pattern.** The Players *history* view already had a "Compare with (optional)" second picker;
  the card compare reuses that UX shape (a scoped second selectbox) rather than inventing one.

### New Skills Acquired

- **Compare on raw, display formatted.** The winner must be decided on the **numeric** value, not the formatted
  string ("1,234" won't compare, "—" isn't a number). Splitting raw vs formatted in the catalog made the winner
  logic trivial and correct — and a per-stat **direction map** (`_BETTER`: higher-better default, `xgc` lower-better,
  `own` neutral) keeps "better" meaningful (fewer goals conceded *wins*; ownership has no winner).
- **`st.selectbox` is already the search.** The owner wanted a "spyglass, type the name" — Streamlit selectboxes
  filter as you type, so a 🔍-labelled one *is* the search; no component, no new dependency.

---

# What Went Well ✅

- **Zero analytics risk** — reused the card values + `decision_xp`; the single-card path is byte-identical when the
  compare picker is on "—".
- **The refactor was transparent** — `_stat_rows` unchanged externally; existing card tests green throughout.
- **Deterministic tests + a preview** — pure `compare_rows`/`compare_card_html` tests (winner directions, alignment,
  missing/tie) + an Artifact preview for the owner to sign off the visual.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Real players are `sqlite3.Row`, not dicts | The new `compare_rows`/`compare_card_html` called `.get()` on the raw input | `dict(a), dict(b)` at the top (the `card_body` pattern) — caught by a real-data smoke, not the dict-fixture tests |
| Same-position alignment | `_stat_rows`' rows are position-keyed + `None`-filtered → two lists don't align by index | Align by **stat key** (via `_stat_catalog`); the picker is scoped same-position; a missing side shows `—` |
| "Winner" is ambiguous for some stats | xGC lower-is-better; ownership isn't "better" either way | A `_BETTER` direction map: `hi`/`lo`/`None` (neutral) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Raw vs formatted | Keep both in the catalog — compare on raw, display formatted; never parse a formatted string back |
| Direction matters | A per-stat higher/lower/neutral map is what makes a comparison honest (xGC, ownership) |
| Dict-safe helpers | Any function taking a "player" should `dict()` it — the app passes `sqlite3.Row` |

---

# Development Lessons 💻

- Smoke with **real data**, not just dict fixtures — it caught the `sqlite3.Row` `.get()` gap the unit tests couldn't.
- Refactor additively: expose new fields, keep the old return shape, so dependents don't move.
- Reuse the codebase's own precedents (the history "Compare with" picker) before designing a new interaction.

---

# AI Collaboration Lessons 🤖

- Display-only: no `decision_xp`/analytics change; the single-card path unchanged. The design was steered in
  conversation (same-position, a searchable picker) and signed off on a **preview** — see
  [[visual-preview-for-ui-signoff]] and [[prefers-conversation-over-modals]].

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-110 — compare two players on the card.** A same-position, winner-highlighted compare on the Players Card view
(🔍 typeable picker → a merged A · stat · B grid); reuses the card's stat catalog + `decision_xp`; a `_BETTER`
direction map. Display-only. The ⚙ panel "compare with…" (owned 15) is a follow-on.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner smoke (once deployed):** Players ▸ Card → pick a forward → 🔍 compare with another forward → the better
  value tints; xGC (for a DEF/GK) tints the *lower* one; ownership stays neutral.
- **Follow-on:** the **⚙ panel "compare with…"** on My Squad (pool = the owned 15) — the same renderer, a second
  picker in the panel.
- **The 2026-08-12 tester intake is now fully cleared** (both waves) — quick wins, the player-actions panel, per-GW
  card, and now compare.
- **GW1 (2026-08-21, ~9 days):** the dormant-weight calibration remains the data-gated thread (ADR-101); and the
  deferred **tap-the-pitch** JS component (ADR-108), feedback-driven.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Split raw/formatted whenever a value is both compared and displayed.

---

# Key Commands Learned

```text
python -m pytest tests/test_player_card.py -q     # compare_rows winners + compare_card_html structure
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| `_stat_catalog` | `{key: (label, raw, formatted)}` — raw for comparison, formatted for display (ADR-110) |
| `_BETTER` | Per-stat direction map — `hi`/`lo`/`None` (neutral) — decides the compare winner |
| `compare_rows` / `compare_card_html` | Aligned same-position winner rows / the two-header comparison card |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-110-player-card-compare.md` | The decision + the same-position + direction-map rationale |
| `src/web_streamlit/player_card.py` (`compare_rows`, `_BETTER`) | The winner logic; the raw-vs-formatted split |

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
