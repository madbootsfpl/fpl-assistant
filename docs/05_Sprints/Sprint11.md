# Sprint 011: The Full 15-Man Squad

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~2 working sessions (a focused extension of the optimiser)
**Carried Over:** None (Sprint 010 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

Checked the stored data before planning (564 players):

- **By position:** GK 62 · DEF 185 · MID 249 · FWD 68 — plenty for a 2/5/5/3 squad.
- **Price range:** £4.0m–£15.5m.
- **Cheapest legal 15-man squad:** **£64.0m** (GK 8.0 · DEF 20.0 · MID 22.5 · FWD 13.5)
  — comfortably inside the £100.0m budget, with room to spend up on the best players.

**No new data or dependency** — pure optimiser work on data already stored. Still
blocked (preseason): `form`, attack/defence strengths.

This sprint is Tony's Sprint 010 pick from the backlog ("getting through the backlog").

---

### 🧭 Architecturally, what's new — the *real* squad, and why the core barely changes

Until now the optimiser answers *one* question: the best **starting XI** (a fixed
1-4-4-2) within a budget. Real FPL is about the **15 you own** — 2 GK, 5 DEF, 5 MID,
3 FWD, ≤ £100.0m, ≤ 3 per club.

The key architectural point: **the optimiser already supports this.** Since Sprint 007
`select_squad` has taken `formation` and `budget` as *parameters* — it maximises a
score under whatever position counts and budget you give it. So the "full squad" is not
a new algorithm; it's a new **caller**:

```
squad        → formation {GK:1, DEF:4, MID:4, FWD:2},  budget £80m   (the XI, today)
squad --full → formation {GK:2, DEF:5, MID:5, FWD:3},  budget £100m  (the 15, new)
```

Same generic core, a different set of constraints at the edge — the pattern that has
recurred all project.

**The bench, and why it's the manager's call.** The optimiser scores *all 15 equally*,
so on its own `--full` would spend almost the whole £100m on 15 near-premium players —
mathematically "best", but no cheap bench. That's deliberate: **the manager chooses the
bench.** You `--include` 4 cheap, vetted players (locking those slots cheap), and the
optimiser spends the rest on the best 11. So the real usage is:

```
squad --full --include <cheap GK> <cheap DEF> <cheap MID> <cheap FWD>
```

This keeps human judgement (which cheap fodder is worth owning) with the human, and lets
the solver do what it's good at (optimise the rest). It reuses `--include` exactly as
built in Sprint 008 — no new mechanism.

---

### 🎯 Sprint Goal

**Objective:** Extend the optimiser from "best starting XI" to the **full 15-man FPL
squad** — 2 GK / 5 DEF / 5 MID / 3 FWD, ≤ £100m, ≤ 3 per club — maximising the chosen
objective, with the bench chosen by the manager via `--include`.

#### Success Criteria
- [x] Full-squad approach agreed (**ADR-012**) before feature code
- [x] `squad --full` picks the **15** (2/5/5/3, default £100m, ≤3/club)
- [x] The output shows all 15 grouped by position, with totals and the objective stated
- [x] `--full` composes with `--objective`, `--budget`, `--include`, `--exclude`
- [x] The `--include`-the-bench workflow is documented (help text + README + Handbook)
- [x] Existing `squad` (the XI) is **unchanged** — a regression test pins it
- [x] Edge case handled — infeasible budget → clear message, no crash
- [x] Tests cover the 15-man selection, the club cap, and include/exclude (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-037 | Agree the full-squad approach (**ADR-012**): 15-man quotas (2/5/5/3), £100m default, ≤3/club, objective applies, **bench via `--include`**, display — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-038 | `squad --full` command: call `select_squad` with the 15-man formation + £100m default; extend the display to show all 15 by position + totals; help text explains the bench workflow. Reuse objective/include/exclude. Tests + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-012 recorded + added to the ADR index — _US-037_
- [ ] Update Architecture doc (full-squad note + changelog) — _US-037_
- [ ] Update `README.md` + `--help` with `--full` and the include-the-bench workflow — _US-038_
- [ ] Handbook Ch 22 (Optimisation) — add the full-squad section — _US-038_
- [ ] Update Backlog: mark "full 15-man squad" done; **flexible formations** stays open — _US-038_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for ten sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| 15-man squad: 2/5/5/3, £100m, ≤3/club | **Flexible formations** (stays in the backlog) |
| Objective applies to the 15 (points/value/xp) | Two-tier XI-vs-bench optimisation (rejected — see ADR) |
| Bench chosen by the manager via `--include` | Auto-picking cheap bench for the user |
| Show all 15 by position, with totals | Captain / vice / chip logic |
| Reuse budget, objective, include/exclude | Transfers / multi-week planning |

**External Dependencies:**
- [ ] Existing players data + PuLP; no new data or dependency (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| `--full` with no includes spends up → no cheap bench | Med | **Intended** — the manager `--include`s the bench; help text + docs state the workflow plainly |
| Display was built for 11; now 15 | Low | Extend `render_squad` to show the given count; keep the XI rendering unchanged |
| Default budget differs by mode (80 vs 100) | Low | `--budget` overrides; default is 100 only when `--full` is set — a test covers both |
| Infeasible budget (too low for 15) | Low | Solver status ≠ Optimal → existing "no legal squad" message (cheapest legal is £64m) |
| Existing `squad` (XI) behaviour drifts | Low | `--full` is purely additive; a regression test pins the current XI output |

---

### 🗝️ Gating decision (US-037 → ADR-012)

Settle before building — **pressure-test with a worked example** (per the standing
lesson). The agreed answers (from Tony's Sprint 011 direction):

1. **Simple full-squad model, not two-tier.** Maximise the objective over **all 15**
   within £100m. *Rejected alternative:* a two-tier "maximise the XI, own a legal 15"
   model — more correct in theory but more complex; the manager achieves the same
   realistic bench more simply via `--include`.
2. **Quotas / budget / club cap.** Exactly 2 GK, 5 DEF, 5 MID, 3 FWD; Σ price ≤ £100m
   (default for `--full`); ≤ 3 per club. All already expressible in `select_squad`.
3. **The bench is the manager's.** No auto-bench logic. `--include` locks 4 cheap,
   vetted players; the solver optimises the remaining 11. Documented as the workflow.
4. **Objective.** Unchanged — points (default) / value / xp from Sprint 010, applied to
   the 15.
5. **CLI.** `squad` = the XI (unchanged, £80m default). `squad --full` = the 15 (£100m
   default). Both take `--objective`, `--budget`, `--include`, `--exclude`.
6. **Display.** `--full` shows all 15 grouped by position with totals and the objective;
   forced (`--include`) picks still marked `*`.

**Worked example to verify at the gate:** run `squad --full` on the real data and show
it spends ~£100m on 15 strong players (no cheap bench); then `squad --full --include`
4 cheap players and show those slots lock cheap while the other 11 improve — confirming
the workflow does what we claim *before* writing the command.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-02 (US-037: ADR-012 — the full-squad model)
* **Completed:** Recorded **ADR-012**: the *simple* full-squad model — `squad --full`
  maximises the objective over all 15 (2/5/5/3, £100m default, ≤3/club); the bench is the
  manager's via `--include`; the two-tier XI/bench model is **rejected** (simplicity), and
  the door documented. **Pressure-tested on real data before writing:** `--full` no
  includes → £100.0m / 2606 pts / no cheap bench; `--full --include <4 cheap>` → bench
  £17m + best 11 at £83m / 2241 pts — confirming the workflow *and* the caveat. Recorded
  the **stated limitation**: the 15-total counts a non-scoring bench, so it's a
  squad-strength proxy, not a weekly return. Added to the ADR index; Architecture §12
  changelog note. US-037 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the
  verification — run live against `data/fpl.db`.
* **Docs touched:** ADR-012 (new) + index, Architecture changelog, Sprint11 board.
* **Issues / Blockers:** None. (Data verified at planning; mechanism + caveat proven on
  real data.)
* **Next Steps:** US-038 — the `squad --full` command + 15-player display + help workflow.

#### Session 2 — 2026-08-02 (US-038: the `squad --full` command)
* **Completed:** `squad --full` picks the 15-man squad. **No optimiser change** — added
  `SQUAD_15`/`FULL_BUDGET` constants and a new *caller*: the handler passes
  `formation=SQUAD_15` and a mode-aware budget (a small pure `resolve_squad_budget`
  helper → £100m full / £80m XI; explicit `--budget` still wins). `render_squad(full=…)`
  names the mode and appends the ADR-012 caveat (the 15-total isn't a weekly score) +
  the `--include` bench workflow. `--help`/epilog, README, Handbook Ch20 + Ch22 updated;
  Backlog: full-squad **done**, flexible formations kept. **9 new tests** (full-squad
  selection, club cap, forced bench, budget resolver both modes, full-mode render +
  caveat, XI-has-no-caveat regression) → **123 total, all green**. US-038 **complete**.
* **Manual smoke test:** ✅ Matches the gate's worked example exactly — `squad --full`
  → £100.0m / 2606 pts / no cheap bench + caveat; `--full --include Dubravka Diop
  Hughes:CRY Kusi-Asare` → 4 forced (`*`), bench £17m, XI upgraded (B.Fernandes 235 now
  affordable) / 2241 pts; plain `squad` XI unchanged; `--help` shows `--full`. The
  `Hughes` disambiguation prompt fired correctly (two Hughes) — the resolver working.
* **Docs touched:** README, Handbook Ch20 + Ch22, Backlog, Sprint11 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 011 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories — US-037 (ADR-012, the full-squad decision) and US-038
  (`squad --full`). The optimiser now answers the *real* FPL question: the best 15
  (2/5/5/3, £100m, ≤3/club) for the chosen objective, with the bench chosen by the
  manager via `--include`. Tests grew 114 → **123**. **No optimiser code changed** and
  **no new dependency.**
* **Carried Forward:** None. Backlog now: flexible formations (deferred this sprint),
  FBref xG/xA, plus season-dependent FPL work.
* **Key Artifacts / Decisions:** ADR-012 (simple full-squad model; two-tier *rejected*;
  the "15-total isn't a weekly score" caveat recorded); `SQUAD_15`/`FULL_BUDGET`
  constants; `resolve_squad_budget()`; `render_squad(full=…)` caveat.

#### Retrospective
* **What Went Well?**
  - **The generic core paid a dividend three sprints late.** The 15-man squad needed
    *no* optimiser change — `select_squad` took `formation`+`budget` as parameters back
    in Sprint 007. The smallest feature in the project, precisely because of earlier
    discipline.
  - **The gate did its job.** Pressure-testing on real data *before* code both proved
    the `--include`-the-bench workflow and surfaced the honest caveat (the 15-total
    counts a non-scoring bench) — which then shaped the display.
  - **Tony's simpler model won.** He rejected the two-tier design in favour of "optimise
    the 15; the manager picks the bench via include" — simpler, and it puts human
    judgement where it belongs. The charter's "prefer simple" in action.
  - The 3-part DoD held for the 11th sprint; the smoke test matched the gate to the pound.
* **What Could Be Improved?**
  - `--full` with no includes returns an unrealistic all-premium 15 — mitigated by docs
    + the caveat, but a first-time user could still be briefly surprised.
  - The display shows all 15 as one list; it doesn't visually separate the manager's
    bench (only the `*` marks forced picks). Fine for now, a possible polish item.
* **Lessons Learned?**
  - Investing in a *generic core* early keeps paying off — later features become new
    callers, not new algorithms.
  - Intellectual honesty belongs *in the output*, not just the ADR — the caveat travels
    with the number so it can't mislead.
  - The simplest model that answers the question, plus an existing mechanism (`--include`)
    for the human's part, beats a cleverer model that does everything.
* **Action Items for Next Sprint (012):**
  - [ ] Consider: flexible formations (the natural pair to this sprint), FBref xG/xA, or
    season-dependent FPL work once it starts — check data first, as always.
  - [ ] Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

**Proposed follow-on (Sprint 012):** flexible formations for the XI (deferred from this
sprint), FBref xG/xA (player-level, spike-first), or data-dependent FPL work once the
season starts.

**Completion Date:** 2026-08-02
**Final Notes:** The optimiser reached the real FPL squad — and it was the *smallest*
build yet, because the generic core was already there. From Tony's backlog pick, and his
call to keep the model simple. Sprint outcome: **Successful** — 2/2 stories, zero
roll-over, DoD held.
