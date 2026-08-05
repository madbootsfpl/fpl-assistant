# Sprint 050: Documentation consolidation & status refresh — before the web UI

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2 working sessions (a docs sprint — no feature code)
**Carried Over:** None (Sprint 049 closed clean)

> **Direction (owner):** we're leaning to the **web UI** next — and agreed it should be *thin*. But first
> bring the docs up to date with where the project actually is, so a new track starts on a clean base.
> Specifically: **consolidate the roadmap into one** (don't care about the history), update the
> **journal**, **README**, **backlog**, and **handbook + glossary**.

---

### 🔎 Verified at planning (a staleness audit on the real docs)

- **README** headline says *"Phase 1 complete; Phase 3 complete (2026-08-04)"* — it **omits Phase 4**
  entirely (the 8 grounded `ask` intents + `chat` + fixtures that are now the flagship).
- **Glossary** (`02_Glossary/glossary.md`) is **17 lines**, ~1 recent term — missing nearly all of
  Sprints 27–49's vocabulary (xMins, decision-xP, fallback rate, archetypes, XI-gain/`best_xi_points`,
  bench-aware/`--weekly`/`--bench-boost`, conversational follow-ups/`converse`, FDR/fixtures modes,
  grounding verifier).
- **Roadmap** (`Roadmap.md`, reframed Sprint 025) coexists with **`Phase1_Reconciliation.md`** — the two
  want **merging into one** forward-looking roadmap; Phase 3/4 status is partly stale.
- **Backlog** lists items already shipped (e.g. the *multi-move transfer planner* = ADR-035; *differential*
  already struck through) alongside genuine live nice-to-haves (bench order, ceiling captaincy, …).
