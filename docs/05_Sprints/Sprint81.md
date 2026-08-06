# Sprint 081: Pool layout · refresh clarity · an AI gameweek recommendation

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/3 stories)
**Capacity:** ~2 sessions (a tiny reorder + a refresh-visibility fix + a new grounded recommendation)
**Carried Over:** none

> **Direction (owner, tester feedback — 3 items):**
> 1. **Players → Pool:** show the **table first**, the bar chart below (the table matters most).
> 2. **Refresh:** the CLI refreshed **572** players but the app shows **569–570** — how do I make sure the
>    Streamlit app is on fresh data?
> 3. **An AI recommendation** on your squad for the upcoming gameweek.

---

### 🔎 Verified at planning (real data)

- **Item 2 root cause:** `data/fpl.db` (a CLI refresh) = **572** players; the committed `data/seed.db`
  (what the Cloud serves) = **570**. `get_players` LEFT-JOINs and filters nothing, so the app shows exactly
  what its DB holds — the tester is viewing the **seed snapshot**, not their fresh cache. Two footguns:
  (a) the **Cloud** is read-only (ADR-053) and only ever reads the *committed* seed — a local `refresh`
  never reaches it; (b) locally, `config.DB_PATH` is resolved **once at import**, so an app started before
  `refresh` created `fpl.db` stays on the seed until restarted.
- **Item 1:** `views/players.py::render_pool` renders the bar **before** the table — a one-block reorder.
- **Item 3:** the pieces already exist — `captain_picks`, `best_legal_xi` (start/bench), `suggest_transfers`,
  and availability flags — plus the grounded narrate-and-verify pipeline (`ask.assemble`, ADR-037). A GW
  recommendation is an *assembly + narration* of these, not new analytics.

---

### 🎯 Sprint Goal

**Objective:** the Pool leads with the table; the app makes its data freshness **obvious** and gives a
**one-command** way to update the live app; and a grounded **"this week"** recommendation (captain · lineup
· a transfer to consider · flags) that the AI narrates, verified.

#### Success Criteria
- [x] **US-218 (Pool layout)** — in `render_pool`, the **table + pagination render first**, the top-15 bar
      below it; nothing else changes
- [x] **US-219 (refresh clarity)** — the freshness caption shows the **player count** ("572 players · data
      as of \<date\>") so a stale snapshot is visible; on the **cloud** a one-line note that it's a snapshot
      (updates on redeploy); a **`python app.py reseed`** command (refresh → copy `fpl.db`→`seed.db`) so
      updating the live app is one step; Help/DEPLOY explain the local (button/restart) vs cloud (reseed +
      push + reboot) refresh story
- [ ] **US-220 (AI gameweek recommendation)** — a grounded **gameweek plan** for a squad: who to **captain**,
      the best **XI vs bench** (any start/bench change), one **transfer to consider**, and **flagged**
      players — assembled from the existing analytics, **narrated** by the LLM and **verified** (✓/⚠).
      Exposed as an `ask`/`chat` intent *and* a **"This week"** view in the **Squads** tab; degrades to the
      analytics summary without Ollama. ADR-070
- [ ] **No analytics drift** — reuses `captain_picks`/`best_legal_xi`/`suggest_transfers`; the web writes
      nothing server-side; existing **585** stay green
- [ ] Docs: ADR-070 + index, Architecture, PROJECT_STATUS, README, Help/DEPLOY (the refresh story)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-218 | **Pool: table first** — reorder `render_pool` so the table + pagination come before the top-15 bar. | High | ✅ Done | ~¼ session |
| US-219 | **Refresh clarity** — player count in the freshness caption; a cloud "snapshot" note; a `reseed` CLI command; document the local vs cloud refresh story. Extends ADR-053/056. | High | ✅ Done | ~½ session |
| US-220 | **AI gameweek recommendation** — a grounded "this week" plan (captain · lineup · a transfer · flags), narrated + verified; an `ask` intent + a "This week" Squads view. ADR-070. | High | ⬜ To do | ~1–1.5 sessions |

---

### 🧭 Design sketch

**US-218.** In `render_pool`: compute `ranked`, render the `paginate` + `st.dataframe` first, then the
top-15 Altair bar (with its caption) beneath. The sort selectbox stays on top.

**US-219.** `render_data_status` adds the player count to the caption (one `Storage().get_players()` count,
cheap). On the cloud (`not is_local()`), add a caption: *"a data snapshot — updates when the app is
redeployed."* New CLI `reseed` (cmd): `ingest.refresh` into `fpl.db` then copy to `seed.db` (the documented
workflow, one command), printing the counts + the "commit + push + reboot to update the live app" reminder.
Note in the Help "Good to know" + DEPLOY.md: **local** = the sidebar 🔄 button (or restart after a CLI
refresh); **cloud** = `reseed` → commit → push → reboot.

