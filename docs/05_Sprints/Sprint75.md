# Sprint 075: A filter on Trending (reuse the shared filter)

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/1 story)
**Capacity:** ~¼ session (reuse the existing filter — no new analytics, no new ADR)
**Carried Over:** none

> **Direction (owner, tester feedback):** **Trending needs a filter, same as Players and Player Stats.**

---

### 🔎 Verified at planning (real data / real code)

- `trending(players, by, …)` rows are the **player dicts** (they carry `team` / `position` / `web_name`,
  and `price`), so the shared `filters.apply` predicate works on them **unchanged**.
- The shared `filter_controls` / `apply` (**ADR-064**) already power Players & Player Stats — so this is a
  **reuse**, not new work; **no new ADR** (executes ADR-064). Its multiselects already carry `help=`
  (ADR-065), so the tooltip coverage test stays green with no extra work.
- **No price control** — matching **Player Stats** (the lens analog); trending is about crowd *movement*,
  not price-shopping (trivial to add `with_price=True` later if wanted).

---

### 🎯 Sprint Goal

**Objective:** the same **Team · Position · Player** filter (AND-combinable) on the Trending page, applied
to all four boards — reusing the shared helper. Nothing else changes.

#### Success Criteria
- [x] **US-210** — `filter_controls(players, key="trending")` once above the boards; each board applies
      `apply(trending(...), sel)` before pagination; the GW1-empty note + the buzz board unchanged
- [x] **No new analytics / ADR** — reuses `filters.py` (ADR-064); the web writes nothing server-side
      (guardrail holds); the help-tooltip coverage test stays green (the filter's help is inherited)
- [x] A test: a chosen team narrows the (always-populated) **owned** board
- [x] Existing stay green — **580** (+1)
- [ ] Docs: Architecture, PROJECT_STATUS, Feedback_Log (resolved) _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-210 | **Trending filter** — the shared Team/Position/Player filter above the four boards, applied to each before pagination. Reuses ADR-064; no new ADR. | High | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

In `pages/11_Trending.py`, inside the `else` (data present), before the tabs:
`sel = filter_controls(players, key="trending")`. In each board:
`rows = apply(trending(players, by=by, limit=len(players)), sel)` — then the existing GW1-empty check +
`paginate` + `_board`. The buzz ("Talked about") board is unchanged. `filter_controls`/`apply` imported from
`web_streamlit.filters` (as Players / Player Stats do).

---

### ✅ Definition of Done

1. **Tests pass** — a chosen team narrows the owned board; the tooltip coverage test still passes (the
   filter's help is inherited); the web-writes-nothing guardrail holds. Existing **579** stay green.
2. **Manual smoke** — on Trending, pick a team + position → every board narrows.
3. **Docs updated** — Architecture, PROJECT_STATUS, Feedback_Log (resolved).

---

### 📝 Session Progress Log

- **US-210 ✅ (build)** — Reused the shared filter (ADR-064) on Trending: `filter_controls(players,
  key="trending")` once above the four boards; each board now runs `apply(trending(players, by,
  limit=len(players)), sel)` before the GW1-empty check + `paginate`. The buzz board is unchanged. No new
  analytics/ADR; the filter's `help=` is inherited (ADR-065), so the tooltip coverage test stays green with
  no extra work. Tests (+1 → **580**): Team=ARS narrows the owned board to ARS-only. **Smoke (real DB):**
  3 filter multiselects; (ARS|LIV) ∧ MID → exactly the 30 ARS/LIV midfielders (teams={ARS,LIV}, pos={MID}),
  no exception. ruff clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — Trending now has the **same Team · Position · Player filter** as Players and
Player Stats, by **reusing** the shared `filters.py` (ADR-064). One import + one call + a per-board `apply`;
no new analytics, no new ADR, and the filter's tooltips came for free (ADR-065).

**What went well** — the payoff of the earlier shared-component investment: a whole tester request became a
few lines because `filter_controls`/`apply` already existed and were page-agnostic. The tooltip coverage
test (ADR-065) stayed green with zero extra work — the new filter inherited its `help=`.

**What to watch** — a momentary "30 → 30" in the smoke looked like the filter wasn't biting, but it was
correct: ARS + LIV really do have 30 midfielders between them (big squads, lots of fringe/youth classed as
MID). The unit-style AppTest (Team=ARS ⇒ ARS-only) was the reliable signal, not the eyeballed count.

**Lessons captured:** `docs/05_Sprints/Sprint75_Lessons_Learnt.md`.
