# Sprint 085: Availability flags in the player tables

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½–1 session (a shared availability-flag helper + a Fit column across the web player tables)
**Carried Over:** none

> **Direction (owner — from the backlog, "availability flags in the ranking views"):**
> Surface **injury / doubt / suspension** flags in the player tables (Players Pool + the stat boards) the
> way the **squad / captain** views already warn — so a user scanning the tables can see *"is this player
> fit?"* at a glance, without cross-checking the News tab.

---

### 🔎 Verified at planning (real data)

- **Meaningful now (preseason).** Status split: **a 512 · i 32 (injured) · d 18 (doubtful) · u 7
  (unavailable) · s 3 (suspended)** → **60 flagged** of 572. Each flagged player carries `status`, `chance`
  (0 for injured/suspended), and a `news` string (e.g. *"Groin injury - Expected back 22 Aug"*). So flags
  are live today (they sharpen further as GW1 nears).
- **`crowd_flags` doesn't cover injuries** — it's ownership / momentum / price / form only (ADR-057). So
  availability is a **separate** flag (a new helper), not folded into Trends.
- **Sourcing the flag per table.** The **Pool** and the **xG** board render **raw player rows** (they have
  `status`) → flag directly. The **over/under · DefCon · clean sheets** boards render *trimmed* analytics
  dicts (web_name/team/position, **no status**) — but each `render_*` already receives the **full `players`
  list**, so the view builds a `{(web_name, team): flag}` lookup from it. **No analytics change.**
- **No per-cell hover in `st.dataframe`** (ADR-072) → the flag is a compact emoji column with a **legend
  caption + a header tooltip**; the **News** tab keeps the full text.

---

### 🎯 Sprint Goal

**Objective:** every web player table shows a compact **Fit** column — 🚑 injured · 🚫 suspended · ⛔
unavailable · ❓ doubtful (blank = available) — so availability is visible where players are ranked, with a
legend and a pointer to News for detail. Display-only; the analytics and rankings are untouched.

#### Success Criteria
- [x] **US-228 (helper + Pool, ADR-074)** — a shared **`availability_flag(player)`** → an emoji (or `""` for
      available), with a stable vocabulary (🚑 i · 🚫 s · ⛔ u/n · ❓ d). A **Fit** column on the **Players
      Pool** (blank = available), a one-line **legend** caption, and a header tooltip. Distinct from the
      rating circles (🟢🟡🟠🔴) so the two don't blur.
- [x] **US-229 (stat boards)** — the **Fit** column on all four stat boards (**over/under · DefCon · clean
      sheets · xG**): direct on xG (raw rows), via a `{(web_name, team): flag}` lookup on the three trimmed
      boards. Same legend/tooltip. No analytics change.
- [ ] **No drift** — `crowd_flags`, the rating (ADR-071/073), the number formatting (ADR-072), and the
      analytics are unchanged; existing **613** stay green; ruff clean. (CLI ranking views = a possible
      follow-up, out of scope here.)
- [ ] Docs: ADR-074 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-228 | **Availability flag helper + Pool** — `availability_flag(player)` (🚑/🚫/⛔/❓, blank=available) + a **Fit** column + legend on the Players Pool. ADR-074. | High | ✅ Done | ~½ session |
| US-229 | **Flags on the stat boards** — the Fit column on over/under · DefCon · clean sheets · xG (join via the full players list for the trimmed boards). | Medium | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

**US-228 (ADR-074).** A pure `availability_flag(player) -> str` (alongside `crowd_flags`/`is_unavailable` in
the analytics — same status vocabulary): `{"i": "🚑", "s": "🚫", "u": "⛔", "n": "⛔", "d": "❓"}.get(status,
"")` (available `"a"` → `""`). Export it. In `views/players.py::render_pool`, add a **Fit** column
(`availability_flag(p)`) — placed early (right after Player/Team/Pos) — plus an `AVAILABILITY_LEGEND` caption
and a column tooltip (via the `column_config` `help=` path, ADR-072). `"Fit"` is a text column (not in
`FORMATS`) → renders as-is.

