# Sprint 112: Price Change Predictor (a directional lens, wired dormant → live GW1)

**Dates:** 2026-08-13 (planned)
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~1 session (a small analytics lens + presentation — no xP change)
**Carried Over:** none

> **Direction (owner steer — the last buildable-now item of the 5-request intake):** *"A Price Change Predictor
> — an indicator flagging players about to **rise/fall** in value, to time transfers."* Buildable now as a
> **directional flag** (not exact price/timing), **dormant preseason → live at GW1** — the Data-Hardening
> pattern (ADR-060). Shown on Players + Squads.

---

### 🔎 Verified at planning (on real data)

- **The inputs are present but flat preseason.** `transfers_in_event` / `transfers_out_event` are **0** for all
  573 players now (net transfers = 0), and `selected_by` (%) is populated. So a pressure signal reads **0 →
  "stable"** today and **lights up at GW1** — exactly the dormant-then-live shape.
- **What already exists (so we don't re-skin it).** `crowd_flags` shows **🔥 in / ❄️ out** (a *flat*
  net-transfer threshold) and **💰↑ / 💸↓** (`cost_change_event` — the change that **already happened**). The
  predictor adds the missing piece: a **forward-looking**, ownership-normalised *pressure* that says a player is
  **about to** move — distinct from "already moved".
- **No schema/ingest change needed.** FPL price moves when net transfers cross a threshold that scales with
  **ownership**. Normalising `net_transfers ÷ selected_by%` makes the signal **comparable across players**, and
  the (constant) total-manager count **cancels out** for direction + relative magnitude — so we need neither
  `total_players` nor a "since last change" counter (neither is in bootstrap). An absolute "% to change" is a
  GW1 calibration refinement, not a blocker.
- **A lens, never xP.** Like the crowd signals (ADR-057), this must **never** feed `decision_xp` — an
  invariance test will pin it.

---

### 🎯 Sprint Goal

**Objective:** a grounded, honest **price-pressure** signal — *likely to rise / fall / stable* — surfaced on
the Players pool and My Squad to help **time transfers**, built wired-but-dormant so GW1 is a switch-flip.
Display/analytics-lens only; the engine + xP untouched.

#### Success Criteria
- [x] **US-285 (price-pressure engine)** — a pure `analytics/price.py`: `price_pressure(player)` =
      **net transfers ÷ ownership%** (signed; `None` when either is absent; **0 preseason**); `price_prediction`
      → **rise / fall / stable** via tunable `config` thresholds (GW1-calibrated); a `price_flag` display helper
      (a **distinct** rise/fall marker, not the retrospective 💰/💸). Reuses `net_transfers`; `decision_xp`
      **unchanged** (an invariance test pins it).
