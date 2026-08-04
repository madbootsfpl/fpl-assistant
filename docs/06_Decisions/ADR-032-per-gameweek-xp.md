# Architectural Decision Record: Per-gameweek xP breakdown (+ `analyse --sort xp`)

**Decision ID:** ADR-032
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Extends ADR-006/007 (xP / horizon) — additive, the total is unchanged
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

xP has always been a single **horizon total** (ADR-007). From the Sprint 029 retro, the owner asked
to *"sort by highest xP and see the xP for each gameweek"* in `analyse`. The per-gameweek view is
also the long-standing **"xp per-gameweek breakdown"** backlog item (from Sprint 006).

A planning probe confirmed the maths is exact: splitting a player's horizon xP into its gameweeks
and summing gives back the total — Haaland `{GW1 6.8, GW2 6.8, GW3 7.5, GW4 6.1, GW5 7.5}` → **34.7
= `player_xp` total 34.7** (B.Fernandes 34.2, Gabriel 27.8 too). A **DGW** (two fixtures in a GW)
sums to a higher GW value; a **BGW** (no fixture) is 0. So per-GW is a *faithful decomposition* of a
number we already have — not a new metric.

#### Decision Drivers
- **Make xP legible** — show *when* the points land, without changing the number.
- **One reusable capability** — serve `analyse` *and* `xp` (close the backlog item at once).
- **Don't disturb existing xP** — the total and its tests must be unchanged.

---

### 💡 Decisions

**1. A faithful decomposition, not a new metric.** Per-GW xP = the player's rate × the sum of
fixture multipliers *in that gameweek*. Summed over the horizon it equals the existing total
(proven). DGW = the gameweek's fixtures summed; BGW = 0. The xP formula (ADR-006/007) is untouched.

**2. Additive analytics.** `player_xp` gains a `by_gameweek` breakdown (per-GW xP, keyed by the
gameweek) and the list of horizon `gameweeks`, alongside the existing `xp` total. Existing consumers
ignore the new keys; **existing totals are unchanged** (the total is still rounded once and is
authoritative). Internally the total is the sum of the *unrounded* per-GW values, so it matches
today's number exactly.

**3. Display: GW columns + a total.** `analyse` (XI + bench) and the `xp` command show `GW1 … GWN`
columns and the total. GW columns are **narrow** (~5 wide); at the default horizon (5) they fit
comfortably. For a large horizon the table widens — acceptable for a CLI; a soft cap / compact form
is a noted refinement, not built now. **Per-GW cells are rounded for display; the total is
authoritative** — so a rounded row may occasionally read ±0.1 off its total (a normal rounding
artifact), noted in the footer.

**4. `analyse --sort xp`.** `analyse` sorts the XI by xP when asked. **Default stays `position`**
(the formation shape is the natural squad read); `--sort xp` gives strongest-first. *(Owner may
prefer xp as the default — a one-line change; flagged.)*

**Not in scope:** changing the xP total; historical per-GW *actuals* (needs GW1 — Data Hardening);
in-season form blending; xMins-weighted per-GW.

---

### 🧪 Worked example (pressure-testing — real data, before code)

Per-GW decomposes the total exactly (proven live):

| Player | GW1 | GW2 | GW3 | GW4 | GW5 | Σ | `player_xp` total |
|---|--:|--:|--:|--:|--:|--:|--:|
| Haaland | 6.8 | 6.8 | 7.5 | 6.1 | 7.5 | **34.7** | 34.7 ✅ |
| B.Fernandes | 7.4 | 7.4 | 6.7 | 6.0 | 6.7 | 34.2 | 34.2 ✅ |

The horizon this preseason is single-GW throughout (no DGW/BGW), but the grouping (a GW's xP = its
fixtures summed) handles both by construction.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** xP becomes legible week-by-week and sortable; one analytics addition serves `analyse`
  + `xp` and closes a Sprint-006 backlog item. No new dependency, no schema change, totals unchanged.
* **Negative / Trade-offs:** wider tables (the GW columns); a per-GW row may read ±0.1 off its total
  (display rounding). Both minor and noted.
* **Risks & Mitigations:**
  - *Breakdown ≠ total* → the total is the sum of unrounded per-GW; a test asserts it; existing
    totals unchanged.
  - *DGW/BGW* → a GW's xP = sum of its fixtures (2 / 0); unit-tested.
  - *Projected vs actual confusion* → labelled projected; actual per-GW is Data Hardening (needs GW1).

---

### 🛠 Implementation & Migration
* **Components Affected:** `src/analytics/xp.py` (a per-GW helper + `by_gameweek`/`gameweeks` in the
  result); `analyse_squad` / the analyse view (per-GW columns + `--sort xp`); the `xp` view (per-GW
  columns). No schema change; no change to the xP total.
* **Action Items:**
  - [x] Record the design + the proven decomposition (US-089)
  - [ ] Per-GW xP analytics + tests (sum, DGW, BGW) (US-090)
  - [ ] `analyse` per-GW + `--sort xp`; `xp` per-GW; width handling; smoke (US-091)
  - [ ] (Backlog) close "xp per-GW breakdown"; a soft cap / compact form for large horizons

---

### 🔄 Review & Reconsideration
* **Review Date:** When GW1 is played (add per-GW *actuals* alongside projections — Data Hardening).
* **Triggers for Reconsideration:**
  - [ ] Large horizons overflow in practice → a compact form / cap.
  - [ ] Owner wants xp-sort as the analyse default → flip the default.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-089 (this), US-090, US-091
- **External Docs:** [ADR-006 (xP v0)](./ADR-006-expected-points-v0.md) · [ADR-007 (horizon)](./ADR-007-multi-week-xp.md) · [ADR-031 (analyser)](./ADR-031-team-analyser.md) · [Sprint 030](../05_Sprints/Sprint30.md)
