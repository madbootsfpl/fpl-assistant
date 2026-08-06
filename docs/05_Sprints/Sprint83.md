# Sprint 083: Consistent number formatting · refresh the Help tab

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½–1 session (a shared column-format convention across the web tables + a Help content refresh)
**Carried Over:** none

> **Direction (owner, tester feedback — 2 items):**
> 1. **Number formatting.** *"Keep to xx.x — Value/£m shows 24.2345, prefer 24.2. Player cost to one
>    decimal too: 6 should be 6.0 to keep the tables aligned."*
> 2. **Update the Help tab** with recent changes and improvements.

---

### 🔎 Verified at planning (real data / code)

- **The offender is real.** `Val/£m` = `rank_players`' `value` is an **unrounded float** (e.g. Guéhi
  `29.833333333333332`); and **299/572** prices are whole numbers (6.0, 8.0, 12.0) that a mixed `st.dataframe`
  column can render as `6` — so the money columns don't line up. This is a **web `st.dataframe`** issue only:
  the **CLI** text tables already format to fixed decimals via their renderers (`24.2345` can't appear there),
  so the CLI is **out of scope**.
- **The fix is column config, not pre-rounding.** `st.column_config.NumberColumn(label, format="%.1f")`
  forces `6.0` / `24.2`, **right-aligns**, and keeps the column **numeric + sortable** — better than
  formatting to a string (which left-aligns and breaks sorting). It also composes with the `help=` tooltips
  added in ADR-071.
- **Tables affected:** the **Pool** (£m · Val/£m · Own% · Form · ICT · Pts), the **four stat boards**
  (`_board`: Mins · Actual/Exp · DC/90 · Thr · xGC/90 · xG/xA/xGI/xGC · Diff/Margin), and the **squad tables**
  (`tables.render_player_table` — Captain/Transfer/…: £m · xP · out/in).
- **Owner's decimal call:** money/value/%/form/ICT → **1dp**; counts (Pts, Mins) → **integer**; the
  **expected-goals family** (xG · xA · xGI · xGC · xGC/90) → **2dp** (FPL-native precision; 1dp would blur
  small ratios like 0.52 vs 0.55); signed diffs (Diff, Margin) → **`%+.1f`**.
- **Help is stale** (post Sprints 080–082): the step-by-step body doesn't mention **This week** (the gameweek
  plan), the **🟢…🔴 quality ratings** on the stat boards, or the **Pool showing the table first**; the
  Squads sub-nav list omits **This week**; the Ask examples lack the *"what should I do this week"* prompt.

---

### 🎯 Sprint Goal

**Objective:** every web table lines up — one decimal for money/value/%, two for the xG family, integers for
counts, `6` always shows as `6.0`; and the Help tab reflects everything shipped since it was written
(This week · quality ratings · Pool table-first).

#### Success Criteria
- [x] **US-223 (number formatting, ADR-072)** — a shared **format convention** (`web_streamlit/formats.py`):
      a label→printf map + a helper that returns `st.column_config.NumberColumn(label, format=…, help=…)`.
      Applied to the **Pool**, the **four stat boards** (`_board`), and the **squad tables**
      (`render_player_table`). Money/value/%/form/ICT → **1dp**; Pts/Mins → **integer**; xG/xA/xGI/xGC/xGC/90
      → **2dp**; Diff/Margin → **`%+.1f`**. Columns stay **numeric + sortable** (NumberColumn, not strings).
      No analytics change; no server writes; the CLI is untouched.
- [x] **US-224 (refresh Help)** — the Help guide reflects the current app: **This week** (the grounded
      gameweek plan) in the Squads flow + a step/pointer; the **quality ratings** noted in the research step;
      the **Pool table-first**; a *"what should I do this week for my-team?"* Ask example; the Squads sub-nav
      list includes **This week**. Content only — no input widgets (the tooltip-coverage test still holds).
- [ ] **No drift** — existing **607** stay green; ruff clean.
- [ ] Docs: ADR-072 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-223 | **Consistent number formatting** — a shared `NumberColumn` format convention (1dp money/value/%, 2dp xG family, integer counts, +/- signed) across the Pool, the four stat boards, and the squad tables. ADR-072. | High | ✅ Done | ~½ session |
| US-224 | **Refresh the Help tab** — add This week / the gameweek plan, the 🟢…🔴 quality ratings, the Pool table-first + the new Ask example; fix the Squads sub-nav list. | Medium | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

**US-223 (ADR-072).** New `src/web_streamlit/formats.py`: `FORMATS` (a `{column-label: printf}` map encoding
the convention) + `column_config(labels, *, help=None, images=())` → a `{label: st.column_config.*}` dict
(NumberColumn with `format=` for numeric labels, ImageColumn for image cols, a plain Column for text like
`Rating`, each carrying its `help=` when given). `render_pool` and `_board` (views/players.py) and
`render_player_table` (tables.py) build their `column_config` through it. `_board` changes the pre-formatted
`Diff`/`Margin` **string** cells (`f"{r['diff']:+.1f}"`) back to the raw **number** so `NumberColumn`
right-aligns them with a `%+.1f` format. The raw analytics values are untouched (formatting is display-only,
so sorting still uses the real number).

