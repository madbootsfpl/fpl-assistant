# Sprint 096: Chip Strategy Guidance — a fixture-run chip-window advisor

**Dates:** 2026-08-07 (planned)
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~1 session (a `chip_advisor` assembler + an `ask` intent + a Squads "Chips" view)
**Carried Over:** none

> **Direction (owner, feature request — the intake item made buildable-now):**
> *"Chip Strategy Guidance: AI advice on when to use **Wildcard · Free Hit · Bench Boost · Triple Captain**
> from your squad, fixtures, and mini-league position."*

---

### 🔎 Verified at planning (real data — the live DB)

- **The per-GW xP primitive already exists.** `decision_xp(..., horizon=8)` returns each player's
  **`by_gameweek`** = `{gw → xP}` (ADR-032, sums to the horizon total). So "which GW scores most" — for one
  player (Triple Captain) or all 15 (Bench Boost) — is a decomposition of numbers we already compute, **no new
  analytics**. Verified: a top player's `by_gameweek` over GW1–8 is `{1:7.0, 2:6.3, 3:7.0, 4:7.7, …}`.
- **The fixture-run signal is usable now.** `team_fdr(upcoming, next_n=5)` gives each team an `avg_difficulty`
  + its `opponents`; today's spread is **LIV 2.60 (NEW·NFO·IPS·FUL·BOU) → FUL/BOU 3.60** — a real 1.0 gap, so
  "easiest window for your teams" (Wildcard/Free Hit framing) is meaningful. `team_schedule(fixtures, team)`
  gives a team's per-GW run.
- **No DGW/BGW preseason** — every GW has exactly **10** fixtures (checked); double/blank GWs are announced
  *in-season*. And there's **no `events` table** (no stored deadline). So chip timing here is **fixture-run +
  xP based**, framed honestly: the classic DGW/BGW timing (Bench Boost / Free Hit) and mini-league position
  **sharpen later** (in-season + GW1). That caption is part of the feature.
- **The pattern is proven** — this mirrors `gameweek_plan` (ADR-070): an **assembler** over existing
  primitives (`decision_xp`/`by_gameweek` · `best_legal_xi` · `captain_picks` · `team_fdr`), surfaced as a
  grounded **`ask` intent + a Squads view** that degrades without Ollama.

---

### 🎯 Sprint Goal

**Objective:** for a loaded squad, a grounded **chip advisor** that recommends **when** (which GW / window in
the horizon) to play each chip — **Triple Captain · Bench Boost · Free Hit · Wildcard** — with the fact it's
based on (the GW's ceiling / the 15's total / the worst week / the run), plus an honest caption on what
sharpens in-season. Reuses the unified xP; no new core metric.

#### Success Criteria
- [ ] **US-251 (`chip_advisor` assembler + `ask` intent, ADR-082)** — a pure
      `analytics/chips.py::chip_advisor(owned, players, upcoming, xp_by_id, *, horizon=8)` returning a
      recommendation per chip (chip · best GW/window · the headline metric · the reason facts · the player(s)),
      each a **decomposition of `by_gameweek`** + the fixture run. A phrase-routed **chips** `ask`/`chat`
      intent (`_decide_chips`, placed after the specific intents so "captain this week" still routes to
      captain) → narrated + **verified** (✓/⚠, ADR-037). A shared `ui/chips.py::render_chip_advice` block.
- [ ] **US-252 (Squads "Chips" view)** — a **"Chips"** option on the Squads segmented control that routes
      through `ask.answer(active_squad=…)` + `render_ask` (degrades to the plain advice without Ollama), using
      the tab's **"Gameweeks ahead"** horizon; honest captions (fixture-run based; DGW/BGW + mini-league
      position sharpen later).
- [ ] **No drift** — an assembler only; `decision_xp`/the analytics unchanged; existing **647** stay green;
      ruff clean.
- [ ] Docs: ADR-082 + index, Architecture, PROJECT_STATUS, Roadmap, README, Help.

---

### 🧭 Design sketch

**The four chip heuristics (each a clear, defensible v0 — "prefer simple"):**

