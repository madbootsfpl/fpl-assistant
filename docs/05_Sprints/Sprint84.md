# Sprint 084: Fix the xG rating flaw · rename This week → AI Tips · Ask examples

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/3 stories)
**Capacity:** ~½–1 session (a correctness fix to the stat rating + two small UI touches)
**Carried Over:** none

> **Direction (owner, tester feedback — 3 items):**
> 1. **Flaw in logic (xG board rating):** *"how can 0 be good and 56 be good?"* — goalkeepers show
>    `xGI 0` / `xGI 0.04` yet get **🟢 excellent / good**, and the single rating sits next to both `xGI`
>    (0) and `xGC` (56) so it reads as ambiguous.
> 2. **Rename** the Squads **This week** tab to **AI Tips**.
> 3. **Ask tab:** show a few **example prompts**.

---

### 🔎 Verified at planning (real data)

- **The flaw is real and has two causes.** (a) `xGI` (attacking) is **noise for goalkeepers** — GK xGI max
  is 0.22, median 0; rating a keeper on it is meaningless. (b) **172 / 572 players have 0 minutes** (backups)
  — no signal, yet they're rated. The rating pool is *all shown rows including the zeros*, so when the board
  is filtered to **GK** the pool is entirely ~0 and a keeper with `0.04` lands **top 19% of keepers → 🟢
  excellent**. The *meaningful* pool (outfield, ≥900 mins) is **n=248, median xGI 4.12, max 28.17** — a
  sensible thing to rate against. (Owner's calls: **rate only meaningful players**; **rename the column to
  "xGI rating" and move it beside xGI**.)
- **Clean sheets is fine** — it's already gated (`defensive_solidity`, DEF/GK, ≥900 mins) and xGC/90 is
  meaningful for everyone it shows; no change there.
- **This week → AI Tips** is a label change on the Squads `st.segmented_control` (the grounded gameweek plan
  behind it, ADR-070, is unchanged). Touches the control, the dispatch, the Help copy (added last sprint),
  and the tests/docs that name "This week".
- **Ask** currently has a title + captions + the chat box, but **no example prompts** on the page (the Help
  tab has them). A short copy-paste list on the Ask page itself satisfies the ask (static text → no new
  input widgets, tooltip-coverage unaffected).

---

### 🎯 Sprint Goal

**Objective:** the xG board's rating only appears where it's honest (real attackers, enough minutes) and is
clearly labelled as an **xGI** rating; the Squads gameweek tab reads **AI Tips**; and the Ask tab shows a few
example prompts so a new user knows what to type.

#### Success Criteria
- [x] **US-225 (xG rating fix, ADR-073)** — on the xG board, `xGI` is rated **only for outfield players with
      ≥900 minutes**, with the percentile computed over **that** pool; GKs and low-minutes players show a
      blank **—** (not a colour). The column is renamed **"xGI rating"** and moved **right after xGI** (away
      from xGC); its tooltip says what it rates + who's excluded. Refines ADR-071; Clean sheets unchanged.
- [x] **US-226 (rename This week → AI Tips)** — the Squads segmented control shows **AI Tips** (was This
      week); the dispatch, help text, Help-tab copy, and tests/docs updated. The engine (the grounded
      gameweek plan, ADR-070) is unchanged.
- [ ] **US-227 (Ask examples)** — a few copy-paste **example prompts** on the Ask page (incl. a gameweek /
      squad / value example), so a new user has a starting point. Static content; no server writes.
- [ ] **No drift** — the rating helper (ADR-071), the gameweek plan (ADR-070), and the analytics are
      otherwise unchanged; existing **612** stay green; ruff clean.
- [ ] Docs: ADR-073 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-225 | **Fix the xG-board rating** — rate xGI only for outfield players ≥900 mins (pool = those players); blank — for GKs / low-minutes; rename the column "xGI rating" and move it beside xGI. ADR-073 (refines ADR-071). | High | ✅ Done | ~½ session |
| US-226 | **Rename This week → AI Tips** — the Squads segmented-control label (+ dispatch, help, Help copy, tests, docs). Engine unchanged. | Medium | ✅ Done | ~¼ session |
| US-227 | **Ask example prompts** — a few copy-paste examples on the Ask page. | Medium | ⬜ To do | ~¼ session |

