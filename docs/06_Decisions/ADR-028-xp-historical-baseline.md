# Architectural Decision Record: xP historical baseline (multi-season rate)

**Decision ID:** ADR-028
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** Extends ADR-006/007 (xP v0 / horizon); consumes ADR-027 (history)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

xP v0 (ADR-006) scores a player as `points_per_game × Σ fixture-multiplier`. The **rate** is a
**single season's** `points_per_game` — and **preseason that is just *last* season**, one noisy
sample. A career-best or an injury-hit or a low-minutes new-signing season badly misrepresents a
player.

A pressure-test on real players (with the Sprint 026 history) made the case concrete:

| Player | `ppg` now (1 season) | multi-season baseline (pp90) | read |
|---|--:|--:|---|
| Haaland | 6.8 | 6.91 | consistent elite — agree |
| Struijk | 3.2 | 2.90 | tempers a career-best season |
| Dorgu | 3.7 | 5.03 | blends a breakout with a weak debut |
| **Marmoush** | **2.7** | **6.51** | **single-season ppg badly understates him** |

Marmoush is the argument: ranking on one season would wrongly write him off. A **multi-season
baseline** corrects it — and it's *most* valuable now, preseason, when there is no current form.

#### Decision Drivers
- **A more robust rate** — many seasons beat one noisy sample.
- **Use only trustworthy fields** — per ADR-027, older-season xG/DC are unreliable (`0.00` = "not
  tracked"); points + minutes are reliable across all seasons.
- **Don't stray into Phase 3** — minutes/rotation forecasting (xMins) is a later phase.

---

### 💡 Decisions

**1. A multi-season baseline rate.** For each player, compute a **recency- and minutes-weighted
points-per-90 over the last ≤3 qualifying seasons**, from `player_history_past`:

```
qualifying     = seasons with minutes ≥ 900     # ~10 full games — else a cameo invents a rate
pp90(season)   = total_points × 90 / minutes
weight(season) = recency_rank × minutes         # newer seasons rank higher; minutes = durability
baseline       = Σ(weight · pp90) / Σ(weight)    # None if no season qualifies
```

Uses **only `total_points` and `minutes`** — the fields ADR-027 confirmed are reliable across all
seasons. `k_seasons = 3` (recent enough to reflect the current player, wide enough to de-noise).

**Minutes gate (≥ 900), added after a live smoke test.** Without it, a fringe player's tiny cameo
(e.g. 2 pts in 20 mins → pp90 90.0) produced an absurd baseline that topped the xP ranking. The
same minutes gate the over/under and DefCon views use (ADR-017/018) — the Sprint 016 Meslier
lesson: small samples make garbage rates, so gate them. A player with no ≥900-minute season gets
no baseline and falls back to the current `ppg`.

**2. Preseason: the baseline *replaces* the single-season rate.** With no current-season games, the
baseline (which already includes last season, weighted highest, plus two more) is strictly more
information than the lone `ppg`. So the xP rate = **baseline when available, else the current
`points_per_game`** (graceful fallback for players with no history — usually young/fringe).

**3. In-season blending is a documented follow-on — not built now.** Blending the baseline with
live current-season form needs data that does not exist yet (GW1 hasn't played); building it now
would be untestable speculation. Deferred to the Backlog, to add once gameweeks accrue.

**4. Policy at the edge — the xP formula is unchanged.** Only the **rate input** changes; the
fixture multiplier, the gameweek horizon (ADR-007), and the availability gate are untouched. The
baseline is computed in analytics and joined to players via a new `players.code` (= `element_code`)
column — the missing join key to `player_history_past`.

**5. Honest caveat — "quality when playing", not a minutes forecast.** `pp90` assumes the player
features ~90 minutes; it does **not** model rotation/minutes risk (that's **xMins, Phase 3**). So a
high-pp90 rotation player looks optimistic. Stated in the `xp` footer, in the spirit of the
DefCon/xGC "a guide, not a guarantee" notes.

**Not in scope:** xMins/rotation; blending with live form; using historical xG/xA/DC (unreliable);
changing the optimiser (it already consumes xP via the pluggable objective, ADR-011).

---

### 🧪 Worked example (pressure-testing — real data, before code)

Baseline vs single-season, computed on live history (points + minutes only):

- **Marmoush** — 2024/25: 73 pts / 1174 min → pp90 5.60; 2025/26: 56 / 691 → 7.29. Minutes-weighted,
  recency-weighted baseline ≈ **6.51**, vs a current `ppg` of **2.7**. The enrichment lifts a player
  the single-season rate would bury.
- **Haaland** — pp90 across 2023/24–2025/26 (7.65 / 5.95 / 7.28) → baseline **6.91** ≈ `ppg` 6.8.
  A stable player barely moves — the baseline doesn't distort the obvious cases.

Confirms the method is sensible at both extremes (corrects the misleading case, leaves the clear
case alone) before any code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** a materially better xP rate preseason — robust to one-season noise; feeds better
  Phase 3 decision support. Reuses Sprint 026's history; no new dependency; the xP formula and the
  optimiser are untouched.
* **Negative / Trade-offs:** `pp90` ignores rotation (xMins, Phase 3) — optimistic for part-timers
  (caveat stated). A slight unit difference between the pp90 baseline and the `ppg` fallback (close
  for starters; the fallback only affects history-less fringe players). Fixed 3-season window.
* **Risks & Mitigations:**
  - *Over-optimism for rotation players* → the "quality when playing" caveat; xMins is Phase 3.
  - *Unreliable historical stats* → baseline uses **points + minutes only** (ADR-027).
  - *Over-modelling* → 3 seasons, simple recency×minutes weights; gated here.

---

### 🛠 Implementation & Migration
* **Components Affected:** `players.code` column (migration) + `Player.from_api` + save/upsert;
  a `baseline_rate()` in analytics; a bulk history getter in `storage`; `player_xp` accepts a
  per-code baseline and uses it as the rate; `cmd_xp` loads history + computes baselines; the `xp`
  view shows the rate used + a caveat. Docs.
* **Action Items:**
  - [x] Record the method + worked example + the caveat (US-078)
  - [ ] `players.code`; `baseline_rate`; enrich `player_xp`; wire `cmd_xp`; display; tests (US-078)
  - [ ] (Backlog) blend baseline with live current-season form once gameweeks play

---

### 🔄 Review & Reconsideration
* **Review Date:** Once the season is underway (blend live form) or if xMins arrives (Phase 3).
* **Triggers for Reconsideration:**
  - [ ] Current-season data accrues → add the blend (weight shifts to live form).
  - [ ] xMins model exists → multiply the rate by expected minutes (retire the "when playing" caveat).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-078 (this); US-076/077 (the history it consumes)
- **External Docs:** [ADR-006 (xP v0)](./ADR-006-expected-points-v0.md) · [ADR-007 (horizon)](./ADR-007-multi-week-xp.md) · [ADR-027 (history + reliability caveat)](./ADR-027-historical-past-seasons.md) · [ADR-011 (pluggable objective)](./ADR-011-squad-objective.md) · [Sprint 026](../05_Sprints/Sprint26.md)
