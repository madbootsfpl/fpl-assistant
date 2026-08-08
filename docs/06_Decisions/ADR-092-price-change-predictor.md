# Architectural Decision Record: A Price Change Predictor (a directional lens, dormant → GW1)

**Decision ID:** ADR-092
**Date:** 2026-08-13
**Status:** Accepted
**Superseded By / Replaces:** extends the **crowd/sentiment lens** (ADR-057) and follows the **wired-dormant →
GW1** pattern (ADR-060). A display/analytics **lens** — it never feeds `decision_xp`.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner's 5-request intake included a **Price Change Predictor** — *"an indicator flagging players about to
rise/fall in value, to time transfers."* FPL prices move when a player's **net transfers** (managers buying −
selling) cross a hidden threshold that scales with the player's **ownership**; the exact algorithm, the
per-player threshold, and the "net transfers since the last change" counter are **not published** and **not in
`bootstrap-static`**.

**What we have:** `transfers_in_event` / `transfers_out_event` (this gameweek's counts) and `selected_by` (%
owned) — both already ingested (ADR-057). **Verified:** net transfers are **0** for all players preseason, and
`selected_by` is populated. So any signal reads **flat now and lights up at GW1** — the dormant-then-live shape
of the Data-Hardening prep (ADR-060).

**What already exists (and must not be re-skinned):** `crowd_flags` shows **🔥 in / ❄️ out** (a *flat*
net-transfer threshold, `TRENDING_NET`) and **💰↑ / 💸↓** (`cost_change_event` — the change that **already
happened**). The gap is a **forward-looking** signal that a player is *about to* move.

#### Decision Drivers
- **Directional, honest** — a *flag, not the truth*: we can't compute the exact price or timing, so don't imply
  we can.
- **Comparable across players** — a big-ownership player needs far more net transfers to move than a
  differential; the signal must account for that.
- **No new ingest** — work from fields already stored; no dependency on unpublished data.
- **A lens, never xP** — like all crowd signals, it must not change `decision_xp` (an invariance test pins it).
- **Dormant → GW1** — reads "stable"/"—" on flat preseason data; calibrated on real net transfers at GW1.

---

### ✅ Decision

**A pure `analytics/price.py` computes an ownership-normalised transfer *pressure* and a directional
prediction:**

```python
price_pressure(player)   = net_transfers(player) / selected_by%    # net per 1% ownership; None-safe; 0 preseason
price_prediction(player) = "rise" | "fall" | "stable"              # config thresholds (GW1-calibrated)
price_flag(player)       = "🔺" | "🔻" | ""                         # display, distinct from the retrospective 💰/💸
```

**Why divide by ownership.** FPL's move threshold is ~proportional to a player's owner count
(`selected_by% × total_players`). Normalising `net ÷ selected_by%` therefore measures *pressure per unit of the
threshold*, so a differential and a template are **comparable** — and the (constant) `total_players` **cancels
out** for direction + relative magnitude, so we need neither `total_players` nor a since-last-change counter
(neither is in bootstrap). An absolute *"% to the next change"* would need those and is a **GW1 refinement**,
not part of v0.

Thresholds live in `config` (`PRICE_RISE_PRESSURE` / `PRICE_FALL_PRESSURE`), set so **nothing fires on flat
data**; they're calibrated on real net transfers at GW1 (like `TRENDING_NET` / `FORM_WEIGHT`). The signal is
surfaced as a **Price** column on the Players pool and a **transfer-timing nudge** on My Squad (US-286),
display-only. `decision_xp` is untouched — an invariance test proves it.

---

### 🔀 Alternatives Considered

- **A flat net-transfer threshold** (like 🔥/❄️). Rejected as the signal — it ignores ownership, so it flags
  every high-ownership player and misses pressured differentials; and it duplicates the crowd flag.
- **Ingest `total_players` for an absolute "% to change".** Deferred — it needs a schema addition **and** a
  since-last-change counter we don't have; the ownership-normalised *pressure* gives the direction + relative
  magnitude without it.
- **Fold price movement into xP.** Rejected — price is a *budget/timing* concern, not expected points; the
  crowd-lens invariant (ADR-057) holds.
- **Reuse the retrospective 💰/💸.** Rejected — those report a change that already happened; the predictor is
  forward-looking (a distinct 🔺/🔻 marker), and the two are complementary.

---

### 🧭 Consequences

**Positive**
- A grounded, ownership-fair "about to rise/fall" signal to time transfers, from fields we already store.
- No ingest/schema change; dormant preseason, a switch-flip at GW1 (raise/calibrate the thresholds).
- A lens only — `decision_xp` and the recommendations are unchanged.

**Negative / risks (mitigations)**
- **Not the exact price or timing** → framed as *directional pressure — a flag, not the truth*, with a "live
  from GW1" caption; no false precision.
- **Uncalibrated thresholds** → placeholders chosen so nothing fires on flat data; calibrated on real net
  transfers at GW1, with the number tunable in `config`.
- **Confusion with the retrospective 💰/💸** → a distinct 🔺/🔻 marker + a legend that names the difference.

---

### 📊 Validation

Verified preseason net transfers are 0 (signal reads "stable") and `selected_by` is populated. Acceptance:
`price_pressure` = net÷ownership (signed, `None`-safe, 0 on flat data); `price_prediction` returns
rise/fall/stable at the thresholds; `price_flag` → 🔺/🔻/""; a `decision_xp` **invariance** test shows the lens
never changes xP; the Pool shows a Price column (all "—" preseason) + the honest caption; existing **730** tests
stay green (new price tests added); ruff clean.
