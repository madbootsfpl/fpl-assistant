# Architectural Decision Record: The differential archetype — ownership data + a ≤5% constraint

**Decision ID:** ADR-044
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Completes the archetype feature (ADR-043) — the third type, deferred there
pending ownership data. Reuses the ILP min-count pattern; extends the ingest (ADR-001) with one field.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-043 defined the **differential** (a low-owned pick you take *instead of* the template) and deferred
it — `selected_by_percent` wasn't stored. This sprint ingests ownership and ships it.

#### A planning probe pinned the definition (and corrected a naive one)
- **Ownership is easy to ingest** — `selected_by_percent` is in `bootstrap-static` (Raya 30.8%); a
  `selected_by` field mirrors exactly how `chance` was added.
- **The optimal squad is template-heavy** — in the £100m xP-optimal 15, **9 of 15 are >10% owned**
  (João Pedro 54.6%, Raya 30.8%, Gabriel 25.9%…). So forcing low-owned players genuinely tilts it.
- **But a naive threshold is a no-op.** Median ownership is **0.4%**; the optimal squad already holds
  **6 players ≤10%** and even ~5 of them are mid-price (£5.5m+ budget enablers like Truffert 4.7%, Stach
  1.4%). So `≤10%` — even with a price floor — leaves "≥3 differentials" **already satisfied → no
  change** (the exact "I asked for it but nothing happened" trap).
- **≤5% is the sweet spot.** The optimal squad has **only 2** players ≤5% owned → "give me 3
  differentials" actually **bites** (forces a 3rd sub-5% pick in, dropping a template player for a small
  xP cost). A truer "off-template" cutoff, and it matches what a manager means.

#### Decision Drivers
- **Bite, not cosmetics** — the constraint must change the squad at intuitive counts.
- **True differential** — genuinely off-template (≤5%), the objective picks the best such players.
- **Reuse** — the ADR-043 min-count pattern; the `chance`-style ingest; `build_squad`'s existing parse.
- **No new dependency.**

---

### ✅ Decision

**1. Definition.** A **differential** = `selected_by_percent ≤ 5.0` (a tunable module constant,
`DIFFERENTIAL_MAX_OWNERSHIP = 5.0`). **No price/xP floor** — the xP objective already picks the *best*
qualifying (low-owned) players, so a forced differential is a good sub-5% pick, not a scrub. (Owner's
call over ≤10%: the optimal squad has 6 ≤10% but only 2 ≤5%, so ≤5% is the one that bites.)

**2. Ingest.** `Player.selected_by: float | None` from `selected_by_percent`; a `selected_by REAL`
storage column (+ migration) written on save and returned by `get_players`; `refresh` populates it.
A player without data is `None` → **not** a differential.

**3. Constraint.** `select_squad(..., min_differentials=None)` → the ILP constraint
`Σ pick[p] (p.selected_by is not None and p.selected_by ≤ 5.0) ≥ N`; the xP objective is unchanged.
Absent → today's behaviour (byte-identical). Over-asking, or no ownership data, → a non-Optimal status
→ a clear message.

**4. Surface.** CLI `squad --full --differential N`; `build_squad` **already parses** the count
(`_archetype_counts`) — wire it and **remove the "coming soon" note**. Grounded + optional, like every
build. Combinable with `--cheap`/`--premium` (each is an independent min-count constraint).

---

### 🔀 Alternatives Considered

- **≤10% ownership** (the loose FPL heuristic). Rejected — the optimal squad already has 6 (incl. cheap
  enablers), so low counts do nothing and it conflates enablers with punts.
- **≤10% + a £5.5m price floor.** Rejected — still ~5 qualifiers in the optimal squad; a no-op at N≤5.
- **≤5% + an xP floor.** Rejected as unnecessary — the objective already maximises xP, so the forced
  differentials are the best available sub-5% players; a floor adds complexity for no gain.
- **Cap template players instead** ("≤M >10%-owned"). Rejected — the owner asked for a *count of
  differentials*; a min-count of low-owned players is the direct, composable expression.

---

### 🧭 Consequences

**Positive**
- The third archetype ships; the manager can tilt off-template on purpose, still xP-optimal given it.
- One new field + one ILP line; reuses the ADR-043 pattern and `build_squad`'s parse.
- The constraint bites at intuitive counts (≤5% → optimal has 2).

**Negative / risks (mitigations)**
- **Sacrifices xP** as N rises (the user's choice) → the objective still picks the best qualifiers; an
  over-ask → a clear infeasible message.
- **Needs a `refresh`** to populate ownership → `None` ≠ differential; no data + a differential ask →
  the message tells the user to refresh.
- **Threshold is a judgement** → pinned on data (optimal squad: 2 ≤5% vs 9 >10%), documented, tunable.

---

### 📊 Validation

Prototyped on the live API + DB: `selected_by_percent` present; the optimal £100m squad has 9 players
>10% owned and only 2 ≤5% — so a `≤5%` differential constraint bites at low counts while `≤10%` is a
no-op. Acceptance for the sprint: `refresh` populates `selected_by`; `squad --full --differential 3` and
`ask "build me a squad with 3 differentials"` tilt the squad (lower-owned picks in, the "coming soon"
note gone); an over-ask or a pre-ingest DB gives a clear message.
