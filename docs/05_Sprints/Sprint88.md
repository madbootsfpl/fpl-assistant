# Sprint 088: UX polish — clickable Ask examples · CLI availability flags · chance% on ❓

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/3 stories)
**Capacity:** ~½–1 session (three small, independent polish wins)
**Carried Over:** none

> **Direction (owner — a polish bundle from the backlog / recent-retro follow-ups):**
> 1. **Clickable Ask examples** — make the Ask tab's example prompts *clickable* (run on click), not
>    copy-paste.
> 2. **Availability flags on the CLI ranking views** — the 🚑 Fit flag on `table`/`search`/`filter`/`xg`,
>    the way the web tables (ADR-074) now show it.
> 3. **A chance% on the ❓ doubtful flag** — show *how* doubtful (e.g. `❓ 75%`).

*No new ADR — these extend **US-227** (Ask examples) and **ADR-074** (availability flags).*

---

### 🔎 Verified at planning (code)

- **Ask examples are a `st.code` block** (US-227) — copy-paste. Making them clickable = a **button per
  example** that runs it through the *same* path the chat box uses (`ask.answer(...)` → append to history).
  `st.chat_input` can't be pre-filled programmatically, so "clickable" means **run on click**.
- **The CLI ranking views share `render_player_table`** (`ui/table.py`, used by `table`/`search`/`filter`)
  built on the byte-aligned `_table.render_rows` (ADR-025). `availability_flag` (ADR-074) is already in
  analytics. Adding a flag column means: **put it last** so an emoji's terminal width (~2 cells) can't
  cascade into the other columns' alignment, and **update the byte-exact table tests** (a column was added).
  `xg` uses its own `render_xg_table` — same last-column treatment.
- **`availability_flag` returns emoji-only today** (`"d" → "❓"`). Real data has `chance` on doubtful players
  (e.g. 75%); adding it (`"❓ 75%"`) enriches **both** the web Fit column and the new CLI column from one
  change.

---

### 🎯 Sprint Goal

**Objective:** the Ask examples are one-click, the CLI ranking tables show availability like the web, and a
doubtful flag shows the chance of playing — small, tester-facing quality wins. Display-only; no analytics
change.

#### Success Criteria
- [x] **US-234 (clickable Ask examples)** — each example prompt on the Ask page is a **button**; clicking it
      runs the question (same grounded pipeline + history as typing it). A shared helper feeds both the chat
      box and the buttons; the built-squad "Use this squad →" bridge still works.
- [x] **US-235 (CLI availability flags)** — a **Fit** column (🚑/🚫/⛔/❓, blank = available) as the **last**
      column on `render_player_table` (→ `table`/`search`/`filter`) and `render_xg_table` (→ `xg`), reusing
      `availability_flag`. Byte-exact table tests updated. Extends ADR-074.
- [ ] **US-236 (chance% on ❓)** — `availability_flag` shows the chance on a doubtful player (`❓ 75%` when
      `chance` is present, else `❓`); other statuses unchanged. Improves the web Fit column + the new CLI
      column at once. The legend still reads "❓ doubtful".
- [ ] **No drift** — display-only; `decision_xp`/the analytics unchanged; existing **622** stay green (some
      CLI-table assertions updated for the new column); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README (no new ADR — extends US-227 / ADR-074).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-234 | **Clickable Ask examples** — a button per example on the Ask page that runs it (shared handler). | Medium | ✅ Done | ~¼ session |
| US-235 | **CLI availability flags** — a last-column **Fit** flag on `render_player_table` (table/search/filter) + `render_xg_table` (xg). Extends ADR-074. | Medium | ✅ Done | ~¼–½ session |
| US-236 | **chance% on ❓** — `availability_flag` appends the chance on doubtful (`❓ 75%`). | Low | ⬜ To do | ~¼ session |

---

### 🧭 Design sketch

**US-234.** `pages/4_Ask.py`: extract `_ask(question)` (answer → `render_ask` → append to `history` → stash
`built_squad`) used by both `st.chat_input` and the example buttons. Replace the `st.code` list with a
column of `st.button(example, key=…)`; on click → `_ask(example)` → `st.rerun()` so the replay loop shows
it. Keep the expander (expanded until the first turn).

**US-235.** `ui/table.py`: append `Col("Fit", W, "<", lambda r: availability_flag(r))` **last** in `_COLS`
(emoji width stays at the row end, so the aligned columns before it are unaffected). Same for
`ui/xg.py::render_xg_table`. Update the byte-exact expectations in the affected table tests. `availability_flag`
is imported from `src.analytics`.

**US-236.** `analytics/crowd.py::availability_flag`: for `status == "d"`, return `f"❓ {chance}%"` when
`chance` is not None, else `"❓"` (read `chance` via the existing `_get`, empty-safe). Other statuses
unchanged. Update the `availability_flag` unit tests (doubtful with/without chance).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — clicking an Ask example records a turn (a stubbed narrator, no network); the CLI
   `table`/`xg` render a Fit column with a flag for a known-injured player + blank for a fit one; a doubtful
   player reads `❓ 75%` (and `❓` with no chance). Existing **622** stay green (CLI-table assertions updated).
2. **Manual smoke** — Ask → click an example → a grounded answer appears; `python app.py table` shows 🚑 on
   injured players; a doubtful player shows `❓ <chance>%`.
3. **Docs updated** — PROJECT_STATUS, Architecture, README.

---

### 📝 Session Progress Log

**US-234 (clickable Ask examples).** Replaced the copy-paste `st.code` list with a **button per example**
(`pages/4_Ask.py`). Extracted a shared `_ask(question)` helper (answer → `render_ask` → append to history →
stash `built_squad`) used by **both** the chat box and the buttons; clicking a button runs `_ask(ex)` then
`st.rerun()` (the replay loop shows the turn). The chat-input handler now also calls `_ask` + `st.rerun()`
(unified). The build-answer "Use this squad →" bridge is unchanged. No new ADR (extends US-227). Smoke: 7
example buttons; clicking one records a grounded turn. Updated the US-227 test → clickable
(`test_ask_page_example_prompts_are_clickable`). ruff clean, full suite **622** green.

**US-235 (CLI availability flags).** Added `Col("Fit", 4, "<", availability_flag)` as the **last** column of
`ui/table.py::_COLS` (→ `table`/`search`/`filter`) and `ui/xg.py::_COLS` (→ `xg`), importing
`availability_flag` from `src.analytics` (a valid ui→analytics dependency; `rank_players` does `dict(row)` so
`status`/`chance` survive). Last-column placement means an emoji's ~2-cell terminal width can't push the
aligned columns before it out of line — verified on real data (Garner/J.Timber 🚑, Wharton ❓, fit players
blank; Player…Val/£m stay aligned). The existing byte-exact table/xg tests are substring-based + their
fixtures lack `status` (→ blank, empty-safe), so none needed changing. Extends ADR-074 (no new ADR). +2
tests. ruff clean, full suite **624** green.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