**US-229.** `render_xg` adds the same `availability_flag(r)` column (raw rows). `render_over_under` /
`render_defcon` / `render_cleansheet` build `flag = {(p["web_name"], p["team"]): availability_flag(p) for p
in players}` and add `"Fit": lambda r: flag.get((r["web_name"], r["team"]), "")`. The `_board` `col_help`
gains the Fit tooltip; the legend caption is shared.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `availability_flag` returns the right emoji per status (i/s/u/n/d) and `""` for `a`; the
   Pool + a stat board render a **Fit** column with a flag for a known-injured player and blank for an
   available one; the legend caption is present. Existing **613** stay green.
2. **Manual smoke** — the Pool shows 🚑 next to injured players (e.g. Saliba/J.Timber) and blank for the fit;
   the stat boards show the same; the News tab still holds the detail.
3. **Docs updated** — ADR-074 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-228 (availability flag helper + Pool, ADR-074).** Surfaced the ingested `status` as a compact flag.
- **Helper** — `analytics/crowd.py::availability_flag(player)` (next to `crowd_flags`, same status vocab):
  `{"i":"🚑","s":"🚫","u":"⛔","n":"⛔","d":"❓"}.get(status,"")` → `""` for available/unknown; empty-safe
  (Row or dict). Emojis chosen **distinct from the rating circles** (🟢🟡🟠🔴). A shared `AVAILABILITY_LEGEND`
  constant; both exported.
- **Pool** — `render_pool` adds a **Fit** column (right after Player/Team/Pos), a legend caption, and a
  header tooltip (via the `column_config` `help=` path, ADR-072). Display-only; `crowd_flags`/rating/analytics
  unchanged.
Smoke (real data): the Pool's Fit column shows 🚑 for injured players (Saliba/J.Timber et al.) and blank for
the fit. Tests: +3 (`availability_flag` per status + distinct-from-other-flags; the Pool Fit column + legend).
ruff clean, full suite **616** green.

**US-229 (Fit column on the stat boards).** Extended the flag to all four boards via `_board`. `_board` now
takes an optional `flag=(row → emoji)`: when given, it inserts a **Fit** column (right after Pos), the Fit
tooltip, and the shared legend caption — one place, so all boards are consistent. **xG** passes
`flag=availability_flag` (raw rows carry `status`); **over/under · DefCon · clean sheets** pass a
`_fit_lookup(players)` closure — a `{(web_name, team): flag}` map built from the full `players` list each
render func already receives (so the trimmed analytics dicts need no `status`). No analytics change.
Smoke: all four boards show 🚑/❓/🚫 in the Fit column, no crash. +1 test (`test_stat_boards_show_the_
availability_fit_column`). ruff clean, full suite **617** green.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **613 → 617** (+4); ruff clean; CI-parity green.

**Delivered**
- **US-228 — availability flag helper + Pool (ADR-074).** `availability_flag(player)` (🚑 injured · 🚫
  suspended · ⛔ unavailable · ❓ doubtful; blank = available), a shared `AVAILABILITY_LEGEND`, and a compact
  **Fit** column on the Players Pool.
- **US-229 — Fit on the stat boards.** The same column on over/under · DefCon · clean sheets · xG, via a
  small `_board(flag=…)` extension.

**What went well**
- **Reused ingested data, zero analytics drift.** `status`/`chance` were already there; a display helper +
  a view-side lookup (for the trimmed boards) meant the analytics dicts stayed untouched.
- **One refactor covered four boards** — `_board`'s optional `flag=` inserts the column + tooltip + legend
  in one place, so the boards can't drift; the join for the trimmed boards keyed off the full `players`
  list each render func already had.
- **Distinct vocabulary** — the availability emojis are guarded (a test) against colliding with the crowd
  flags or the rating circles, so a glance reads cleanly.

**Watch-outs / follow-ups**
- Emoji-only can be cryptic → mitigated with a legend caption + a header tooltip + the News tab for detail;
  there's no per-cell hover in `st.dataframe`.
- The trimmed boards join by `(web_name, team)` (the dicts lack an id) — fine for a display flag.
- **CLI ranking views** (`table`/`xg`) don't show the flag yet — a possible follow-up.
- **Reseed the deploy** so testers see Sprints 081–085 (the Cloud seed is still 570-player / stale).

See `Sprint85_Lessons_Learnt.md` for the detailed retro.
