# Lessons Learned

**Sprint:** Sprint 083 — Consistent number formatting · refresh the Help tab

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make every web table line up — one decimal for money/value/%, two for the xG family, integers for counts,
`6` always as `6.0` — and bring the Help tab up to date with everything shipped since it was written
(This week · the quality ratings · the table-first Pool).

---

# Knowledge Compounded 📈

## Skills Strengthened

- Fixing a display problem **at the display layer** — without touching the data or its sort order.
- Centralising a cross-cutting convention in one module so parallel surfaces can't drift.

### New Skills Acquired

- `st.column_config.NumberColumn(label, format="%.1f")` pins decimals **and** right-aligns **and** keeps the
  column numeric/sortable — strictly better than pre-formatting cells to strings (which left-align and sort
  lexically, so "10.0" < "9.0").
- Streamlit `column_config` objects are **plain dicts**, so a test can assert equality against the same
  `st.column_config.*` call — no reaching into internals.
- `NumberColumn` with a `%+.1f` format keeps the sign (for signed diffs) while still aligning.

---

# What Went Well ✅

- **Right layer, right tool.** Formatting via `NumberColumn` fixed the alignment without rounding the data
  (sorting stays truthful) — a test proves the frame keeps the raw float, not a string.
- **One convention module.** `formats.py` (`FORMATS` + `column_config`) means the Pool, the stat boards, and
  the squad tables share the exact same policy and it composed with the ADR-071 tooltips for free.
- **Caught a stray data change.** `data/seed.db` had drifted to 572 players (vs the committed 570) from an
  incidental write; spotting it in `git status` and reverting kept the commits pure.
- Small, focused sprint: 607 → 612 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `Val/£m` showed `24.2345`; whole prices showed `6` | `value` is an unrounded float; a mixed column doesn't pin decimals | `NumberColumn(format=…)` per column — display-only |
| Signed `Diff`/`Margin` were pre-formatted strings | strings left-align + sort lexically | Pass the raw number; format with `%+.1f` so `NumberColumn` aligns + signs |
| The convention could drift across 3 tables | each built its own `column_config` | One shared `formats.py` (`FORMATS` + `column_config`) used by all three |
| `_BADGE` constant left dead after the refactor | its logic moved into `column_config` | Removed it (ruff would have flagged) |
| `data/seed.db` modified unexpectedly (572 vs 570) | an incidental write during the session | Reverted to HEAD; seed only moves via a deliberate `reseed` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Format at the edge | Fix display in the display layer (`column_config`), never by rounding the source value |
| NumberColumn > strings | Aligns, pins decimals, and keeps the column numeric/sortable |
| One convention, one place | A shared `FORMATS` map stops three tables drifting and is the single knob to change |
| Test column configs by equality | They're plain dicts → compare to the same `st.column_config.*` call |
| Watch `git status` | An incidental data-file change is easy to sweep into an unrelated commit — check before staging |

---

# Development Lessons 💻

- Prefer a display directive over mutating data when the ask is purely cosmetic.
- Centralise a convention the first time a third caller appears — it stops silent drift.
- Keep an eye on generated/data files in `git status`; stage explicitly, never `git add -A` a data snapshot
  into a code commit.

---

# AI Collaboration Lessons 🤖

- The owner's "keep the xG family at 2dp" call was the right nuance — a blanket 1dp would have blurred the
  small expected-goal ratios; the convention encodes the exception rather than flattening it.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-072 | **Consistent number formatting (web tables)** — a shared `web_streamlit/formats.py` convention (`FORMATS` + `column_config`) formatting the Streamlit tables via `NumberColumn` (aligned + still numeric/sortable): money/value/%/form/ICT → 1dp, counts → integer, the xG family → 2dp, signed diffs → `%+.1f`. Applied to the Pool, the four stat boards, and the squad tables; display-only, analytics untouched; CLI unchanged; no server writes | Accepted |

(US-224 — the Help refresh — was content only, no ADR.)

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Reseed the deploy** so testers see fresh (572-player) data + all the recent UI: `python app.py reseed`
  → commit → push (US-219 workflow). Currently the Cloud serves the 570-player snapshot.
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.
- Possible: extend the `NumberColumn` convention if new tables/columns appear; a rating on the Pool itself.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- The "check `git status` for stray data files before staging" habit paid off — keep it.

---

# Key Commands Learned

```text
python -m pytest tests/test_formats.py -q     # the number-format convention (1dp / int / 2dp / signed)
git checkout -- data/seed.db                  # revert an incidental seed-snapshot change
python app.py reseed                          # deliberately refresh the deploy seed (then commit + push)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Column config | Streamlit's per-column display directive (`NumberColumn`/`ImageColumn`/`Column`) — a dict |
| Display-only formatting | Pinning decimals in the view without changing the underlying value |
| Format convention | One `FORMATS` map defining the decimal policy for every table column |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-072 | The formatting decision + the NumberColumn-vs-strings rationale |
| `src/web_streamlit/formats.py` | The shared `FORMATS` map + `column_config` helper |
| `src/web_streamlit/pages/7_Help.py` | The refreshed step-by-step guide |

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

- US-223 Consistent number formatting — a shared `NumberColumn` convention (`formats.py`) across the Pool,
  the four stat boards, and the squad tables (1dp money/%, 2dp xG family, integer counts, signed diffs);
  display-only (ADR-072)
- US-224 Refresh the Help tab — This week / the gameweek plan, the 🟢…🔴 quality ratings, the table-first
  Pool, and the new Ask example

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
