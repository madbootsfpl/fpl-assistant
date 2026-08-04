# Architectural Decision Record: Sane low-evidence xP + transfer dedup (trust the numbers)

**Decision ID:** ADR-040
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Extends ADR-028 (the ≥900-min xP baseline) to the *fallback* path; fixes a
bug in ADR-030 (`suggest_transfers`). Complements ADR-038 (xMins).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner challenged three data outputs on squad **RoboTS** (Sprint 038 notes). A planning probe traced
each to a root cause:

1. **Implausible xP.** `transfer --no-xmins` offered **Benitez (£4.5 GK) at 35.0 xP**. Cause: a
   **single game** (90 mins, 7 pts → `points_per_game` 7.0). The ≥900-min gate (ADR-028) protects the
   *baseline* rate, but when no season qualifies the code falls back to **raw `ppg` with no sample
   gate** — so one cameo projects like a 7-pts/GW superstar. *(xMins already masks this in the default
   view — Benitez's weight is 0.026 → weighted xP 0.9 — but masking a bad number with a second model is
   fragile; the raw rate must be honest, and `--no-xmins` is a legitimate view.)*
2. **Duplicate incoming.** `suggest_transfers` chose `best = max(candidates by xp)` **independently per
   out-player**, so two GKs (Kelleher, Raya) both resolved to Benitez — the same buy listed twice.
3. **"start/bench ≠ my lineup."** Not a bug: default `analyse` and start/bench give the **same** XI
   (both xMins-weighted `select_squad`; confirmed). The owner compared `analyse --no-xmins` (raw) with
   start/bench (xMins) — a flag mismatch. A **transparency** gap.

#### Decision Drivers
- **Honest raw numbers** — no cameo should project like a star, independent of xMins.
- **Regress the unknown, don't invent it** — low evidence → a conservative estimate, not a wild one.
- **Don't disturb trusted players** — anyone with a real ≥900-min baseline is untouched.
- **Fix the actual bug** (duplicate incoming) and **make consistency legible** (raw vs xMins).
- **Lightweight & transparent** — no ML, no new dependency; a documented, tunable rule.

---

### ✅ Decision

**1. Low-evidence xP damping (the core).** When a player has **no qualifying baseline** (no season
≥900 min in the look-back) but *does* have some history, replace the raw-`ppg` fallback with an
**evidence-shrunk rate**:

```
fallback_rate = career_pp90 × c + PRIOR × (1 − c)
    career_pp90 = Σ points / Σ minutes × 90       (rate estimate — all history_past seasons)
    c           = min(1, best_season_minutes / 900)   (confidence — the biggest single season)
    PRIOR       = 2.0  pp90                         (replacement level)
```

**Confidence comes from the biggest single season, not the career sum** — scattered cameos must not
*compound* to false confidence. (Smoke found **Enes Ünal**: 317 + 330 + 214 min at ~10 pp90; a
career-sum `c` trusted the flukey rate → 46.9 xP. Best-season `c` = 330/900 shrinks it to a sane ~5.
The recurring "probe broadly" lesson — the gate's Benitez case was a single season, so it hid this.)

- **`PRIOR = 2.0`** is pinned on real data: the pp90 of 900-minute regulars runs p10 = 2.88, median =
  3.92, so 2.0 sits deliberately *below* the 10th percentile — players who never reached 900 minutes
  are weaker than those regulars. Global (not per-position) for v0; documented and tunable.
- **Behaviour:** Benitez (90 career min → c ≈ 0.1) collapses 7.0 → **2.5** (xP ~12.5, not 35); a player
  with lots of career minutes but no single 900-min season keeps ~their career pp90 (c → 1); a genuine
  **≥900-min player is untouched** (they have a baseline). No history at all → `fallback_rate` is None,
  so the caller still uses `ppg` (unchanged — rare; usually ~0 for new players).
- **Wiring:** the caller precomputes `fallback_by_code`; `player_xp` uses it **only when the baseline is
  None**. Absent (existing callers/tests) → today's `ppg` behaviour, byte-identical.

**2. Transfer dedup.** `suggest_transfers` builds the shortlist so an **incoming player appears at most
once** — greedily: sort candidate moves by gain and skip a move whose incoming player was already taken
(each out-player still gets its best *still-available* target). No repeated buys.

**3. Consistency, made legible.** No behaviour change — default `analyse` and start/bench already agree
(both xMins-weighted `select_squad`). Locked by a test (`analyse` XI ≡ start/bench XI) and a one-line
note that `--no-xmins` is the raw *"assumes 90"* view; the default is minutes-weighted.

---

### 🔀 Alternatives Considered

- **A hard min-minutes gate on the fallback** (cliff: <N min → rate 0 or a fixed value). Rejected — a
  cliff is jumpy and zeroes genuinely fringe-but-useful players; shrinkage degrades smoothly.
- **A positional plausibility cap** (GK ≤ x, FWD ≤ y). Rejected as the primary fix — crude, still
  leaves a 1-gamer at the cap; a cap doesn't regress toward what we'd actually expect. (Could layer on
  later.)
- **Per-position priors.** Deferred — the global prior tames the bug cleanly on real data; positional
  priors are a later refinement (and a GW1-era tuning task, alongside the ≥900 baseline itself).
- **Rely on xMins to hide it.** Rejected — it works in the default view but not `--no-xmins`, and a
  wrong raw number is a latent trap. Fix the number.
- **Also re-tune the ≥900 baseline** (optimistic partial seasons like Okafor 6.32/1553-min). Out of
  scope — those clear the gate on real minutes; whether 900 is enough is a separate GW1 tuning question.

---

### 🧭 Consequences

**Positive**
- The raw xP is plausible everywhere (captain/transfer/squad/analyse and `--no-xmins`); no cameo tops a
  ranking. Trust in the numbers is restored without leaning on xMins to hide them.
- A real bug (duplicate incoming) is gone; the consistency question has a test + a note.
- Reuses stored data; no ML, no new dependency; the rule is transparent and tunable.

**Negative / risks (mitigations)**
- **Low-ppg fringe players get bumped toward the prior** (e.g. 0.9 → ~2.5). Honest ("assume replacement"
  under low evidence) and xMins further dampens them; acceptable.
- **The prior/threshold are choices** → pinned on real data, documented in this ADR, easy to tune.
- **No-history players still use `ppg`** → a residual edge (usually ~0); noted, deferred.

---

### 📊 Validation

Prototyped on the live DB before code: with `PRIOR = 2.0`, Benitez 7.0 → 2.5 (xP 35 → ~12.5);
Okafor/Wilson/Haaland untouched (they have baselines); 124 players use the new fallback, the trusted 352
are unchanged. Acceptance for the sprint: `transfer --squad RoboTS --no-xmins` shows a sane Benitez xP
and **no repeated incoming**, and default `analyse` ≡ start/bench XI.
