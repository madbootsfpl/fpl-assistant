# Sprint 089: A configurable prediction horizon on the Squads tab

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a shared GW selector threaded through the squad views + the ask layer)
**Carried Over:** none

> **Direction (owner, tester feedback):**
> Squads tab: *"Need the flexibility to select the number of gameweeks the tool predicts over. Starting the
> season or wildcarding → the next 4–6 GW matter; mid-season → the next 1–2. Want that flexibility throughout
> the tab and sub-tabs — maybe a dropdown 'select GW' box."*

---

### 🔎 Verified at planning (code)

- **The analytics already take a horizon.** `decision_xp(..., horizon=5)`, `analyse_squad(..., horizon=5)`,
  `player_xp` — all parameterised; the CLI exposes `--next N`. The **web Squads views hard-use the default 5**
  (they call `decision_xp` with no horizon → 5; verified: `gameweeks = [1,2,3,4,5]`). So the selector just
  **threads a chosen N** where 5 is currently implicit — **default 5 = no change** for anyone who leaves it.
- **The renderer already adapts.** `render_squad_analysis` labels the window from `analysis["horizon"]`
  ("next GW" for 1, "N GW" otherwise) — so a shorter/longer horizon reads correctly.
- **Captain is inherently a one-week decision** — `captain_picks` is next-GW; the selector must **not** apply
  to it (you captain for a single gameweek). A caption will say so.
- **AI Tips routes through `ask`**, which uses a module `_HORIZON = 5`. Covering AI Tips (owner's call) needs
  a small, backward-compatible **`horizon` param on `ask.answer`** threaded to `_decide_gameweek` →
  `_squad_xp`; and the gameweek plan's "over 5 GW" label must reflect the chosen N.
- **Build/wildcard is exactly the tester's case** — the xp objective optimises the 15 over the horizon, so a
  4–6 GW horizon changes which squad is "best" (wildcard planning). It's in scope.

---

### 🎯 Sprint Goal

**Objective:** a single **Gameweeks ahead** dropdown on the Squads tab drives the prediction horizon across
**Build · My Squad · Health · Transfer · AI Tips** (Captain stays next-GW), so a manager can plan for the
next 1 or the next 6. Default 5 (unchanged behaviour); no analytics change (reuses the existing horizon
params).

#### Success Criteria
- [x] **US-237 (the selector + the analytic views, ADR-077)** — a shared `st.selectbox("Gameweeks ahead",
      1..8, default 5)` on `pages/3_Squads.py`, threaded as `horizon` into **Build · My Squad · Health ·
      Transfer** (each passes it to `decision_xp` / `analyse_squad` / the transfer renderers). The views'
      xP/projection reflects N GW; the analysis label already adapts. **Captain** is unchanged with a "always
      the next gameweek" caption.
- [x] **US-238 (AI Tips respects it)** — `ask.answer(..., horizon=N)` (a new, backward-compatible param)
      threaded to `_decide_gameweek` → `_squad_xp`; the gameweek plan's transfer line reads "over N GW" (not
      a hard 5). The AI Tips view passes the selected horizon. Captain within the plan stays next-GW.
- [ ] **No drift** — default 5 preserves today's behaviour; `decision_xp`/the analytics unchanged; the CLI /
      the Ask tab keep the 5-GW default; existing **625** stay green; ruff clean.
- [ ] Docs: ADR-077 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-237 | **GW selector + analytic views** — a shared "Gameweeks ahead" dropdown (1–8, default 5) threaded through Build · My Squad · Health · Transfer. Captain = next-GW. ADR-077. | High | ✅ Done | ~½ session |
| US-238 | **AI Tips respects the horizon** — a `horizon` param on `ask.answer` → the gameweek plan; the plan label reads "over N GW". | Medium | ✅ Done | ~½ session |

---

### 🧭 Design sketch

**US-237 (ADR-077).** `pages/3_Squads.py`: `horizon = st.selectbox("Gameweeks ahead", list(range(1, 9)),
index=4, help="How many upcoming gameweeks the projections look over — short for mid-season, longer for a
wildcard/start.")`, placed by the Tool control. Add a `horizon` param to `render_build` / `render_my_squad`
/ `render_health` / `render_transfer`; inside, pass `horizon=horizon` to `decision_xp(...)` (and
`analyse_squad(..., horizon=horizon)` on Health; the transfer renderers' `horizon=` for the label). `render_captain`
unchanged + a caption "Captaincy is always the next gameweek." The dispatch in the page passes `horizon`.

**US-238.** `ask.answer(question, *, store=None, narrator=…, active_squad=None, horizon=_HORIZON)` threads
`horizon` through `_fresh` → `_dispatch` → `_decide_gameweek(..., horizon=horizon)` → `_squad_xp(...,
horizon=horizon)` (a new keyword, default `_HORIZON`, so the other squad decides are unchanged). Pass the
horizon to `render_gameweek_plan(plan, squad_name, horizon=…)` so its transfer line reads "over N GW". The
AI Tips view: `ask.answer(f"what should I do this week for {name}?", active_squad=squad, horizon=horizon)`.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the Squads page has a "Gameweeks ahead" selectbox; setting it to 2 makes Health project
   over 2 GW (the analysis window/`by_gameweek` reflect 2, not 5); a Build over 8 GW still returns a legal 15;
   `ask.answer(horizon=2)` yields a gameweek plan whose transfer line reads "over 2 GW"; Captain is unchanged.
   Existing **625** stay green.
2. **Manual smoke** — Squads → set Gameweeks to 2 → Health/Transfer/My Squad/Build/AI Tips all reflect 2 GW;
   set to 6 → they widen; Captain still says next-GW.
3. **Docs updated** — ADR-077 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-237 (the selector + the analytic views, ADR-077).** A shared `st.selectbox("Gameweeks ahead", 1..8,
index=4)` on `pages/3_Squads.py`, threaded as a keyword `horizon` into `render_build` / `render_my_squad` /
`render_health` / `render_transfer` (each passes it to `decision_xp` — and `analyse_squad(horizon=…)` on
Health, and the transfer renderers' `horizon=` for the "over N GW" label). Default 5 → today's behaviour.
**Captain** unchanged + a caption ("Captaincy is always the next gameweek — the selector doesn't apply").
No analytics change (reuses the existing horizon params). Smoke: default 5; set to 2 → Health shows a GW2
column + "2 GW", no GW5. Tests: +2 (the selector drives the horizon; the Captain caption); **5 positional
`selectbox`/`slider` tests re-pointed to select by label** (a new page-level selectbox shifted indices) —
the label-not-index lesson. ruff clean, full suite **627** green.

**US-238 (AI Tips respects the horizon).** Threaded a backward-compatible `horizon` keyword through the ask
layer: `answer(..., horizon=_HORIZON)` → `_fresh` → `_dispatch` → `_decide_gameweek(..., horizon=…)` →
`_squad_xp(..., horizon=…)` (default `_HORIZON`, so the other squad decides + the CLI/Ask tab are unchanged).
`render_gameweek_plan(plan, squad_name, horizon=…)` now labels the transfer window ("over N GW", or "next GW"
for 1). The AI Tips view passes the selected `horizon` into `ask.answer`. Smoke: `render_gameweek_plan`
horizon 5/2/1 → "over 5 GW"/"over 2 GW"/"next GW"; `_decide_gameweek(horizon=2)` → detail has "over 2 GW".
Fixed one grounded-gameweek test's `_squad_xp` monkeypatch to accept the new kwarg; +1 horizon assertion.
ruff clean, full suite **627** green.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
