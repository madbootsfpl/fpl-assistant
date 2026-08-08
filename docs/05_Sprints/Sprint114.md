# Sprint 114: Four-tier ownership badges — one ownership language

**Dates:** 2026-08-15 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a crowd-lens refinement + the explanation vocabulary — no analytics change)
**Carried Over:** none

> **Direction (tester feedback):** *"Could we use these badges to represent ownership %? (Challenge if you have
> better.)"* — 💎 **Differential** <5% · ⭐ **Popular** 5–20% · 🟦 **Template** 20–60% · 👑 **Essential** >60%
> (highly owned; going without is a major rank risk).

---

### 🔎 Verified at planning (on real data)

- **The proposal fills real gaps.** Today `crowd_flags` badges only **🟦 template (≥20%)** and **💎 differential
  (≤5%)** — so the **5–20%** band (57 players) is **unbadged**, and the one **>60%** player (Haaland, 74.5%) is
  lumped in with template. All four tiers **populate now** (preseason: **500** ≤5 · **57** 5–20 · **15** 20–60 ·
  **1** >60), so this is **live immediately**, not dormant — though preseason ~500/573 read 💎 until ownership
  concentrates at GW1 (the legend will say so).
- **One shared function → every tab.** `crowd_flags` is the "Trends" column on the **Players Pool**, **Build**,
  **Analyse**, the **My Squad pitch**, **Captain** and the **Trending** page — so refining it there gives one
  consistent ownership language everywhere (owner's steer: *apply everywhere*).
- **Aligned to the existing filter.** The differential tier uses **≤5% (`DIFFERENTIAL_OWN`)** — the same cut
  `ask "best differential …"` (ADR-061) uses — so the badge matches what that query returns.
- **The explanations already speak ownership.** `explain_captain`/`explain_worth`/… say *"Template pick (N%
  owned)"* / *"Big differential (N%)"* — so they can adopt the **same tier vocabulary** (Essential/Template/
  Differential) for one language across badges + "why".

---

### 🎯 Sprint Goal

**Objective:** ownership reads as **four clear tiers** — 💎 differential · ⭐ popular · 🟦 template · 👑 essential
— consistently across every tab, and the recommendation "why" speaks the **same** language. A crowd-lens +
explanation refinement; the analytics/xP untouched (the ownership lens never feeds `decision_xp`).

#### Success Criteria
- [ ] **US-289 (four-tier ownership badges, everywhere)** — a pure `analytics/crowd.py::ownership_tier(player)`
      → **💎 differential** (≤5%) · **⭐ popular** (5–20%) · **🟦 template** (20–60%) · **👑 essential** (>60%),
      via `DIFFERENTIAL_OWN` / `TEMPLATE_OWN` / a new **`ESSENTIAL_OWN = 60`** (tunable, GW1-calibrated);
      `crowd_flags` uses it (replacing the 2-tier block), so it propagates to the Pool, Build, Analyse, My
      Squad, Captain and Trending. `CROWD_LEGEND` rewritten to the four tiers with the tester's meanings. Still
      a **lens** (never xP). Empty-safe.
- [ ] **US-290 (one language in the "why" + Trending/Help)** — the explanation ownership wording uses the tier
      label: a **>60%** pick reads **"Essential (N% owned)"** (✓), a **20–60%** pick **"Template pick (N%
      owned)"** (✓), a **≤5%** pick **"Differential (N% owned)"** (⚠) — across `explain_captain` /
      `explain_worth` / `explain_transfer` / `explain_squad`. The Trending page + Help show the tier legend.
- [ ] **No drift** — display/vocabulary only; `decision_xp`/the ranking/grounding unchanged (the ownership lens
      still never touches xP — the invariant test holds); existing **738** stay green (crowd/explain assertions
      updated for the tiers); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (extends **ADR-057** (crowd lens) +
      **ADR-089** (explainability) — noted; no new ADR).

---

### 🧭 Design sketch

