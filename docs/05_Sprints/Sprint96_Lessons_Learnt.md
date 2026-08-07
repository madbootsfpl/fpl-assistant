# Lessons Learned

**Sprint:** Sprint 096 — Chip Strategy Guidance (a fixture-run chip-window advisor)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

For a loaded squad, a grounded **chip advisor** that recommends **when** (which GW / window) to play each chip
— **Triple Captain · Bench Boost · Free Hit · Wildcard** — from the squad's own projections, with an honest
caption on what sharpens in-season. Reuses the unified xP; no new core metric.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **The assembler pattern** (ADR-070 → ADR-082) — orchestrate existing primitives into a new decision instead
  of adding analytics, so the new answer can't drift from the standalone tools.
- **Grounded + verified intents** — analytics decide, the LLM narrates, `verify_grounding` checks every
  number/name (ADR-037).

### New Skills Acquired

- `decision_xp` already returns each player's **`by_gameweek`** (`{gw → xP}`, ADR-032) — so "which GW scores
  most" for one player (TC) or all 15 (BB) is a pure **argmax/argmin reduction** of numbers we already have.
- **Keyword-routing collisions need a plan**: `triple captain` ⊃ "captain", `bench boost` ⊃ "bench",
  `wildcard` ∈ build_squad. Solve with *distinctive multi-word phrases placed first* and deliberately **exclude
  the bare colliding words** — then pin it with a routing test.
- Reading the code's constraints before crafting a test fixture saves a loop: `best_legal_xi` enforces
  **≤3/club** (a same-club synthetic squad returns an empty XI) and `select_squad` reads `total_points` for a
  tiebreak — the synthetic 15 must satisfy both.

---

# What Went Well ✅

- **No new analytics** — four chips = reductions of `by_gameweek` + `best_legal_xi`; the feature is a pure
  assembler + a thin intent + a thin view.
- **De-risked before the gate** — a live check (`by_gameweek` sums; `team_fdr` spread; no DGW/BGW / no
  `events` table) made ADR-082 a known-scope decision and kept the honest captions accurate.
- **The grounding net proved itself live** — Ollama's chip narration drifted; `verify_grounding` flagged it
  (⚠) while the block stayed correct. The ADR-037 contract, visible in a real smoke.
- 647 → 658 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Chip phrases hijack existing routes | "triple captain"/"bench boost"/"wildcard" contain other intents' keywords | Distinctive multi-word phrases placed first; exclude bare colliding words; a routing test pins it |
| Synthetic XI came back empty | `best_legal_xi` enforces ≤3/club; all-same-club squad is infeasible | Spread the 15 over 6 clubs |
| `KeyError: total_points` in the solve | `select_squad` sorts on `total_points` | Add the field to the synthetic players |
| Preseason windows sit close together | fixtures are near-uniform pre-GW1 | Correct mechanism; an honest caption that it sharpens in-season |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| `by_gameweek` is the key primitive | Per-GW xP already exists → chip timing is a reduction, not new analytics |
| Assembler > new metric | Reuse `best_legal_xi`/`captain_picks`; the chip answer can't diverge |
| Route on distinctive phrases | Multi-word, placed first, excluding bare collisions — and test it |
| Verify catches a weak LLM | The block is truth; ⚠ flags drift — no code change needed |

---

# Development Lessons 💻

- Check the real data + the callee's constraints *before* writing the gate or the fixture — it removes guesswork
  and rework.
- When a keyword router grows, new intents must be designed against the existing ones (collisions), not just
  added — a routing test is the guard.
- Ship the honest scope: fixture-run + xP now; DGW/BGW + mini-league position deferred and captioned, not faked.

---

# AI Collaboration Lessons 🤖

- "Chip strategy" mapped to: one `decision_xp` pass → four per-GW reductions → a grounded intent → a thin view.
  The grounding contract (analytics decide, LLM narrates, verified) let me surface an LLM answer *safely* even
  when the local model is weak — the ⚠ line makes the trust boundary visible to the tester.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-082 | **Chip-strategy advisor** — a pure `chip_advisor` reduces per-GW xP (`by_gameweek`) + `best_legal_xi` into a best GW/window per chip (TC = max starter ceiling · BB = best all-15 GW · FH = weakest XI GW · WC = weakest rolling window); a grounded, verified `chips` `ask`/`chat` intent (distinctive routing) + a Squads "Chips" view. An assembler (ADR-070 shape); no new analytics. Fixture-run + xP based; DGW/BGW + mini-league position deferred | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Chip Strategy — the gated half:** DGW/BGW detection (in-season) + **mini-league position** (leagues API,
  GW1) to sharpen the advice.
- **AI Chat Assistant** (owner intake) — still needs a grounded-vs-free-form design/ADR + a willing LLM.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the Price Change Predictor lights up.
- Backlog still open: persisted chat context; season countdown / deadline banner; server-side squad persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "verify on real data before the gate" step — it made this a clean one-session sprint.

---

# Key Commands Learned

```text
python app.py ask "which chip should I use for <squad>?"   # TC/BB/FH/WC windows, grounded + verified
python app.py chat                                          # "chip strategy" as a conversational turn
python -m src.web_streamlit                                 # Squads → Chips tab (degrades without Ollama)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Chip window | The GW (or rolling stretch) a chip is best played in |
| `by_gameweek` | Per-GW xP for a player (`{gw → xP}`), summing to the horizon total (ADR-032) |
| Assembler | A function that orchestrates existing primitives into a new answer (no new analytics) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-082 | The chip-advisor decision + the four heuristics + the deferrals |
| `src/analytics/chips.py` (`chip_advisor`) | The pure per-GW reductions |
| `src/ask.py` (`_decide_chips`, `_INTENT_KEYWORDS["chips"]`) | The grounded intent + the routing collision guard |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-251 `chip_advisor` assembler + grounded `chips` intent — per-GW reductions of `by_gameweek` (ADR-082)
- US-252 Squads "Chips" view — routes through `ask.answer`, degrades without Ollama, horizon-aware

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
