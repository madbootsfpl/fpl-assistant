# Sprint 071: Web build parity — full `squad` options on Build Squad + tab reorg

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2–3 stories)
**Capacity:** ~1–2 sessions (an edge/UI sprint — the engine is untouched)
**Carried Over:** none

> **Direction (owner, tester feedback):** the web can't build a squad with the **full CLI `squad`
> options** — only budget/cheap/premium/differential are exposed. Want to build with any/all options,
> save into the session so **My Squad** picks it up to tweak, then download. Owner's calls (scoping):
> full options as **form widgets on Build** (not fragile NL); **My Squad stays the tweaker** + a
> "Rebuild in Build Squad →" link; **rename** "Squads"→"Squad Health", "Build"→"Build Squad" and
> **reorder** them grouped (Build Squad · My Squad · Squad Health); the **Ask** "build a squad" answer
> gains a "Use this squad →" button (optional bridge).

---

### 🔎 Verified at planning (real data — the engine already does it)

Smoke on the live DB (2026-08-06) — every option the new controls will pass is already supported by
`select_squad`; **no engine change needed:**

- **xp objective + include Saka + exclude Salah + ≥2 differentials + weekly bench** → `Optimal`, £100.0m,
  Saka **in**, Salah **out**.
- **xgi objective + XI-only pinned 3-4-3** → `Optimal`, exact shape `{GK 1, DEF 3, MID 4, FWD 3}`.
- The web builds the **formation dict from widgets** (DEF/MID/FWD selectors) — no string parsing.
- Objectives: `xp` → `decision_xp` (xMins-weighted, honours no-xmins); `points`/`value`/`xgi` →
  `objective_scores` — exactly the CLI split.