**US-220 (ADR-070).** A pure-ish assembler `gameweek_plan(squad, players, upcoming, history, …)` → a dict:
`captain` (top `captain_picks`), `lineup` (`best_legal_xi` vs the current bench → start/bench deltas), a
`transfer` (top `suggest_transfers`, bank 0), and `flags` (unavailable/doubtful owned players). An
`ask.py` `_decide_gameweek` humanises it into facts + a `task`, so `assemble` narrates + verifies (✓/⚠,
ADR-037) — a **"gameweek"/"this week"** intent routed for a squad. A **"This week"** view in Squads calls it
(via `ask.answer(..., active_squad=squad)`) and shows the recommendation + trust line; degrades to the
facts without Ollama.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — Pool renders the table before the bar; the freshness caption shows a count; `reseed`
   refreshes + copies (a fake client, tmp paths); `gameweek_plan` assembles captain/lineup/transfer/flags
   and `_decide_gameweek` is grounded (verified); the "This week" view renders. Existing **585** green.
2. **Manual smoke** — Pool shows the table first; the caption reads "N players · data as of …"; `python
   app.py reseed` updates `seed.db`; `ask "what should I do this week for <squad>?"` + the Squads "This
   week" view give a coherent, verified recommendation.
3. **Docs updated** — ADR-070 + index, Architecture, PROJECT_STATUS, README, Help/DEPLOY.

---

### 📝 Session Progress Log

**US-218 (Pool: table first).** Reordered `render_pool` (`views/players.py`): the `paginate` + `st.dataframe`
now render before the top-15 Altair bar (+ its caption), which sits beneath. The `sort` selectbox stays on
top; the bar still reads from the same `ranked`/`sort`, so it stays filter- and sort-responsive. A one-block
move, no new ADR. Players AppTests 8/8, ruff clean, smoke = 1 table + 1 bar (table first), full suite 585 green.

**US-219 (refresh clarity).** Diagnosed root cause: the tester views the committed **seed** (570), not their
fresh CLI cache (572). Three fixes, no new ADR (extends ADR-053/056):
- **Visibility** — `status.py` freshness caption now leads with the **player count**
  (`{count} players · data as of {date}`, via the existing cheap `count_players()`), so a stale snapshot is
  obvious at a glance. On the **cloud** (`not is_local()`) a second caption: *"🌐 A data snapshot — updates
  when the app is redeployed."*
- **One-command update** — new CLI **`reseed`** (`cmd_reseed`): `ingest.refresh` into the live cache, then
  `shutil.copyfile(fpl.db → seed.db)`, printing counts + a commit/push/reboot reminder. Added
  `config.LIVE_DB_PATH` so `reseed` targets `fpl.db` explicitly even when `DB_PATH` has fallen back to the
  seed. (Local runs never need it — the 🔄 button / a restart reads `fpl.db` directly.)
- **Docs** — DEPLOY.md's "After it's live" now splits the **cloud** (`reseed` → push) vs **local** (button /
  restart) refresh stories; the Help "Good to know" explains the snapshot-vs-live-refresh distinction.

Tests: +3 (reseed routes + reseed refresh→copy behaviour on tmp paths + cloud-shows-snapshot-note); the
freshness test now also asserts the count. ruff clean, reseed smoke OK, full suite **588** green.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
