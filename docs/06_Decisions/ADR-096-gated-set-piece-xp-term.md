# Architectural Decision Record: A gated set-piece xP term (tier-restricted, wired-dormant)

**Decision ID:** ADR-096
**Date:** 2026-08-27
**Status:** Accepted
**Superseded By / Replaces:** extends the **one xP metric** (`decision_xp`/`player_xp`, ADR-041) and the
**wired-dormant rate-term** pattern (form blend, ADR-060). A **modelling** change to the xP *rate* — a different
category from the **lens** rule (ADR-057, "signals never touch `decision_xp`"), which still holds for
crowd/price/media. Builds on the ingested set-piece data (ADR-081).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Penalty (and, less so, corner / free-kick) takers have a **real scoring edge** — a penalty is a high-xG shot a
specific player is nominated to take. The owner asked to reflect this in the recommendations, i.e. in
`decision_xp` (not just the existing display flags). The set-piece takers are **known now** (`penalties_order` /
`corners_order` / `freekicks_order` are ingested, ADR-081; `set_piece_flags` shows #1 takers as a lens).

**Verified from the code — where a term slots + the key risk:**
- `decision_xp → player_xp` builds a per-90 **rate** (a trusted ≥900-min **baseline** → a shrunk **fallback** →
  current `ppg`), blends **form** into that rate (ADR-060), then xP = `weight · rate · Σ fixture-multipliers`. A
  set-piece term is naturally a **rate adjustment**, like the form blend.
- **⚠️ Double-counting.** The baseline rate is the player's **historical pp90**, which **already includes their
  past penalty/set-piece points**. A blanket set-piece boost therefore **double-counts** for an established
  taker (their pens are already priced in). The boost is genuinely *new information* only where the history does
  **not** capture the current duty — a **new signing**, a **role change**, a young player — i.e. the
  **fallback / current** rate tiers, **not** the trusted `hist` tier.
- **Calibration is hard preseason** — there are no in-season returns yet to fit a magnitude to, and the effect
  partly overlaps the baseline. Guessing a live weight risks making recommendations *worse*.

#### Decision Drivers
- **Reflect a real edge** in xP (a modelling improvement, not just a flag).
- **Never double-count** — don't add a duty the baseline already prices.
- **No change until it's justified** — ship it **off by default**; the public numbers must be unchanged today
  (an invariance test), calibrated at GW1 on real data.
- **Keep one xP metric** (ADR-041) — the term lives in the *one* recipe, applied once.
- **Auditable** — a change to xP must be **explainable + grounded** (ADR-037/089), not a black box.
- **A modelling change, categorised honestly** — distinct from the lens rule (ADR-057).

---

### ✅ Decision

**Add a conservative, tier-restricted set-piece rate bonus to `player_xp`, gated by `SET_PIECE_WEIGHT` (default
0 — wired-dormant), applied only to the rate tiers where it doesn't double-count. Ship the mechanism + tests +
explanation now; calibrate the weight at GW1.**

**1. The term — a tier-restricted rate bonus.** A pure `set_piece_bonus(player) -> float` maps set-piece duties
to a per-90 rate bonus: **penalties (#1) carry the most** (a penalty ≈ a high-xG shot), **corners / free-kicks
(#1) less** (an indirect goal/assist chance). In `player_xp`, after the form blend:
```
if SET_PIECE_WEIGHT and rate is not None and rate_source != "hist":
    rate += SET_PIECE_WEIGHT * set_piece_bonus(player)
```
The **`rate_source != "hist"` guard is the crux** — the trusted multi-season baseline already prices an
established taker's pens, so the bonus applies **only** to the **fallback / current** tiers (the players whose
history doesn't capture their current role). This structurally prevents double-counting.

**2. Wired-dormant, off by default.** `config.SET_PIECE_WEIGHT = 0.0` — exactly the `FORM_WEIGHT` pattern
(ADR-060). At 0, `rate` is unchanged, so **every xP is byte-identical to today** (an invariance test pins the
ADR-041 invariant). The mechanism + tests + explanation ship now; the owner flips the weight to see it live and
**calibrates at GW1** against real returns.

**3. Auditable when active.** A set-piece xP contribution is **explainable + grounded** (ADR-037/089): when the
weight is on, `explain_captain` / `explain_transfer` gain a "⚽ on penalties — a set-piece xP edge (+X)" reason
and the number joins the **facts**, so a narrated figure still **verifies ✓**. Dormant → no reason is added
(byte-unchanged). *(The set-piece **flags** already exist as a display lens, ADR-081; this adds the **xP** link.)*

**4. A modelling change, not a lens.** This legitimately alters `decision_xp` (like form/xMins), so it is **not**
governed by the lens invariant (ADR-057, which keeps crowd/price/media out of xP). Those lens invariance tests
still hold unchanged. Recorded here so the distinction is explicit.

**5. GW1 calibration + honest limits.** At GW1: set `SET_PIECE_WEIGHT` and **backtest** — do boosted picks beat
the unboosted for role-changers? Limits recorded: it's a **coarse proxy** (no per-team penalty rate — we don't
know how many pens a team wins); **duty can change** mid-season; and it must **never re-double-count** (hence the
tier guard).

---

### 🔀 Alternatives Considered

- **A blanket boost for every #1 taker.** Rejected — **double-counts** the baseline for established takers
  (their pens are already in the rate); it would inflate exactly the premiums that need it least.
- **A display lens only (the status quo, ADR-081).** Kept as the complement, but it doesn't move the
  recommendation, which was the ask.
- **Fold set-pieces into a crowd/price-style lens.** Rejected — this is an **xP** signal (it changes the
  decision), not a display lens; conflating them would blur ADR-057.
- **Model per-team penalty rates + conversion.** The "right" long answer, but it needs data we don't have (team
  pens won) and real returns to fit — deferred to a post-GW1 modelling effort.
- **Active-now with a guessed weight.** Rejected — no in-season data to calibrate; an over-boost could worsen
  picks. Wired-dormant + the tier guard is the safe ship; flip + calibrate at GW1.
- **Boost by absolute duty regardless of tier, but shrink it.** Rejected in favour of the clean tier guard — a
  shrink still double-counts a bit and is harder to reason about than "only where history doesn't capture it".

---

### 🧭 Consequences

**Positive**
- A **principled** way to reward set-piece duty in xP that **cannot double-count** (the tier guard), shipped
  **without changing today's numbers** (dormant + an invariance test) — zero risk now.
- The change is **auditable** — when on, the contribution is explained and the number is grounded (verifies ✓).
- Stays within **one xP metric** (ADR-041) and the wired-dormant precedent (ADR-060); the lens invariant
  (ADR-057) is untouched and still tested.

**Negative / risks (mitigations)**
- **A coarse proxy** (no per-team pen rate). *Mitigation:* conservative, gated, calibrated at GW1; documented.
- **The tier guard is a heuristic** for "history doesn't capture the duty" — a role-changer with a long history
  still lands on `hist` and gets no boost. *Mitigation:* accepted; a duty-change detector is deferred (the guard
  errs toward *not* double-counting, the safer failure).
- **Duty changes mid-season.** *Mitigation:* the order fields refresh; the term reads them live.
- **Another knob to calibrate.** *Mitigation:* default 0 (a no-op) until GW1; the backtest sets it.

---

### 🧾 Status & follow-ups

- **Accepted.** Implemented this sprint (US-313 the term + invariance; US-314 the grounded explanation), shipped
  **dormant** (`SET_PIECE_WEIGHT = 0`).
- **GW1 (2026-08-21+):** set the weight + **backtest** on real returns; revisit the tier guard against observed
  role-changers.
- **Deferred:** per-team penalty-rate/conversion modelling; a mid-season duty-change detector; auto-detecting
  "newly the taker" beyond the rate tier.