**Design refinement (formation).** `--formation` applies to a **starting XI (11)**, but the
save→My Squad flow needs a **15** (the bench sets a 15's shape). So formation is a **display-only "best XI
shape" preview**, *not* part of the saveable build — the "Use this squad →" save stays a full 15.

---

### 🎯 Sprint Goal

**Objective:** bring the web to **full CLI build parity** via reliable form controls, keep the
Build → save → My Squad → tweak → download flow, and tidy the squad tabs into a logical group.

#### Success Criteria
- [x] Approach agreed (**ADR-062**) — full `squad` options as **widgets on Build Squad** (not NL); the
      15-man build is the saveable one; formation = an XI-only display preview; My Squad stays the tweaker
      + a rebuild link; the Ask-build → session-squad bridge; the tab rename/reorder
- [x] **US-200 (Build Squad — full option parity)** — widgets for **include · exclude · declared bench ·
      objective (points/value/xp/xgi) · no-xmins · weekly | bench-boost · include-unavailable** (budget /
      cheap / premium / differential already there), all wired to the *same* `select_squad`; the build
      stays a full 15; **Download** + **Use this squad →** unchanged; a display-only **best-XI-shape**
      preview (optional formation) that does **not** save
- [x] **US-201 (Tab reorg)** — rename `Squads`→**Squad Health**, `Build`→**Build Squad**; reorder the
      sidebar so **Build Squad · My Squad · Squad Health** are grouped; **My Squad** points to Build Squad
      for a full rebuild (a caption — `st.page_link` crashes AppTest); AppTest refs + Home.py copy updated
- [ ] **US-202 (Ask bridge, optional)** — the Ask "build me a squad…" answer surfaces the built squad so
      the web offers **"Use this squad →"** (sets the session squad → My Squad), for the NL-supported
      options; degrades unchanged when it's not a build answer
- [ ] **No engine change** — the optimiser/`decision_xp` are untouched; a test still asserts the web
      writes nothing server-side (`.save(`); existing **556** stay green
- [ ] Docs: ADR-062 + index, Architecture, README (web section), PROJECT_STATUS, Feedback_Log (resolved)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-200 | **Build Squad — full CLI option parity** (include/exclude/bench/objective/no-xmins/weekly/bench-boost/include-unavailable as widgets → same `select_squad`; 15-man build stays saveable; a display-only best-XI-shape preview). ADR-062. | High | ✅ Done | ~1 session |
| US-201 | **Tab rename + logical reorder** (Squads→Squad Health, Build→Build Squad; group Build Squad · My Squad · Squad Health; My Squad "Rebuild in Build Squad →" link; fix AppTest refs + Home copy). ADR-062. | High | ✅ Done | ~½ session |
| US-202 | **Ask-build → session squad bridge** (the "build a squad" answer → a "Use this squad →" button; the ask decision carries the built ids). *Optional / stretch.* ADR-062. | Medium | ⬜ To do | ~½ session |

---

### 🧭 Design sketch (to settle in ADR-062)

**Build Squad controls (US-200).** Group the widgets: **Budget · Name** | **Objective** (selectbox:
xp *(default)* / points / value / xgi) · **no-xmins** (checkbox, xp only) | archetypes **cheap · premium ·
differential** (as now) | **include · exclude · bench** (multiselects over player names) | **build mode**
(radio: *Balanced* / *Weekly (playing bench)* / *Bench Boost*) · **include-unavailable** (checkbox). Reuse
the CLI logic verbatim: `full=True` (15), `available_players(keep_ids=include∪bench)` unless
include-unavailable, `bench_weight=WEEKLY_BENCH_WEIGHT` for weekly, `archetype_bands` + `min_differentials`,
`decision_xp`/`objective_scores` for the score. Conflicts (include∩exclude, weekly+declared-bench) → a soft
`st.warning`, mirroring the CLI's `validate_*`. **Save flow unchanged** (Download / Use this squad → 15).
A small **"Preview best XI shape"** expander (optional formation via DEF/MID/FWD selectors, size 11,
`objective_scores`/`decision_xp`) — **display only**, no save (an XI ≠ a 15).

**Tab reorg (US-201).** Streamlit derives the sidebar label + order from the filename. Rename
`3_Squads.py`→`5_Squad_Health.py`, `6_Build.py`→`3_Build_Squad.py`, and renumber to group the trio:
proposed **1 Players · 2 Fixtures · 3 Build Squad · 4 My Squad · 5 Squad Health · 6 Transfer · 7 Captain ·
8 Ask · 9 News · 10 Trending** *(tweakable)*. Update the ~dozen `AppTest.from_file(_PAGES / "…")` refs and
Home.py’s page list. My Squad adds `st.page_link("pages/3_Build_Squad.py", label="🔧 Rebuild in Build Squad")`.

**Ask bridge (US-202, optional).** `_decide_build_squad` already computes a squad — surface its
`player_ids`/`bench_ids`/`name` in the decision dict (a `squad` field) and thread it onto `AskResult`; the
web Ask page, when present, renders a **"Use this squad →"** button calling `set_active_squad`. CLI output
unchanged. If the contract change feels heavy, defer — US-200 already covers the core need.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — AppTest drives Build Squad with each new control (objective switch, an exclude, a
   weekly build, include-unavailable) and asserts a 15 renders + Download/Use present; the reorg test refs
   resolve to the renamed files; the web-writes-nothing guardrail still holds. Existing **556** stay green.
2. **Manual smoke** — on the live app: build with an objective + include/exclude + bench-boost → a valid
   15; **Use this squad →** then open **My Squad** and tweak + download; the tabs read **Build Squad ·
   My Squad · Squad Health** in order; the "Rebuild in Build Squad →" link works; (US-202) an Ask build
   offers "Use this squad →".
3. **Docs updated** — ADR-062 + index, Architecture, README, PROJECT_STATUS, Feedback_Log (mark resolved).

---

### 📝 Session Progress Log

- **US-200 ✅ (gate + build)** — Recorded **ADR-062** (+ index; covers US-201/202). Rebuilt
  `pages/6_Build.py` (title "Build Squad") with the **full CLI option set** as widgets: **objective**
  (xp/points/value/xgi) · **no-xmins** (xp-only) · **build mode** radio (Balanced / Weekly / Bench Boost) ·
  **include-unavailable** · **include / exclude / declare-bench** multiselects (label → id, so a specific
  player is picked even when web_names repeat) — alongside the existing budget/name/cheap/premium/
  differential. All feed the **same** engine verbatim: `full=True` (15), `available_players(keep_ids=
  include∪bench)` unless include-unavailable, `bench_weight=WEEKLY_BENCH_WEIGHT` for Weekly, `archetype_bands`
  + `min_differentials`, score from `decision_xp` (xp, honours no-xmins) or `objective_scores`
  (points/value/xgi; xP still shown for reference with a caption). Soft `st.warning`s mirror the CLI's
  `validate_*` (include∩exclude, bench>4, weekly+declared-bench). **The saveable build stays a full 15** —
  Download / **Use this squad →** unchanged. A display-only **"Preview best XI shape"** expander (formation
  selectbox → size-11 build) that **does not save**. No engine change. Tests (+5 → **560**): objective
  switch rebuilds; weekly + include-unavailable; the formation preview adds no second download; and the
  **exclude control removes the player from the saved 15** (end-to-end). Existing Build tests unchanged.
  ruff clean. _US-201 (rename `6_Build.py`→`3_Build_Squad.py` + reorder) and US-202 (Ask bridge) next._

- **US-201 ✅ (build)** — `git mv` renamed 5 pages to rename the sidebar labels + regroup them:
  `6_Build.py`→**3_Build_Squad**, `8_My_Squad.py`→**4_My_Squad**, `3_Squads.py`→**5_Squad_Health**,
  `5_Transfer.py`→**6_Transfer**, `4_Ask.py`→**8_Ask** — so the sidebar reads **Players · Fixtures ·
  Build Squad · My Squad · Squad Health · Transfer · Captain · Ask · News · Trending** (the squad trio
  grouped). The Squad Health page's title/page_title updated (was "Analyse"). **My Squad** gains a
  caption pointing to **Build Squad** for a full rebuild — a **caption, not `st.page_link`**, because
  page_link to another page crashes under `AppTest` (no multipage runtime); the sidebar nav makes a text
  pointer sufficient. Updated the ~26 `AppTest.from_file` refs, Home.py's page list, and the
  `web_streamlit/__init__` docstring. Tests (+2 → **562**): the rename/regroup (new files exist, old gone)
  + My Squad points to Build Squad; all existing web tests pass under the new names. No seed/data change.
  ruff clean. _US-202 (Ask-build → session-squad bridge) next (optional)._

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
