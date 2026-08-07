# Architectural Decision Record: Explainability — grounded Why / Risk / Confidence

**Decision ID:** ADR-089
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** extends the grounded-answer contract (ADR-034/037). A new **analytics** layer
(`explain.py`) that turns the signals a decision already used into a visible **Why / Risk / Confidence**.
Triggered by tester feedback ("introduce explainability into the Ask tab").
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester: *"show **why** a recommendation was made, not just what — traceable to xP · fixtures · xMins ·
penalties · form · injuries · ownership · news, with a **Confidence**, a **Why** (✓) and a **Risk** (⚠)."*
Today `ask` shows the decision + flat facts; the *reasoning* is implicit.

**The constraint (the trust model):** the reasons and the confidence must be **derived from real signals** —
never invented by the LLM. This is an **analytics** feature (compute the reasons from the data), not an
LLM-prose feature; the LLM may still narrate, and the narration is still **verified** (ADR-037).

**Verified in code (real data):** a `captain_picks` pick carries `xp`, `opponent`, `venue`, `penalty_taker`,
`doubtful`, `chance`, `minutes_weight` (xMins) and `difficulty`; the player row adds `selected_by`,
`corners_order`/`freekicks_order`, `form`, `status`. For B.Fernandes: xp 5.9 (highest), xMins 0.89, on
penalties + FKs, 48.7% owned, Hull (A), **only +0.2 over Haaland** → an honest confidence ≈ **69 / Medium**.

#### Decision Drivers
- **Grounded** — every ✓/⚠ and the number come from the data, auditable, never an LLM guess.
- **Honest confidence** — a *transparent heuristic*, presented as such (not a calibrated probability); a near
  coin-flip must read Medium, not High.
- **Reusable** — one framework for captain now, transfer next, squad/chips later.
- **Degrade + verify** — the block shows without the LLM; narrated numbers still verify.

---

### ✅ Decision

**A pure `analytics/explain.py` that produces a grounded `Explanation` from a decision's signals.**

**1. The shape.** `Explanation = {reasons: [str], risks: [str], confidence: int, band: str}` — `reasons` are
the ✓ signals *for* the pick, `risks` the ⚠ signals *against*; each string carries its real value (e.g.
*"Highest projected points (5.9)"*, *"Away fixture"*, *"Narrow lead over Haaland (+0.2)"*).

**2. Captain (US-269).** `explain_captain(picks, players_by_id)` builds, for the top pick:
- **Why (✓):** highest projected points (`xp`) · on penalties (`penalty_taker`) · also on free-kicks/corners
  (`freekicks_order`/`corners_order == 1`) · expected to start (`minutes_weight ≥ 0.7` → *"~90 mins"*) ·
  template pick (`selected_by ≥ 20%`) · favourable fixture (`difficulty ≤ 2` or home) · in form
  (`form ≥ FORM_MIN`, GW1+).
- **Risk (⚠):** away fixture (`venue == 'A'`) · doubtful (`chance%`) · rotation risk (`minutes_weight < 0.7`) ·
  tough fixture (`difficulty ≥ 4`) · **narrow lead over the runner-up** (`xp_gap < 0.5`, using `picks[1]`) ·
  big differential (`selected_by ≤ 5%`). A zero/absent signal simply produces no line (empty-safe, honest).

**3. The confidence heuristic (documented, so the number is auditable).**
```
plays     = minutes_weight                      # 0..1 — how likely to actually play
clearness = min(1.0, max(0.0, xp_gap) / 0.8)    # 0..1 — a ≥0.8 xP lead over #2 is a "clear" pick
fixture   = 1.0 if (venue == 'H' or difficulty <= 2) else (0.6 if venue == 'A' else 0.8)
score     = 100 * (0.45*plays + 0.40*clearness + 0.15*fixture) + (4 if penalty_taker else 0)
if doubtful:  score = min(score, (chance or 50) * 0.8)   # a doubtful captain can't be high-confidence
confidence = clamp(round(score), 1, 99)
band = "High" if confidence >= 75 else "Medium" if confidence >= 55 else "Low"
```
So B.Fernandes ≈ `100*(0.45·0.89 + 0.40·0.25 + 0.15·1.0) + 4 ≈ 69` → **Medium** — nailed-on to play, but a
near coin-flip and away. A runaway home pick with a big lead → **High**. It is **not** a probability, and a
caption says so.

**4. Surfacing + grounding.** `_decide_captain` puts the confidence + signal values into `facts` (so a narrated
number still traces, ADR-037) and renders a **Confidence · Why · Risk** block (`ui/captain.py`) in `ask`/`chat`,
the CLI, and the web Captain view — above the existing table. The block shows with or without the LLM.

---

### 🔀 Alternatives Considered

- **Let the LLM write the reasons.** Rejected — ungrounded; it would invent plausible-but-wrong "why"s. The
  reasons are computed; the LLM only phrases the summary and is verified.
- **A bare number (no band, no basis).** Rejected — false precision; the score + band + the ✓/⚠ basis + a
  "heuristic" caption keep it honest (owner steer).
- **A calibrated probability model.** Deferred — needs in-season data + validation; a transparent heuristic is
  honest and useful now.

---

### 🧭 Consequences

**Positive**
- The grounding becomes **visible as reasons** — the "not a black box" promise, delivered; a user can trust,
  challenge, or disagree.
- Reusable across decisions; reads the signals a decision already computed → **no engine change**.
- Honest by construction (grounded ✓/⚠, a heuristic confidence that tempers coin-flips and doubts).

**Negative / risks (mitigations)**
- **Confidence looks precise** → shown as a heuristic with its ✓/⚠ basis + a caption; a band accompanies the
  number.
- **Some signals are preseason-gated** (form / goal-involvement % / opponent xGC) → omitted until live, and
  the block notes momentum/form light up at GW1.
- **A tunable formula** → the weights live in one documented place (`explain.py` + this ADR); easy to calibrate.

---

### 📊 Validation

Verified: the captain pick carries the signals; B.Fernandes ≈ 69/Medium by the formula. Acceptance:
`captain_confidence` is deterministic + bounded (runaway nailed-on → High; doubtful/coin-flip/away → lower,
capped by chance); `explain_captain` emits the right ✓/⚠ for a crafted pick and skips zero signals; the captain
answer renders Confidence/Why/Risk and still **verifies** (a narration restating the values is ✓); the engine +
existing **693** tests are unchanged (new tests added); ruff clean.
