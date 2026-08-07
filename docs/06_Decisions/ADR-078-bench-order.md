# Architectural Decision Record: Bench order — the auto-sub priority

**Decision ID:** ADR-078
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** new decision-support helper. Sits alongside `best_legal_xi` (ADR-040); reuses
the shared `decision_xp` (ADR-041). Display-only recommendation. Triggered by a backlog item ("bench order").
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Backlog: *"Bench order — which bench player subs on first."* When a starter plays 0 minutes, FPL
auto-substitutes a bench player, and the **order** you set decides who comes on. The tool builds/declares a
4-man bench but never surfaces the **sub priority** — so a manager can't see who'd come on first if a
starter blanks.

**Verified in code:** no auto-sub logic exists; `bench_ids` is stored as a list but **ordered by squad
position**, not sub priority; `render_pitch` shows the bench by position. The declared `bench` (4 players) +
the horizon-aware `xp_by_id` are already in `render_my_squad`, so a recommendation is a pure function over
them.

**The FPL rule:** on a 0-minute starter, FPL brings on the **first bench player (in your set order) that
keeps a legal XI**; the **bench GK only ever replaces the starting keeper**. The exact sub depends on which
starter blanks and the resulting formation legality — a runtime detail. So the tool should **recommend a
priority**, not simulate every blank.

#### Decision Drivers
- **Answer "who subs first?"** — a clear, ordered bench.
- **Honest to the rules** — the GK is separate (keeper-only); note "the first that keeps a legal XI".
- **Reuse the xP** — the same horizon-aware `decision_xp` the rest of the tab uses (no drift).
- **Simple** — a recommendation (order by value), not a per-blank auto-sub simulator.

---

### ✅ Decision

**1. A pure `bench_order(bench, scores)` helper (analytics, next to `best_legal_xi`).** Returns
`[(role, player)]`: the **outfield** bench ranked by `scores` (xP) desc → roles `"1st"`, `"2nd"`, `"3rd"`
(your most valuable bench player first), then the **bench GK** → role `"GK"` (it can only replace the
starting keeper). Empty-safe (a Row or a dict); exported from `src.analytics`.

**2. Display it on My Squad (US-242).** Under the pitch, a **"Bench order (auto-subs)"** caption naming the
subs in priority with their xP, plus a one-line explainer: *"FPL brings on the first that keeps a legal XI;
the bench GK only covers your keeper."* Shown when a bench is declared; the xP is the horizon-aware
`xp_by_id` (so the order tracks the *Gameweeks ahead* selector, ADR-077).

**3. A recommendation, not a simulator.** We rank outfield subs by xP (what most managers set, and the most
valuable player to bring on) rather than modelling every possible blank + formation-legality permutation.
The caption states the real rule so the recommendation isn't over-claimed.

---

### 🔀 Alternatives Considered

- **Simulate each starter blanking + apply FPL's legality rule.** Rejected for now — combinatorial and of
  marginal extra value over "order by xP"; the caption already states the legality rule.
- **Let the user *set* the bench order (persist an ordered bench).** Deferred — a reorder UI + an ordered
  `bench_ids` is a bigger change; showing the *recommended* order delivers the insight first.
- **Order by price / ownership.** Rejected — xP (expected points) is the value you'd want on the pitch.
- **Fold the GK into the xP ranking.** Rejected — a bench GK can only replace the keeper, so it's a separate
  slot; ranking it against outfielders by xP would mislead.

---

### 🧭 Consequences

**Positive**
- A manager sees who subs first, ranked by value, with the GK correctly separated.
- Pure + tested; reuses the horizon-aware xP (tracks the *Gameweeks ahead* selector); display-only.
- A clear base to later *set* the order or simulate blanks, if wanted.

**Negative / risks (mitigations)**
- **Not a per-blank simulation** → the caption states FPL applies "the first that keeps a legal XI", so the
  recommendation isn't over-claimed.
- **Preseason xP is carryover** → the order is directional now, sharper in-season (as with every xP view).
- **Only shown with a declared bench** → a squad without one has no bench slots to order (intended).

---

### 📊 Validation

Verified: no prior auto-sub logic; the bench + horizon xP are on hand in My Squad. Acceptance: `bench_order`
ranks the outfield bench by xP (`1st` = highest), places the bench GK last as `GK`, and is empty-safe +
tie-stable; My Squad shows a "Bench order" caption naming the subs (a session squad with a declared bench);
`decision_xp`/the analytics are otherwise unchanged; the existing 629 tests stay green (new tests added).
