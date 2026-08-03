# Sprint 015: Evaluate soccerdata (a spike → decision)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~2–3 working sessions (an **evaluation spike**, not a feature)
**Carried Over:** None (Sprint 014 closed clean)

---

### 🧭 What kind of sprint this is

This is a **spike**, not a feature sprint. Its output is **evidence + a decision (ADR-016)**,
**not** production code. The project's `src/` and `requirements.txt` stay untouched: no
dependency is taken on until (and unless) the ADR says adopt. Spike scripts live in
`spikes/015-soccerdata/` and run in a **throwaway venv** (`pip install soccerdata`), never
the project venv.

**Why a spike:** `soccerdata` is a heavy scraping dependency (pandas, lxml, a TLS-client
binary, a cache layer) against a charter that values simplicity — and FPL already gives us
xG/xA/xGI/xGC/per-90/goals/assists by id. Adopting it is a genuine product-owner /
architecture decision, so we *measure before we commit*.

This sprint is **Tony's own discovery** — he found soccerdata and did initial analysis;
this evaluates it rigorously.

---

### 🔎 Verified at planning (per the standing lesson)

A feasibility probe already established:

- **It installs here** — `soccerdata` 1.9.1 in a throwaway venv.
- **Sources are reachable** — Understat **570 players / 3.4s**; FBref **580 / 36s** (it
  downloads a TLS-client `.dylib` to defeat FBref's 403 anti-bot).
- **Name-matching is the risk** — a *naive* match hit only **29–37%**, but that number is
  **confounded**: it compared Understat **2023** to FPL's **current** roster (different
  seasons) and used crude normalisation. Unmatched samples (`emile smithrowe`, `cedric
  soares`) show the real work is season-alignment + accent/space handling + team
  disambiguation. **Measuring the achievable rate is US-047's job.**

So feasibility is proven; **value vs cost** is what this sprint decides.

---

### 🎯 Sprint Goal

**Objective:** Decide — with evidence — whether to adopt `soccerdata` as a data source.
Quantify (1) how reliably FPL players match a soccerdata source, and (2) what soccerdata
uniquely adds over FPL's own data (chiefly **npxG**); weigh that against the dependency and
fragility costs; record the call in **ADR-016**.

#### Success Criteria
- [ ] A **name-matching prototype** (same-season, team-aware) with a **measured match rate**
      and a catalogue of failure modes
- [ ] A **quantified unique-value** finding: npxG vs FPL xG for penalty-takers (and a list
      of what else soccerdata offers that FPL lacks)
- [ ] A recorded **operational cost**: install weight, speed, offline-testing impact, caching
- [ ] **ADR-016** with an explicit recommendation — **adopt / conditional / defer** — and the
      reasons; the backlog/roadmap updated to match
- [ ] All spike code in `spikes/015-soccerdata/`; **`src/` and `requirements.txt` unchanged**
- [ ] Findings are **reproducible** (a reader can re-run the scripts in a throwaway venv)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-047 | **Name-matching prototype**: match FPL ↔ Understat for the *same* season, with accent/space normalisation and team as a tiebreaker; measure the match rate; catalogue what fails and why | Critical | ✅ Complete | 1 session |
| US-048 | **Quantify the unique value**: pull npxG (and note other unique fields); compare npxG vs FPL xG for penalty-takers on matched players; record speed / dependency / offline-testing costs | High | ✅ Complete | 1 session |
| US-049 | **ADR-016 — the decision**: synthesise the evidence into adopt / conditional / defer, with the trade-offs and (if adopt) a sketch of the integration shape (best-effort source, like ClubElo). Update backlog/roadmap | High | ✅ Complete | 0.5 session |

---

### ✅ Definition of Done (adapted for a spike)

A feature-sprint DoD (tests → smoke → docs) doesn't fit an evaluation. This sprint's DoD:
1. **Evidence is real and reproducible** — the spike scripts run in a throwaway venv and
   produce the quoted numbers (no hand-waving).
2. **The decision is explicit** — ADR-016 says adopt / conditional / defer, with reasons a
   future reader can weigh, not just a vibe.
