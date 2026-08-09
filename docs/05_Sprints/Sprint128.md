# Sprint 128: CLI catch-up — a `chips` command + a price "who's about to rise?" intent

**Dates:** 2026-08-29
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~½ session (two surfacing stories — reuse existing analytics + renderers; no new analytics)
**Carried Over:** none

> **Direction:** bring two web/ask-only features to the terminal — a standalone **CLI `chips`** command, and a
> **"who's about to rise?"** price `ask`/`chat` intent. Both surface analytics that already exist.

---

### 🔎 Verified at planning (on real data + the code)

- **Chips is fully assembled + rendered already** — `analytics.chip_advisor(owned, by_gameweek_by_id, gameweeks)`
  (ADR-082) + `explain_chips` (confidences, ADR-089) + a **console renderer** `ui/chips.py::render_chip_advice(
  advice, squad_name, horizon, confidences)`. The `ask` `_decide_chips` shows the exact assembly; **there is no
  CLI `chips` command** — so a `cmd_chips` is a thin edge mirroring `cmd_analyse` (load a saved squad →
  `decision_xp` with `by_gameweek` → `chip_advisor` → `render_chip_advice`).
- **Price analytics exist** — `analytics.price_prediction(player)` → rise/fall/stable, `price_pressure` (net per
  1% ownership), `price_flag` (🔺/🔻); **but no `ask` price intent**. Preseason `price_pressure` is **0** (net
  transfers flat) → the intent must **degrade** to a "nothing's moving yet — live at GW1" note.
- **The `ask` router is keyword-first** (`_INTENT_KEYWORDS` + `route`, ADR-034): a new **`price`** intent slots in
  with distinctive cues ("about to rise/fall", "price rise/drop", "who's rising"), a `_decide_price` that ranks
  the pool by price signal, grounded (analytics decide, the LLM narrates, verified ADR-037). A **global** intent
  (all players), not squad-scoped.
- **No new analytics, no drift** — both stories are surfacing: the chips path reuses the one `decision_xp`
  assembly (so the CLI agrees with `ask`/web by construction); the price intent reuses `price_prediction`.

---

### 🎯 Sprint Goal

**Objective:** the terminal reaches parity on two features — `python app.py chips <squad>` and `ask "who's about
to rise?"` — reusing the existing analytics + renderers. No new analytics; grounded; degrade honestly preseason.

#### Success Criteria
- [x] **US-316 (a CLI `chips` command)** — `python app.py chips <squad> [--next N] [--type …] [--no-xmins]`
      mirrors `cmd_analyse`: load the saved squad, build the horizon `decision_xp` (with `by_gameweek`), call
      `chip_advisor` + `explain_chips`, print `render_chip_advice`. Unknown/absent squad → the same friendly
      nudge `analyse` gives (list the saved names). Agrees with `ask`/web by construction (one assembly).
- [x] **US-317 (a price "who's about to rise?" `ask`/`chat` intent)** — a `price` intent (`_INTENT_KEYWORDS` +
      `_decide_price`) ranks the pool by `price_pressure`/`price_prediction` → the likely **risers 🔺** (and
      **fallers 🔻**), a grounded shortlist; **preseason → a "no price movement yet (live at GW1)" note** (0
      pressure). Works in `ask` + `chat`; the LLM narrates only the facts (verified ✓).
- [x] **No drift** — surfacing only; `decision_xp`/`chip_advisor`/`price_*` unchanged; existing **805** stay
      green (**811** with +6); ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, README (the CLI `chips` + the new `ask` intent), Backlog
      (the two follow-ups marked done); no new ADR — surfacing.

---

### 🧭 Design sketch

**US-316.** `cli.py::cmd_chips(args)`: `squad = SquadStore().load(args.squad)` (not-found → print the saved
names, like `cmd_analyse`); `owned = [p for p in players if p["id"] in set(squad["player_ids"])]`;
`ranked = decision_xp(players, upcoming, history, horizon=args.next, gw_history_by_code=…)`;
`by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}`, `gameweeks = ranked[0]["gameweeks"]`;
`advice = chip_advisor(owned, by_gameweek_by_id, gameweeks)`; `print(render_chip_advice(advice, args.squad,
horizon=args.next, confidences=explain_chips(advice)))`. Add the `chips` subparser (`<squad>` + `--next`/`--type`/
`--no-xmins`, aligned with `analyse`). Empty/None advice → a graceful note.

**US-317.** A `price` intent in `_INTENT_KEYWORDS` (cues above), placed so it doesn't shadow `worth`/`shortlist`.
`_decide_price(store, question)`: rank all available players by `price_pressure`; take the top risers
(`price_prediction == "rise"`) and top fallers, each with 🔺/🔻 + the pressure + Own%; a small renderer
(`ui/price.py::render_price_movers` or reuse the shortlist shape). **Grounded:** the facts carry the named
players + numbers; `subjects` = those names so `verify_grounding` doesn't flag them; `task` = "name who's about
to rise/fall from the facts, note it's live at GW1". **Preseason:** all pressure 0 → return a clear "no price
movement yet — this lights up from GW1" message (a first-class answer, like other dormant-preseason intents).

