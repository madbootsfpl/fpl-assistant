# Sprint 025: Phase 1 Close-Out & Roadmap Reconciliation

**Dates:** 2026-08-03
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2 working sessions (a **documentation sprint — no new code**)
**Carried Over:** None (Sprint 024 closed clean; build phase feature-complete)

---

### 🔎 Verified at planning (per the standing lesson — here the "data" is our own docs)

Read the **original** `docs/04_Roadmap/Roadmap.md` and mapped it against all 24 sprints. The
finding that shapes this sprint:

- **What we built cuts _across_ the original phases — it isn't literally "Phase 1."** We shipped
  the **analytical + optimisation core as a CLI**, and *deliberately* skipped Phase 1's
  infrastructure items:
  - ✅ **Built** (spanning original P1/P2/P5): FPL API client + SQLite cache (migrations, upsert);
    custom FDR (overall + Elo); Points-per-£m value; xP v0 + multi-week horizon; xG/xA/xGI/xGC;
    over/under-performance; DefCon; clean-sheet xGC; ILP squad selector (full 15, flexible
    formations, bench, include/exclude, pluggable objective); saved squads (user state);
    availability filtering; retry + graceful degradation.
  - ❌ **Not built** (carry to Phase 2+): web dashboard UI; CI/CD + pre-commit; session auth
    (`/my-team/`); historical backfill + price-trend schema; auto-refresh scheduling; price-change
    predictor; form-per-£m + rolling trends; Attack/Defence FDR split; a first-class xP engine
    with uncertainty; **all** of decision-support (xMins, captain, transfers, team analyser),
    AI/RAG, chip optimisers, and the evaluation/feedback loops.