---

### 🧭 Design sketch

**US-225 (ADR-073).** In `views/players.py::render_xg`: a predicate `_rate_xgi(r)` = `position != "GK"` and
`minutes ≥ 900` and `xgi is not None`; `pool = [r["xgi"] for r in rows if _rate_xgi(r)]`; the column becomes
`"xGI rating": lambda r: rating_cell(r["xgi"], pool, higher_is_better=True) if _rate_xgi(r) else "—"`,
ordered **xG · xA · xGI · xGI rating · xGC**. Tooltip: *"Attacking quality (xGI) vs outfield players with
≥900 mins; keepers & low-minutes players aren't rated."* `rating_cell`/`quality_band` (ADR-071) are
unchanged — only *which* rows are rated and *what* pool they're rated against.

**US-226.** `pages/3_Squads.py`: rename the option `"This week"` → `"AI Tips"` in the `segmented_control`
list + the `elif view == …` dispatch; update the control `help=`. Update the Help tab copy (This week →
AI Tips), the `test_web_streamlit` view test, and the docs that name "This week". `render_this_week` keeps
its name internally (the label is UI only), or is renamed to `render_ai_tips` for clarity.

**US-227.** `pages/4_Ask.py`: a small **"Try one of these"** block (an `st.expander` or a caption + a
`st.code` list) above/near the chat with ~5 examples — e.g. *what should I do this week for my-team?* ·
*best differential midfielders under £8m* · *is Haaland worth the money?* · *who should I captain from
my-team?* · *when does Arsenal play next?*. Static; mirrors the Help tab's example set.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — a GK / a zero-minute player gets a blank xGI rating (not a colour); an outfield ≥900-min
   player is rated against the outfield pool; the column is named "xGI rating" and sits before xGC; the
   Squads control shows "AI Tips" and its view still renders the gameweek plan; the Ask page shows example
   prompts. Existing **612** stay green.
2. **Manual smoke** — filter the xG board to GK → all ratings blank; an elite attacker still reads 🟢; the
   Squads tab reads **AI Tips**; the Ask page lists example prompts.
3. **Docs updated** — ADR-073 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-225 (xG rating fix, ADR-073).** Fixed the tester's "how can 0 be good?" flaw — the xG board rated xGI
for everyone, but xGI is noise for keepers (max 0.22) and the 172 zero-minute players, and the pool was all
shown rows, so a GK-filtered view rated a keeper's 0.04 as "top 19% → 🟢 excellent".
- `render_xg`: a `_rate_xgi(r)` predicate (`position != "GK"` and `minutes ≥ 900` and `xGI is not None`);
  the pool is now **only the rated rows**; unqualified rows show a blank **—**.
- Column renamed **"Rating" → "xGI rating"** and moved **right after xGI** (order xG · xA · xGI · xGI rating
  · xGC), with a tooltip saying what it rates + who's excluded. `_RATING_MIN_MINUTES = 900` constant added.
- `quality_band`/`rating_cell` (ADR-071), the analytics, and Clean sheets are unchanged — only which rows
  are rated and against what pool.
Smoke: top attacker B.Fernandes (xGI 23.07) → 🟢 excellent (top 1%); **filtered to GK → every rating is —**.
Test rewritten (`test_xg_board_rates_only_meaningful_players`): column named/placed correctly + GKs unrated.
ruff clean, full suite **612** green.

**US-226 (rename This week → AI Tips).** The Squads segmented control now reads **AI Tips** (was This week):
label + `elif` dispatch + the control `help=`; `render_this_week` → `render_ai_tips`; the Help tab copy
(quick-start, the sub-nav caption, step 4) updated to "AI Tips"; the `ui/gameweek.py` docstring reference
fixed. The engine (the grounded gameweek plan, ADR-070) is unchanged — the plan block still reads
"This week — squad X" (it *is* this gameweek's plan) and the NL Ask example keeps its phrasing. Tests
updated (`test_squads_ai_tips_view_renders_a_gameweek_plan`; the Help test now asserts "AI Tips"). ruff
clean, full suite **612** green.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
