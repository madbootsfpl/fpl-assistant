# Sprint 169: Player DNA — the AI Verdict (US-412/413, ADR-118)

**Dates:** 2026-08-18
**Status:** ✅ Complete — ADR-118 + US-412/413. Step 2 of the arc (S168 radar ✅). A headline **verdict** above the
radar: a one-word call + a 0–100 gauge + a grounded Edge/Risk line. Was **mostly wiring** — `explain_worth` /
`worth_confidence` / `confidence_band` already existed (ADR-061/089) and had **no caller** until now. 1027 → 1043
tests. **Vocabulary owner-confirmed** (ownership-neutral Strong pick/Solid/Risky/Avoid; Buy/Hold/Sell waits for the
My Squad entry, S171).

> **Owner:** "start Sprint 169 — looks good" (the radar render signed off).

---

### 🎯 Scope

**US-412 — the verdict heuristic (`src/analytics/explain.py`, pure).** A new `Verdict` dataclass +:
- `verdict_score(xp_pct, value_pct, consistency_pct, *, available, doubtful, chance)` → **1–99**, a **transparent
  display heuristic** (ADR-089 style — *not* a probability, **never fed into any decision**, `decision_xp`
  untouched): mostly **projected-points standing** (0.55 × xP percentile-in-position) + **value** (0.25) + **minutes
  reliability** (0.20); **unavailable caps it low**, a **doubtful** player is capped by their chance of playing.
- `verdict_label(score, *, available)` → **Strong pick · Solid pick · Risky · Avoid** (ownership-neutral — see the
  vocabulary note).
- `player_verdict(row, *, xp, xp_percentile, value, median, rank, n_peers, value_percentile,
  consistency_percentile, available, doubtful, chance, horizon)` → a `Verdict(label, score, band, edge, risk)` —
  the score/label from the heuristic, and the grounded **Edge**/**Risk** lines **reused from `explain_worth`**
  (projects-N-points · above/below median value · top-third rank · penalty taker · set-pieces · ownership · form),
  with availability surfaced first when flagged.

**US-413 — the verdict card (`src/web_streamlit/verdict_card.py`) + wire into Players ▸ Card.** A self-contained
dark card with a **server-built SVG gauge** (an arc filling to the score, purple→teal) + the verdict word + the
**Edge (✓) / Risk (⚠)** lines. Placed **between the player card and the DNA radar** (card → *verdict* → radar
detail). The web layer computes the inputs by **reusing what `render_card` already has**: `xp` (the `decision_xp`
already computed there), the **Value + Consistency percentiles from the DNA object** (US-410), and a small
same-position value rank/median + `is_unavailable`/`status`/`chance`. **No new store read, no `decision_xp`
change.**

**Vocabulary note (owner sign-off welcome, one-line to change).** The ADR sketch said *Buy/Hold/Sell*, but that's
**ownership-relative** — on the Players browse card we don't know if you own the player, so v1 uses an
**ownership-neutral backing strength** (Strong pick / Solid / Risky / Avoid). The **Buy/Hold/Sell** framing arrives
naturally with the **My Squad entry (S171)**, where ownership *is* known (owned → Hold/Sell; not → Buy). Easy to
relabel if you'd rather.

---

### ✅ Definition of Done (3-part)
- **Tests (~+10):** the score heuristic (an elite available player scores high; unavailable caps low; a doubtful
  player capped by chance; percentile → score monotonic); the labels at each threshold; `player_verdict` assembly
  (edge/risk reused from `explain_worth`, availability first when flagged; `sqlite3.Row` safe); the gauge SVG (arc
  length tracks the score); the card HTML (label · score · edge · risk); the Card view shows a verdict.
- **Manual smoke:** Players ▸ Card ▸ Haaland (Strong pick, high score, "penalty taker / projects N pts" Edge, a
  premium-price / median-value Risk) · a flagged player (Avoid, capped) · a cheap mid-table player (Risky/Solid).
- **Docs:** ADR-118 build-progress; PROJECT_STATUS; Roadmap; this doc + lessons.

### ⚠️ Watch-items
- **Display heuristic, not a metric** — `verdict_score` is a transparent composite of existing signals; pin that
  `decision_xp` is unchanged (the invariant).
- **Don't double-count** — the score leans on xP (which already encodes fixtures/minutes); value + consistency are
  light adjustments, not a second ranking.
- **Reuse the DNA percentiles** already computed for the radar — don't recompute (one `player_dna` per selection).

---

### 🎯 Delivered

- **`analytics/explain.py` (US-412) — the verdict heuristic.** A `Verdict` dataclass + `verdict_score`
  (1–99, transparent display heuristic: 0.55·xP-percentile + 0.25·value + 0.20·consistency; unavailable capped
  ≤20, doubtful capped by chance), `verdict_label` (Strong pick/Solid/Risky/Avoid), and `player_verdict` which
  assembles the score/label + **Edge/Risk lines reused from `explain_worth`** (availability first when flagged).
  **Not a probability, never fed into `decision_xp`** (ADR-041 intact); exported from `src.analytics`.
- **`web_streamlit/verdict_card.py` (US-413) — the card.** A dark card: a **server-built SVG gauge** (arc → score,
  tone by verdict word) + the call + grounded Edge (✓) / Risk (⚠). `build_verdict` computes the value
  rank/median + xP percentile and **reuses the `xp` map + the `PlayerDNA` percentiles** the Card view already
  holds. Wired **above the radar** in `render_card` — no new store read.
- **Tests: +16** (10 heuristic · 6 renderer). Full suite **1043 green**; ruff clean. Live-render verified
  (Haaland Strong-87 w/ premium-price risk; injured → Avoid, capped).

### 🧠 Lessons

- **The grounded machinery was already there.** `explain_worth` (ADR-061) had sat with **no caller** — the verdict
  is mostly *composition*, so the Edge/Risk wording matches the value view for free, and no new "why" logic.
- **A verdict is a display lens, not a metric.** The score is a documented heuristic over existing signals
  (xP + value + minutes + availability) — kept out of `decision_xp` (the one metric), the same discipline as the
  confidence heuristics (ADR-089).
- **Match vocabulary to what the surface knows.** *Buy/Hold/Sell* implies ownership the browse card doesn't have,
  so an ownership-neutral call is the honest choice until the My-Squad entry supplies context (S171).
- **Compose, don't recompute.** The verdict rides on the `player_dna` + `decision_xp` already computed for the
  radar — one selection, one compute.