**US-224.** Edit `pages/7_Help.py` (content): add **This week** to the Quick-start + the Squads sub-nav
caption + a short line in step 4 (or a new sub-step) describing the gameweek plan (captain · lineup · a
transfer · flags, verified); note the **🟢…🔴 quality rating** in step 5 (research → Players stat boards);
mention the **Pool shows the table first**; add `what should I do this week for my-team?` to the Ask
examples. Keep it static (no widgets).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — a `formats` unit test (the map returns NumberColumn with the right `format` per column
   type; integer vs 1dp vs 2dp vs signed); the Pool + a stat board + a squad table apply the config (AppTest:
   the dataframe renders, no crash, columns present); Help renders and contains the new content (This week /
   rating / the new Ask example). Existing **607** stay green.
2. **Manual smoke** — the Pool shows `6.0` and `24.2` (not `6` / `24.2345`), right-aligned; xGI still `4.42`;
   the Help tab reads current (This week, ratings, the gameweek Ask example).
3. **Docs updated** — ADR-072 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-223 (number formatting, ADR-072).** A shared display-only convention so the web tables line up.
- **`src/web_streamlit/formats.py`** — a `FORMATS` label→printf map + `column_config(labels, *, help, images)`
  → a `{label: st.column_config.*}` dict: `NumberColumn(format=…, help=…)` for numeric labels, `ImageColumn`
  for image labels, a plain `Column(help=…)` for text-with-help, omitted otherwise. Policy: money/value/%/
  form/ICT → **1dp**; Pts/Mins → **integer**; xG/xA/xGI/xGC/xGC/90 → **2dp**; Diff/Margin/+xP → **`%+.1f`**.
- **Applied** in `views/players.py` (Pool + `_board`) and `tables.py` (`render_player_table`, keyed by the
  union of row labels). The `_board` `Diff`/`Margin` cells switch from pre-formatted **strings** to raw
  **numbers** so `NumberColumn` right-aligns + signs them. Removed the now-dead `_BADGE` constant.
- **Display-only** — the raw analytics values are untouched (a test proves the frame stays numeric/sortable,
  not stringified). CLI unchanged; no server writes.
Smoke (real data): `value` 29.833… now shows as `29.8`, whole-number prices as `6.0`; xGI still `4.42`.
Tests: +5 (4 `formats` unit — 1dp/int/2dp/signed, image/text/help, the coverage guard; 1 web — Pool money
columns stay numeric). ruff clean, full suite **612** green.

**US-224 (refresh the Help tab).** Brought the step-by-step guide up to date with Sprints 080–083:
- **Quick start** + the Squads sub-nav caption now include **This week**.
- **Step 4** retitled *"Plan your week & improve it → Squads → This week · Transfer · Captain"* with a lead
  paragraph on the grounded gameweek plan (captain · lineup · a transfer · flags, verified; degrades without
  Ollama).
- **Step 5 (research → Players)** notes the **table-first** Pool and the **🟢…🔴 quality rating** (vs the
  players shown) on clean sheets / xG.
- **Ask examples** gained `what should I do this week for my-team?`.
Content only — no widgets. The Help test now also asserts "This week", the gameweek Ask example, and the
"quality rating" note. ruff clean, full suite **612** green.

**Housekeeping:** noticed `data/seed.db` had drifted to 572 players (vs the committed 570) from an incidental
write during the session — restored it to HEAD so the seed changes only via a deliberate `reseed` + commit.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **607 → 612** (+5); ruff clean; CI-parity green.

**Delivered**
- **US-223 — consistent number formatting (ADR-072).** A shared `web_streamlit/formats.py` convention
  (`FORMATS` + `column_config`) formatting every web table via `st.column_config.NumberColumn` — money/value/
  %/form/ICT → 1dp (`6.0`, `24.2`), counts → integer, the xG family → 2dp, signed diffs → `%+.1f`. Applied
  to the Pool, the four stat boards, and the squad tables. Display-only (columns stay numeric/sortable);
  CLI untouched.
- **US-224 — refresh the Help tab.** The guide now reflects Sprints 080–083: This week (the gameweek plan),
  the 🟢…🔴 quality ratings, the table-first Pool, and a "this week" Ask example.

**What went well**
- **The right layer for a display fix** — formatting via `NumberColumn` (not rounding the data, not
  stringifying) kept the columns sortable and the analytics pure; a test pins that the frame stays numeric.
- **One convention, one place** — `FORMATS` means the three tables can't drift, and it composed cleanly with
  the ADR-071 tooltips (same `NumberColumn`).
- Caught + reverted an **incidental `data/seed.db` drift** (572 vs the committed 570) so the commits stayed
  pure — the deploy seed only moves via a deliberate `reseed`.

**Watch-outs / follow-ups**
- A new numeric column must be added to `FORMATS` or it renders at Streamlit's default — the `formats`
  coverage-guard test makes that visible.
- The deployed seed is still **570** (stale vs a live 572-player refresh). When you want testers on fresh
  data: `python app.py reseed` → commit → push (the US-219 workflow).

See `Sprint83_Lessons_Learnt.md` for the detailed retro.
