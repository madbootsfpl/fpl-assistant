# Sprint 077: Team-scoped player multiselect

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/1 story)
**Capacity:** ~¼ session (refine the shared filter — no new analytics, no new ADR)
**Carried Over:** none

> **Direction (owner):** the filter's **Player** multiselect lists all ~570 names — scope it to the
> selected team(s) so it's usable (the follow-up noted across recent retros).

---

### 🔎 Verified at planning (real Streamlit behaviour)

- The Player multiselect is rendered **after** Team/Position, so its options can be recomputed from the
  current Team/Position selection on each rerun — **natural Streamlit reactivity**, no callbacks needed.
- Prototyped the shrink-under-a-stale-selection case: Streamlit **tolerates** a stored value that's no
  longer an option (no exception; it drops it). We'll still **prune** the stored selection to the in-scope
  names — so a de-scoped player can't linger invisibly or resurrect if the team is re-added (predictable).
- This lives in the **shared** `filter_controls`, so **Players · Player Stats · Trending** all inherit it
  from one change. Refines **ADR-064** (no new ADR).

---

### 🎯 Sprint Goal

**Objective:** the Player multiselect only offers players from the currently-selected **team(s) and
position(s)** (empty = all), across all three pages — from one edit to the shared filter.

#### Success Criteria
- [x] **US-213** — in `filter_controls`, the Player options are scoped by the current Team ∧ Position
      selection (empty dims = all); the stored player selection is **pruned** to the in-scope names before
      the widget renders; the help text notes the scoping
- [x] **No behaviour change to the filter logic** — `apply` (the AND predicate) is unchanged; scoping only
      limits *which* players you can pick; the web writes nothing server-side
- [x] A test: choosing a team narrows the Player multiselect's **options** to that team's players
- [x] Existing stay green (incl. the filter-narrowing + help-coverage tests) — **581** (+1); ruff clean
- [ ] Docs: Architecture, PROJECT_STATUS, Feedback_Log (resolved) _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-213 | **Team-scoped player multiselect** — scope the Player options by the selected team(s)/position(s) in the shared `filter_controls`; prune stale selections. Refines ADR-064; no new ADR. | High | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

In `web_streamlit/filters.py` `filter_controls`, after rendering Team + Position:
```
scoped = [p for p in players
          if (not team_sel or _get(p, "team") in set(team_sel))
          and (not pos_sel or _get(p, "position") in set(pos_sel))]
names = sorted({_get(p, "web_name") for p in scoped if _get(p, "web_name")})
pkey = f"{key}_player"
if pkey in st.session_state:                       # prune a now-out-of-scope selection (predictable)
    st.session_state[pkey] = [n for n in st.session_state[pkey] if n in names]
player_sel = cols[2].multiselect("Player", names, key=pkey,
    help="Pick specific players (scoped to the team/position above; empty = all).")
```
Everything else (the returned `sel` dict, `apply`) is unchanged.

---

### ✅ Definition of Done

1. **Tests pass** — an AppTest asserts Team=ARS scopes the Player options to Arsenal players only; the
   existing filter-narrowing + help-coverage tests still pass; the web-writes-nothing guardrail holds.
   Existing **580** stay green; ruff clean.
2. **Manual smoke** — on Players (or Trending / Player Stats): pick a team → the Player dropdown shows only
   that team's players; add a position → it narrows further; changing team doesn't strand a stale pick.
3. **Docs updated** — Architecture, PROJECT_STATUS, Feedback_Log (resolved).

---

### 📝 Session Progress Log

- **US-213 ✅ (build)** — In the shared `filter_controls`, the **Player** options are now scoped by the
  current **Team ∧ Position** selection (empty dims = all); the stored player pick is **pruned** to the
  in-scope names before the widget renders (so a de-scoped player can't linger/resurrect), and the help
  notes the scoping. One edit → **Players · Player Stats · Trending** all inherit it. `apply` (the AND
  predicate) is unchanged. Refines ADR-064 (no new ADR). Tests (+1 → **581**): choosing a team scopes the
  Player options to that team's players (and they really are that team's). **Smoke (real DB):** Player
  options **555 → 28 (ARS) → 15 (ARS ∧ MID)** (the actual Arsenal midfielders), no exception. No server
  writes.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the Player multiselect is now a short, relevant list (scoped by the selected
team ∧ position) instead of ~570 names, across **Players · Player Stats · Trending** — from one edit to the
shared `filter_controls`. `apply` is unchanged; no server writes.

**What went well** — prototyping the shrink-under-a-stale-selection case at planning removed the only real
risk before building: Streamlit tolerates it, and the explicit prune makes the behaviour predictable
(a de-scoped pick can't linger or resurrect). Another payoff of the shared-component investment — the third
consumer got it for free.

**What to watch** — the scope uses **Team ∧ Position** together (both narrow the list), which is the
intuitive reading of the AND filter; if anyone expects the Player list to ignore Position, that's the place
to revisit. The smoke (555 → 28 → 15) is the quick sanity check that it's actually scoping.

**Lessons captured:** `docs/05_Sprints/Sprint77_Lessons_Learnt.md`.
