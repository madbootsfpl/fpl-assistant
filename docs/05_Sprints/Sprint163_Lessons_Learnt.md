# Lessons Learned

**Sprint:** Sprint 163 — UX Sprint D (My Squad density redesign)

**Dates:** 2026-08-17

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Declutter the golden page via progressive disclosure (ADR-115): a 5-metric wall + 4 caption lines → a 3-number
strip + one status line; pitch-led with one visible primary (⚙ Players & lineup); Rename + Set-whole-bench into a
flat ⚙ Manage; and consolidate transfers on the Transfer tab. Owner-approved wireframe. No feature loss. Completes
the app-wide UX audit (Sprints A·B·C·D).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reorganise, don't rewrite.** A ~350-line function halved by moving/grouping blocks and reusing every existing
  helper (`render_pitch`/`substitute`/`set_captain`/`move_bench_sub`/`set_bench`/`rename`/`apply_transfer`) — pure IA.
- **Lean on the test wall for a big diff.** The ~20 My-Squad tests pinned every control; each failure pointed at a
  moved/removed element to repoint (not delete).

## New Skills Acquired

- **Verify a "duplicate" claim before deleting.** The audit called the in-page transfer a duplicate of the Transfer
  tab; reading the code showed the tab is the **suggested** tool and the in-page one the **manual** picker — moving
  it (not deleting) preserved a real capability. Second time this audit that reading-first beat the naive plan.
- **Design around Streamlit's no-nested-expanders rule** — grouped sections go flat inside one expander; a panel
  that owns an expander stays top-level.

---

# What Went Well ✅

- The page is genuinely shorter and pitch-led; owner signed off the wireframe first, so the build matched intent.
- The transfer capability was *preserved and consolidated* (suggested + manual on one tab), a better outcome than
  the planned deletion.

# What Was Tricky ⚠️

- The big single-function diff broke several My-Squad tests — expected; each was a moved control to repoint.
- The "duplicate" misread nearly deleted the manual transfer; caught by reading `render_transfer` before trusting
  the plan.

# Process / Meta 🛠️ _(for Tony)_

# Personal Reflections 💭 _(for Tony)_
