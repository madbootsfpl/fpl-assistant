# Architectural Decision Record: A cold-start xP floor from FPL's `ep_next`

**Decision ID:** ADR-104
**Date:** 2026-08-12
**Status:** Accepted
**Superseded By / Replaces:** **extends** the rate-tier ladder (ADR-028 baseline · ADR-040 low-evidence fallback):
adds a **cold-start floor** below the *current-ppg* tier so a player with **no FPL history** isn't projected at **0**.
Changes `decision_xp` / `player_xp` output for that cohort — the first deliberate change to the one-xP metric
(ADR-041) beyond the dormant weights. No new data source or dependency (`ep_next` is already on every player row).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester feedback (2026-08-12): new/promoted players score **0 / near-0** and it reads as *broken* — undermining
trust in every other number. Investigation on the **real data** pinned the cause and reframed it honestly:

- **The scoring rate ladder** (ADR-028/040): a **≥900-min historical baseline** → a **shrunk fallback** (some
  history) → the current season's **`points_per_game`**. A player with **no FPL history** falls to the last tier,
  and **preseason `points_per_game` is 0** → rate 0 → **xP 0**.
- **Measured:** **69 available players show xP = 0 at GW1** — all no-history (`rate_source="current"`, minutes-weight
  **1.0**, so the 0 is purely the rate). **Every one has a non-zero FPL `ep_next`** (1.0–2.5, median 1.5) — FPL's own
  *expected points next GW* — which **we carry in the data but don't use**.
- **The reframe — this is *not* "we're too low vs FFH".** The flagged players *with* history aren't a bug:
  **O'Shea** (3 seasons, 8,113 mins) gets a real baseline ≈ **1.6**, while **FPL's own `ep_next` for him is 1.0** —
  so **we're *higher* than FPL**, and **FFH's 4.7 is the bullish outlier.** Matching FFH would be *wrong*; our model
  agreeing with FPL's over a paid model is reassuring. **The genuine defect is narrow:** the 69 no-history players at 0.

**We deliberately do not chase FFH parity.** FFH has paid Opta + projected-lineup + prior-season data we don't buy
(ADR-016); the honest fix is to stop projecting a plausible starter at **0**, using a number we already hold.

#### Decision Drivers
- **Credibility** — a promoted-team starter at **0** makes a tester distrust the whole tool; fix it before GW1.
- **Honest, not invented** — floor with **FPL's own `ep_next`**, not a made-up number.
- **Targeted** — only the no-history cohort; leave every player with a real baseline/fallback **unchanged**.
- **No new data/deps** — `ep_next` is already on the player row (`ADR-041` one-xP stays *one* number).
- **Transparent** — a distinct `rate_source` so the pick can be grounded honestly ("FPL's estimate, no history yet").

---

### ✅ Decision

**Floor the cold-start (no-history) tier with FPL's `ep_next`:** when a player's rate would fall to the current
`points_per_game` tier (no baseline, no fallback), use **`rate = max(points_per_game, ep_next)`** instead of a bare
`points_per_game`. Preseason (`ppg` 0) → the rate becomes `ep_next`; once the player actually scores, their real
`ppg` takes over. Established players (baseline/fallback tiers) are **untouched**.

**1. Where it applies — the last tier only.** In `player_xp`'s rate selection, the floor sits in the `else`
(current-ppg) branch. The **baseline** (≥900-min) and **fallback** (shrunk career) tiers are unchanged — no
double-counting, no touching O'Shea/Haaland. A player with a real rate keeps it.

**2. The mapping.** `ep_next` is a **per-GW** points estimate; our pipeline multiplies a per-fixture **rate** by the
fixture multiplier and sums over the horizon. Use **`rate = ep_next`** (the natural mapping at neutral difficulty,
`_multiplier ≈ 1`); our fixture multiplier then refines it per GW, and the horizon extrapolates FPL's forward view
— an acceptable *floor*, not a precise multi-week model.

