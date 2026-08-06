# Sprint 082: Make the stat numbers interpretable · per-tab header graphics

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1–1.5 sessions (a reusable quality-rating helper + caption/tooltip clarity; a cosmetic header pass)
**Carried Over:** none

> **Direction (owner, tester feedback — 2 themes):**
> 1. **Interpreting the stat boards.** *"For Players, what does xGI 9.72 mean — or is it just relative to
>    others in the table?"* The tester correctly worked out `xGC/90 = xGC × 90 ÷ mins` (Calafiori 0.52) but
>    asks how a **casual user** reads it, and suggests a **colour graphic beside the score** (they shared a
>    ChatGPT band table: 0.5 excellent → 2.0+ very poor).
> 2. **Per-tab header graphics.** *"You have a nice graphic on Home (⚽ FPL Assistant) — could we do the same
>    for each of the other tabs?"*

---

### 🔎 Verified at planning (real data)

- **The derivation is right; the values are absolute.** `xGI`/`xGC` are **absolute season totals** (a model's
  expected goals, last-season carryover preseason), not rankings; `xGC/90` normalises xGC by minutes so
  players compare fairly. Whether a number is "good" is only meaningful **relative to peers** — which is
  exactly the tester's uncertainty.
- **The ChatGPT band table is miscalibrated for FPL.** Measured on real data (117 DEF/GK, ≥900 mins):
  xGC/90 **median 1.36**, p25–p75 **1.22–1.40**, min 0.52 (Calafiori), max 2.04. Applying ChatGPT's fixed
  bands (0.5 excellent … 2.0 very poor) buckets **91/117 as "poor"** and only **1 as "excellent"** — nearly
  everyone red. ChatGPT's scale is *team goals-per-match* (≈1.1 average); FPL's *player xGC/90* attribution
  sits higher. **A fixed absolute band copied from ChatGPT would mislead** → bands must come from the real
  FPL distribution. (Owner's call: **hybrid** — relative quintile band + the percentile shown inline.)
- **xGI direction is clean** (higher = better; n=376, median 2.67, p90 9.90, max 28.17) → a good second board
  for a rating. The **over/under diff** and **DefCon margin** boards are *signed* (they already show +/-
  direction), so they're **out of scope** for the colour rating (owner's call: **xGC/90 + xGI**).
- **The "Home graphic" is just an emoji-led title** (`st.title("⚽ FPL Assistant")` + a caption) — no image.
  The other tabs use a plain `st.title("Players")`. So item 2 = give each tab a consistent **emoji + tagline**
  header. Cosmetic, low-risk. (Streamlit `st.dataframe` has **no per-cell hover tooltip** primitive, so the
  percentile rides **inline** in the rating cell — colour + number, both visible.)

---

### 🎯 Sprint Goal

**Objective:** a casual user can read the stat boards at a glance — each metric says what it is (absolute vs
per-90) and carries a **self-calibrating colour rating** (best/worst vs the current pool) with the percentile
inline; and every tab gets a consistent, friendly **emoji header** like Home.

#### Success Criteria
- [x] **US-221 (interpretable stat boards, ADR-071)** — a reusable **`quality_band`** helper: given a value
      + the pool + a direction, returns a **quintile** colour (🟢 excellent · 🟢 good · 🟡 average · 🟠 poor
      · 🔴 very poor) **and** the player's percentile ("top N%"). A **Rating** column on **Clean sheets**
      (xGC/90, lower=better) and **xG** (xGI, higher=better), e.g. `🟢 excellent (top 8%)`; a one-line
      **legend** caption ("rated vs the players shown — 🟢 best 20% … 🔴 worst 20%"); **clearer captions +
      per-column `help=` tooltips** on all four stat boards saying what each number means (absolute season
      total vs per-90). Display-only (a web helper); analytics untouched; no server writes.
- [x] **US-222 (per-tab header graphics)** — a consistent **emoji-led header + one-line tagline** on every
      tab (Players 👟 · Fixtures 📅 · Squads 🧩 · Ask 💬 · News 📰 · Trending 📈 · Help 🧭), matching Home's
      look. Copy/UI only; no behaviour change.
- [ ] **No analytics drift** — `defensive_solidity`/`over_under`/`defcon_reliability`/xGI ranking unchanged;
      existing **598** stay green; ruff clean.
- [ ] Docs: ADR-071 + index, Architecture, PROJECT_STATUS, README, Help (a note on reading the ratings).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-221 | **Interpretable stat boards** — a `quality_band` helper (quintile colour + percentile); a **Rating** column on Clean sheets (xGC/90) and xG (xGI) + a legend; clearer captions + per-column tooltips on all four boards. ADR-071. | High | ✅ Done | ~1 session |
| US-222 | **Per-tab header graphics** — an emoji-led header + tagline on all 7 tabs, like Home. | Medium | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