**Deferred:** a **CLI price column** on `table`/`xg` (the ask intent covers the query; a column is a separate
polish); an absolute "% to the next change" (needs `total_players` + a since-last-change counter — a GW1 data
item); chip-timing that spans DGW/BGW (in-season).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-316 | **A CLI `chips` command** — surface `chip_advisor` in the terminal (reuses the renderer). | High | ✅ Done | ~¼ session |
| US-317 | **A price "who's about to rise?" `ask`/`chat` intent** — surface `price_prediction`. | High | ✅ Done | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `chips <squad>` prints the advice (contains "Triple Captain"/"Bench Boost"); an
   unknown/absent squad prints the nudge; the assembly matches `ask` (same `chip_advisor` inputs). The `price`
   intent **routes** ("who's about to rise?") and **decides** — a grounded movers list, or the preseason
   "nothing moving / live GW1" note (0 pressure); `verify_grounding` clean. Existing **805** stay green; ruff
   clean. No `.save(`, no analytics change.
2. **Manual smoke** — `python app.py chips <a demo squad>` prints the four chips; `python app.py ask "who's about
   to rise?"` → the preseason note (net transfers flat); with forced pressure, named risers/fallers.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Backlog.

---

### 📝 Session Progress Log

- **US-316 (a CLI `chips` command)** — added `cli.py::cmd_chips` (mirrors `cmd_analyse`): load the saved squad
  (unknown → the same "Saved: …" nudge), build the horizon `decision_xp` (with `by_gameweek`), call
  `chip_advisor` + `explain_chips`, print the **existing** `ui/chips.py::render_chip_advice`. New `chips`
  subparser (`--squad` required · `--next` default 8 · `--type` · `--no-xmins`); imported `chip_advisor`,
  `explain_chips`, `render_chip_advice`. Reuses the one `decision_xp` recipe → the CLI advice **agrees with
  ask/web by construction** (no drift). Smoke: `python app.py chips --squad TS` prints the four chips (Triple
  Captain GW3 Haaland · Bench Boost GW7 · Free Hit GW6 · Wildcard GW4–6) with confidences; unknown squad → the
  nudge. +3 tests (routing · unknown-squad nudge · real-DB advice). ruff clean. **808** total.
- **US-317 (a price "who's about to rise?" `ask`/`chat` intent)** — added a **`price`** intent to
  `_INTENT_KEYWORDS` (prediction-specific cues: "about to rise/fall", "price risers/fallers", "likely to
  rise/fall", …), placed **first** so it beats rules' explanatory "price rise" + trends' bare "risers" (verified:
  "who's about to rise?"/"price risers" → price; "how do price rises work?" → rules; "who are the risers?" →
  trends). `_decide_price` ranks the available pool by `price_pressure` → the likely **risers 🔺 / fallers 🔻**
  (`price_prediction`), grounded (facts + subjects + task); a new `ui/price.py::render_price_movers`. **Preseason
  (net transfers flat → 0 pressure) → a first-class "no movement yet — live at GW1" message.** Dispatched in
  `_dispatch` (so `ask` + `chat` both route it). A **lens** — never `decision_xp`. +3 tests (routing · preseason
  message · active risers/fallers named). Smoke: preseason → the GW1 note; forced pressure → Riser +24,000 🔺 /
  Faller −24,000 🔻. ruff clean. **811** total.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ both stories shipped — the terminal/`ask` reach parity on two web-only features, purely by
**surfacing** existing analytics. A CLI `chips` command (reusing the renderer) and a `price` "who's about to
rise?" `ask`/`chat` intent, both degrading honestly until GW1. No new analytics, no ADR.

**Delivered**
- **US-316** — `cli.py::cmd_chips` (mirrors `cmd_analyse`) → `chip_advisor` + the existing `render_chip_advice`;
  a `chips` subparser. Matches `ask`/web by construction (one `decision_xp` recipe). +3 tests.
- **US-317** — a `price` intent (placed first, prediction-specific cues) + `_decide_price` → likely risers 🔺 /
  fallers 🔻 by `price_pressure`, grounded; a new `ui/price.py`. Preseason → a "live at GW1" message. +3 tests.

**Verified at planning + build** — chips was fully assembled + rendered already (no CLI edge); price analytics
exist but had no `ask` intent; the routing was checked for collisions ("price risers" → price, "how do price
rises work?" → rules, "who are the risers?" → trends).

**Metrics** — 811 tests (805 → +6) · ruff + CI-parity green · 97 ADRs (no new) · 2 stories, ~½ session.

**What went well**
- **Reuse paid off** — both stories are thin edges over existing analytics + renderers; the CLI chips advice
  can't drift from `ask`/web because it's the *same* `decision_xp` assembly.
- **Routing precedence handled carefully** — placing `price` first (with prediction-specific cues) fixed the
  "price risers" → rules collision without stealing genuine rules questions; the checks pin it.
- **Honest degrade preserved** — the price intent returns a first-class "live at GW1" message preseason, matching
  the trends/momentum pattern, so it never fabricates movement from flat data.
- **The lens line held** — the price intent is display only; `decision_xp` is untouched.

**Even better if**
- The price intent's value is small **preseason** (net transfers flat) — it's built + tested, but it earns its
  keep from GW1 when transfers flow.
- A **CLI price column** on `table`/`xg` was deferred (the `ask` intent covers the "who's rising?" query).

**Deferred / backlog** — a CLI price column; an absolute "% to the next price change" (needs a GW1 counter);
DGW/BGW chip-timing (in-season). The buildable-now backlog is now essentially exhausted before **GW1
(2026-08-21)**, which unlocks the calibration work (set-piece/DefCon/form + momentum).

---

### 📌 For Tony

_(sprint-review reflection fields — left blank for you)_

- **Biggest learning this sprint:**
- **Pause small work until GW1, or keep banking polish? (pause/keep):**
- **Confidence the CLI/ask are at parity now (1–5):**
