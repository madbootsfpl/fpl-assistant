# Sprint 146: Split the Squads tab — Squad Lab + My Squad (ADR-105)

**Dates:** 2026-08-12
**Status:** ✅ Complete — US-359 + US-360 (ADR-105). 964 → 966 tests
**Capacity:** ~¾–1 session (a page split + a nav renumber + a test-harness update, then a polish story)
**Carried Over:** none

> **Direction (tester → owner, ADR-105):** the single **Squads** page is a busy **7-way "Tool" switch**, and *Build*
> (a **create** tool) sits first among six **manage-your-team** tools. Split into **two top-level tabs** — **Squad
> Lab** (the renamed *Build*) + **My Squad** (the pitch/edit + the five tools as sub-tabs). Owner's name: **Squad
> Lab**; functional nav labels + the **mascot on the page**; full MADBOOTS vocabulary deferred (branding-E). Design
> principle: **clean, modern, easy to navigate.**

---

### 🔎 Verified at planning (on the code + tests)

- **`pages/3_Squads.py`** loads the data once, then a `st.segmented_control("Tool", [Build, My Squad, AI Tips, Chips,
  Health, Transfer, Captain], default=Build)` + a **"Gameweeks ahead"** horizon, dispatching to `views/squads.py`'s
  renderers. **Build** = `render_build` (no picker); the other six share **`squad_picker()`** + the horizon.
- **The renderers are reused unchanged** — this is IA plumbing, no engine/analytics change.
- **Test surface:** **one helper** `_squads_view(view)` (30 calls) opens `3_Squads.py` and sets the switch — so the
  split is a **one-helper** change (route "Build" → Squad Lab, the six → My Squad). The real churn is the **nav
  renumber**: putting Squad Lab at position 4 shifts **Ask→5 · News→6 · Trending→7 · Help→8 · Feedback→9 · Admin→10**
  (~39 hard-coded `_PAGES / "N_*.py"` refs across the tests). Handle it with **named page-path constants** in the
  harness + a careful high-→-low rename.

---

### 🎯 Sprint Goal

Replace the 7-way Squads switch with **two clear top-level tabs** — **Squad Lab** (create) and **My Squad** (manage +
five tool sub-tabs, workflow order) — reusing the existing renderers, with a mascot-themed Squad Lab header and a
guided new-user pointer. No engine/analytics change; the full suite stays green.

#### Success criteria
- [ ] **US-359 (the split + renumber + harness)** — `3_Squads.py` becomes **`3_My_Squad.py`** (the pitch + a 6-way
      sub-tab **`[My Squad · AI Tips · Captain · Transfer · Chips · Health]`**, default *My Squad*; the squad picker +
      horizon here) and a new **`4_Squad_Lab.py`** (`render_build` + a horizon; no picker). **Renumber** Ask→Admin
      (5–10). Update the test harness: `_squads_view` routes by view → the two pages; introduce **page-path
      constants**; re-point the renumbered paths. Renderers reused unchanged. Existing **964** green; ruff clean.
- [ ] **US-360 (mascot header + guided entry + copy)** — a **mascot-themed Squad Lab header** (the MB badge +
      "Build your squad"); on **My Squad with no active squad**, a prominent **→ Squad Lab** `st.page_link`; update
      **Home** + **Help** copy to the new two-tab structure. Display-only.
- [ ] **No drift** — IA/display only; the one-xP + read-only invariants hold; **964** green; ruff clean.
- [ ] **Docs** — PROJECT_STATUS; Architecture; memory.

---

### 🧭 Design sketch

**The two pages** (both load their own data; a small shared loader can dedupe later):
- **`3_My_Squad.py`** — `st.segmented_control("Tool", ["My Squad","AI Tips","Captain","Transfer","Chips","Health"],
  default="My Squad")` + the horizon + `squad_picker()`; dispatch to the six renderers (as today, minus Build). Title
  **🧩 My Squad**.
- **`4_Squad_Lab.py`** — the mascot header + a horizon + `render_build(...)` + its existing "Use this squad →"
  (hands the built 15 to the session → My Squad). Title / header **🥾 Squad Lab — build your squad**.

**The renumber** (rename **high → low** to avoid collisions): `9_Admin→10_Admin`, `8_Feedback→9_Feedback`,
`7_Help→8_Help`, `6_Trending→7_Trending`, `5_News→6_News`, `4_Ask→5_Ask`; then `3_Squads→3_My_Squad`; add
`4_Squad_Lab`. Resulting nav: `Home · Players · Fixtures · My Squad · Squad Lab · Ask · News · Trending · Help ·
Feedback (· Admin)`.

**The harness update** — add constants (`_MY_SQUAD`, `_SQUAD_LAB`, `_ASK`, `_NEWS`, `_TRENDING`, `_HELP`,
`_FEEDBACK`, `_ADMIN`) and point tests at them; `_squads_view(view)` opens `_SQUAD_LAB` for "Build", else `_MY_SQUAD`,
then sets the sub-tab. The per-view content assertions are unchanged.

**Deferred (separate intake items):** MADBOOTS vocabulary in the cards (branding-E); per-GW xP display (A5); the
player-actions consolidation (A6); persistence + Google auth (C-cluster).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-359 | **The page split + renumber + harness** — 3_Squads → My Squad + Squad Lab; renumber Ask–Admin. | High | ✅ Done | ~½ session |
| US-360 | **Squad Lab mascot header + guided entry + Home/Help copy.** | Med | ✅ Done | ~¼ session |

---

### ✅ Definition of Done

