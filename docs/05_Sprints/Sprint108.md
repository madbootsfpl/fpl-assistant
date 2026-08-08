# Sprint 108: A structured "Captain Pick" answer + a shared Model note

**Dates:** 2026-08-09 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a presentation upgrade of explainability — no analytics change)
**Carried Over:** none

> **Direction (tester feedback):**
> *"Explainability is really good — to evolve it further, I'd like the captaincy answer to read like this:"*
>
> ```
> Captain Pick
>
> 🥇 Bruno Fernandes
> Man Utd · MID
> Projected: 5.9 pts
>
> Confidence: 69/100 (Medium)
>
> Why
> ✓ Highest projected points
> ✓ Penalty taker
> ✓ Set-piece involvement
> ✓ Strong fixture vs HUL
> ✓ Expected ~80 mins
>
> Risks
> ⚠ Away fixture
> ⚠ Only +0.2 pts ahead of Haaland
>
> Alternatives
> 🥈 Haaland 5.7 pts
> 🥉 Rice 4.5 pts
>
> Model note:
> The recommendation is data-driven; AI explains the reasoning.
> ```

---

### 🔎 Verified at planning (on real data)

- **The numbers already match the mockup.** `ask "who should I captain?"` today returns **B.Fernandes 5.9 xP,
  Confidence 69/100 Medium**, with ✓ *Highest projected points · On penalties · Takes set-pieces · Expected to
  start (~80 mins) · Favourable fixture (HUL)* and ⚠ *Away fixture (HUL) · Narrow lead over Haaland (+0.2)*.
  So this sprint is a **presentation** change, not an analytics one — `explain_captain`/`captain_confidence`
  already compute every reason, risk and the number (ADR-089).
- **Every field the card needs is already on the pick rows** — `web_name`, `team` (short code), `position`,
  `xp` (the "Projected" line), plus `opponent`/`venue`. The **Alternatives** are just `picks[1]` / `picks[2]`
  with their `web_name` + `xp`. A **friendly team name** ("Man Utd") comes from `store.get_teams()`
  (`short_name → name`) — the one new lookup to thread in.
- **The Ask captain answer has no alternatives today.** `_decide_captain` renders the header + the
  Why/Risk/Confidence block only; the ranked shortlist table is CLI-only. So the 🥈🥉 **Alternatives** section
  is genuinely new content in the Ask/web answer (a small, grounded add from data already in hand).
- **One surface upgrades three edges.** The web **Captain** view + **Ask** tab both route through
  `ask.answer` → `render_ask`, and the CLI `chat`/`ask` share it — so a new renderer in `_decide_captain`
  lands in the CLI, the web Ask tab, and the web Captain view at once.

---

### 🎯 Sprint Goal

**Objective:** the captaincy answer reads like the mockup — a clear **Captain Pick** card (medal · Team · Pos ·
Projected pts · a clean Confidence line · Why · Risks · **Alternatives** 🥈🥉) closed by an honest **Model
note** — and that same Model note + sharper phrasing carry across the **whole explainability family**. Grounded
throughout: the analytics decide, the wording only presents; every number still verifies (✓, ADR-037).

#### Success Criteria
- [ ] **US-277 (the structured Captain Pick answer)** — a new renderer produces the mockup layout: a
      **`Captain Pick`** header; the 🥇 pick as a card (**name** / **Team · Pos** / **Projected: N pts**); a
      clean **`Confidence: NN/100 (Band)`** line; **Why** (✓) and **Risks** (⚠); an **Alternatives** section
      (🥈 / 🥉 with name + pts); and the **Model note** footer. Reuses `explain_captain` + the ranked `picks`;
      phrasing aligned to the mockup. Wired into `_decide_captain` → CLI `ask`/`chat` + web **Ask** + web
      **Captain**. Scope (a squad vs all players) is preserved as a small subheading.
- [ ] **US-278 (a shared Model note + phrasing, everywhere)** — a single reusable **`MODEL_NOTE`** (with the
      folded heuristic caveat) appended **once** to each explained answer — **transfer · squad · chips ·
      gameweek** as well as captain (never repeated inside the composite gameweek block); the sharper phrasing
      applied where it reads naturally; and the **CLI `captain`** command brought into the structured format.
- [ ] **No drift** — display-only; `explain_*`/`captain_confidence`/the analytics unchanged; the ✓/⚠ grounding
      still verifies; existing **708** stay green (captain/explain assertions updated for the new wording);
      ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (extends **ADR-089** — noted; a short
      **ADR-090** only if we decide to formalise the Model note as a contract element, agreed at the gate).

---

### 🧭 Design sketch

