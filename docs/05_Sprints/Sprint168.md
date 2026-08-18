# Sprint 168: Player DNA v1 — the percentile radar (foundation) (US-410/411, ADR-118)

**Dates:** 2026-08-18
**Status:** 📋 Planned — gate before build (ADR-118 accepted). Target: the first, self-contained slice of the
Player DNA page — the differentiator's core, buildable **now** on data we already hold.

> **Ask (owner, 2026-08-18):** start ADR-118 now while the ideas are fresh — GW1 brings a flood of updates and
> feedback, so get the fresh 🟢 core done first. **This sprint = the percentile radar** (the standout piece);
> the AI Verdict, rate cards, insights and full-page assembly follow in their own sprints.

---

### 🗺️ The ADR-118 build arc (this sprint = step 1 of 4)

1. **Sprint 168 — the percentile radar (foundation).** ← *this sprint.* The pure percentile-within-position
   engine + the 8-axis SVG radar, shown on **Players ▸ Card**. Highest value, lowest risk, fully self-contained.
2. **Sprint 169 — the AI Verdict.** Buy/Hold/Sell + a 0–100 score + a grounded Edge/Risk line, reusing
   `explain_worth()` / `decision_xp` (mostly wiring — the engine exists).
3. **Sprint 170 — key-rate cards + AI Insights.** Percentile-backed rate cards (reuse the engine) + grounded
   insight bullets.
4. **Sprint 171 — assemble the full page + the My Squad entry + 🟡 GW1 placeholders.** Reflow Card → the full
   DNA page; wire **My Squad ▸ Players & lineup** to the same component; honest "fills in from GW1" empty-states
   for the trend line / sparklines / form (they self-populate once the season runs).

---

### 🎯 Scope of this sprint

**US-410 — the percentile engine (`src/analytics/player_dna.py`, pure/no-Streamlit).**
`player_dna(target, pool, *, min_minutes=450)` → a structured result: for each of the 8 axes, `(label, sublabel,
raw_value, percentile)`. **Percentile-within-position** = the target's value ranked against **same-position players
with ≥ `min_minutes`** (denoise fringe players); the target is always included even if below the floor (flagged).
The 8 axes (ADR-118, owner-approved), each mapped to real fields:

| Axis | Metric | From |
|---|---|---|
| Goal Threat | xG / 90 | `xg`, `minutes` |
| Creativity | xA / 90 | `xa`, `minutes` |
| Set Pieces | set-piece score | `penalties_order` (weighted top) · `corners_order` · `freekicks_order` |
| FPL Output | points / 90 | `total_points`, `minutes` |
| Consistency | minutes | `minutes` |
| Value | points / £m | `total_points`, `price` |
| Bonus Potl | ICT / 90 (**proxy** — no raw BPS) | `ict_index`, `minutes` |
| Team Attack | team xG | Σ `xg` by `team` (percentile across teams) |

- **dict + `sqlite3.Row` safe** (a `_get` accessor — the recurring Row `.get()` trap).
- **Safe on zeros/preseason** — a 0-minute pool (nobody past the floor) or a 0-value axis never divides-by-zero;
  returns a percentile of `None`/0 gracefully, never raises.
- Preseason it ranks on **last-season totals** (what we carry, and the best preseason signal — same basis as xP).

**US-411 — the SVG radar + wire it into Players ▸ Card (`src/web_streamlit/dna_card.py`).**
`radar_svg(dna, *, size=…)` builds a **server-side `<svg>`** (⚠ **not** canvas+JS — `st.markdown` doesn't execute
`<script>`; the preview's canvas can't run in-app): rings (25/50/75/100), 8 spokes + labels, the percentile
polygon (brand purple→teal fill), vertex dots coloured by band (`≥85` GOOD · `60–84` teal · `<60` amber, via
`brand.FDR_STYLE`/tokens), and a row of percentile **chips** beneath. Wired into `views/players.render_card` as a
**"🧬 Player DNA"** section under the card (before the Boot Battle compare). Reuses the existing `decision_xp`
compute already in `render_card` — **no new store read**, display-only, **no `decision_xp`/analytics change**.

**Out of this sprint** (later steps): the AI Verdict (169), rate cards + insights (170), full-page reflow + My
Squad entry + GW1 placeholders (171). Position-adaptive **axis sets** (e.g. DEF → clean sheets/DefCon, like the
position-adaptive stat grid) = a tracked follow-up; v1 uses the same 8 axes ranked within each position (an
attacking-threat rank for a defender is still meaningful).

---

### ✅ Definition of Done (3-part)

- **Tests (~+8):** percentile math (Haaland FWD → Goal Threat ~100th, a mid forward ~50th); per-90 with the
  minutes floor; the set-piece score (pen-taker > corners/FK > none); team-xG aggregation; the zero-minute /
  empty-pool / zero-price guards; `sqlite3.Row` **and** dict inputs; the SVG has 8 axis labels + an 8-point
  polygon + 8 chips + band colours; the Card view renders a "Player DNA" section (AppTest).
- **Manual smoke:** `streamlit run` → **Players ▸ Card ▸ Haaland** → the radar shows the real shape (Goal Threat /
  Consistency / Team Attack high, Value mid); check a DEF and a low-minute player render without error.
- **Docs:** ADR-118 follow-up note (v1 slice shipped); PROJECT_STATUS + Roadmap tick; this doc + lessons.

### ⚠️ Risks / watch-items
- **Static SVG only** (no JS) — the radar is Python-built markup; verify it renders cleanly in `st.markdown` and
  scales on mobile (viewBox + `max-width:100%`).
- **Percentile pools are small per position** (~30 forwards past the floor) — fine, but note the floor in the UI so
  a 92nd-percentile reads honestly ("vs 30 forwards"), as the preview does.
- **Low-minute target** (new signing / promoted) — still render, but caption "limited minutes" so the shape isn't
  over-read.
- **No engine change** — pin the `decision_xp` invariant; this is display-only.