3. **The project is left clean** — no dependency, no `src/` change; spike code is boxed in
   `spikes/015-soccerdata/` and the roadmap/backlog reflect the decision.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Measuring FPL↔soccerdata name-matching | Production integration into `refresh`/storage |
| Quantifying npxG and other unique fields | Adding soccerdata to `requirements.txt` / the project venv |
| A recorded operational-cost assessment | A new view/objective built on soccerdata |
| ADR-016 with a clear recommendation | Committing to adopt before the evidence is in |

**External Dependencies:**
- [ ] `soccerdata` in a **throwaway** venv only; the FPL API (already used) for the FPL side

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| The spike quietly becomes a production integration | High | Hard rule: nothing in `src/`, nothing in `requirements.txt`; spike code boxed in `spikes/` |
| Name-matching turns out unreliable | Med | That *is* a valid finding — a low match rate → the ADR recommends *defer*, with the number |
| npxG's edge is marginal | Med | Also a valid finding — quantify it; if small, *defer* is the honest call |
| Sinking time into an open-ended evaluation | Med | Time-boxed to ~2–3 sessions; three concrete deliverables, then decide |
| Confusing last sprint's FPL xG with soccerdata's | Low | Keep them clearly labelled; the comparison is the point |

---

### 🗝️ How the decision will be judged (the rubric for ADR-016)

`soccerdata` is worth adopting only if **all** hold; otherwise defer:
1. **Matching is reliable** — a high enough automatic match rate (say ≥ 90% of relevant
   attackers) with a safe fallback for the rest (no silent wrong matches).
2. **The unique value is real** — npxG (or another field) measurably changes a decision the
   FPL data can't (e.g. it re-ranks penalty-takers).
3. **The cost is acceptable** — the dependency/fragility/offline-testing hit is worth it for
   that value, given the charter's "prefer simple".

The ADR states each verdict with its number, then the overall call. A *defer* with good
evidence is a **successful** sprint — the point is to decide well, not to adopt.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-047: name-matching prototype)
* **Completed:** Built `spikes/015-soccerdata/match_fpl_understat.py` and measured
  FPL ↔ Understat (2024/25) matching. **Result: 95% confident automatic match** among
  players actually in both datasets (259 matched, 12 name-form misses), via a two-layer
  matcher — formal full-name, then FPL `web_name` (the *common* name) as a token, with team
  as tiebreaker. The naive first pass was 88%; the common-name layer closed most of the gap
  (FPL stores full legal names, `david raya martin`; Understat uses `David Raya`). Residual
  ~3–5% are ambiguous common names (`gabriel`, `rodrigo`) needing a small hand-maintained
  override map — the same pattern as the shipped `CLUBELO_TO_FPL`. The real coverage ceiling
  is **roster drift** (32% of FPL-played players aren't in Understat 24/25 — new signings /
  promoted clubs), which degrades to `None`, exactly like FPL's own xG for newcomers.
  Findings written to `spikes/015-soccerdata/FINDINGS.md`. **Rubric #1 (matching reliable?)
  → ✅ Yes.**
* **Spike discipline:** ✅ `src/` and `requirements.txt` untouched; all code in `spikes/`,
  run in a throwaway venv.
* **Docs touched:** Sprint15 board, `spikes/015-soccerdata/FINDINGS.md`, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** US-048 — quantify the unique value (npXG vs FPL xG for penalty-takers) +
  operational cost.

#### Session 2 — 2026-08-03 (US-048: unique value + operational cost)
* **Completed:** Built `compare_npxg.py`. **npXG is genuinely unique and material** — FPL's
  xG includes penalties; Understat's npXG strips them, and penalty-takers inflate by 3–7
  xG (**Palmer's open-play threat is 5.7 vs a raw 10.6 — nearly half is penalties**).
  Ranking the top-10 by npXG vs FPL xG swaps ~3 of 10. **Rubric #2 → ✅ Yes** (real, but
  narrow — one field, mostly for penalty-takers). Surfaced a **season-alignment trap**:
  FPL's xG is 2025/26, and pulling Understat 2024/25 silently mis-joined (Thiago 20.6 vs
  0.1 — an injury-season offset, also hiding transfers); aligning seasons fixed it and
  raised matches 231 → 316. **Operational cost measured: 14 → 72 packages** (pandas, numpy,
  selenium + seleniumbase browser stack), scraping fragility, offline-testing rework.
  **Rubric #3 → ⚠️ High.** All in `spikes/015-soccerdata/FINDINGS.md`.
