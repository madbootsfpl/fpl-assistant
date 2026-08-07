# Sprint 106: Explainability for the AI Tips gameweek plan

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (reuse the explain framework for a composite decision)
**Carried Over:** none

> **Direction (owner):** *"explainability for the AI Tips gameweek plan."* The last major decision without it —
> extends the Why · Risk · Confidence pattern (ADR-089), already on captain · transfer · squad · chips.

---

### 🔎 Verified at planning

- **The plan is a composite** (`gameweek_plan`, ADR-070): **captain** · **lineup** (start/bench change) ·
  **transfer** · **flags** (unavailable/doubtful). Two of those already have grounded explanations —
  `explain_captain` and `explain_transfer` — so this sprint is mostly **reuse**: run them on the plan's own
  captain + move, add a short **lineup** rationale, and give the week an **overall** Confidence · Why · Risk.
- **One wiring point.** `_decide_gameweek` builds the plan and renders it (`render_gameweek_plan`); the web
  **AI Tips** view routes through `ask.answer`, so wiring the explanation once reaches Ask, `chat`, and the web.
- **A gap to close first.** `gameweek_plan` computes the captain with `limit=1`, so there's no runner-up for
  `explain_captain`'s lead-margin / "narrow lead" risk. Bumping the limit and exposing the ranked picks fixes
  it (additive).
- **The flags are the week's risks already** — availability is exactly what an explanation's ⚠ should surface,
  so the plan-level Risk is grounded in data we already show.

---

### 🎯 Sprint Goal

**Objective:** the AI Tips plan shows **why** — each recommendation (captain, the lineup change, the transfer)
carries a **Confidence + a short Why**, and the week gets an **overall Confidence · Why · Risk** — every reason
computed from the data (reusing `explain_captain`/`explain_transfer`), verified. A user sees *why* the week's
plan is what it is, and can challenge it.

#### Success Criteria
- [ ] **US-273 (per-recommendation explainability, extends ADR-089)** — `analytics/explain.py::
      explain_gameweek(plan, players_by_id, *, horizon)` → `{captain: Explanation, transfer: Explanation|None,
      lineup: [str]}`, reusing `explain_captain` (on the plan's ranked captain picks) + `explain_transfer` (on
      the plan's move + the buy's row), plus a grounded lineup rationale (start X over Y — higher xP / plays).
      `gameweek_plan` exposes the ranked captain picks so the captain lead-margin works. `render_gameweek_plan`
      appends **· Confidence NN/100 · Band** + a compact Why to the captain + transfer lines and the lineup
      why.
- [ ] **US-274 (plan-level Confidence · Why · Risk)** — a `gameweek_confidence(captain_conf, n_flags)`
      heuristic (captain-driven — the week's biggest lever — tempered by flagged players) + a top-of-plan
      **Confidence · Why (the settled/actionable points) · Risk (the flagged players)** block. `_decide_gameweek`
      puts confidence/why/risk into `facts` (so a narrated number **verifies ✓**). Shown in Ask, `chat`, CLI,
      and the web **AI Tips** view.
- [ ] **No drift** — display-only over existing signals (+ the additive captain-limit change); the engine/
      `decision_xp` unchanged; existing **705** stay green; ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help (ADR-089 extended — noted).

---

### 🧭 Design sketch

**US-273.** `gameweek_plan`: `picks = captain_picks(..., limit=3)`, `captain = picks[0]`, add
`"captain_ranked": picks` to the return (additive; existing callers ignore it). `explain_gameweek(plan,
players_by_id, *, horizon)`:
- **captain** → `explain_captain(plan["captain_ranked"], players_by_id)` (reuse).
- **transfer** → `explain_transfer(plan["transfer"], players_by_id[buy_id], horizon)` when a move exists.
- **lineup** → short reasons: for each `bring_in`/`drop` pair, *"start {in} over {out} — higher projected xP"*.
`render_gameweek_plan(plan, squad_name, horizon, explanation=None)` appends the confidence + a one-line Why to
the captain and transfer lines, and the lineup rationale under the lineup line.

**US-274.** `gameweek_confidence(captain_conf, n_flags)` → `max(1, captain_conf − 8*n_flags)` (documented). A
top block: `Confidence NN/100 · Band` + **Why** (✓ captain nailed-on / one clear upgrade available / no
changes needed) + **Risk** (⚠ the flagged players, or "none — all available"). `_decide_gameweek` computes the
explanation, sets `facts["confidence"/"why"/"risk"]`, and prepends the block to the plan detail.

**Deferred:** a confidence on the *lineup* change itself (a one-line rationale is enough); the gated "why"
signals (form/news) enrich it at GW1; a richer web-native render.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-273 | **Per-recommendation explainability** — `explain_gameweek` (captain/transfer reuse + lineup why) rendered into the plan. | High | ⬜ To do | ~⅔ session |
| US-274 | **Plan-level Confidence · Why · Risk** — `gameweek_confidence` + a top-of-plan block; facts wiring. | High | ⬜ To do | ~⅓ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `explain_gameweek` reuses the captain/transfer explanations + emits the lineup rationale
   (and is empty-safe on a plan with no transfer / no change); `gameweek_confidence` is bounded + drops with
   flags; the AI Tips answer carries the per-recommendation confidences + the plan-level block, and a narration
   restating the values verifies ✓. Existing **705** stay green.
2. **Manual smoke** — `ask "what should I do this week for RoboTS?"` shows the captain's Confidence/Why, the
   transfer's (if any), the lineup rationale, and a top-of-plan Confidence · Why · Risk; the web AI Tips view
   shows the same.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help (ADR-089 extended — noted).

---

### 📝 Session Progress Log

**US-273 — per-recommendation explainability (extends ADR-089).** ✅ Done.
- `gameweek_plan` now runs the captain with `limit=3` and returns `captain_ranked` (additive) so the captain
  explanation has a runner-up for its lead-margin.
- `analytics/explain.py::explain_gameweek(plan, players_by_id, xp_by_id, *, horizon)` → `{captain: Explanation,
  transfer: Explanation|None, lineup: [str], overall: Explanation}` — **reuses** `explain_captain` (on
  `captain_ranked`) + `explain_transfer` (on the move + the buy's row), adds a grounded lineup rationale
  (*"Start X over Y — higher projected xP: a vs b"*), and an overall block (US-274). Robust to missing ids
  (empty-safe). `gameweek_confidence` documented (captain-driven, −8 per flag). Exported.
- `ui/gameweek.py::render_gameweek_plan(explanation=…)` appends **· Confidence NN/100 · Band** + a compact
  **Why** to the captain + transfer lines, and the lineup rationale under the lineup line. `_decide_gameweek`
  computes + passes it. The web **AI Tips** view inherits it (it routes through `ask.answer`).
- **Tests (+2):** `gameweek_confidence` bounded + dropped by flags; `explain_gameweek` reuses the
  captain/transfer explanations + emits the lineup rationale + the flagged player as the week's risk +
  empty-safe. Fixed `explain_captain`/`explain_gameweek` to tolerate a missing id. **707** green, ruff clean.
- **Manual smoke (TS):** *Captain B.Fernandes · Confidence 69/100 · Medium · Why: highest xP, penalties,
  set-pieces* · *Transfer Ampadu → Zubimendi · Confidence 95/100 · High · Why: +9.3 XI, higher xP* — in Ask
  and the web AI Tips view.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
