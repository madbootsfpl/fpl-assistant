# Lessons Learned

**Sprint:** Sprint 119 — My Squad edit: a position filter + an affordable check

**Dates:** 2026-08-20

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make editing your team quicker in the My Squad "Swap a player" expander: a **position filter** (GK/DEF/MID/FWD)
scoping the "Replace" list, and an **"Affordable only"** checkbox (with your **bank** shown) scoping the "With"
candidates. Edit-UI only — the swap engine (`apply_transfer`), `decision_xp`, and the analytics untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Change the view, not the engine** — both stories are display filters over an already-correct swap.
- **Pre-filter vs enforce** — hiding what won't fit is a UX layer *on top of* the budget check, not a second one.

### New Skills Acquired

- **A filter can scope more than the widget it sits on.** Because a swap is same-position by design, the
  "Replace" position filter transitively scopes the "With" candidates — one control, the whole edit narrows.
- **Derive, don't store.** The bank is `FPL_BUDGET − sum(owned prices)` computed at render — no new state, no
  chance of it drifting from the squad.
- **Keep one source of truth for a rule.** `apply_transfer` already rejects an over-budget swap; the "Affordable
  only" checkbox only *hides* the too-dear picks, so the budget rule still lives in exactly one place.
- **Guard the empty-after-filter case explicitly.** A filter that empties a non-empty list needs its own caption
  (*"No affordable replacement — untick to see all."*) so the UI never looks broken or silently stuck.

---

# What Went Well ✅

- **No analytics/engine change** — risk stayed inside the My Squad view.
- **The affordable check is a pure display filter** over the budgeted engine — no double source of truth.
- **Verified on real data first** — All → 15 Replace, GK → 2; bank £0.0m (fully-spent demo squad); "With" 60 → 42.
- 764 → 766 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Where does the position filter belong? | a swap is same-position | Scope "Replace"; the "With" list follows the picked player's position |
| Is "affordable" a new rule? | `apply_transfer` already validates budget | Make the checkbox a **pre-filter**, not new enforcement |
| Bank could go stale | if stored in session | Derive it at render from `FPL_BUDGET − sum(owned prices)` |
| Filter can empty a real list | e.g. no pick ≤ out.price + bank | Add an explicit "untick to see all" caption |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Transitive scoping | One same-position filter narrows both "Replace" and "With" |
| Derive over store | Compute the bank at render — no drift, no new state |
| Pre-filter vs enforce | Hide what won't fit; keep the budget rule in the engine |
| Empty-state captions | A filter that empties a list needs its own message |

---

# Development Lessons 💻

- Put an edit affordance in the view; leave the engine (`apply_transfer`) and analytics alone.
- Prefer a derived value (bank) over a stored one when it's cheap to compute and must stay consistent.
- Test a filter by its invariant (`affordable ≤ unfiltered`), not a brittle exact count that shifts with seed data.

---

# AI Collaboration Lessons 🤖

- The edit controls never touch `decision_xp` — the xP ranking still orders the candidates; the filters only
  choose which of them to show. The recommendation stays data-driven; the UI just narrows the field.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-299/300 extend **ADR-055** (the editable, session-only squad). New: a `Position`
`st.segmented_control` + an "Affordable only" `st.checkbox` + a bank `st.caption` in `render_my_squad`'s "Swap a
player" expander (`web_streamlit/views/squads.py`); the "With" candidates gain a `price ≤ out.price + bank`
pre-filter._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A price/xP sort toggle** + a **max-price slider** on the candidate list (deferred — the affordable check
  covers the common "what fits" case).
- **The same position/affordable filters on the Transfer/Build pickers** (out of scope here — the feedback was
  My Squad edit).
- Post-**GW1 (2026-08-21)**: per-manager picks unlock (live import), momentum boards, Data Hardening + xP
  calibration.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep new edit affordances as view-layer filters over the existing engine; don't fork the rule.

---

# Key Commands Learned

```text
python -m src.web_streamlit     # Squads → My Squad → Swap: Position filter + Affordable only + Bank
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Pre-filter | A display filter that hides options the engine would reject anyway |
| Derived bank | `FPL_BUDGET − sum(owned prices)`, computed at render (not stored) |
| Transitive scoping | One filter narrowing a dependent list as a side effect |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/views/squads.py` (`render_my_squad`) | The "Swap a player" expander — where both stories live |
| `src/web_streamlit/squads.py` (`FPL_BUDGET`, `apply_transfer`) | The budget constant + the engine that still enforces it |

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

- US-299 A position filter on the swap (GK/DEF/MID/FWD + All) scoping "Replace" (ADR-055)
- US-300 An "Affordable only" checkbox + a bank caption scoping "With" (ADR-055)

**Stories Carried Forward:**

- None. (A price/xP sort toggle + a max-price slider are follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