- **Existing homes to reconcile against** (don't invent structure): `docs/04_Roadmap/Roadmap.md`
  (the 5-phase plan), `docs/Backlog.md` (already the nice-to-have home — and slightly **stale**:
  "Saved / persistent squad" is listed active but shipped in Sprint 023; the shared renderer
  isn't listed), `docs/01_Journal/` (session journal), `docs/06_Decisions/` (ADR log).

**Owner's decision (made at planning):** *"declare SUCCESS and move these items into Phase 2."* →
**Reframe around reality:** declare a **Phase 1 — CLI Analytics MVP** complete, and carry every
unbuilt item forward into a reframed Phase 2+ (nothing dropped). No new code.

---

### 🧭 What's new — the map catches up with the territory

For 24 sprints we built by *learning*, sprint-to-sprint, and the code outran the original
aspirational roadmap. This sprint makes the **map match the territory**: an honest built-vs-plan
reconciliation, a clear line under "Phase 1 (CLI Analytics MVP) — done", and every remaining idea
re-homed into future phases or the nice-to-have backlog. It's a project-hygiene sprint, squarely
in the Charter's priority order (Understanding & Documentation first).

---

### 🎯 Sprint Goal

**Objective:** Reconcile the 24 sprints against the original Roadmap, **review for anything left
before close**, then **declare Phase 1 (CLI Analytics MVP) complete** and reframe the Roadmap so
all unbuilt items live in Phase 2+ / the backlog — nothing dropped, everything traceable.

#### Success Criteria
- [ ] Approach + declaration agreed (**ADR-026**) before rewriting anything
- [ ] A **built-vs-Roadmap matrix** — every original Roadmap item marked Done / Partial / Deferred,
      and every one of the 24 sprints accounted for (no orphans either way)
- [ ] A **completeness review** — an end-to-end sweep for loose ends; either "nothing blocks the
      MVP declaration" or a short, explicit punch-list
- [ ] `Roadmap.md` rewritten: **Phase 1 — CLI Analytics MVP ✅** (with what was delivered) + a
      reframed **Phase 2+** holding the carried-forward items
- [ ] `Backlog.md` synced (done items moved; anything new captured)
- [ ] A **Journal milestone entry** marking Phase 1 closed
- [ ] `PROJECT_STATUS.md` reflects Phase 1 complete / MVP milestone
- [ ] **No new code** — `src/` and `tests/` untouched (a documentation sprint)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-073 | **Gate.** Build the built-vs-Roadmap **reconciliation matrix** (every roadmap item ↔ every sprint) and record the decision in **ADR-026**: declare *Phase 1 — CLI Analytics MVP* complete; reframe the roadmap; carry all unbuilt items to Phase 2+ (nothing dropped) | Critical | ✅ Done | 1 session |
| US-074 | **Completeness review** — an end-to-end sweep (commands, tests, docs, loose ends) for anything genuinely left before declaring the MVP done. Output: a short verdict + punch-list (empty is a valid result) | High | ✅ Done | 0.5 session |
| US-075 | **Execute the reframe** — rewrite `Roadmap.md` (Phase 1 ✅ + reframed Phase 2+), sync `Backlog.md`, add a `01_Journal` milestone entry, update `PROJECT_STATUS.md` → Phase 1 closed | High | ✅ Done | 0.5 session |

#### Technical Tasks & Maintenance
- [x] ADR-026 recorded + added to the ADR index — _US-073_
- [x] Completeness review run; verdict = nothing blocks. 5-item doc-hygiene punch-list handed to
      US-075 (incl. README FastAPI/Goals drift, PROJECT_STATUS ADR count, Backlog sync) — _US-074_
- [x] Cross-check every doc link the rewrite touches still resolves — _US-075_ (verified)

---

### ✅ Definition of Done (this sprint — adapted: no code)

There's no code, so the 3-part DoD adapts (as it did for the Sprint 015 spike):
1. **Verified, not tested** — the matrix accounts for **every** Roadmap item *and* every sprint
   (nothing orphaned); links resolve. (Stands in for "automated tests pass".)
2. **Read-through check** — the rewritten Roadmap / Backlog / Journal / PROJECT_STATUS read
   coherently and cross-reference correctly. (Stands in for the manual smoke test.)
3. **Documentation updated & checked** — Roadmap, Backlog, Journal, ADR + index, PROJECT_STATUS,
   sprint board (Charter Documentation Rules: Journal, Architecture-if-touched, Roadmap, Decisions).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Built-vs-Roadmap matrix + completeness review | **Any new feature or code** (`src/`, `tests/` untouched) |
| Declaring Phase 1 (CLI Analytics MVP) complete | *Building* any Phase 2 item (web UI, CI, auth, …) |
| Reframing Roadmap Phase 2+ (carry, don't drop) | Re-litigating past ADRs / deferrals |
| Syncing Backlog + a Journal milestone | Changing the tool's behaviour |

**External Dependencies:** None (documentation only).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| "Complete" overstates it (infra never built) | Med | Name it precisely — *CLI Analytics MVP* — and list what was **deferred**, not hidden; the matrix is explicit |
| An item silently dropped in the reframe | Med | Matrix must account for **every** original item; carry-forward, don't delete; Backlog captures nice-to-haves |
| Revisiting settled decisions | Low | Deferrals already have ADRs (016 soccerdata, 012 two-tier, etc.) — reference, don't re-argue |
| Scope creep into "just build CI quickly" | Med | Explicitly no-code this sprint; CI/web/auth are Phase 2 line-items, not this sprint's work |

---

### 🗝️ Gating decision (US-073 → ADR-026)

Owner already chose the framing at planning; the gate records it and pressure-tests the matrix.
Proposed content (Tony to confirm/redirect at "start US-073"):

1. **Declaration.** *Phase 1 — CLI Analytics MVP* is **complete**: a working CLI FPL analytics &
   optimisation tool (25 ADRs, 227 tests, 12 commands, FPL + best-effort ClubElo sources).
2. **Reframe, don't drop.** The original Roadmap was aspirational and pre-dates the build. Rewrite
   it to match reality; **carry every unbuilt item into a reframed Phase 2+** (or the Backlog).
   Nothing is deleted — the matrix is the audit trail.
3. **Vehicle.** Record this as **ADR-026** (a milestone/roadmap decision) + a Journal entry. *(If
   you'd rather keep it lighter — a Roadmap header note, no ADR — say so at the gate.)*
4. **Pressure-test the matrix:** it passes only if **every** Roadmap bullet maps to Done / Partial
   / Deferred **and** all 24 sprints appear — no orphan on either side.

---

### 📝 Session Progress Log

- **US-073 (gate) ✅** — Built the two-way reconciliation
  ([Phase1_Reconciliation.md](../04_Roadmap/Phase1_Reconciliation.md)): every original Roadmap
  bullet classified Done/Partial/Deferred (with sprint + ADR), and all 24 sprints accounted for —
  no orphans either way. Surfaced the honest tension (we built the analytics/optimisation core
  across original P1/2/5 as a CLI; deferred the P1 infra spine). Recorded the decision in
  **ADR-026**: declare *Phase 1 — CLI Analytics MVP* complete, reframe the Roadmap, carry every
  unbuilt item to Phase 2+ (nothing dropped). ClubElo re-checked at planning — still down (timeout).
- **US-074 (completeness review) ✅** — **Verdict: nothing blocks the MVP declaration.** All 12
  commands smoke-tested working; 227 tests green; no code loose ends (no TODO/FIXME, no surfaced
  warnings). Non-issues confirmed: `fixtures --team` required (by design), `fdr --type elo`
  degrades gracefully with ClubElo down (resilience working), PuLP 4.0 deprecation intentionally
  suppressed (already on Backlog). **Doc-hygiene punch-list for US-075** (all documentation):
  (1) PROJECT_STATUS "ADRs: 25" → 26; (2) README Technology lists **FastAPI** (never used — CLI,
  ADR-002/003); (3) README Goals list transfers/captains/AI as if current (deferred → P2+ — reframe
  current-vs-planned); (4) Backlog stale (saved-squad shipped S23; renderer S24 unrecorded);
  (5) clarify "25-ADR build (001–025)" vs 26 total. The review caught the README front-door
  overstating the tool — the exact map-vs-territory drift this sprint closes.
- **US-075 (execute the reframe) ✅** — Rewrote `Roadmap.md`: **Phase 1 — CLI Analytics MVP ✅
  COMPLETE**, with a reframed **Phase 2 (Infrastructure, Data Depth & Analytics Hardening)** that
  leads with the carried-forward infra, and built items marked ✅ across Phases 3–5 + cross-cutting.
  Cleared the punch-list: `PROJECT_STATUS` (Phase 1 closed, ADRs 25→26); README (removed FastAPI →
  real stack; **split Goals into "What it does today (MVP)" vs "Planned (Phase 2+)"**); `Backlog`
  synced (saved-squad + shared-renderer → Done; shared *squad* renderer added to tech-debt);
  clarified "25 ADRs (001–025)" wording. Added a **Phase 1 milestone** to `01_Journal`. All doc
  links verified resolving; 227 tests unchanged (no code touched — a documentation sprint).

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-073 (reconciliation matrix + ADR-026), US-074 (completeness
  review), US-075 (execute the reframe). **Phase 1 is formally declared complete as the "CLI
  Analytics MVP"**, the Roadmap is reframed to match what was actually built (carry, don't drop),
  and the front-door docs are honest again. A **documentation sprint — no code**; 227 tests
  unchanged. *The map now matches the territory after 24 build sprints.*
* **Carried Forward:** None. The reframed Phase 2+ holds every unbuilt item; Sprint 026 will
  prioritise it and pick a direction.
* **Key Artifacts / Decisions:** ADR-026 (declare + reframe); `Phase1_Reconciliation.md` (the
  two-way audit); rewritten `Roadmap.md`; `Phase1_Complete_Milestone.md`; synced `Backlog.md`;
  honest README (Goals split into today vs planned).

#### Retrospective
* **What Went Well?**
  - **An honest close, not a flattering one.** The reconciliation named the real shape — we built
    the analytics/optimisation core (across original P1/2/5) as a CLI and *deferred* the P1 infra
    spine — so "complete" got the precise qualifier *CLI Analytics MVP*, with deferrals listed, not
    buried.
  - **A two-way matrix caught everything.** Classifying every roadmap bullet *and* accounting for
    every one of the 24 sprints (no orphans either way) is what made the declaration defensible.
  - **The completeness review earned its keep** — it caught the README overstating the tool
    (FastAPI + unbuilt features listed as current). A close-out sprint that *found* drift, not one
    that rubber-stamped.
  - **Nothing dropped.** Every deferred idea traces from the reframed Phase 2+ back to an original
    bullet via the matrix.
  - DoD held (adapted for no-code): matrix balances both ways, links resolve, docs read coherently.
* **What Could Be Improved?**
  - The dev **Journal** had stalled at Session 1 (Sprint 001) — 24 sprints went unjournalled. A
    milestone entry patches the gap, but the per-session journal habit lapsed early (the sprint
    docs + ADRs carried the record instead).
  - The reframed **Phase 2 is large and unordered** — prioritising it is a Sprint 026 job, not done
    here.
* **Lessons Learned?**
  - Reconcile the plan against reality periodically — building by learning means the code outruns
    the roadmap, and the map needs to catch up.
  - Name a milestone for what was *built*, and list what was *deferred* — precision beats a
    flattering headline.
  - A close-out sweep is worth running even when you expect "nothing left" — it found the README.
* **Action Items for Next Sprint (026):**
  - [ ] Prioritise the reframed **Phase 2** and pick the next direction (web UI? CI/CD? historical
        data? or jump to a Phase 3 decision-support feature). Check first.
  - [ ] Decide whether the dev Journal habit resumes, or the sprint docs + ADRs remain the record.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 026):** the first Phase 2 sprint — prioritise the reframed backlog and
choose a direction. Owner to steer (this is a fresh planning conversation).

**Completion Date:** 2026-08-03
**Final Notes:** Phase 1 closed cleanly and honestly — declared as the *CLI Analytics MVP*, every
unbuilt item carried forward, the front door made truthful. Sprint outcome: **Successful** — 3/3
stories, zero roll-over, DoD held (adapted for a no-code sprint).
