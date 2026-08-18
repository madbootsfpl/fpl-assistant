# Sprint 171: Player DNA — the page, the My Squad doorway & the GW1 trend (US-416/417, ADR-118)

**Dates:** 2026-08-18
**Status:** ✅ Complete — ADR-118 + US-416/417. The **finale** of the arc (S168 radar ✅ · S169 verdict ✅ · S170
insights ✅ · **S171 page + doorway + trend ✅**). One reusable **Player DNA** section, reachable from **two**
doorways, with a per-GW trend that lights up at GW1. 1056 → 1069 tests. **The ADR-118 arc is complete.**

> **Owner:** "start Sprint 171 — preview looks great."

---

### 🎯 Scope

**US-416 — one reusable section + owned-aware verdict + the GW1 trend (`web_streamlit/player_dna_view.py`).**
- **`render_player_dna(player, players, xp_by_id, *, gw_history=None, owned=None)`** — composes the four pieces in
  the approved order: **AI Verdict → DNA radar → AI Insights → Performance trend**. Extracted from `render_card`
  so **both** the Players tab and My Squad render the *same* component (no duplication). The layout stays the
  approved vertical stack (reads well on mobile).
- **Owner-aware verdict** — `verdict_label` (and `player_verdict`/`build_verdict`) gain `owned`: browse
  (`owned=None`) keeps **Strong pick/Solid/Risky/Avoid**; from My Squad (`owned=True`) it reads **Strong
  Hold/Hold/Sell**; a not-owned player viewed with squad context (`owned=False`) reads **Buy/Consider/Pass**. This
  delivers the ADR's Buy/Hold/Sell where ownership is actually known.
- **The performance trend (🟡 → auto-populates GW1).** A pure `player_gw_points(gw_history, code, *, last=8)` in
  `analytics/player_dna.py` → the player's **points-per-gameweek** series (from `player_history`), and a
  server-built `perf_trend_svg`. **Empty preseason → an honest "fills in from Gameweek 1" placeholder**; once real
  results land, the **line draws itself** (tested with synthetic per-GW rows). *W-D-L dots and per-stat sparklines
  are deferred* (the points line is the headline trend; per-stat needs more per-GW columns — a follow-up).
- Refactor `render_card` (Players) to call `render_player_dna` (capturing the `gw_history` it already loads for
  `decision_xp`). Display-only; **no `decision_xp` change.**

**US-417 — the My Squad doorway.** Wire `render_my_squad`'s **⚙ Players & lineup** panel (the existing "Select a
player" → card) to also call `render_player_dna(picked, players, xp_by_id, gw_history=gw_history, owned=True)` — so
tapping one of your XI shows their **Hold/Sell** verdict + radar + insights + trend, right where you manage the
squad. Reuses the panel's `xp_by_id`/`gw_history`; no new compute.

**Deliberately not shown:** the **shot map** (Opta/Understat event data — ADR-016; a future gated `soccerdata`
ADR). We don't advertise what v1 doesn't have.

---

### ✅ Definition of Done (3-part)
- **Tests (~+12):** owned-aware labels (Hold/Sell/Buy at thresholds; unavailable → Sell when owned, Avoid when
  browsing); the verdict tone covers the new words; `player_gw_points` (last-N, skips null points, empty preseason,
  `Row`-safe); `perf_trend_svg` draws a polyline for a series; the trend panel shows the placeholder when empty and
  a line when populated; `render_player_dna` composes all four (a smoke via the HTML builders); the My Squad panel
  invokes it.
- **Manual smoke:** Players ▸ Card ▸ Haaland (Strong pick, placeholder trend preseason) · My Squad ▸ pick an owned
  player (reads **Hold/Sell**, same radar/insights) · a synthetic-GW check that the line renders.
- **Docs:** ADR-118 build-progress → **arc complete**; PROJECT_STATUS; Roadmap; this doc + lessons.

### ⚠️ Watch-items
- **One component, two doorways** — extract cleanly so Players and My Squad can't drift.
- **Honest placeholder** — the trend must clearly read "from GW1", never a fake line preseason.
- **No engine change** — `decision_xp` untouched; owned-aware labels are display-only.
- **GW1 follow-up (tracked):** per-stat sparklines + W-D-L form dots (need more per-GW columns / results —
  build + verify when the data lands).

---

### 🎯 Delivered

- **`web_streamlit/player_dna_view.py` (US-416) — one reusable section.** `render_player_dna(player, players,
  xp_by_id, *, gw_history, owned)` composes **verdict → radar → insights → performance trend**, extracted from
  `render_card` so Players + My Squad share it. **Owned-aware verdict** (`verdict_label`/`player_verdict`/
  `build_verdict` gain `owned`): browse → *Strong pick/…*; owned → *Strong Hold/Hold/Sell*; not-owned-in-context →
  *Buy/Consider/Pass*. **The per-GW trend** — pure `player_gw_points` (points-per-GW series, empty preseason) +
  `perf_trend_svg`; an honest **"fills in from Gameweek 1"** placeholder that **auto-draws a line** once results
  land (tested with synthetic rows).
- **`views/squads.py` (US-417) — the My Squad doorway.** The ⚙ Players & lineup panel now renders the **same** DNA
  section (owned → Hold/Sell) below the actions for the picked owned player, skipped while Boot-Battle comparing.
  Reuses the panel's `xp_by_id` + `gw_history`.
- **Tests: +15** (owned labels · `player_gw_points` · trend SVG/panel · verdict tone · composition · **2 AppTest
  e2e** — Players Card + My Squad Hold/Sell). Full suite **1069 green**; ruff clean. No `decision_xp` change.

**Tracked GW1 follow-ups:** the *real* per-stat **sparklines** + **W-D-L form dots** (need more per-GW columns /
match results — build + verify on real data). The **shot map** stays out (a future `soccerdata` ADR).

### 🧠 Lessons

- **Extract once, wire twice.** A single `render_player_dna` means Players and My Squad can't drift — the same four
  panels, one code path, two doorways.
- **Match the verdict to what the surface knows.** *Buy/Hold/Sell* only makes sense with ownership — so the label
  framing is a parameter, neutral on the browse card, Hold/Sell in the squad.
- **A placeholder can be honest *and* future-proof.** The trend reads "fills in from GW1" now and draws a real line
  the moment `player_history` has rows — no redeploy, and it's unit-tested with synthetic gameweeks.
- **Build only what you can verify.** The points trend is real (we have `round`+`total_points`); per-stat
  sparklines / form dots wait for the columns + results that make them verifiable — tracked, not faked.