- **Bonus:** `CLAUDE.md` §"Current Phase" still reads *"Documentation and architecture phase. Do not
  build features before the design is agreed"* — badly stale after ~49 feature sprints. **Flagged for
  the owner** (an instruction file — updated only with the owner's OK, not silently).
- **The canonical facts to make agree everywhere:** 49 ADRs · 421 tests · Phases 1, 3, 4 complete · 8
  `ask` intents + a `chat` mode · web UI = *next*; preseason (GW1 2026-08-21).

---

### 🧭 What's new — the docs match reality; the roadmap is one forward-looking page

No feature code. The map (Roadmap), the story (Journal/README), the captured ideas (Backlog) and the
reference (Handbook/Glossary) all catch up to Sprint 049, and the roadmap becomes a **single** page that
points forward (web UI, then data hardening). A clean base to start the web-UI track on.

---

### 🎯 Sprint Goal

**Objective:** every named doc surface reflects the project as of Sprint 049, the **roadmap is
consolidated into one** forward-looking page (`Phase1_Reconciliation.md` retired — history lives in the
per-sprint docs + git), and the canonical facts (ADR/test counts, phase status, feature list, "web UI
next") are **consistent across README · PROJECT_STATUS · Roadmap · Journal**.

#### Success Criteria
- [x] **Roadmap consolidated** — one `Roadmap.md` (P1/P3/P4 done; next = web UI, then Data Hardening;
      every unbuilt item carried); `Phase1_Reconciliation.md` retired and all references updated
- [x] **Backlog reconciled** — shipped items marked/removed; only live nice-to-haves + tech-debt remain
- [x] **Journal** — a Phase-4 milestone entry (Sprints 033–049 arc)
- [x] **README** — Status line + feature list + "Planned" refreshed (Phase 4; web UI next)
- [x] **Handbook + Glossary** — the glossary gains the Sprints 27–49 vocabulary; the handbook
      index/glossary-index stay coherent
- [x] **Consistency check** — the canonical facts agree across README/PROJECT_STATUS/Roadmap/Journal; no
      dangling links to retired docs
- [x] **CLAUDE.md "Current Phase"** — updated (owner-approved) + a Working Rhythm section

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-148 | **Roadmap consolidation + Backlog reconcile** — merge `Roadmap.md` + `Phase1_Reconciliation.md` into one forward-looking `Roadmap.md` (P1/P3/P4 done; next = web UI → Data Hardening; carry unbuilt); retire `Phase1_Reconciliation.md` + fix references; reconcile `Backlog.md` (mark shipped, keep live) | High | ✅ Done | 0.5–1 session |
| US-149 | **Journal + README refresh** — a **Phase-4 Complete** journal milestone + a Sprints 36–49 arc entry; refresh README (Status → +Phase 4, feature list, "Planned" → web UI next) | High | ✅ Done | 0.5–1 session |
| US-150 | **Handbook + Glossary refresh** — glossary gains the Sprints 27–49 terms; handbook index (`Developer_Handbook`, `19_Glossary_Index`) coherence; a consistency sweep of the canonical facts; **CLAUDE.md** §Current-Phase iff approved | High | ✅ Done | 0.5–1 session |

#### Technical Tasks & Maintenance
- [ ] No ADR (editorial, not an architecture decision) — noted in the sprint log
- [ ] Run the suite once at close to confirm the quoted **421 tests / 49 ADRs** are current

---

### ✅ Definition of Done (this sprint)

A docs sprint — the DoD is adapted (no new tests):
1. **Every named surface updated** — Roadmap (consolidated), Backlog, Journal, README, Handbook, Glossary
   reflect the project at Sprint 049.
2. **Consistency & links checked** — the canonical facts (49 ADRs · 421 tests · P1/P3/P4 done · 8 intents
   + chat · web UI next) agree across README/PROJECT_STATUS/Roadmap/Journal; **no references to the
   retired `Phase1_Reconciliation.md`**; the ADR index still matches the ADR files; the test count is
   re-verified against a `pytest` run.
3. **The sprint is self-documented** — board + session log + a Lessons file, PROJECT_STATUS header flipped
   at retro (as usual).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Consolidating the roadmap into one; retiring `Phase1_Reconciliation.md` | Rewriting the per-sprint docs / ADRs (they *are* the history — left as-is) |
| Refreshing Journal, README, Backlog, Handbook, Glossary | Any web-UI code (that's Sprint 051) |
| A canonical-facts consistency sweep | New analytics or features |
| CLAUDE.md §Current-Phase — **only with owner approval** | Silently editing the instruction file |

**External Dependencies:** None.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Losing the Phase-1 audit trail by retiring the reconciliation doc | Low | The per-sprint docs + git history preserve it; the new Roadmap keeps a one-line "P1 delivered as CLI" summary |
| Docs drift again next sprint | Low | PROJECT_STATUS stays the single live status; the arc journal entry sets a cadence (a milestone per phase) |
| Editing CLAUDE.md without intent | Med | Flagged — changed only on explicit owner OK |
| Quoted counts go stale between edit and commit | Low | Re-verify the test/ADR counts with a run at close |

---

### 🗝️ No gate this sprint

Documentation is editorial, not an architecture decision — so **no ADR**. The one judgment call is
recorded here for the owner to veto at "start US-148": **retire `Phase1_Reconciliation.md`** (fold a
one-line summary into the new Roadmap; the detailed audit lives in the per-sprint docs + git). Everything
else is a straight refresh to Sprint-049 reality.

---

### 📝 Session Progress Log

- **US-148 ✅** — **Roadmap consolidated** into a single forward-looking `Roadmap.md`: **Delivered**
  (the CLI analytics core · decision support · the NL layer — 8 `ask` intents + `chat` + fixtures · CI),
  **▶ Next** (the thin FastAPI+Jinja web UI, Sprint 051), **Then** (Data Hardening, post-GW1), **Later**
  (chips · probabilistic xMins · evaluation), plus carried infrastructure + the guiding principles.
  Fixed two more staleness bugs along the way: **Phase 4 is done** (the old doc showed it all ⬜) and
  **CI is built** (GitHub Actions — was ⬜). **`Phase1_Reconciliation.md` retired** as a tombstone
  pointing to the Roadmap (so the historical links from ADR-026 / Sprint 25 / the Phase-1 milestone still
  resolve; the audit lives in git + the per-sprint docs); the live README link dropped. **Backlog
  reconciled** — the multi-move planner marked ◑ (coordinated plan shipped, ADR-035/046; the −4/roll
  maths remains), and three recent deferrals added as live nice-to-haves (differentials/value intent,
  persisted/pronoun-aware chat, team-level squad-fixtures). Consistency check: no live links to the
  retired doc; **49 ADRs / 421 tests** re-verified. _(No ADR — editorial.)_
- **US-149 ✅** — **Journal:** added `Phase4_Complete_Milestone.md` (Sprints 033–049) — the NL-layer
  milestone, matching the Phase-1/Phase-3 milestone format: the eight grounded `ask` intents, grounding
  verification (ADR-037), the `chat` conversational mode, the `fixtures` modes, and the arc's engine
  maturing (one xP metric, xMins v0, archetypes, bench-aware, XI-aware transfers); tests 279 → 421, ADRs
  32 → 49, no new runtime dependency; the "cheapest feature reuses what exists" and grounding-is-
  engineered lessons; honest boundaries + what's next (the web UI). **README:** the Status line now
  carries **Phase 4 complete** + the canonical facts (49 ADRs · 421 tests · CI green · web UI next); the
  intro notes it can be *talked to*; the **Planned** section reframed to Next (web UI) / Then (Data
  Hardening) / Later; Ollama added to Technology (optional, narrates only). The command/feature body was
  already current (maintained each sprint).
- **US-150 ✅** — **Glossary** expanded from 14 generic terms to a themed reference (General & tooling ·
  Data & sources · Analytics · Optimisation · Natural language) covering the Sprints 5–49 vocabulary
  (decision xP, xMins, xGI/xGC, DefCon, ILP, XI-gain, archetype/differential, bench-aware, grounding,
  intent, follow-up, …), plain-English throughout. **Handbook `19_Glossary_Index`** — the weak FDR/xP →
  Roadmap pointers repointed to the real analytics/optimisation chapters, and the domain terms added with
  their chapter homes (Ch 20/21/22/23/24/25). **CLAUDE.md** (owner-approved) — the stale "Current Phase"
  ("Documentation and architecture phase") replaced with the real state (P1/P3/P4 done; web UI next) + a
  **Working Rhythm** section encoding the gate-per-feature + 3-part-DoD loop we actually follow (keeping
  the original "don't build before the design is agreed" as *the gate*). **Consistency sweep:** 421
  tests / 49 ADRs agree across README/PROJECT_STATUS/Roadmap/Journal; no live links to the retired doc;
  tests green; ruff clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — a clean documentation base before opening the web-UI track. Every named
surface now reflects the project at Sprint 049, the roadmap is a **single forward-looking page**, and the
canonical facts (**49 ADRs · 421 tests · P1/P3/P4 done · web UI next**) agree across README ·
PROJECT_STATUS · Roadmap · Journal. No feature code; no ADR (editorial).

**Delivered**
- **US-148** — Roadmap consolidated (Delivered / Next / Then / Later); `Phase1_Reconciliation.md`
  tombstoned; Backlog reconciled (multi-move planner → ◑; three recent deferrals added).
- **US-149** — a `Phase4_Complete_Milestone` journal entry (Sprints 033–049); README refreshed (Status
  → +Phase 4, Planned → web UI next, Ollama in Technology).
- **US-150** — Glossary expanded to a themed domain reference; handbook glossary-index repointed;
  CLAUDE.md's stale Current Phase replaced + a Working Rhythm section (owner-approved).

**What went well**
- **The staleness audit paid off** — probing the *real* docs (not assumptions) found README omitting all
  of Phase 4, a 17-line glossary, CI marked ⬜ though it's built, and CLAUDE.md two phases behind.
- **A consolidation is also a correctness pass** — rewriting the roadmap surfaced that Phase 4 and CI
  were done; the single page is now the honest picture.
- **A tombstone beat a delete** — retiring the reconciliation doc without breaking the history links from
  ADR-026 / Sprint 25 / the Phase-1 milestone.
- **The facts now have one home each** — PROJECT_STATUS is the single live status; a milestone-per-phase
  cadence is set to stop drift.

**Challenges / how they were handled**
- **Retire vs preserve history** — resolved with a tombstone (content gone, links intact); the audit
  lives in git + the per-sprint docs, matching the owner's "don't carry the history."
- **Editing the instruction file** — CLAUDE.md changed only on explicit owner approval; kept the original
  "don't build before design agreed" intent, reframed as the gate.
- **Counts drifting between edit and commit** — re-verified 49 ADRs / 421 tests with a run at close.

**Carried forward:** None.