- [x] **US-286 (surface it)** — a **Price** prediction column on the **Players Pool** (🔺 rising / 🔻 falling /
      — stable + a `PRICE_LEGEND` + an honest *"directional pressure from net transfers — a flag, not the exact
      price/timing; live from GW1"* caption); and on **My Squad** a **transfer-timing nudge** naming owned
      players **likely to fall** (*consider selling before the drop*) or **rise** (*hold / buy now*). Display
      only; no server writes.
- [x] **No drift** — a lens only; `decision_xp`/the analytics unchanged; preseason it reads all *stable*/"—"
      with the live-GW1 note; **737** green (730 → +7: 5 price-engine + Pool column + My Squad nudge); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, Roadmap, Backlog, README, Help, ADR index (a short **ADR-092** for the
      predictor — agreed at the gate).

---

### 🧭 Design sketch

**US-285 — the engine (the gate writes ADR-092).** `analytics/price.py`:
```python
def price_pressure(player):
    net = net_transfers(player)                 # in − out this GW (crowd.py)
    own = _get(player, "selected_by")           # % owned
    if net is None or not own:
        return None
    return net / own                            # net per 1% ownership — cross-player comparable; 0 preseason

def price_prediction(player):                   # "rise" | "fall" | "stable" (config thresholds, GW1-calibrated)
    p = price_pressure(player)
    if p is None:            return "stable"
    if p >= config.PRICE_RISE_PRESSURE:  return "rise"
    if p <= -config.PRICE_FALL_PRESSURE: return "fall"
    return "stable"

def price_flag(player):                         # display: 🔺 rising / 🔻 falling / "" (distinct from 💰/💸)
    return {"rise": "🔺", "fall": "🔻"}.get(price_prediction(player), "")
```
`config.PRICE_RISE_PRESSURE`/`PRICE_FALL_PRESSURE` are placeholders tuned so nothing fires on flat data
(calibrate on real net transfers at GW1, like `TRENDING_NET`/`FORM_WEIGHT`). Pure + empty-safe; no ingest.

**US-286 — presentation.** A **"Price"** column on the Pool (`views/players.py`) via `price_flag`, with a
shared `PRICE_LEGEND` + the honest caption; My Squad (`views/squads.py`) adds a caption listing owned players
predicted to fall/rise (a sell/hold timing nudge). Both display-only; the read-only web guardrail holds.

**Deferred:** an absolute "% to the next change" (needs `total_players` + a since-last-change counter, not in
bootstrap); a CLI column; a price-move backtest (Tier-3, post-GW1); an `ask` "who's about to rise?" intent.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-285 | **Price-pressure engine** — `price_pressure`/`price_prediction`/`price_flag` (net ÷ ownership; dormant → GW1); xP untouched (ADR-092). | High | ✅ Done | ~½ session |
| US-286 | **Surface the prediction** — a Price column on the Pool + a My Squad sell/hold nudge; legend + live-GW1 caption. | High | ✅ Done | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `price_pressure` is `net/own` (signed), `None`-safe, and **0** on flat preseason data;
   `price_prediction` returns rise/fall/stable at the thresholds; `price_flag` maps to 🔺/🔻/""; a **decision_xp
   invariance** test shows the lens never changes xP; the Pool shows a Price column (all "—" preseason) + the
   legend/caption; My Squad's nudge lists a falling player on synthetic net-transfer data. Existing **730** stay
   green. No `.save(` (guardrail holds).
2. **Manual smoke** — Players → Pool shows the Price column + the "live from GW1" caption (all stable now); a
   synthetic net-transfer row flags 🔺/🔻; My Squad shows the timing nudge.
3. **Docs updated** — PROJECT_STATUS, Architecture, Roadmap, Backlog, README, Help, ADR-092.

---

### 📝 Session Progress Log

**US-285 — price-pressure engine.** ✅ Done. **ADR-092** written first (the gate).
- New pure `analytics/price.py`: **`price_pressure(player)`** = `net_transfers ÷ selected_by%` (signed;
  `None` when net transfers or ownership is absent; **0** on flat preseason data), **`price_prediction`** →
  `rise`/`fall`/`stable` via module thresholds **`PRICE_RISE_PRESSURE`/`PRICE_FALL_PRESSURE`** (placeholders
  that don't fire on flat data — calibrated at GW1, like `TRENDING_NET`), and **`price_flag`** → **🔺 / 🔻 /
  ""** (a **distinct** forward-looking marker, not the retrospective crowd 💰↑/💸↓). Reuses `net_transfers`;
  exported from `analytics`. A `PRICE_LEGEND` for the UI.
- **Ownership normalisation needs no `total_players`** — the constant total-manager count cancels for direction
  + relative magnitude, so a template + a differential are comparable from fields we already store (no
  ingest/schema change).
- **A lens, never xP** — a `decision_xp` **invariance** test forces strong pressure on every player (5M net-in
  → the lens fires 🔺) and shows xP is **identical**.
- **Verified on real data:** all 573 players read **stable / no flag** preseason (dormant); a synthetic
  10%-owned row with +400k net → 🔺 rise, −350k → 🔻 fall, +10k → stable; empty-safe.
- **Tests (+5):** pressure = net÷own (signed, `None`-safe, 0 flat); prediction thresholds; flag mapping (+
  distinct from 💰/💸); the xP invariance. **735** green, ruff clean.

**US-286 — surface the prediction.** ✅ Done.
- **Players Pool:** a new **"Price"** column (`price_flag` → 🔺 rising / 🔻 falling / — stable) between Own% and
  Form, with the `PRICE_LEGEND` as its tooltip **and** a caption — honest that it's *directional pressure, a
  flag not the exact price/timing; live from GW1*. Distinct from the retrospective crowd 💰↑/💸↓ in Trends.
- **My Squad:** a **transfer-timing nudge** after the who's-flagged line — names owned players predicted to
  **fall** (*sell before the change to keep value*) or **rise** (*hold, or buy now*); preseason (flat net
  transfers) it shows the honest dormant note *"💷 No price moves flagged … live from GW1."*
- **Display-only** — reuses the US-285 engine; no server writes (the read-only guardrail holds); the Pool's
  numeric columns + the other flags are unchanged.
- **Tests (+2):** the Pool has a Price column (only 🔺/🔻/"" markers, all "—" preseason) + the live-GW1 caption;
  My Squad's nudge lists a 🔻 player under forced pressure. **737** green, ruff clean.
- **Manual smoke:** Players → Pool shows the Price column + the live-GW1 caption (all stable now); My Squad
  shows the dormant price note; a forced-pressure player reads 🔺/🔻.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **730 → 737** (+7: 5 price-engine + a Pool column + a
My Squad nudge). Ruff clean; CI-parity green. **New ADR-092** (price-change predictor). No analytics change —
a display/analytics **lens**; a `decision_xp` invariance test pins it.

**Delivered**
- **US-285 — price-pressure engine (ADR-092).** `analytics/price.py`: `price_pressure` (net ÷ ownership%),
  `price_prediction` (rise/fall/stable), `price_flag` (🔺/🔻) — wired dormant (0 preseason → live GW1), never xP.
- **US-286 — surface it.** A **Price** column on the Players Pool + a **transfer-timing nudge** on My Squad,
  with an honest "live from GW1" caption; display-only.

**What went well**
- **The maths cancelled the missing data.** FPL's price threshold scales with ownership, so `net ÷ selected_by%`
  makes players comparable **and** the (unavailable) total-manager count cancels for direction + relative
  magnitude — so a principled signal needed *no* new ingest, no `total_players`, no since-last-change counter.
- **Honest about the limits.** It's framed as *directional pressure — a flag, not the exact price/timing*, with
  a "live from GW1" caption and a distinct 🔺/🔻 (vs the retrospective 💰/💸) — no false precision.
- **The lens invariant held.** The predictor reads the same transfer fields the crowd lens does, and the
  `decision_xp` invariance test (force 5M net-in → 🔺 fires, xP identical) proves it never leaks into the
  recommendations.
- **Dormant-but-visible.** Preseason it reads all "—"/stable, but the Pool column + legend and the My Squad
  dormant note make the feature discoverable now and a switch-flip at GW1 (raise/calibrate the thresholds).

**Watch-outs / follow-ups**
- **Thresholds are uncalibrated placeholders** (`PRICE_RISE/FALL_PRESSURE` = 20k net per 1% owned) — chosen so
  nothing fires on flat data; **calibrate on real net transfers at GW1** (like `TRENDING_NET`/`FORM_WEIGHT`).
- **No absolute "% to the next change"** — that needs `total_players` + a since-last-change counter (neither in
  bootstrap); the v0 gives direction + relative magnitude only. A GW1/Tier-3 refinement.
- **Deferred:** a CLI Price column; an `ask` "who's about to rise?" intent; a price-move backtest post-GW1.

See `Sprint112_Lessons_Learnt.md` for the detailed retro.