**US-277 — the Captain Pick card (text).**
- A new pure renderer — `ui/captain.py::render_captain_pick(picks, explanation, *, scope, team_names)` (or a
  sibling of `render_explanation`) — building the mockup block from the ranked `picks` + the `Explanation`:
  - **Header:** `Captain Pick` (+ a faint scope line, e.g. *from squad 'RoboTS'* / *all players*).
  - **Pick:** `🥇 {web_name}` · `{friendly team} · {position}` · `Projected: {xp} pts`.
  - **Confidence:** `Confidence: {score}/100 ({band})` — clean (the caveat moves to the Model note).
  - **Why / Risks:** the existing ✓ reasons / ⚠ risks, with wording nudged to the mockup — "Penalty taker",
    "Set-piece involvement", "Strong fixture vs {OPP}", "Expected ~{N} mins", "Only +{gap} pts ahead of {name}",
    and **"Highest projected points"** without the redundant `(5.9)` (it's in the card header now).
  - **Alternatives:** `🥈 {name} {xp} pts` / `🥉 {name} {xp} pts` (from `picks[1]`, `picks[2]`; omitted if
    absent).
  - **Model note:** the shared line (US-278).
- Thread a `short_name → name` map from `store.get_teams()` into `_decide_captain` so the card shows "Man Utd".
  `_captain_facts` keeps feeding the verifier the same numbers, so narration still checks out.
- The wording nudges live in `explain_captain`'s reason/risk strings (the single source), so the CLI `captain`
  command (US-278) inherits them for free.

**US-278 — a shared Model note + phrasing across the family.**
- A single constant — `ui/explain.py::MODEL_NOTE` = *"Model note: The recommendation is data-driven; AI explains
  the reasoning. Confidence is a heuristic from the signals, not a probability."* — plus a tiny
  `render_model_note()` helper.
- Appended **once per answer** at the assembler level (`_decide_captain`, `_decide_transfer`,
  `_decide_build_squad`, `_decide_chips`, `_decide_gameweek`), **not** inside `render_explanation` (so the
  composite gameweek plan shows it once at the foot, never three times).
- Drop the "(a heuristic … not a probability)" tail from `render_explanation`'s confidence line (it now lives in
  the Model note) — one edit, inherited everywhere.
- Bring the **CLI `captain`** command onto `render_captain_pick` (or add the card above its shortlist table) so
  the terminal matches the mockup too.

**Deferred:** a **web-native** styled captain card (medals/chip HTML) — the text card reads well and lands on
all edges first; a visual pass can follow if wanted. DGW/BGW-aware alternatives (in-season).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-277 | **Structured "Captain Pick" answer** — the mockup card (medal · Team·Pos · Projected · Confidence · Why · Risks · Alternatives 🥈🥉) in Ask/CLI/web. | High | ⬜ To do | ~½ session |
| US-278 | **Shared Model note + phrasing** — one honest footer across captain·transfer·squad·chips·gameweek; caveat folded in; CLI `captain` on the new format. | High | ⬜ To do | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `render_captain_pick` produces the header · medal pick (Team·Pos·Projected) · clean
   Confidence · Why · Risks · Alternatives 🥈🥉 · Model note, from real picks + an `Explanation` (empty-safe:
   no runner-ups → no Alternatives section); the Ask captain answer + the CLI `captain` show it; the friendly
   team name resolves; the `MODEL_NOTE` appears **once** on each explained answer (incl. the composite gameweek
   plan); `render_explanation`'s confidence line no longer carries the caveat. Existing **708** stay green
   (wording assertions updated). No `.save(` / no analytics change (guardrails hold).
2. **Manual smoke** — `ask "who should I captain?"` reads like the mockup; a squad-scoped captain question keeps
   its scope; transfer/squad/chips/gameweek answers each end with the Model note exactly once.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log.

---

### 📝 Session Progress Log

**US-277 — the structured "Captain Pick" answer.** ✅ Done.
- New pure renderer `ui/captain.py::render_captain_pick(ranked, explanation, *, scope, team_names)` builds the
  mockup card: `Captain Pick` header · a scope line · the 🥇 pick (**name** / **Team · Pos** / **Projected:
  N pts**) · a clean **`Confidence: NN/100 (Band)`** · **Why** (✓) / **Risks** (⚠) · **Alternatives** (🥈/🥉 +
  their xP) · the **Model note**. Empty-safe (no runner-ups → no Alternatives; no picks → a soft message).
- The wording nudges live in **`explain_captain`**'s reason/risk strings (single source): "Penalty taker",
  "Set-piece involvement", "Expected ~N mins", "Strong fixture vs {OPP}", "Only +{gap} pts ahead of {name}",
  and "Highest projected points" without the redundant number (it's on the card's Projected line). So the CLI
  `captain` command + the composite gameweek plan inherit the sharper phrasing for free.
- `MODEL_NOTE` (with the heuristic caveat folded in) added to `ui/explain.py`. `_decide_captain` threads a
  `short_name → name` map from `get_teams` ("MUN" → "Man Utd") and renders the card as `detail`; the facts
  (confidence/why/risk/xp) still feed the verifier, so narration checks ✓.
- **Scope is shown always** ("from squad 'X'" | "all players") — I kept the all-players line rather than the
  mockup's clean omission, so the answer never hides its scope; a "next" follow-up reads "Option #2 · …". The
  venue risk is terse **"Away fixture"** (per the mockup); the opponent still appears in the Strong/Tough-fixture
  lines, so it's never lost.
- **Reaches three edges from one change** — CLI `ask`/`chat`, the web **Ask** tab, and the web **Captain** view
  all route through `_decide_captain`.
- **Tests (+2):** `render_captain_pick` card + empty-safety; the captain Ask assertions updated for the new
  format (`Captain Pick` · `Alternatives` · `Model note:`); the explain wording assertions updated. **710**
  green, ruff clean.
- **Manual smoke:** `ask "who should I captain?"` → matches the mockup (B.Fernandes · Man Utd · MID · 5.9 ·
  69/100 Medium · 🥈 Haaland 5.7 · 🥉 Mbeumo 5.0); squad-scoped it self-tempers to 99/High.

_(US-278 next — "start US-278".)_

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
