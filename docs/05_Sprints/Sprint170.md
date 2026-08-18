# Sprint 170: Player DNA — AI Insights (US-414/415, ADR-118)

**Dates:** 2026-08-18
**Status:** ✅ Complete — ADR-118 + US-414/415. Step 3 of the arc (S168 radar ✅ · S169 verdict ✅). A grounded **AI
Insights** panel below the radar: 3–5 plain-English observations synthesised from the data (*the AI explains*).
1043 → 1056 tests. **Rate cards dropped** (would duplicate the card grid + radar chips) → the sparkline version
moves to S171.

> **Owner:** "start Sprint 170".

---

### 🔎 Scope decision — AI Insights, not standalone rate cards

The ADR sketch paired "key-rate cards" with AI Insights, but a scan of the surface shows the rate cards would
**duplicate what's already on screen**:
- the **player card** (ADR-084) already renders a **position-adaptive stat grid** (pts · goals · xGI · xG · xA ·
  ICT · DefCon/90 · …), and
- the **DNA radar chips** (S168) already show the **percentile + raw** for all 8 rates.

The *only* distinct rate card is one with a **per-GW sparkline** — and that's per-GW-history data (🟡 GW1). So the
sparkline trend-cards move to **S171** (with the performance-trend line, form dots and the other GW1 placeholders),
and S170 delivers the non-redundant, on-brand half: **AI Insights**. *(Keeps "avoid duplication / unnecessary
complexity".)*

---

### 🎯 Scope

**US-414 — the insights engine (`src/analytics/player_dna.py`, pure).** An `Insight(kind, text)` dataclass +
`player_insights(player, dna, *, max_items=5)` → a prioritised, **grounded** list synthesised from the DNA
percentiles + the player row + crowd tier (reuse `crowd.ownership_tier`):
- **Availability first when flagged** — unavailable / doubtful-with-chance (⚠).
- **Top 1–2 strengths** — the highest-percentile *skill* axes → "Elite {axis}: top {N}% of {pos}s ({sublabel}
  {raw})" (✓).
- **Team context** — a top-attack team from the Team-Attack axis (ℹ).
- **Set-piece floor** — first-choice penalty taker / on corners-or-FKs (⚡).
- **Ownership** — essential/template/differential from the tier (ℹ).
- **Cautions** — premium price with only mid-pack value; limited minutes (⚠).
- Pure, dict + `sqlite3.Row` safe, empty-safe (a blank/zero player yields fewer bullets, never raises).

**US-415 — the insights card (`src/web_streamlit/insights_card.py`) + wire below the radar.** A self-contained
dark card: a list of bullets, each with a kind icon (✓ strength · ⚡ set-piece · ℹ info · ⚠ caution). Rendered in
`render_card` **after** the DNA radar (card → verdict → radar → **insights**), reusing the `dna` already computed —
no new store read, no `decision_xp` change.

---

### ✅ Definition of Done (3-part)
- **Tests (~+10):** strengths surface the top axes with "top N%" wording; availability leads when flagged; penalty
  taker → a ⚡ line; ownership tiers (essential vs differential); the premium-mid-value caution; `max_items`
  respected; empty/`sqlite3.Row` safe; the card HTML has a bullet + icon per insight.
- **Manual smoke:** Players ▸ Card ▸ Haaland (elite threat · top attack · penalty taker · near-template) · a cheap
  differential · a flagged player (availability leads).
- **Docs:** ADR-118 build-progress; PROJECT_STATUS; Roadmap; this doc + lessons.

### ⚠️ Watch-items
- **Don't just echo the verdict** — insights are a *fuller, differently-framed* list (percentile strengths, team
  context, ownership); some overlap with Edge/Risk is fine, wholesale repetition isn't.
- **Grounded only** — every bullet must trace to a value (percentile, order, tier, price); no invented prose.
- **Reuse the `dna`** already computed for the radar (one `player_dna` per selection).

---

### 🎯 Delivered

- **`analytics/player_dna.py` (US-414) — the insights engine.** An `Insight(kind, text)` + `player_insights(player,
  dna, *, max_items=5)`: availability first when flagged → top 1–2 **skill** strengths ("Elite {axis}: top {N}% of
  {pos}…") → team context (top-attack) → set-piece floor (⚡ penalty/set-pieces) → ownership tier → premium-mid-value
  / limited-minutes cautions. Reuses `crowd.ownership_tier` + `is_unavailable`; **Set Pieces excluded from the
  strengths** (it gets its own ⚡ line, so no double-up); dict + `sqlite3.Row` safe, empty-safe. Exported from
  `src.analytics`.
- **`web_streamlit/insights_card.py` (US-415) — the card.** A dark card of grounded bullets, an icon per kind
  (✓ good · ⚡ set-piece · ℹ info · ⚠ warn), rendered **below the radar** in `render_card`, reusing the `dna`
  already computed — no new store read.
- **Tests: +13** (9 engine · 4 renderer). Full suite **1056 green**; ruff clean. Live-render verified on real data.

**Deferred to S171:** the sparkline **rate trend-cards** (per-GW history = 🟡 GW1) — the non-sparkline rates are
already on the card grid + radar chips.

### 🧠 Lessons

- **Check for duplication before adding a panel.** The card's stat grid + the radar chips already show every raw
  rate + percentile — so "rate cards" would have been redundant; the honest add was Insights (and the sparkline
  version waits for the data that actually makes it distinct).
- **Grounded synthesis, not new prose.** Every bullet traces to a value (percentile, order, tier, price) — the same
  "analytics decide, the AI explains" contract, now as a scannable list.
- **De-dup within the feature too.** Set Pieces earns one line (the ⚡ floor note), not two — a small exclusion
  keeps the list clean.
- **Compose on the DNA.** Insights ride on the `player_dna` already built for the radar — one compute feeds radar,
  verdict *and* insights.