| Chip | Signal (from `by_gameweek` over the squad's 15) | Recommends |
|------|--------------------------------------------------|------------|
| **Triple Captain** | per GW, the **max single-player** `by_gameweek[gw]` among likely starters | the GW with the highest ceiling + that player |
| **Bench Boost** | per GW, the **sum over all 15** `by_gameweek[gw]` (surface the bench's share) | the GW where the whole 15 scores most |
| **Free Hit** | per GW, the **best-legal-XI xP**; the **lowest** such GW | your single worst week (a one-off to cover) |
| **Wildcard** | the **weakest sustained stretch** (lowest rolling XI-xP window) + the run's fixture difficulty | reset *before/around* that dip |

**US-251 (ADR-082).** `analytics/chips.py::chip_advisor(...)` builds `xp_by_id` for the 15 (one `decision_xp`
pass over the horizon), then the four per-GW reductions above → a list of typed recommendations (dataclass or
dicts) carrying only **self-describing facts** (chip, gw, metric value, player names, opponent) so the LLM
narrates without inventing numbers (ADR-034/037). `_decide_chips` in `ask.py` routes a **chip/wildcard/bench
boost/triple captain/free hit** cue (after the specific intents), assembles facts, narrates + verifies.
`ui/chips.py::render_chip_advice(advice)` renders the block (CLI + web reuse it).

**US-252.** `pages/3_Squads.py`: add **"Chips"** to the segmented control; a `render_chips(...)` that calls
`ask.answer(question="chip advice", active_squad=…, horizon=horizon)` and `render_ask`, degrading to
`render_chip_advice` without Ollama. A caption: *"Based on your squad's fixture run + projected points over N
GWs. Double/blank gameweeks and mini-league position sharpen this in-season."*

**Deferred (honest):** mini-league position (needs league data → GW1); DGW/BGW detection (in-season);
season-long (38-GW) windows (v0 uses the tab horizon ≤8); a standalone CLI `chips` command (surface via `ask`
+ the Squads view first, like AI Tips).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-251 | **`chip_advisor` + chips `ask` intent** — the assembler (4 per-GW heuristics over `by_gameweek`/fixtures) + a grounded, verified intent + `render_chip_advice`. ADR-082. | High | ⬜ To do | ~⅔ session |
| US-252 | **Squads "Chips" view** — a segmented-control option routing through `ask.answer` (degrades without Ollama), horizon-aware, honest captions. | High | ⬜ To do | ~⅓ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `chip_advisor` picks the right GW on **synthetic** per-GW xP (a crafted `by_gameweek`
   makes each chip's best GW deterministic); the chips intent is **grounded + verified** (every narrated number
   is a fact; a monkeypatched narrator path asserted like the other intents); the Squads "Chips" view renders
   (AppTest) and degrades without Ollama. Existing **647** stay green.
2. **Manual smoke** (the demo squad) — Squads → Chips names a TC GW, a BB GW, a FH GW, and a WC window with
   the reason facts; the horizon dropdown changes the window; no Ollama → the plain advice still shows.
3. **Docs updated** — ADR-082 + index, Architecture, PROJECT_STATUS, Roadmap, README, Help.

---

### 📝 Session Progress Log

**US-251 — `chip_advisor` assembler + chips `ask` intent (ADR-082).** ✅ Done.
- `analytics/chips.py::chip_advisor(owned, by_gameweek_by_id, gameweeks)` — a pure reduction of the per-GW xP
  (`by_gameweek`, ADR-032) + `best_legal_xi` per GW into one recommendation per chip: **TC** (max single
  starter's GW ceiling), **BB** (best all-15 GW + bench share), **FH** (weakest best-XI GW), **WC** (weakest
  rolling 3-GW window, clamped to the horizon). Exported + `CHIP_NAMES`.
- `ui/chips.py::render_chip_advice` — the plain-text block (CLI + web reuse it) with an honest
  "sharpens in-season" note.
- `ask.py`: a `chips` intent — `_decide_chips` (reuses `_squad_xp`, same horizon xP as the other tools) +
  `_chips_facts` (self-describing, every number traceable) → grounded + **verified** (ADR-037). Routing:
  a new `_INTENT_KEYWORDS["chips"]` placed **first** with distinctive phrases (`chip`/`chips`/`chip strategy`/
  `which chip`/`triple captain`/`free hit`/`use my bench boost`/`use my wildcard`) — **not** bare
  `bench boost`/`wildcard`/`captain`/`bench`, so it can't hijack build/captain/start_bench. Wired into
  `_dispatch` + `_needs_squad`.
- **Tests (+10):** `chip_advisor` picks the deterministic best GW per chip on a crafted `by_gameweek` (+ empty-
  safe + short-horizon clamp + render); routing (chips phrases route; build/captain/bench unaffected);
  `_chips_facts` carry every number; `_decide_chips` is grounded + verified. **657** green, ruff clean.
- **Real-data smoke (demo squad):** `ask "which chip should I use for RoboTS?"` → TC GW1 (B.Fernandes, xP 5.9),
  BB GW1 (all 15 project 62.3, bench +13.0), FH GW4 (XI 46.5), WC GW3–GW5 (avg XI 46.8). Preseason-flat but
  the mechanism is correct.

**US-252 — Squads "Chips" view.** ✅ Done. (No new ADR — extends ADR-082.)
- `views/squads.py::render_chips(squad_name, squad, *, horizon)` — mirrors `render_ai_tips`: routes through
  `ask.answer("which chip should I use for <squad>?", active_squad=…, horizon=…)` + `render_ask`, degrading
  to the plain advice block without Ollama; a caption frames the fixture-run basis + what sharpens in-season.
- `pages/3_Squads.py`: **"Chips"** added to the segmented control (after AI Tips), horizon-aware, dispatched
  lazily; the control's help updated.
- **Tests (+1):** the Chips view renders the advice block with all four chips (AppTest). **658** green,
  ruff clean.
- **Manual smoke (demo squad, Ollama present):** the block is correct (TC/BB/FH/WC with facts). The local LLM
  narration drifted (invented "45.5", miscounted) — and the **verifier flagged it** ("⚠ Unverified … figures
  2, 45.5 — the data above is the source of truth"). Exactly the ADR-037 safety net: the block is
  authoritative, the prose is a checked bonus. Not a bug — honest behaviour on a weak local LLM.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **647 → 658** (+11); ruff clean; CI-parity green.
ADRs **81 → 82** (ADR-082). No data change (an assembler over the existing xP).

**Delivered**
- **US-251 — `chip_advisor` + grounded `chips` intent (ADR-082).** A pure `analytics/chips.py::chip_advisor`
  reduces the per-GW xP (`by_gameweek`) + `best_legal_xi` into a best GW/window per chip (TC/BB/FH/WC); a
  `chips` `ask`/`chat` intent narrated + verified; `ui/chips.py::render_chip_advice` is the shared block.
- **US-252 — Squads "Chips" view.** A segmented-control option routing through `ask.answer` (degrades without
  Ollama), horizon-aware, honest captions.

**What went well**
- **The assembler pattern paid off again** — `decision_xp` already returns `by_gameweek` (ADR-032), so all four
  chips are argmax/argmin reductions of numbers we already compute. No new analytics, no drift; the whole
  feature is pure + a thin intent + a thin view.
- **De-risked before the gate** — a live check confirmed `by_gameweek` sums to the total, `team_fdr` has a
  usable spread, and there are no DGW/BGW / no `events` table preseason. That turned the ADR into a
  known-scope decision and kept the honest captions accurate.
- **Routing collisions handled cleanly** — `triple captain` ⊃ "captain", `bench boost` ⊃ "bench", `wildcard`
  ∈ build. Distinctive multi-word chip phrases placed *first*, deliberately excluding the bare colliding
  words, so a routing test pins that "build me a squad for a bench boost" still builds.
- **The grounding net proved itself live** — with Ollama present the local model's chip narration drifted
  (invented a figure, miscounted), and `verify_grounding` flagged it (⚠) while the authoritative block stayed
  correct. Exactly the ADR-037 contract, visible in a real smoke.

**Watch-outs / follow-ups**
- **Preseason-flat fixtures** → the chip windows sit close together now (e.g. TC/BB both land GW1); the
  mechanism is correct and spreads as fixtures diverge in-season. Captioned honestly.
- **Deferred (in ADR-082):** DGW/BGW detection (in-season); **mini-league position** (needs the leagues API →
  GW1); a season-long (38-GW) scan (v0 uses the ≤8 tab horizon); a standalone CLI `chips` command.
- **Weak local narration** → the block is the source of truth and the ⚠ trust line is honest; a stronger LLM
  (or the cloud's degrade-to-block) reads better. No code issue.

See `Sprint96_Lessons_Learnt.md` for the detailed retro.