1. **Tests** — the two pages render (My Squad's six sub-tabs each render as before; Squad Lab builds a squad); the
   nav lists both tabs; a no-squad My Squad shows the Squad-Lab pointer; the mascot header renders. The full suite is
   re-pointed to the renumbered paths and stays green (**964**); ruff clean.
2. **Manual smoke** — the sidebar shows **My Squad** + **Squad Lab** (Build gone from a switch); My Squad's tools all
   work; Squad Lab builds + "Use this squad →" lands in My Squad; a fresh session is pointed at Squad Lab.
3. **Docs** — PROJECT_STATUS; Architecture; memory; Help/Home copy.

---

### 📝 Session Progress Log

- **US-359 (the page split + renumber + harness)** — `pages/3_Squads.py` → **`3_My_Squad.py`** (the pitch/edit + a
  6-way sub-tab in workflow order `[My Squad · AI Tips · Captain · Transfer · Chips · Health]`, default My Squad; the
  squad picker + horizon live here) and a new **`4_Squad_Lab.py`** (`render_build` + its own horizon + "Use this
  squad →"). **Renumbered** Ask→Admin to 5–10; nav is now `Home · Players · Fixtures · My Squad · Squad Lab · Ask ·
  News · Trending · Help · Feedback (· Admin)`. **Renderers reused unchanged** (no engine/analytics change); `Home.py`
  's `page_link` re-pointed → My Squad. **Test harness:** `_squads_view` routes *Build → Squad Lab* else *My Squad*;
  repointed the **13 Build-view tests** to Squad Lab; renumbered ~39 page paths; fixed `_TAB_EMOJI` /
  `test_sidebar_pages` (added Squad Lab 🥾) + the perf/tooltip tests. **Pragmatic call** (prefer-simple): a **direct
  sed renumber**, not a page-path-constants refactor — same green result, less churn. **964 tests unchanged**
  (a restructure — tests repointed, not added). ruff clean. (US-360 next: the mascot header + guided entry + copy.)
- **US-360 (mascot header + guided entry + copy)** — **Squad Lab** now leads with the **MB badge** (`st.image`) above
  its **🥾 Squad Lab** title + a "**Build your squad**" caption. On **My Squad with no team built/loaded**
  (`active_squad() is None`), an **info pointer** guides new users to the **🥾 Squad Lab** tab. Rebranded the **Home**
  copy (My Squad = team + tools · Squad Lab = build) + the whole **Help** guide (quick-start, the step headers, the
  "your team lives on My Squad / build in Squad Lab" caption) to the two-tab structure; the Home docstring's page
  list too. **Gotcha:** `st.page_link` to a page path **raises in AppTest bare mode** (no page registry) — it broke
  every no-squad My Squad test — so the pointer is a clean **info-text** to the sidebar tab, not a clickable
  `page_link` (Home dodges this by guarding its own `page_link` behind the deadline urgency). **+2 tests** (Squad Lab
  builds + has the mascot header · empty My Squad points to Squad Lab) + updated the Help-content + points-to-build
  assertions. ruff clean. **964 → 966.** Sprint 146 complete — the Squads tab is now **My Squad** + **Squad Lab**.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Complete — the busy 7-way **Squads** switch is now **two clear top-level tabs**: **My Squad** (the
pitch/edit + the five tools as workflow-ordered sub-tabs) and **🥾 Squad Lab** (build a fresh 15, mascot-themed). IA
only — the `views/squads.py` renderers are reused unchanged; no engine/analytics change.

**Shipped**
- **US-359** — `3_Squads.py` → `3_My_Squad.py` (6-way sub-tab, default My Squad; picker + horizon here) + new
  `4_Squad_Lab.py` (`render_build`). Renumbered Ask→Admin (5–10); nav = `Home · Players · Fixtures · My Squad ·
  Squad Lab · Ask · News · Trending · Help · Feedback (· Admin)`. Test harness: `_squads_view` routes *Build → Squad
  Lab*; 13 Build tests repointed; ~39 paths renumbered; `_TAB_EMOJI`/`test_sidebar_pages`/perf/tooltip fixed.
- **US-360** — the Squad Lab **mascot header** (badge + 🥾 + "Build your squad"); a no-squad My Squad **→ Squad Lab**
  pointer; Home + Help copy rebranded to the two tabs. +2 tests.

**Tests:** 964 → **966** (a restructure — repointed, not added; +2 for US-360). ruff clean; CI-parity green.

**What went well:** mapped the test-surface cost up front; kept it to plumbing (renderers untouched); caught the
`st.page_link`-in-AppTest limitation on the first run and swapped to a clean info pointer.

**Owner follow-up (browser smoke):** the sidebar shows My Squad + 🥾 Squad Lab; the tools work under My Squad's
sub-tabs; a fresh session shows the Squad-Lab pointer; Squad Lab builds + "Use this squad →" lands in My Squad.

**Lessons:** `docs/05_Sprints/Sprint146_Lessons_Learnt.md`.

---

### 📌 For Tony — confirm before I start US-359

1. **The nav renumber** — Squad Lab at position **4** (right after My Squad) gives the clean adjacent pair, but
   shifts **Ask→Admin to 5–10** (~39 test path refs — mechanical, handled via harness constants + the full-suite
   check). Agree it's worth the clean nav? *(My rec: yes — the alternative, parking Squad Lab at the bottom to dodge
   the renumber, reads worse.)*
2. **Squad Lab horizon** — keep a **"Gameweeks ahead"** selector on Squad Lab (a season-start build benefits from a
   longer window), or just default it? *(My rec: keep it.)*
3. **Squad Lab header** — the **MB badge + "🥾 Squad Lab — build your squad"**, brand mascot on the page (not the nav
   label). Good? *(The full illustration hero is a homepage thing; the badge suits an in-app header.)*
