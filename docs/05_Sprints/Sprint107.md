# Sprint 107: Ask readability + a "fit" emoji

**Dates:** 2026-08-08 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (two display fixes from tester feedback)
**Carried Over:** none

> **Direction (tester feedback):**
> 1. *"Ask tab — sentences aren't wrapping and are a bit hard to read; and it doesn't auto-scroll down to the
>    answer to the current question."*
> 2. *"Players → Fit — should there be an emoji if a player **is fit** rather than leaving it blank?"*

---

### 🔎 Verified at planning

- **Ask answers render in `st.code(answer, language=None)`** — a monospace block that **doesn't wrap**, so long
  narration sentences overflow. This Streamlit's `st.code` has a **`wrap_lines=True`** flag (verified) → it
  wraps long lines *and* keeps short lines (the aligned squad tables / plan / Why-Risk blocks) intact. One-word
  fix, no restructuring.
- **The Ask history replays oldest-first**, so a new answer appends at the **bottom** and the page doesn't
  scroll to it. The app runs in an iframe with **same-origin access** to the parent, so a tiny scroll-to-bottom
  script (after the history) brings the newest answer into view.
- **`availability_flag` is used two ways:** as the **Fit column** display *and* as a **truthiness test** for
  "is this player a concern" (the My Squad *who's-flagged* caption; the gameweek plan's flags). So it must keep
  returning `""` for a fit player — a **fit ✅ emoji** needs a **separate display helper**, not a change to
  `availability_flag`.

---

### 🎯 Sprint Goal

**Objective:** the Ask tab reads well (wrapped prose, the newest answer in view) and the Fit column shows a
positive **✅** for fit players (not just blank) — small, honest display fixes; the analytics/engine untouched.

#### Success Criteria
- [ ] **US-275 (Ask readability + auto-scroll)** — render Ask answers with **`st.code(…, wrap_lines=True)`** so
      long sentences wrap (tables/blocks still align); after replaying the history, a small **scroll-to-bottom**
      (an `st.iframe`/`components` script, same-origin) brings the latest Q&A into view. No content change.
- [ ] **US-276 (a "fit" emoji)** — a `fit_flag(player)` display helper = the availability flag when flagged,
      else **✅** (fit); used in the **Fit** column on the **Pool**, the **stat boards**, and the **CLI** tables.
      `availability_flag` is **unchanged** (its `""`-for-fit truthiness still drives the flagged-players logic).
      The `AVAILABILITY_LEGEND` gains "✅ fit".
- [ ] **No drift** — display-only; `availability_flag` semantics + the analytics unchanged; existing **707**
      stay green (Fit-column tests updated to expect ✅ for fit); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help (extends ADR-052/074 — noted).

---

### 🧭 Design sketch

**US-275.** `pages/4_Ask.py`: change the history replay to
`st.chat_message("assistant").code(answer, language=None, wrap_lines=True)`. After the loop, when there's
history, render a one-off scroll nudge — a minimal `st.iframe`/`components.html` with
`window.parent.scrollTo(0, window.parent.document.body.scrollHeight)` (in a `setTimeout` so it runs after
layout). Height 0 so it's invisible. Purely presentational.

**US-276.** `analytics/crowd.py`: `fit_flag(player) -> str` = `availability_flag(player) or "✅"` (empty-safe);
extend `AVAILABILITY_LEGEND` with "✅ fit". Swap the **Fit** column source from `availability_flag` →
`fit_flag` in `views/players.py` (Pool + `_board` / `_fit_lookup`) and the CLI (`ui/table.py`, `ui/xg.py`).
The truthiness-based flagged logic (My Squad caption, gameweek flags) keeps using `availability_flag` (still
`""` for fit — unchanged).

**Deferred:** nothing material.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-275 | **Ask readability + auto-scroll** — `wrap_lines=True` + a scroll-to-bottom nudge. | High | ⬜ To do | ~¼ session |
| US-276 | **A "fit" ✅ emoji** — a `fit_flag` display helper on the Fit columns; legend updated. | High | ⬜ To do | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the Ask page renders wrapped answers (a code block with `wrap_lines`) without crashing;
   `fit_flag` returns ✅ for a fit player and the availability flag when flagged (empty-safe); the Pool/stat
   boards show ✅ in the Fit column for fit rows; `availability_flag` still returns `""` for fit (the flagged
   logic unchanged); the legend mentions ✅. Existing **707** stay green (Fit assertions updated).
2. **Manual smoke** — Ask: a long answer wraps and the page scrolls to the latest Q&A; Players → Pool: fit
   players show ✅, injured/doubtful keep 🚑/❓.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help.

---

### 📝 Session Progress Log

**US-275 — Ask readability + auto-scroll.** ✅ Done.
- `pages/4_Ask.py`: the answer now renders with **`st.code(answer, language=None, wrap_lines=True)`** — long
  narration sentences **wrap** while the aligned tables / plan / Why-Risk blocks stay readable.
- After replaying the history, a one-off **scroll-to-bottom** nudge (a `height=1` `st.iframe` running
  `window.parent.scrollTo(…, behavior:'smooth')` in a `setTimeout`, using the iframe's same-origin access)
  brings the newest Q&A into view. Invisible; only when there's history.
- **Tests (+1 assertion):** the clickable-examples test now asserts the rendered answer has `wrap_lines=True`.
  **707** green, ruff clean. (Fixed `st.iframe` height: 0 is invalid → 1.)
- **Manual smoke:** a long Ask answer wraps instead of overflowing; the page scrolls down to the latest answer.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
