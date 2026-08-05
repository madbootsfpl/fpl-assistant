# Architectural Decision Record: Crowd & sentiment signals as a lens (Phase 6, Tier 1)

**Decision ID:** ADR-057
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Opens **Phase 6 (Crowd & Sentiment Signals)**. Complements the grounded xP
(ADR-006/041) and the differential archetype (ADR-044) — adds a **display lens**, changes no prediction.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner wants to fold *"what managers are doing"* and expert/pundit signals into the picks, predictions
and analysis. An investigation found that **most of the useful, structured signal is already free in the
FPL `bootstrap-static` payload** — no scraping needed to start: crowd behaviour (`transfers_in/out_event`,
`cost_change_event`/`_start`, `selected_by_percent`) and official form/underlying signals (`form`,
`ict_index` + Influence/Creativity/Threat, `value_form`, `ep_next`). External social (Reddit/X) and pundit
video are a much bigger, flakier, costlier tier.

Two owner decisions frame this: **crowd signals are a complementary lens + flags, not blended into xP**
(the grounded, verified prediction must stay trustworthy — the crowd is often wrong/herding); and **free
FPL signals first** (external/pundit deferred).

#### Verified at planning (live FPL data)
- The Tier-1 fields are present per player. **Live now:** ownership (max **74.9%**; **≥20% = 17 players**,
  **≤5% = 422**), `ict_index` (max 381). **0 in preseason → live at GW1 (2026-08-21):** `transfers_*_event`,
  `cost_change_event`, `form`.
- `cost_change_event` is in **£0.1m units** (any `>0` = a rise). The schema-migration pattern (`_migrate`,
  ADR-027) adds the columns idempotently to a live/seed DB.

#### Decision Drivers
- **Trust** — don't let noisy crowd sentiment degrade the grounded xP.
- **Value now, plumbing for GW1** — ownership/ICT are live; momentum lights up at GW1.
- **Free first** — no scraping/APIs to start; the FPL payload already has it.
- **Generic core** — a pure signal→flags function; the edges render it.

---

### ✅ Decision

**1. Crowd signals are a complementary LENS + flags — never blended into xP.** `decision_xp` and the
grounded answers are unchanged; the crowd is shown **alongside** xP (a test asserts xP doesn't read the
crowd fields). This keeps the prediction grounded and explainable.

**2. Tier-1 fields only (free, structured).** Ingest into the `Player` model + storage:
`transfers_in_event` · `transfers_out_event` · `cost_change_event` · `cost_change_start` · `form` ·
`ict_index` (+ `influence` / `creativity` / `threat`) · `value_form`. (`selected_by` already stored.)
External social + pundit NLP = **Tier 2/3, deferred** (later, optional, degrade like ClubElo).

**3. The flag set + thresholds** — a pure **`crowd_flags(player)`** helper returns display flags, empty-safe
(0 / None → no flag, no crash). Thresholds live as **tunable constants** in one place, calibrated on real
data (ownership now; momentum/form at GW1):

| Flag | Rule | Threshold (initial) |
|------|------|---------------------|
| 🟦 **template** | high ownership | `selected_by ≥ 20%` (≈ top 17; tunable) |
| 🟨 **differential** | low ownership | `0 < selected_by ≤ 5%` (reuse ADR-044) |
| 🔥 **trending in** / ❄️ **out** | net `transfers_in_event − out` | `≥ TRENDING_NET` (calibrate at GW1) |
| 💰 **price ↑ / ↓** | `cost_change_event` sign | any `> 0` / `< 0` (no threshold) |
| 📈 **in form** | recent form | `form ≥ FORM_MIN` (≈ 6.0; calibrate at GW1) |

`ict_index`, `form` and net transfers are also shown as **numeric columns** (not just flags). ICT is an
official underlying composite (shown, not a binary flag).

**4. Surfaces.** The **Players** tab first, via the shared `render_player_table` (so the squad tabs inherit
the flags). Captain / Transfer / an `ask` **"trends"** intent can follow (this sprint or the next).

**5. `crowd_flags` is a pure analytics function** (generic core); the Streamlit/CLI edges render it — the
core imports no edge.

---

### 🔀 Alternatives Considered

- **Blend sentiment into xP** (a weighted adjustment). Rejected (owner): it compromises the grounded,
  verifiable prediction — harder to trust/explain, and the crowd herds.
- **Start with external social (Reddit/X)/pundit NLP.** Rejected for now: bigger, flakier, costlier; the
  free FPL signals deliver most of the value first. Kept as Tier 2/3.
- **A momentum-blended transfer/captain nudge.** Deferred — a *labelled* tie-breaker could come later, but
  Tier 1 is display-only first (simplest, safest).
- **Absolute-count "trending" threshold set now.** Can't calibrate preseason (all 0) — so a tunable
  constant, fixed on the first live gameweek.

---

### 🧭 Consequences

**Positive**
- A rich "what's the crowd doing" lens from **free** data; ownership/ICT value **now**, momentum at GW1.
- The grounded xP stays exactly as trustworthy — the crowd informs, never overrides.
- One pure `crowd_flags` helper, reused across surfaces; the core stays generic.

**Negative / risks (mitigations)**
- **Preseason zeros** → ship the ownership/ICT lens now; the momentum plumbing is tested with 0 + a GW1
  follow-up to confirm it lights up.
- **Sentiment creeping into xP** → display-only; a test asserts `decision_xp` is unchanged.
- **Arbitrary thresholds** → few, tunable constants, calibrated on real data; ownership set now, the rest
  at GW1.
- **Scope creep to scraping** → Tier 2/3 explicitly deferred here + in the Roadmap.

---

### 📊 Validation

Probed on the live API: ownership + ICT are live (thresholds set from the real distribution); momentum/price/
form are 0 preseason (live at GW1); `cost_change_event` is £0.1m units. Acceptance for the sprint: the
Tier-1 fields ingest + round-trip; `crowd_flags` returns the right flags at its thresholds and is empty-safe;
the Players tab shows the lens; a test asserts `decision_xp` is **unchanged** by the crowd fields; the
existing 487 tests stay green.
