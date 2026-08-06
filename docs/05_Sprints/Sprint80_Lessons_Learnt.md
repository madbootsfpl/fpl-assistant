# Lessons Learned

**Sprint:** Sprint 080 — Consolidate the sidebar (Players & Squads)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Cut the sidebar from **12 tabs to 7** by merging Players+Player Stats → **Players** and the five squad tools
→ **Squads**, each behind a lazy segmented-control sub-nav — with **no behaviour change**.

---

# Knowledge Compounded 📈

## Skills Strengthened

- A big edge refactor kept safe by a strong test net (every prior assertion preserved, just re-reached).
- Extracting top-level page scripts into reusable `render_*` functions.

### New Skills Acquired

- `st.segmented_control` is a **lazy** tab-like sub-nav — only the selected option's body runs (unlike
  `st.tabs`, which executes them all) — the key to a fast multi-tool page.
- AppTest can drive a segmented control (`set_value(view).run()`), so consolidated pages stay testable.
- **Label-filter buttons in tests** (`[b for b in at.button if …]`) — positional `button[0]`/`text_input[0]`
  is fragile once a shared sidebar adds widgets.

---

# What Went Well ✅

- **Players first** de-risked the pattern (extract → `views/` → thin page + control → rewire tests) before
  the heavier Squads merge.
- **Lazy sub-nav** — the 5-tool Squads page computes only the shown view (Build ILP / transfer / captain /
  health don't all run each render).
- **No behaviour change, proven** — 585 tests stayed green (rewired, not weakened); a `_squads_view()`
  helper made the ~38-ref rewire tractable.
- **Robust tests** — label-filtering buttons survived the sidebar's Import button shifting indices.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `st.tabs` would recompute all 5 squad tools each render | it executes every tab body | `st.segmented_control` — only the selected view runs |
| Top-level page scripts can't be called conditionally | they run on import | Extract each body into a `render_*` function (`views/` package) |
| Positional `button[0]`/`text_input[0]` were fragile | the shared sidebar adds widgets | Filter by label; filter the Squad-name input by its label |
| ~38 AppTest refs to the merged pages | 12 → 2 consolidated pages | A `_squads_view()` helper + mechanical filename remaps; keep every assertion |
| Home/Help referenced the old tabs | copy predates the merge | Rewrote both to the 7-tab nav + the in-tab view switches |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Lazy vs eager sub-nav | `segmented_control` renders one view; `st.tabs` renders all — matters when views are heavy |
| Extract to render functions | Consolidating pages is "wrap each body in `render_*`, load once, dispatch on the control" |
| Test by label, not index | Robust AppTest assertions target widgets by label/role, not position |
| Behaviour-preserving refactor | A green (rewired) suite is the proof that a big move changed nothing |

---

# Development Lessons 💻

- Prove a risky pattern on the lighter case first (Players), then apply it to the heavy one (Squads).
- When a shared component (the sidebar) can shift widget order, address by label in tests.
- Keep the onboarding copy (Home/Help) in lockstep with a nav change.

---

# AI Collaboration Lessons 🤖

- The owner's IA call (merge into Players/Squads) + the recommendation (segmented control, Players first)
  set a clear, low-risk plan; the size was real but the pattern made it mechanical.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-069 | **Sidebar consolidation** — 12 → 7 tabs (Players · Fixtures · Squads · Ask · News · Trending · Help); merge Players+Player Stats and the five squad tools behind a lazy `st.segmented_control` (only the shown view computes); view bodies extracted to `web_streamlit/views/`; a shared filter (Players) / picker (Squads manage views); no behaviour/output change; tests rewired | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Intended as the **settling point** for the sidebar. Open items: pronoun-aware chat; small
  decision-support gaps (bench order, availability flags); and — post-GW1 (2026-08-21) — the Data Hardening
  flip + calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the extract-to-`render_*` + segmented-control pattern for any future page consolidation; test by label.

---

# Key Commands Learned

```text
python -m src.web_streamlit          # the 7-tab sidebar; Players & Squads switch views with a control
python -m pytest tests/test_web_streamlit.py -q   # the rewired web suite (via _squads_view)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Segmented control | A tab-like single-select strip; renders only the chosen option (lazy) |
| View extraction | Moving a page's body into a `render_*(…)` function so a page can call it conditionally |
| Label-filtered assertion | Selecting an AppTest widget by its label/role rather than positional index |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-069 | The consolidation decision (segmented control · extract to views · 7 tabs) |
| `src/web_streamlit/views/` | The reusable player + squad view renderers |
| `pages/1_Players.py` · `pages/3_Squads.py` | The thin consolidated pages |

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

- US-216 Consolidate Players — Players + Player Stats → one Players page (segmented control; shared filter)
- US-217 Consolidate Squads — Build/My Squad/Health/Transfer/Captain → one Squads page (segmented control;
  shared picker); final 7-tab sidebar

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