* **Spike discipline:** ✅ `src/` and `requirements.txt` still untouched.
* **Docs touched:** Sprint15 board, `FINDINGS.md` (US-048 section), PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** US-049 — synthesise into ADR-016 (adopt / conditional / defer).

#### Session 3 — 2026-08-03 (US-049: the decision — ADR-016)
* **Completed:** Recorded **ADR-016: Defer.** Rubric verdicts — matching ✅ reliable (~95%),
  unique value ⚠️ real but **narrow**, cost ❌ high (14 → 72 packages, selenium/pandas,
  scraping fragility, season-alignment trap). **Tony's decision (as Product Owner):** the
  data adds some value but isn't essential to a decision — you don't deselect Haaland for a
  low npXG *because he takes penalties*, so FPL's penalty-inclusive xG is the relevant
  signal; the cost is very high with real tech-debt risk. Push soccerdata to the backlog as
  *validated but deferred*; proceed with the lighter FPL-native model. Added to the ADR
  index; backlog updated. **A well-evidenced defer — a successful spike.**
* **Spike discipline:** ✅ `src/` and `requirements.txt` untouched throughout the sprint.
* **Docs touched:** ADR-016 (new) + index, Backlog, Sprint15 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 015 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-047 (name-matching, ✅ ~95%), US-048 (npXG value +
  cost), US-049 (**ADR-016: Defer**). The spike answered "adopt soccerdata?" with evidence
  and a clear decision. **Zero production code; `src/` and `requirements.txt` untouched.**
* **Carried Forward:** None. soccerdata → backlog as *validated, deferred*.
* **Key Artifacts / Decisions:** ADR-016 (Defer); `spikes/015-soccerdata/` (FINDINGS.md +
  two reproducible scripts); a memory note on Tony's cost-over-completeness preference.

#### Retrospective
* **What Went Well?**
  - **A spike did its job: it said no, with evidence.** Matching (~95%) and npXG were real,
    but the cost (14 → 72 packages, selenium/pandas, scraping, a season-alignment trap) and
    the *narrow, nice-to-know* value made defer the right call. We avoided years of tech debt.
  - **Tony's product judgement was sharp** — the Haaland point (you own penalty-takers
    *because* they take penalties, so penalty-inclusive xG is the FPL-relevant signal) cut
    to the heart of why npXG isn't decision-driving here.
  - **Discipline held** — nothing leaked into `src/`; the whole evaluation is boxed and
    reproducible in a throwaway venv.
  - The probe caught a subtle **season-alignment trap** (FPL 2025/26 vs Understat 2024/25)
    that would have silently mis-joined data in a naive integration — a real save.
* **What Could Be Improved?**
  - The first npXG comparison used the wrong Understat season and looked like false matches;
    a season-sanity check up front would have saved a diagnostic detour (now documented).
* **Lessons Learned?**
  - Evaluate a dependency *before* adopting it — a boxed spike in a throwaway venv turns a
    "should we?" argument into measured evidence.
  - Distinguish **decision-driving** value from **nice-to-know**; only the former justifies cost.
  - A well-evidenced **defer is a successful sprint** — deciding well is the deliverable.
* **Action Items for Next Sprint (016):**
  - [ ] Proceed with the **lighter FPL-native model** — the over/under-performance lens
    (expected vs actual attacking points), no new dependency, decision-relevant.
  - [ ] Keep the spike-before-adopt habit for future dependency questions.

---

**Proposed follow-on (Sprint 016):** the FPL-native **over/under-performance** lens
(expected attacking points from xG/xA vs actual) — the "lighter model" we chose over
soccerdata. Fully data-supported, no new dependency.

**Completion Date:** 2026-08-03
**Final Notes:** The first sprint to ship *no* code — and the right outcome. A validated,
evidence-backed **defer** of soccerdata, on Tony's product call. Spike outcome:
**Successful** — 3/3 stories, a clear decision, the project left clean.
