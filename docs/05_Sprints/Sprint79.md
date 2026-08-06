# Sprint 079: A Help tab — build your team with the assistant

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/1 story)
**Capacity:** ~½ session (a new content page — no analytics, no data dependency)
**Carried Over:** none

> **Direction (owner, tester feedback):** a **Help** tab — a step-by-step guide a new user follows to build
> their unique team **with AI help**. Owner's calls: placed **last** (after Trending; zero renumber churn);
> a **static step-by-step guide** (numbered steps in expanders, copy-paste `ask` examples).

---

### 🔎 Verified at planning

- The tabs to reference already exist and are named: **Build Squad · My Squad · Squad Health · Transfer ·
  Captain · Players · Player Stats · Fixtures · Trending · News · Ask**. The guide points to these — it
  **complements Home** (which carries a short overview) with a deeper walkthrough, not a duplicate.
- **Static only** — markdown + `st.expander` per step; **no data/analytics dependency**, so it renders
  even before `refresh`. No input controls → it's outside the help-tooltip coverage test (nothing to gate).
- Placed **last** as `pages/12_Help.py` → no other page files move (Streamlit orders by the numeric prefix).

---

### 🎯 Sprint Goal

**Objective:** a self-contained **Help** page that walks a user through the recommended loop — *build →
make it yours → check → improve → research → ask → save* — with concrete, copy-paste `ask` examples and a
pointer from each step to the right tab.

#### Success Criteria
- [x] Approach agreed (**ADR-068**) — a static, step-by-step Help page placed last; complements Home;
      no data dependency; a render + key-content test
- [x] **US-215** — `pages/12_Help.py`: a numbered walkthrough (a step per `st.expander`) covering Build
      Squad → My Squad → Squad Health → Transfer/Captain → research tabs → **Ask** (copy-paste examples) →
      **save/download** (+ manager-ID import); an honest note on data freshness + what lights up at **GW1
      (2026-08-21)**; a one-line pointer to Help added on **Home**
- [x] **No behaviour change** — static content; the web writes nothing server-side (guardrail holds)
- [x] A test: the Help page renders (no data needed) and contains the key steps + at least one `ask` example
- [x] Existing stay green — **585** (+1); ruff clean
- [ ] Docs: ADR-068 + index ✅; Architecture, PROJECT_STATUS, README (mention the Help tab) _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-215 | **Help tab** — a static step-by-step guide (`pages/12_Help.py`) to building a team with the assistant; expander per step, copy-paste `ask` examples, tab pointers; a Home pointer. ADR-068. | High | ✅ Done | ~½ session |

---

### 🧭 Design sketch (content, to settle in ADR-068)

`pages/12_Help.py` — title *"Help — build your team with the assistant"*, a one-line philosophy
(*analytics decide, the AI narrates; your squad lives in your session — download to keep it*), then a
**Quick start**, then a step per `st.expander` (first one or two expanded):

1. **Build your squad** → *Build Squad*: budget · archetypes (cheap/premium/differential) · include/exclude ·
   objective · weekly/bench-boost · include-injured → *Use this squad* or *Download*.
2. **Make it yours** → *My Squad*: rename · swap · set the bench · set a captain · download.
3. **Check its health** → *Squad Health*: projected xP over 5 GW + weak links.
4. **Improve it** → *Transfer* (bank slider → XI-aware swaps) · *Captain* (who to (vice-)captain).
5. **Do your research** → *Players* (filter/sort) · *Player Stats* (over/under · DefCon · clean sheets · xG) ·
   *Fixtures* (the ticker) · *Trending* (crowd + Community Signals) · *News*.
6. **Ask the assistant** → *Ask*: copy-paste examples — *"build me a squad for £100m with 3 differentials"*,
   *"best differential midfielders under £8m"*, *"is Haaland worth the money?"*, *"who should I captain from
   \<squad>?"*, *"which of \<squad>'s teams have the best fixtures?"* — and the **✓/⚠ trust line** (grounded).
7. **Save your team** → *Download* the `squad.json` (that file **is** your save); re-upload later; or import
   by **manager-ID** (from GW1).

Close with: *Data as of …* freshness; preseason vs **GW1 (2026-08-21)** — momentum/form + live picks light
up then; crowd signals are a *lens, not truth*.

---

### ✅ Definition of Done

1. **Tests pass** — an AppTest renders `12_Help.py` (no data needed — no exception) and asserts a couple of
   key steps + an `ask` example are present. Existing **584** stay green; ruff clean.
2. **Manual smoke** — the Help tab reads as a clear step-by-step; the expanders open; the examples are
   copy-paste-able.
3. **Docs updated** — ADR-068 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

- **US-215 ✅ (gate + build)** — Recorded **ADR-068** (+ index). New `pages/12_Help.py` — a static
  step-by-step guide, **7 expander steps**: 1 Build your squad · 2 Make it yours · 3 Check its health ·
  4 Improve it (Transfer/Captain) · 5 Do your research (Players/Player Stats/Fixtures/Trending/News) ·
  6 Ask the assistant (a copy-paste `ask` code block + the ✓/⚠ trust line) · 7 Save your team (download /
  upload / manager-ID). A **Quick start** line up top + an honest close on data freshness and what lights
  up at **GW1 (2026-08-21)** (crowd = a lens, not truth). Static markdown only — **no data/analytics
  dependency** (renders before any refresh) and **no input widgets** (outside the tooltip-coverage test).
  Added a one-line **Help pointer on Home** + Help to the package docstring. Placed **last** (`12_`) → no
  other page files moved. Tests (+1 → **585**): the Help page renders with no DB and carries the key steps
  + an `ask` example. **Smoke:** 7 steps render, no exception, the code block present. ruff clean, no server
  writes.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — a **Help** tab now walks a new user through building + managing their team with
the assistant: 7 clear steps (build → make it yours → check → improve → research → ask → save), with
copy-paste `ask` examples. Static content, no data dependency; Home points to it.

**What went well** — keeping it a **static recipe** (markdown + expanders) made it robust (renders before
any refresh), test-friendly (a key-content assertion), and easy to keep accurate. Placing it **last** meant
zero renumber churn. It complements Home (the one-screen overview) rather than duplicating it.

**What to watch / lessons** — a guide can drift from the app, so it's written as a *recipe* (tabs + `ask`
examples), not a spec; the key-content test flags if the core steps/examples vanish, but **wording stays a
review concern** — worth a quick re-read whenever a tab is renamed or an `ask` intent changes. It has no
input widgets, so it's intentionally outside the tooltip-coverage test.

**Lessons captured:** `docs/05_Sprints/Sprint79_Lessons_Learnt.md`.
