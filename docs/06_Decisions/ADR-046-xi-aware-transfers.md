# Architectural Decision Record: XI-aware transfers — rank by the fielded-XI improvement

**Decision ID:** ADR-046
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Changes the ranking metric of `suggest_transfers` (ADR-030); pairs with
bench-aware builds (ADR-045); reuses the best-XI idea (ADR-041 `best_legal_xi`) via a fast helper.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`transfer` ranks single swaps by **raw player xP gain** (`in.xp − out.xp`). So it "upgrades" a cheap
bench with a big paper gain that doesn't change the team you field — misleading, and it clashes with the
bench-aware `--weekly` build (ADR-045), whose bench is deliberately cheap. The right question is *how
much does this swap improve my starting XI?*

#### A planning probe pinned the metric, the speed, and the value
- **The metric is XI-gain** = `best-XI-xP(after) − best-XI-xP(before)`. On a `--weekly` squad (£3 bank),
  the raw ranking tops with *Kusi-Asare → João Pedro **+19.3*** (bench fodder — the XI barely moves);
  XI-aware tops with *Guéhi → Gabriel **+3.0 XI xP*** (the real improvement).
- **A fast best-XI makes it cheap** — enumerate the ~7 legal formations and take top-N per position:
  it **matches `best_legal_xi` exactly** (235.3 = 235.3) and ranks ~750 candidate swaps in **0.02s** (no
  per-candidate ILP).
- **It pairs with `--weekly`** — XI-aware transfer maximises the XI, as `--weekly` builds it.

#### Decision Drivers
- **Answer the real question** — the swap that most improves the fielded XI, not a headline number.
- **No misleading gains** — a bench-only swap has XI-gain 0 and drops out.
- **Cheap & exact** — a fast best-XI that matches the ILP.
- **Consistency with the weekly build** — same "maximise the XI" lens.

---

### ✅ Decision

**1. The metric — XI-gain.** A swap's value = `best_xi_points(owned − out + in) − best_xi_points(owned)`
(on the unified xP). `suggest_transfers` keeps positive-XI-gain swaps, ranked by it; the shown "gain" is
the **XI gain**. Legality (same position, ≤3/club, affordable), the greedy disjoint dedup (ADR-040), and
the `(b)` marker are unchanged.

**2. The helper — `best_xi_points(players, scores)`.** The best legal XI's total score, by enumerating
the legal formations (GK 1; DEF 3–5, MID 2–5, FWD 1–3, outfield = 10) and summing top-N per position.
Fast (~O(1) per squad), and pinned to **match `best_legal_xi`** (a test asserts equality on real squads).

**3. XI-aware is the default** (owner's call). `transfer` (and the plan + `ask "what transfer…"`) rank by
XI-gain by default; **`--raw`** restores the old raw-player-gain ranking. *(This means a max-15 squad now
shows real XI upgrades — its XI isn't maximised — which is honest, not a false "free transfer".)*

**4. Surfaces.** The shortlist (`suggest_transfers`), the plan (`suggest_transfer_plan`, which threads
XI-gain through its greedy state), and the `ask` transfer intent all use XI-gain; combinable with
`--bank`/`--count`.

---

### 🔀 Alternatives Considered

- **Keep raw gain the default, XI-aware a mode.** Considered (symmetric with the squad `--weekly` mode),
  but the owner chose XI-aware default — the raw "+19.3 for a bench swap" answers the wrong question.
  `--raw` keeps the old view.
- **A bench-weighted transfer value** (`XI-gain + ε·bench-gain`, like `bench_weight`). Deferred — pure
  XI-gain is the weekly-relevant number; a bench-cover nuance can come later.
- **Per-candidate `best_legal_xi` ILP.** Rejected on speed (~seconds); the formation-enumeration best-XI
  is exact and ~0.02s.
- **Re-derive the squad's declared bench.** Not needed — the metric works off the best XI directly.

---

### 🧭 Consequences

**Positive**
- `transfer` answers the real question: the swap that most lifts the team you field. Bench-fodder swaps
  stop topping the list.
- Pairs with `--weekly` (both maximise the XI); fast and exact via `best_xi_points`.
- `--raw` preserves the old ranking for anyone who wants it.

**Negative / risks (mitigations)**
- **A max-15 squad now shows XI upgrades** (its XI isn't maximised) → honest (a real improvement), and a
  clear "ranked by XI improvement" note; `--raw` for the old behaviour.
- **`best_xi_points` must match `best_legal_xi`** → pinned by a test on real squads.
- **Bench cover is undervalued** (XI-gain 0) → deliberate for the weekly view; a bench-weighted variant is
  a later option.

---

### 📊 Validation

Prototyped on the live DB: the fast best-XI matches `best_legal_xi` (235.3); XI-aware ranks *Guéhi →
Gabriel +3.0 XI* where raw tops with the misleading *Kusi-Asare → João Pedro +19.3*; ~750 swaps in
0.02s. Acceptance for the sprint: on a `--weekly` squad `transfer` no longer tops with a bench-fodder
swap; it surfaces real XI upgrades; the plan + `ask` agree; `--raw` restores the old ranking.