**US-221 (ADR-071).** A new display helper `src/web_streamlit/ratings.py`:
`quality_band(value, pool, *, higher_is_better) -> {"emoji", "label", "percentile"}`. `pool` = the finite
list of the metric's values currently shown; the percentile is "top N%" (share of the pool a player beats —
for xGC/90, lower beats higher). Quintile → `(🟢 excellent, 🟢 good, 🟡 average, 🟠 poor, 🔴 very poor)`.
In `views/players.py`: `render_cleansheet` and `render_xg` add a **Rating** column
(`f"{emoji} {label} ({percentile})"`), a legend `st.caption`, and richer per-column `help=` on every board's
columns (via `st.column_config` where the `_board` renderer allows, else a fuller caption). The rating is
**relative to the players shown** (so it re-scales as the filter narrows — the legend says so). No change to
the analytics or the sort order.

**US-222.** Each `pages/*.py`: `st.title("<emoji> <Name>")` + a single `st.caption("<tagline>")`, consistent
with `Home.py`. A tiny shared list keeps the emoji/tagline per tab in one place if it reads cleaner. No
data/logic; the tooltip-coverage + existing render tests still pass.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `quality_band` returns the right quintile + percentile for lower- and higher-is-better
   metrics (incl. ties, a 1-element pool, and the best/worst extremes); the Clean-sheets + xG boards render
   a Rating column + a legend (AppTest); every stat board shows a clarifying caption; the per-tab headers
   render with their emoji. Existing **598** stay green.
2. **Manual smoke** — Clean sheets shows Calafiori `🟢 excellent (top ~1%)` and Dubravka near `🔴 very poor`;
   xG shows the elite attackers 🟢; each tab shows its emoji header.
3. **Docs updated** — ADR-071 + index, Architecture, PROJECT_STATUS, README, Help.

---

### 📝 Session Progress Log

**US-221 (interpretable stat boards, ADR-071).** A display-only quality rating that answers the tester's
"is 0.52 good, or just relative?" honestly.
- **Helper** — `src/web_streamlit/ratings.py`: `quality_band(value, pool, *, higher_is_better)` →
  `{emoji, label, percentile}` (quintile 🟢 excellent…🔴 very poor + "top N%"); `rating_cell` formats
  `🟢 excellent (top 8%)`. **Relative** to the pool shown (not fixed bands — real xGC/90 median 1.36 makes
  ChatGPT's table mislabel 91/117 "poor"); self-calibrating; ties share a band; empty/1-element pools handled.
- **Boards** — `views/players.py`: **Clean sheets** (xGC/90, lower=better) + **xG** (xGI, higher=better) gain
  a **Rating** column computed over the *filtered* board (stable across pages) + a legend caption. All four
  boards get clearer captions (absolute season total vs per-90) + per-column `help=` tooltips (`_board` now
  takes `col_help`). The two signed boards (over/under, DefCon) get captions/tooltips but no colour rating.
- **Docs** — ADR-071 + index.
Smoke (real data): Calafiori `🟢 excellent (top 1%)`, median `🟡 average`, Dubravka `🔴 very poor (top 99%)`.
Tests: +8 (6 `ratings` unit — both directions, ties, extremes, 1-elem/empty; 2 web — Rating column + legend
on Clean sheets, Rating on xG). ruff clean, full suite **606** green.

**US-222 (per-tab header graphics).** Each tab now leads with a distinct emoji + a one-line tagline, matching
Home's ⚽: **Players 👟 · Fixtures 📅 · Squads 🧩 · Ask 💬 · News 📰 · Trending 📈 · Help 🧭**. Titles trimmed
of their " — descriptive" suffix (moved into the tagline caption where one wasn't already present). Copy/UI
only — no logic, no ADR. +1 test (every tab's title carries its emoji, no crash); full suite **607** green.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **598 → 607** (+9); ruff clean; CI-parity green.

**Delivered**
- **US-221 — interpretable stat boards (ADR-071).** A display-only quality **rating** — `quality_band`
  rates a value **relative to the players shown** (quintile 🟢 excellent…🔴 very poor) + the **percentile**
  inline; a **Rating** column on **Clean sheets** (xGC/90) and **xG** (xGI) + a legend; clearer captions +
  per-column tooltips on all four boards. Analytics untouched; no server writes.
- **US-222 — per-tab header graphics.** A distinct emoji-led title + tagline on every tab
  (👟📅🧩💬📰📈🧭), matching Home.

**What went well**
- **Real-data verification changed the design.** The tester's ChatGPT band table would have mislabeled
  91/117 defenders "poor"; checking it against the actual distribution (median 1.36) turned a plausible
  copy-the-table story into an honest, self-calibrating *relative* rating. This is the gate-on-real-data
  rhythm doing its job.
- **Small surface, clean layering** — the rating is a web-side display helper; the analytics core stayed
  pure, and the two signed boards were left alone (they already show direction).
- The header pass was genuinely trivial and low-risk (a title + caption per page), closing the tester's
  third item cheaply.

**Watch-outs / follow-ups**
- The rating is *relative to the players shown*, so a narrow filter → a tiny pool → coarse quintiles; the
  legend states this. Preseason values are last-season carryover — the rating sharpens at GW1 with no code
  change.
- Streamlit `st.dataframe` has no per-cell hover, so the percentile rides inline (colour + number) rather
  than on hover — a platform limitation, not a design choice.
- Possible later: extend ratings to the CLI stat commands, or a rating on the Players Pool itself.

See `Sprint82_Lessons_Learnt.md` for the detailed retro.
