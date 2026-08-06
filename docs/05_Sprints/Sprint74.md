# Sprint 074: Help tooltips (ⓘ) across the web app

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (UI polish — mechanical, no analytics change)
**Carried Over:** none

> **Direction (owner, tester feedback):** add a small **ⓘ help tooltip** over **all feature options** so a
> user can understand what each control does.

---

### 🔎 Verified at planning (real code)

- Streamlit renders an **ⓘ tooltip** for any widget given a `help="…"` string — exactly what the tester
  wants. It's on `selectbox`/`multiselect`/`slider`/`number_input`/`text_input`/`checkbox`/`radio`/`button`/
  `download_button`/`file_uploader`. **Exceptions:** `st.tabs` labels and `st.chat_input` (Ask) take no
  `help=` → those keep their existing captions.
- **AppTest exposes `.help`** on widgets → a **coverage test** can assert every input control has a
  non-empty tooltip (enforces "all options", stops regressions).
- **High-leverage shared components** — adding `help=` once covers many pages:
  `filters.py` (Team/Position/Player + price → Players & Player Stats), `paginate.py` (the page selectbox →
  3 pages), `squads.py` (`render_sidebar` import/upload + `squad_picker` → every squad page).
- **Current coverage:** Build Squad has 4 `help=` (objective/no-xmins/mode/bench); everywhere else is bare.

---

### 🎯 Sprint Goal

**Objective:** a concise, consistent **ⓘ tooltip on every feature option** across the web — added at the
shared components (for leverage) and on each page's own controls — with a coverage test enforcing it.
Analytics untouched.

#### Success Criteria
- [x] Approach agreed (**ADR-065**) — concise, action-oriented `help=` on **every input control**
      (selectbox/multiselect/slider/number_input/text_input/checkbox/radio); added at the shared components
      + per page; important **buttons** get help too; tabs/chat_input keep captions; a coverage test
- [x] **US-208 (shared + browse pages)** — `help=` in `filters.py`, `paginate.py`, `squads.py`
      (`render_sidebar`, `squad_picker`); + Players (sort), Fixtures (weeks), Trending (the buzz button).
      The **coverage test** built here (asserts input widgets on these pages carry help)
- [x] **US-209 (squad/decision pages)** — `help=` on the remaining Build Squad controls, My Squad (rename ·
      swap · bench), Transfer (bank · count · apply), Captain (set-captain); coverage test extended to all
      nine pages
- [x] **No behaviour change** — help text only; no analytics/data change; the web writes nothing
      server-side (guardrail holds); existing tests stay green — **579** (+1)
- [ ] Docs: ADR-065 + index ✅; Architecture, PROJECT_STATUS _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-208 | **Help tooltips — shared + browse pages** — `filters.py` · `paginate.py` · `squads.py` (sidebar + picker) · Players · Fixtures · Trending; + a coverage test asserting input widgets carry help. ADR-065. | High | ✅ Done | ~½ session |
| US-209 | **Help tooltips — squad/decision pages** — Build Squad (remaining) · My Squad · Transfer · Captain; coverage test extended. ADR-065. | High | ✅ Done | ~½ session |

---

### 🧭 Design sketch (to settle in ADR-065)

**Convention.** One short, action-oriented sentence per control — *what it does / what picking it means* —
in a consistent voice. Written **inline** (`help="…"` right on the widget, so the control + its help live
together); the shared components carry help for the controls they own. Examples:
- Filter — Team: *"Show only players from these teams (empty = all)."*; Player: *"Pick specific players to
  focus on."*
- Players — Sort by: *"Order the table: total points, value (pts/£m), team, or position."*
- Build Squad — Budget: *"The most you'll spend on all 15."*; Build mode: *"Balanced · Weekly (a cheap
  playing bench) · Bench Boost (maximise all 15)."*
- Sidebar — Manager-ID: *"Your FPL team's numeric id (from the FPL site URL) — imports your real squad
  (from GW1)."*

**Coverage test (`tests/test_help_tooltips.py`).** For each page, AppTest-run it and assert **every**
`selectbox/multiselect/slider/number_input/text_input/checkbox/radio` has a non-empty `.help`. (Buttons are
checked loosely — key ones get help, but the strict gate is the input "options" the tester named.)
`st.tabs`/`st.chat_input` are exempt (no `help=`; captions cover them).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the coverage test asserts input widgets on the sprint's pages carry non-empty help;
   the web-writes-nothing guardrail holds. Existing **578** stay green.
2. **Manual smoke** — on the live app: hovering the ⓘ on the filters, sort, budget, build-mode, bank slider,
   manager-import etc. shows a helpful sentence.
3. **Docs updated** — ADR-065 + index, Architecture, PROJECT_STATUS.

---

### 📝 Session Progress Log

- **US-208 ✅ (gate + build)** — Recorded **ADR-065** (+ index; covers US-209). Added concise, action-
  oriented `help=` to the **shared components** — `filters.py` (Team / Position / Player + max-price),
  `paginate.py` (the page selectbox), `squads.py` (`squad_picker` + `render_sidebar`'s upload · manager-ID ·
  Import button) — so Players, Player Stats, Trending and every squad page inherit tooltips. Plus the
  browse-page controls: Players **Sort by**, Fixtures **Weeks to show**, Trending's buzz **button**. New
  `tests/test_help_tooltips.py` — a coverage test that AppTest-runs each **browse page** (Players ·
  Player Stats · Fixtures · Trending) and asserts **every** input widget
  (selectbox/multiselect/slider/number_input/text_input/checkbox/radio) has a non-empty `.help`
  (tabs/chat_input exempt). +1 test → **579** green, ruff clean. **Smoke (real DB):** every Players control
  shows its tooltip (Team/Position/Player/Sort/Page/Max price). No behaviour change. _US-209 (squad/decision
  pages) next._

- **US-209 ✅ (build)** — `help=` on the remaining squad/decision controls: **Build Squad** (budget · name ·
  include-unavailable · cheap/premium/differential · must-include · must-exclude · formation preview —
  objective/no-xmins/mode/bench already had it), **My Squad** (rename · replace · with · bench), **Transfer**
  (bank · transfers-count · apply-swap), **Captain** (set-captain). Squad Health has no page-specific inputs
  (its picker is covered by `squads.py`). Extended the coverage test to all nine pages. **Smoke (real DB):**
  Build Squad's 14 input controls (incl. the sidebar manager-ID) all carry help, none missing. **579** green
  (the coverage test now gates all pages), ruff clean. No behaviour change.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
