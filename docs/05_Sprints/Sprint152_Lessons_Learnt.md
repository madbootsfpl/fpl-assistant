# Lessons Learned

**Sprint:** Sprint 152 — Wave-3 polish (Boot Battle band + static GW1–3)

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Two wave-3 tester tweaks on just-shipped features: **US-371** a MADBOOTS "Boot Battle" brand band on the compare
card; **US-372** the per-GW hover card shows a **static GW1–3** regardless of the "Gameweeks ahead" selector.
Display-only; no new ADR (extends ADR-110/109).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **A dropped feature can leave a seam.** Removing the Total column (S150) meant the per-GW row's reliance on the
  page horizon suddenly showed as GW2/GW3 = 0.0 at horizon 1 — a case the Total had masked. A later tweak surfaced it.
  Lesson: when you drop part of a feature, re-check the edges the removed part used to cover.
- **Reuse the brand seam.** The "Boot Battle" band is the same `brand.mark_html()` + `.plc-band` the single card uses
  — a one-line addition, consistent by construction.

### New Skills Acquired

- **Decouple a display from a control when they answer different questions.** The "Gameweeks ahead" selector drives
  the *totals/tools*; the per-GW card row answers "what are the next three weeks?" — a fixed question. Sourcing it
  from a fixed 3-GW compute (reusing the existing one when it already spans ≥3) fixed the bug without a second
  compute in the common case.

---

# What Went Well ✅

- **Tiny, reversible diffs** — a band line + a per-GW source swap; no analytics touched.
- **Green + previewed** — 982 tests; the compare preview refreshed for owner sign-off before commit.
- **No extra cost in the common case** — the horizon-3 recompute only runs when the page horizon is < 3.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| GW2/GW3 = 0.0 at horizon 1 | The per-GW row read `by_gameweek` from the horizon-driven compute; horizon 1 → only GW1 | Source the card's per-GW from a fixed 3-GW view (reuse when horizon ≥ 3) |
| Don't double the compute | A naive fix recomputes `decision_xp(horizon=3)` every render | Reuse `ranked` when `horizon ≥ 3`; recompute only for horizon 1/2 |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Display vs control | A card that answers a fixed question shouldn't ride a variable selector |
| Edges after a removal | Dropping a feature (the Total) can unmask a case it was covering (0-filled cells) |
| Cheap invariance tests | "cells identical at horizon 1 vs 5" pins the decoupling without asserting exact values |

---

# Development Lessons 💻

- After removing part of a feature, look for the cases it silently covered.
- Reuse an existing compute before adding a new one — gate the extra work behind the case that needs it.

---

# AI Collaboration Lessons 🤖

- Display-only: no analytics change. The visual (Boot Battle band) was signed off on a refreshed preview before
  commit — see [[visual-preview-for-ui-signoff]].

### Notes _(for Tony)_

---

# Decisions Made 📋

No new ADR — extends **ADR-110** (compare card → the Boot Battle band) and **ADR-109** (per-GW card → horizon-
independent, static GW1–3).

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner smoke (once deployed):** the compare card shows the **Boot Battle** band; My Squad with "Gameweeks ahead" =
  1 → the hover card still shows GW1–3 real scores (not 0.0).
- **The 2026-08-12 intake + its wave-3 polish are now all shipped.**
- **GW1 (2026-08-21, ~9 days):** the dormant-weight calibration remains the data-gated thread (ADR-101); the deferred
  **tap-the-pitch** JS component (ADR-108) and the **⚙ panel "compare with…"** follow-on stay feedback-driven.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep publishing a preview for any card/pitch visual tweak — the sign-off loop is cheap and catches it early.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_streamlit.py -q -k "horizon_independent"   # the per-GW decoupling invariant
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Boot Battle | The MADBOOTS brand-band title on the two-player compare card (ADR-110) |
| Horizon-independent card | The per-GW row always shows GW1–3, decoupled from the "Gameweeks ahead" selector (ADR-109) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/player_card.py` (`compare_card_html`) | The Boot Battle band (reuses `brand.mark_html`) |
| `src/web_streamlit/views/squads.py` (`card_bg_by_id`) | The fixed-3-GW source for the per-GW card row |

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
