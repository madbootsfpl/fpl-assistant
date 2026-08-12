# Lessons Learned

**Sprint:** Sprint 146 — Split the Squads tab (Squad Lab + My Squad)

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Replace the busy 7-way **Squads** switch with **two clear top-level tabs** — **Squad Lab** (build a fresh 15) and
**My Squad** (the pitch/edit + the five tools as sub-tabs, workflow order) — reusing the existing renderers, with a
mascot-themed Squad Lab header and a guided new-user pointer. IA only, no engine change. (ADR-105.)

---

# Knowledge Compounded 📈

## Skills Strengthened

- **A big refactor rides on the test surface.** The user-facing change was small (two tabs), but the *cost* was the
  page renumber + ~39 test path refs — mapping that up front (one `_squads_view` helper vs. the renumber) set the
  plan honestly.
- **Reuse the renderers, move the plumbing.** Splitting pages without touching `views/squads.py` kept it IA-only —
  zero analytics/engine change, the whole diff mechanical.

### New Skills Acquired

- **Rename pages high → low to avoid collisions.** `9→10, 8→9, … 4→5` then add the new page — no intermediate clash;
  distinct name suffixes (Ask/News/…) made a single sed safe across the tests.
- **Route the test helper, don't rewrite the calls.** `_squads_view("Build")` → the Squad Lab page, everything else →
  My Squad — one helper change covered 30 call sites; only the 13 *build* tests needed repointing (identified by the
  enclosing `test_build_*` function name).
- **`st.page_link` to a page path raises in AppTest bare mode** (no page registry → `KeyError: 'url_pathname'`). Home
  dodged it by guarding its `page_link` behind the deadline urgency (which is "calm" in tests); an *unconditional*
  one broke every no-squad My Squad test. Lesson: prefer a **text pointer** for a guided nudge, or guard the
  `page_link` — and it's a test-env limitation, not a prod bug.
- **When ADR-069 (consolidate) became the clutter, ADR-105 (split) is evolution, not reversal.** The right IA depends
  on how many things share the tab — and that changed as the app grew. Record the *why now*, not just the *what*.

---

# What Went Well ✅

- **Grounded the cost first** — the plan named the renumber churn, so there were no surprises; the sed + one-helper
  route did most of it.
- **Renderers untouched** — the split is pure IA; every view behaves identically, just relocated.
- **Caught the `page_link` limitation early** (the first test run) and swapped to a clean info pointer.
- 964 → 966 tests (a restructure: +2 for US-360, the rest repointed); ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| ~39 test path refs + a page renumber | the numbered-file nav convention | Rename high→low + a single safe sed (unique name suffixes) |
| 13 Build tests silently mis-targeted | the sed pointed them at the (Build-less) My Squad page | Repoint only `test_build_*` funcs → Squad Lab |
| `st.page_link` raised in AppTest | bare mode has no page registry (`url_pathname`) | An info-text pointer to the sidebar tab, not a `page_link` |
| Help/Home copy asserted "Squads" | the copy rebranded to My Squad + Squad Lab | Update the copy + the two content assertions |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Page renumber | Rename high→low; distinct name suffixes make a single sed collision-free |
| Test-helper routing | Route one helper (`_squads_view`) instead of editing 30 call sites |
| AppTest limits | `st.page_link` to a page path raises in bare mode — text pointer or guard it |
| IA evolves | Consolidate vs. split depends on tab load; record the "why now" (ADR-069 → ADR-105) |

---

# Development Lessons 💻

- Map the *test surface* of a refactor before starting — it's often the real cost, not the app change.
- Keep a restructure to plumbing: reuse the renderers, move only the pages/nav, and the diff stays mechanical.
- Prefer a text nudge over `st.page_link` for a guided pointer (AppTest-safe + prod-safe).

---

# AI Collaboration Lessons 🤖

- Pure IA/display: `views/squads.py`'s renderers are byte-identical; the analytics/engine, `decision_xp`, and the
  read-only guardrail are untouched. Brand personality landed on the *page* (the Squad Lab mascot header) with
  functional nav labels — the agreed "clean map, brand on the page" split (ADR-105).

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-105 — split the Squads tab.** Two top-level tabs: **Squad Lab** (the old *Build*, renamed; mascot-themed
header) + **My Squad** (the pitch/edit + `[My Squad · AI Tips · Captain · Transfer · Chips · Health]` sub-tabs). The
renderers are reused unchanged; a no-squad → Squad Lab pointer guides new users; functional nav labels, brand on the
page, full MADBOOTS vocabulary deferred (branding-E).

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (browser smoke):** the sidebar shows **My Squad** + **🥾 Squad Lab**; My Squad's tools work under its
  sub-tabs; a fresh session shows the "build in Squad Lab" pointer; Squad Lab has the mascot header + "Use this
  squad →" lands in My Squad.
- **Still on the P1/P2 list (2026-08-12 intake, `docs/Backlog.md`):** MADBOOTS vocabulary in the cards (branding-E);
  the persistence + Google-auth review (C-cluster); per-GW xP display (A5); the player-actions consolidation (A6).
- **GW1 (2026-08-21, ~9 days):** the dormant-weight calibration remains the data-gated thread (ADR-101).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- For any nav/IA change on the numbered-pages convention, budget for the renumber's test churn up front.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_streamlit.py -k "squad_lab or sidebar_pages or every_tab" -q   # the new nav
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Squad Lab | The build-a-fresh-15 tab (the old *Build*), its own page + a mascot header |
| My Squad (tab) | The manage tab: pitch/edit + AI Tips · Captain · Transfer · Chips · Health |
| Page renumber | Shifting the numbered page files (Ask→Admin: 5–10) to insert Squad Lab at 4 |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-105-squad-ia-split.md` | The IA decision + the naming rationale |
| `src/web_streamlit/pages/3_My_Squad.py` · `4_Squad_Lab.py` | The two split pages |
| `tests/test_web_streamlit.py` (`_squads_view`) | The routed test helper |

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

- US-359 The page split + renumber + test-harness update (3_Squads → My Squad + Squad Lab; Ask–Admin → 5–10)
- US-360 The Squad Lab mascot header + the guided new-user pointer + the Home/Help copy

**Stories Carried Forward:**

- None. (The P1/P2 intake items — branding-E vocabulary, persistence+auth, per-GW display, player-actions — remain.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