**US-289 — the tiers.** `crowd.py`:
```python
ESSENTIAL_OWN = 60.0   # > this % owned → "essential" (a must-own; tunable, GW1-calibrated)

def ownership_tier(player):
    own = _get(player, "selected_by")
    if own is None:                 return ""
    if own <= DIFFERENTIAL_OWN:     return "💎 differential"   # ≤5  (matches the differential filter)
    if own < TEMPLATE_OWN:          return "⭐ popular"        # 5–20
    if own <= ESSENTIAL_OWN:        return "🟦 template"       # 20–60
    return "👑 essential"                                     # >60
```
`crowd_flags` swaps its `🟦/💎` block for `tier = ownership_tier(player); if tier: flags.append(tier)` — the
momentum/price/form flags are unchanged. `CROWD_LEGEND` → the four tiers + their meanings + the existing
🔥/❄️/💰/📈 note (and "ownership concentrates once the season runs").

**US-290 — one vocabulary.** A small `crowd.py::ownership_label(player)` (the tier word without the emoji) drives
the explanation text: the `own >= TEMPLATE_OWN` ✓ reason becomes **"Essential"** (>60) / **"Template pick"**
(20–60); the `≤ DIFFERENTIAL_OWN` ⚠ risk reads **"Differential (N% owned)"**. The 5–20 "popular" band stays
unlabelled in the "why" (neither a strong reason nor a risk), as today. The Trending page + Help render the tier
legend. `render_explanation`/`MODEL_NOTE` unchanged.

**Deferred:** a dedicated ownership-tier *column* (the badge in the Trends column is enough); per-tier
thresholds beyond the three constants; a `worth`-style tier verdict.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-289 | **Four-tier ownership badges** — `ownership_tier` (💎/⭐/🟦/👑) in `crowd_flags`, everywhere; legend rewritten. | High | ⬜ To do | ~½ session |
| US-290 | **One ownership language** — the tier vocabulary in the explanations (Essential/Template/Differential) + the Trending/Help legend. | High | ⬜ To do | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `ownership_tier` returns 💎/⭐/🟦/👑 at the ≤5 / 5–20 / 20–60 / >60 boundaries (empty-safe);
   `crowd_flags` shows exactly one ownership tier (+ the momentum/price/form flags); `CROWD_LEGEND` names all
   four; a **>60%** player's explanation reads "Essential (N% owned)", a 20–60% one "Template pick", a ≤5% one
   "Differential"; the `decision_xp` ownership-lens **invariant** still holds. Existing **738** stay green. No
   `.save(` / no analytics change.
2. **Manual smoke** — the Trends column shows 💎/⭐/🟦/👑 across the Pool + Trending + squad tabs; `ask "who
   should I captain?"` (Haaland-tier) reads **Essential** in the Why; the Trending legend lists the four tiers.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log.

---

### 📝 Session Progress Log

**US-289 — four-tier ownership badges, everywhere.** ✅ Done.
- New pure `analytics/crowd.py::ownership_tier(player)` → **💎 differential** (≤5%) · **⭐ popular** (5–20%) ·
  **🟦 template** (20–60%) · **👑 essential** (>60%), or `""` when ownership is absent — via `DIFFERENTIAL_OWN`
  / `TEMPLATE_OWN` / a new **`ESSENTIAL_OWN = 60`** (tunable). The differential cut is ≤5% (matches the "best
  differential" filter, ADR-061); 0% is included.
- `crowd_flags` swapped its 2-tier 🟦/💎 block for `ownership_tier`, so the four tiers propagate to **every**
  surface that shows the Trends column — Pool · Build · Analyse · My Squad pitch · Captain · Trending — and each
  player now shows **exactly one** ownership tier (the 5–20% "popular" band was previously unbadged).
- `CROWD_LEGEND` rewritten to name all four tiers with the tester's meanings + a note that ownership concentrates
  once the season starts. Still a **lens** (never xP — the `decision_xp` invariant test holds). Exported from
  `analytics`.
- **Verified on real data:** the spread is **1 essential** (Haaland 74.5% 👑) · **15 template** · **57 popular**
  (e.g. Palmer 11.9% ⭐, Saka 10.7% ⭐ — now badged) · **500 differential** — matching the distribution.
- **Tests (net +1):** `ownership_tier` per band + empty-safe + `crowd_flags` shows exactly one tier; the legend
  names all four; the distinctness test covers ⭐/👑. **738** green, ruff clean.

_(US-290 next — "start US-290".)_

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