**3. Minutes weight.** `ep_next` **already prices expected minutes**, so the `ep_next`-floored rate is **not**
re-scaled by our `minutes_weight` (avoid double-discounting) — the cold-start cohort is minutes-weight 1.0 today, so
this is a guard, not a behaviour change, but it's specified so a future minutes model can't silently re-zero the floor.

**4. Availability unchanged.** The floor only rescues **available** players (`status == 'a'`, ADR-006). A flagged
no-history player still → 0 (correct — they're not expected to feature).

**5. Transparency.** The floored rate carries **`rate_source = "ep_next"`** (a new label), so Ask/CLI/web grounding
(ADR-037) can say the honest thing: *this is FPL's own estimate — the player has no history yet.*

**6. What this is *not*.** Not a blend of `ep_next` into *every* player's rate (that would double-count established
players and drift the metric). Not a positional replacement-level floor (less honest, inflates fringe players). Not
an attempt to match FFH. Not a new data source.

---

### 🔀 Alternatives Considered

- **Status quo (0 for no-history players).** Rejected — the credibility problem; a plausible starter at 0 is the
  single most trust-eroding thing a tester sees.
- **A positional replacement-level floor** (a min pp90 by position). Rejected — it *invents* a number, and it can't
  tell a nailed £5.5m new signing from a £4.0m fringe player, so it inflates the fringe. `ep_next` is FPL's per-player
  view and separates them for free.
- **Blend `ep_next` into every player's rate.** Rejected — double-counts players who already have a trusted
  historical baseline, and drifts the whole metric off its documented basis for no gain on the players who matter.
- **Chase FFH's numbers.** Rejected — paid data we don't have (ADR-016); and FPL's own `ep_next` shows FFH is often
  the outlier, not us. Parity isn't the goal; *not projecting a starter at 0* is.
- **Use `ep_this` instead of `ep_next`.** Considered — `ep_next` is the forward-looking one (the next GW), which is
  what a squad decision needs; `ep_this` is the current GW. Prefer `ep_next`.

---

### 🧭 Consequences

**Positive**
- **69 no-history players go from 0 → a sane, FPL-grounded xP** (≈ their `ep_next`) — the credibility fix, before GW1.
- **Honest + minimal** — FPL's own number, only the cold-start tier, no new data/deps; grounding stays truthful via
  the `ep_next` `rate_source`.
- **Established xP is unchanged** — baseline/fallback players (the vast majority) are byte-identical.

**Negative / risks (mitigations)**
- **It changes the one-xP metric for the cohort** — intentional. *Mitigation:* scoped to the no-history tier;
  documented here; the affected picks are labelled `ep_next`.
- **`ep_next` is FPL's estimate, not ours** — a floor, not a precise model; it can be optimistic. *Mitigation:* it's
  a *floor* (max with real `ppg`), transparently sourced; real performance overrides it once the player plays.
- **Extrapolating a one-GW estimate across the horizon** is rough. *Mitigation:* it's a floor for otherwise-0
  players; the fixture multiplier still applies; established players (real multi-week rates) are unaffected.
- **Breaks the xP-invariance tests** for cold-start players (they were 0, now `ep_next`-based). *Mitigation:* update
  those assertions — this is the deliberate, gated metric change; the dormant-weight invariance (form/set-piece/
  DefCon → byte-identical) still holds for everyone else.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (next story): the `max(ppg, ep_next)` floor in `player_xp`'s current-ppg tier +
  `rate_source="ep_next"`; verify on real data (the 69 rise to sane values; established players unchanged); update
  the xP-invariance tests for the cold-start cohort; a test that a no-history available player with `ep_next>0` gets
  a non-zero xP and a flagged one still gets 0. Docs: PROJECT_STATUS, Architecture, memory.
- **Not this ADR:** matching FFH; a positional floor; projected-lineup/minutes data (ADR-016 deferred); the broader
  GW1 calibration of the dormant weights (ADR-101 — a separate, data-gated thread from GW4–6).
