# Architectural Decision Record: Bench-aware squad optimisation (weekly XI vs Bench Boost)

**Decision ID:** ADR-045
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Extends the squad optimiser (ADR-008/012) with a starting-XI-aware
objective; complements the XI/bench breakout (Sprint 044) and the archetype constraints (ADR-043/044).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`squad --full` maximises the **15-total** xP. But on a normal week only the best **XI** scores, so the
max-15 build over-invests in a bench that won't play — the XI is weaker than it could be. The owner
wants a **weekly/rotation** mode (maximise the XI, cheap-but-playing bench) and a **Bench Boost** mode
(the max-15, since all 15 score under that chip).

#### A planning probe pinned the model, the weight, and the composition
A prototype ILP — a `start[i]` binary per player, an XI formation, objective `Σ xp·start + W·xp·(pick −
start)` — on the £100m pool:
- `W = 1.0` (max-15 / Bench Boost): best XI **233.6**, bench 72.2 (£27.5m bench);
- `W = 0.0` (pure XI): XI **243.1**, bench 0.6 (a dead £17m bench);
- **`W = 0.1`:** XI **241.2** (only −1.9), bench **39.7** (£18.5m — a *playing* bench). **+7.6 XI xP**
  over today's best XI, *with* rotation cover.
- **Composes with archetypes** — `--weekly --premium 1 --differential 2` stays Optimal; over-asks go
  Infeasible; solve time ~0.07s (the doubled binaries are cheap).

#### Decision Drivers
- **Maximise the right thing** — the XI you actually field, not the 15-total.
- **Rotation cover** — a small bench weight buys a *playing* bench, not dead fodder.
- **No regression** — keep the transfer-consistent default; make bench-aware opt-in.
- **Reuse & compose** — one `bench_weight`; works with the archetypes; designates the XI natively.

---

### ✅ Decision

**1. The model.** `select_squad(..., bench_weight=W)`. When `W is not None` (a full-15 build), add a
`start[i]` binary per player and:
- `start[i] ≤ pick[i]`; `Σ start = 11`; the XI within `XI_FLEX` ranges (1 GK, DEF 3–5, MID 2–5, FWD 1–3);
- objective **`Σ xp·start[i] + W·xp·(pick[i] − start[i])`** (the 15 still meet the full shape / budget /
  club cap / archetypes).
- Non-starters are flagged `bench = True` — the build **designates its XI**.
- **`bench_weight = None` → today's model** (no `start` vars, maximise the picked total), byte-identical.

**2. Modes** (CLI). **`--weekly`** → `W = 0.1` (pinned: a strong XI + a playing bench for rotation);
**`--bench-boost`** → `W = 1.0` (the max-15). The **default `squad --full` is unchanged** (max-15,
`bench_weight = None`) — Bench-Boost-optimal *and* transfer-consistent (no "free transfers", ADR-041) —
the owner's call, so bench-aware is opt-in. Both flags **imply `--full`** and use the **xP** scores
(the weekly metric). *(An optional `--bench-weight X` power knob may be added; confirm at build.)*

**3. Save / display.** A bench-aware build designates the bench, so the XI/bench breakout (Sprint 044)
is **exact** (not post-hoc) and `--weekly --save` records the recommended bench. The default max-15
build keeps Sprint-44's post-hoc auto-XI display and an empty saved bench.

**4. `ask`.** `build_squad` parses **"bench boost"** → boost (`W = 1.0`) and **"rotation"/"weekly"** →
weekly (`W = 0.1`); otherwise the default. Combinable with the archetypes; grounded + optional.

---

### 🔀 Alternatives Considered

- **Make weekly the default.** Rejected by the owner — it changes today's output *and* the cheap bench
  would let `transfer` suggest bench "upgrades" (the "free transfers" wrinkle from ADR-041 returns).
  Keep max-15 default; `--weekly` opt-in.
- **`W = 0` (pure XI).** Rejected as the weekly default — a dead £4 bench has no rotation value; `W = 0.1`
  buys a playing bench for ~2 XI xP.
- **Post-hoc best XI only (Sprint 044).** Kept for the default build, but bench-aware *designs* the XI —
  a better XI, and an exact split.
- **Make `transfer` XI-aware now.** Deferred — a separate change; keeping the default max-15 preserves
  consistency without it.

---

### 🧭 Consequences

**Positive**
- `--weekly` builds the team you'd field: a materially stronger XI (+7.6 xP) with rotation cover.
- `--bench-boost` is the honest chip build (max-15), now nameable.
- One `bench_weight`; composes with the archetypes; the XI is designed, not guessed; fast (~0.07s).

**Negative / risks (mitigations)**
- **A bigger ILP** (2× binaries) → guarded behind `bench_weight`; byte-identical when None; measured fast.
- **`--weekly` bench invites transfer "upgrades"** → default unchanged keeps the consistency; `--weekly`
  is opt-in; transfer flags bench swaps `(b)`.
- **Weight is a choice** → pinned on data (`0.1` = the XI/rotation knee), documented, tunable.

---

### 📊 Validation

Prototyped on the live pool: `W = 0.1` → XI 241.2 / bench 39.7 (a playing £18.5m bench), +7.6 XI xP over
the max-15's best XI; `--weekly --premium 1 --differential 2` stays Optimal (~0.07s); over-asks go
Infeasible. Acceptance for the sprint: `squad --full --weekly` shows a stronger XI + a playing bench;
`--bench-boost` = max-15; the default `squad --full` and `transfer` are unchanged; `--weekly --save`
records the bench; `ask "… for a bench boost / for rotation"` selects the mode.
