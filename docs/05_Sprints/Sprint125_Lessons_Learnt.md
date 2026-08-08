# Lessons Learned

**Sprint:** Sprint 125 — History polish (a coloured Δ£ + cross-player comparison)

**Dates:** 2026-08-26

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Two display touches on the web History view: a **coloured Δ£** (🟢 rise / 🔴 fall) and an optional **second
player overlaid** (season table + line chart). Display-only, real past-season data; `player_history` and
`decision_xp` untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **A pure helper for a merge** — `align_seasons` is unit-tested in isolation; the view stays a thin renderer.
- **Additive, non-destructive** — the compare sits below the single-player view; no selection → unchanged.

### New Skills Acquired

- **Match the approved preview, don't over-build.** Δ£ as an emoji-in-a-string (`+0.5 🟢`) is what Tony saw and
  approved — simpler and more robust than a pandas Styler, and trivially testable (`assert "🟢" in cell`).
- **An outer-join is the right shape for a comparison.** Two players rarely share the exact same seasons, so
  `align_seasons` outer-joins on the season label with None-fill — the table shows a blank where one didn't play,
  instead of silently dropping rows.
- **Overlay what has data now, gate the rest.** Per-GW form is empty preseason, so the overlay compares **season
  points** (real today); the richer per-GW sparkline stays GW1-gated — ship the version with data.
- **Guard the display edge case.** Two players can share a `web_name` → the comparison table's columns would
  collide, so same-name is disambiguated by team.

---

# What Went Well ✅

- **One pure merge helper** (`align_seasons`), unit-tested; the view is a thin renderer.
- **Non-destructive** — the compare is additive; the single-player view is byte-unchanged without a selection.
- **Real data to verify against** — Saka's 8 past seasons made both features testable now, not "at GW1".
- 791 → 794 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Colour a numeric Δ£ cell | dataframe styling vs config | An emoji-in-a-string (matches the preview; no Styler) |
| Two players' seasons differ | different careers | `align_seasons` outer-joins on the label, None-fill |
| Per-GW overlay has no data | per-GW is empty preseason | Overlay **season** points (real now); sparkline → GW1 |
| Same web_name columns collide | two players named alike | Disambiguate the second by team |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Preview-matched display | An emoji cue beats a Styler for a simple, testable cue |
| Outer-join for comparison | Align on the shared key, None-fill the gaps |
| Data-now vs gated | Overlay what has data; defer the GW1 sparkline |
| Pure merge helper | Keep the join in analytics, unit-tested; view renders |

---

# Development Lessons 💻

- Build the display cue the user approved; don't reach for a heavier mechanism than the preview needs.
- Put a data merge in a pure, importable helper with a unit test; keep the page a thin renderer.
- Make a new panel additive so the existing view is unchanged when it's not used.

---

# AI Collaboration Lessons 🤖

- History stays a **read-view lens** — `align_seasons` reads stored rows and never touches `decision_xp`; the
  comparison presents the same shape, it doesn't compute a new recommendation.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-311/312 extend **ADR-027/060** (history) + **ADR-069** (the Players sub-nav). New:
`views/players.py::_delta_cell` (the 🟢/🔴 Δ£ cue) and a pure `analytics/history.py::align_seasons` (outer-join
two players' seasons) + a "Compare with" overlay in `render_history`._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A rolling-form sparkline overlay** (per-GW) once the season starts (GW1, 2026-08-21).
- **A stat picker** for the overlay (xGI / Pts-90 beside points).
- Post-**GW1**: the History per-GW trend + the sparkline light up; Data Hardening (form/price calibration).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep merges/joins in pure, unit-tested helpers; keep the display edge thin.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Players → History → Δ£ 🟢/🔴 + "Compare with (optional)"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Δ£ cue | The season price move shown with a 🟢 rise / 🔴 fall marker |
| Season align | Outer-join two players' seasons on the label (None where one didn't play) |
| Additive panel | A view section that appears only when used; the base view is unchanged |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/history.py` (`align_seasons`) | The pure season outer-join |
| `src/web_streamlit/views/players.py` (`render_history`, `_delta_cell`) | The Δ£ cue + the compare overlay |
| `tests/test_history_view.py` | The unit tests (delta cell + align_seasons) |

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

- US-311 A coloured Δ£ (🟢 rise / 🔴 fall) on the web History season table
- US-312 Cross-player History comparison — `align_seasons` + a season table & overlaid line chart

**Stories Carried Forward:**

- None. (A rolling-form sparkline overlay + a stat picker are GW1/follow-up items.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
