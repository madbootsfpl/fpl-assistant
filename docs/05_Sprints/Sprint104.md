# Sprint 104: Explainability in Ask — Why · Risk · Confidence

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a grounded explainability framework + captain, then transfer)
**Carried Over:** none

> **Direction (tester feedback):** *"Introduce **explainability** into the Ask tab — show **why** a
> recommendation was made, not just what. Every decision traceable to the signals (xP · fixtures · xMins ·
> penalties · form · injuries · ownership · news). A user can understand, trust, or challenge it."* Example
> (captain): a **Confidence** score + a **Why** (✓ highest xP · on penalties · expected 90' · good fixture) +
> a **Risk** (⚠ away).

> **Owner steer (this planning):** confidence = a **score + band** (e.g. *"72 / 100 · Medium"*), a transparent
> heuristic whose basis is the visible ✓/⚠ signals. Scope this sprint: **captain + transfer**.

---

### 🔎 Verified at planning (real data — the captain pick)

- **The signals are already in hand.** A `captain_picks` pick carries `xp`, `opponent`, `venue`,
  `penalty_taker`, `doubtful`, `chance`, `minutes_weight` (xMins), and `difficulty`; the player row adds
  `selected_by` (ownership), `corners_order`/`freekicks_order` (set-pieces), `form`, `status`. So the **Why /
  Risk** bullets are **grounded** — computed from data, never invented by the LLM (the trust model, ADR-037).
- **Real B.Fernandes pick:** xp **5.9** (highest) · xMins-weight **0.89** (nailed-on) · **on penalties** +
  first-choice **free-kicks** · **48.7%** owned (template) · **Hull (A)** · **only +0.2** ahead of Haaland
  (5.7). So an honest confidence ≈ **~69 / Medium** — high certainty he *plays*, but **away** and a **near
  coin-flip** on the choice. That honesty is the whole point.
- **Preseason-gated signals** (form 0, no team-goal totals, thin xGC) → shown only when live (e.g. *"in form"*,
  *"involved in N% of team goals"*, *"opponent Nth for xGC"* light up at **GW1**); the banner is honest about it.

---

### 🎯 Sprint Goal

**Objective:** an Ask recommendation shows **why** — a **Confidence** (score + band), a **Why** list (✓ the
grounded signals for it) and a **Risk** list (⚠ the ones against) — so a user can understand, trust, or
challenge it. A reusable framework, applied to **captain** and **transfer**. Grounded + verified; the LLM never
invents a reason or the number.

#### Success Criteria
- [ ] **US-269 (explainability framework + captain, ADR-089)** — a pure `analytics/explain.py`:
      `explain_captain(picks, players_by_id)` → an `Explanation` `{reasons:[…], risks:[…], confidence:int,
      band:str}` from the signals (✓ highest xP · on penalties · set-pieces · expected minutes · template ·
      favourable fixture; ⚠ away · doubtful · rotation risk · tough fixture · **narrow lead over the runner-up**
      · big differential). A **transparent, documented** `captain_confidence(...)` (blends xMins · the xP lead ·
      fixture; penalty bonus; capped by chance-of-playing when doubtful) + `confidence_band(score)`. Rendered as
      a **Why / Risk / Confidence** block in `ask`/`chat`, the CLI, and the web Captain view; the values enter
      the facts so the narration still **verifies (✓/⚠)**; a caption notes it's a heuristic, not a calibrated
      probability.
- [ ] **US-270 (transfer explainability)** — `explain_transfer(move, out_row, in_row)` → why the swap (✓ the
      buy's xP/XI-gain edge · better fixture/minutes/penalties; ⚠ the risks — price, the sold player's value,
      ownership) + a confidence from the **XI-gain margin**. Wired into the `transfer` intent's answer.
- [ ] **No drift** — the analytics/engine unchanged (explain reads existing signals); grounded + verified;
      existing **693** stay green; ruff clean.
- [ ] Docs: ADR-089 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 🧭 Design sketch

**US-269 (ADR-089).** `analytics/explain.py`:
- `Explanation` (a dataclass: `reasons`, `risks`, `confidence`, `band`).
- `captain_confidence(minutes_weight, xp_gap, penalty, venue, difficulty, doubtful, chance) -> int` — e.g.
  `100 * (0.45·plays + 0.40·clearness + 0.15·fixture) + penalty_bonus`, clamped 1–99, capped by `chance` when
  doubtful (`plays` = xMins; `clearness = min(1, xp_gap/0.8)`; `fixture` from venue/difficulty). Documented in
  the ADR so the number is auditable.
- `confidence_band(score)` → High (≥75) / Medium (≥55) / Low.
- `explain_captain(picks, players_by_id)` → builds the reason/risk strings (each tied to a real value) + the
  confidence for the top pick, using `picks[1]` as the runner-up for the "narrow lead" risk.

`_decide_captain` calls it, puts the confidence + signal values in `facts` (so `verify_grounding` can trace a
narrated number), and passes the `Explanation` to the renderer. `ui/captain.py::render_captain_picks` gains a
**Confidence: NN / 100 · Band** line + **Why** (✓) / **Risk** (⚠) bullets, above the existing table.

**US-270.** `explain_transfer(...)` mirrors it for a single swap; `_decide_transfer` + `render_transfers` show
the Why/Risk/Confidence for the top move.

**Deferred:** explainability for squad-build + chips (same framework, later); the GW1-gated signals
(form / goal-involvement % / opponent xGC rank) — shown when live.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-269 | **Explainability framework + captain** — `explain.py` (reasons/risks/confidence), a Why/Risk/Confidence block in Ask/CLI/web captain. ADR-089. | High | ⬜ To do | ~⅔ session |
| US-270 | **Transfer explainability** — `explain_transfer`, the Why/Risk/Confidence for the top swap in Ask. | High | ⬜ To do | ~⅓ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `captain_confidence` is deterministic + bounded (a nailed-on runaway pick → High; a
   doubtful/coin-flip/away pick → lower, capped by chance); `explain_captain` lists the right ✓/⚠ for a crafted
   pick (penalty/away/narrow-lead/template) and skips gated-zero signals; the captain answer renders the
   Why/Risk/Confidence and still **verifies** (a narration restating the values is ✓); the transfer explanation
   lists the swap's why/risks. Existing **693** stay green.
2. **Manual smoke** — `ask "who should I captain from RoboTS?"` shows *Confidence 69/100 · Medium* + Why
   (✓ 5.9 xP · on penalties · ~90' · template · Hull) + Risk (⚠ away · +0.2 over Haaland); a transfer answer
   shows why the swap.
3. **Docs updated** — ADR-089 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 📝 Session Progress Log

**US-269 — explainability framework + captain (ADR-089).** ✅ Done.
- `analytics/explain.py` (pure): an `Explanation` dataclass (`reasons`, `risks`, `confidence`, `band`);
  `captain_confidence(...)` — the documented heuristic (blends xMins · the xP lead over the runner-up ·
  fixture; penalty bonus; capped by chance-of-playing when doubtful; clamped 1–99); `confidence_band` (High
  ≥75 / Medium ≥55 / Low); `explain_captain(picks, players_by_id)` → grounded ✓ reasons (highest xP · on
  penalties · set-pieces · expected minutes · template · favourable fixture · in form) + ⚠ risks (away ·
  doubtful · rotation · tough fixture · **narrow lead over the runner-up** · big differential), zero/gated
  signals omitted. Exported from `analytics`.
- `ui/explain.py::render_explanation` — the shared **Confidence · Why (✓) · Risk (⚠)** block (a "heuristic,
  not a probability" caption). Wired into: **Ask** (`_decide_captain` sets a self-contained `detail` +
  puts confidence/why/risk in `facts` so a narrated number still **verifies ✓**), the **web Captain** tab, and
  the **CLI** `captain` command (`render_captain_picks(explanation=…)`).
- **Tests (+5):** `captain_confidence` bounded + reflects the signals (runaway→High, coin-flip/away→lower,
  doubtful capped by chance); `explain_captain` lists the right ✓/⚠ + skips gated-zero signals + empty-safe;
  the Ask captain answer carries the block + facts and shows the score+band. **698** green, ruff clean.
- **Manual smoke (RoboTS):** *Confidence 99/100 · High* + Why (✓ 5.9 xP · on penalties · set-pieces · ~80' ·
  49% template · Hull) + Risk (⚠ away) — in Ask, CLI, and the web Captain tab; the LLM narration restates the
  99 + reasons and **verifies ✓**. (Against the all-players pool the same pick is 69/Medium — the +0.2 lead
  over Haaland surfaces as a "narrow lead" risk: honest, context-aware grounding.)

**US-270 — transfer explainability (extends ADR-089).** ✅ Done.
- `explain.py`: `transfer_confidence(gain, …)` (scales with the XI-gain margin — a ≥3 gain reads High; capped
  by a doubtful buy) + `explain_transfer(move, in_row, horizon)` → ✓ reasons (**+gain to your XI** · higher
  projected points · on penalties · set-pieces · frees cash · template · in form) + ⚠ risks (costs £ from the
  bank · **selling the out player** · doubtful buy · big differential · marginal gain). Exported.
- `_decide_transfer` (single-move path): computes the explanation from the buy's full row, sets a
  self-contained `detail` (Why/Risk/Confidence) + puts confidence/why/risk in `facts` (so narration
  **verifies ✓**).
- **Tests (+2):** `transfer_confidence` scales with the gain + is capped/bounded; `explain_transfer` lists the
  gain/price/signals + is empty-safe. **700** green, ruff clean.
- **Manual smoke (TS):** *Ampadu → Zubimendi · Confidence 95/100 · High* + Why (✓ +9.3 XI over 5 GW · 17.1 vs
  7.8 xP) + Risk (⚠ selling Ampadu · big differential); the LLM restates the 95 + reasons and **verifies ✓**.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
