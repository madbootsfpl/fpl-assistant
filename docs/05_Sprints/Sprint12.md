# Sprint 012: A Declared Bench (`--bench`)

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~2 working sessions (a display + annotation extension of the optimiser)
**Carried Over:** None (Sprint 011 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

Data is unchanged since Sprint 011's check (same season, preseason). The relevant facts
for a *bench* feature — cheap players exist in every position to bench:

- **Cheapest by position:** GK £4.0m · DEF £4.0m · MID £4.5m · FWD £4.5m.
- 564 players; cheapest legal 15-man squad £64.0m (verified Sprint 011).

**No new data or dependency** — this is CLI + display + result-annotation on data already
stored. Still blocked (preseason): `form`, attack/defence strengths.

This sprint is **Tony's own idea**, from the Sprint 011 reflection: *"rather than using
include we should use bench and name 1–4 players you want in there, double-`*` them and
sort to the end of the list … managers may want 2–3 players always benched unless using a
wildcard. This adds better/clearer visibility."*

---

### 🧭 Architecturally, what's new — the manager *declares* the bench

In Sprint 011 the full squad reused `--include` for cheap bench fodder — but `--include`
doesn't *say* "this is my bench". All 15 render as one list, and the points total counts
players who won't start. This sprint adds a **dedicated `--bench`** so the bench is
explicit:

```
squad --full --bench Dubravka Diop     → forces those players into the 15 AND
                                          tags them as bench: marked **, sorted to
                                          the bottom under a "Bench" heading
```

The important design point (the recurring lesson): **the optimiser barely changes.** A
benched player is forced into the squad exactly as `--include` does (`pick == 1`) — the
*only* additions are a **bench tag** on the result, a **`**` marker**, and **sorting the
bench to the end**. It's annotation + display, not new optimisation.

**And it makes the number honest.** Because the manager now declares the bench, we know
which players are the *starters* — so we can show a **starters' points subtotal**
alongside the squad total. That directly answers the ADR-012 caveat ("the 15-total counts
a non-scoring bench"): the starters' subtotal *is* a fair weekly proxy.

**Why not just keep using `--include`?** `--include` means "own this player" (starter or
bench, we can't tell). `--bench` means "own this player *and* sit them" — a different
intent that earns a different marker, a different place in the list, and a more honest
total. Same forcing mechanism underneath; clearer meaning on top.

---

### 🎯 Sprint Goal

**Objective:** Let the manager **declare a bench** — `squad --full --bench <1–4 players>`
— so the full squad renders as a clear **starters + bench** view (bench marked `**`,
sorted to the end), with a **starters' points subtotal** that finally means "weekly".

#### Success Criteria
- [x] `--bench` design agreed (**ADR-013**) before feature code
- [x] `squad --full --bench A B` forces A/B into the 15 and tags them bench
- [x] Benched players are marked **`**`** and **sorted to the end** under a "Bench" heading
- [x] The output shows a **starters' subtotal** (non-bench points) beside the squad total
- [x] `--bench` **implies `--full`** (a bench is a 15-man concept; an XI has none)
- [x] At most **4** bench players (a 15-man squad has 4 bench slots) — else a clear error
- [x] Conflicts are caught — bench ∩ exclude, bench ∩ include → clear message, no crash
- [x] `--bench` composes with `--objective`, `--budget`, `--include`, `--exclude`
- [x] Existing `squad` / `squad --full` output is unchanged when `--bench` is absent
- [x] Tests cover the tag, the `**`/sort, the cap, and the conflicts (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-040 | Agree the `--bench` design (**ADR-013**): force-in + bench tag + `**` + sort-to-end; implies `--full`; cap 4; conflict rules; **starters' subtotal** + refined caveat; display format — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-041 | Implement `--bench`: CLI flag + resolve/validate (cap 4, conflicts, implies `--full`); `select_squad` tags bench (`bench_ids`); `render_squad` shows the Bench section + `**` + starters' subtotal. Tests + smoke test | High | ✅ Complete | 1–1.5 session |

#### Technical Tasks & Maintenance
- [ ] ADR-013 recorded + added to the ADR index — _US-040_
- [ ] Update Architecture doc (declared-bench note + changelog) — _US-040_
- [ ] Update `README.md` + `--help` with `--bench` — _US-041_
- [ ] Handbook Ch 22 (Optimisation) — add the declared-bench section — _US-041_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for eleven sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| `--bench` names 1–4 players; forces them in + tags bench | Auto-*choosing* the bench for the user (that's the rejected two-tier model) |
| `**` marker + sort to the end under "Bench" | Bench *order* (who subs on first) |
| Starters' points subtotal | Captain / vice / chip / wildcard logic |
| Implies `--full`; composes with the rest | Persisting a bench across runs / saved squads |

**External Dependencies:**
- [ ] Existing players data + PuLP; no new data or dependency (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| `--bench` silently implying `--full` surprises a user | Med | Documented; the output header says "15-man squad", so the mode is visible |
| `**` vs `*` markers confuse | Low | A clear legend line ("`**` = benched, `*` = forced in"); only show each if used |
| Starters' subtotal misleads when < 4 are benched | Med | Label it by count ("Starters (13)…"); note it's a true XI only at a full 4-man bench |
| Sort change alters existing `--full` order | Low | Bench sort only applies to tagged players; with no bench the order is unchanged (a regression test pins it) |
| Naming > 4, or a benched player also excluded | Low | Validate up front (cap 4; conflict checks) → clear error, no solve |

---

### 🗝️ Gating decision (US-040 → ADR-013)

Settle before building — **pressure-test with a worked example** (per the standing
lesson). Proposed answers (Tony to confirm/redirect):

1. **Mechanism.** A benched player is forced into the 15 (`pick == 1`, exactly like
   `--include`); `select_squad` gains a `bench_ids` set and tags each result row
   `bench=True`. No new constraint, no objective change.
2. **Marker & order.** Bench rows are marked `**` and sorted **after** all starters,
   under a "Bench" heading. `--include` starters keep `*`. A row is one or the other.
3. **Implies `--full`.** `--bench` turns on the 15-man squad automatically (an XI has no
   bench). `full = args.full or bool(args.bench)`.
4. **Cap 4.** A 15-man squad has 15 − 11 = 4 bench slots; naming > 4 is an error.
5. **Conflicts.** bench ∩ exclude and bench ∩ include are errors (reuse the resolver +
   the existing conflict pattern).
6. **Starters' subtotal & caveat.** Show squad total (all 15) **and** starters' subtotal
   (non-bench). When exactly 4 are benched, the subtotal is the true starting-XI points
   (soften the caveat); otherwise keep the caveat and label the subtotal by count.
7. **Display.** Starters grouped by position (as today) → "Bench" divider → bench rows;
   totals + subtotal + a marker legend.

**Worked example to verify at the gate:** on real data, `squad --full --bench <cheap GK>
<cheap DEF>` should force those two to the bottom marked `**`, leave the other 13 as
starters, and print a starters' subtotal below the squad total — confirming the tag,
the sort, and the honest number *before* the command is written.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-02 (US-040: ADR-013 — the declared-bench design)
* **Completed:** Recorded **ADR-013**: `--bench` forces named players into the 15 (like
  `--include`) but tags them `bench`, marks them `**`, and sorts them to the end under a
  "Bench" heading; implies `--full`; cap 4; bench ∩ include/exclude are errors. Knowing
  the bench yields a **starters' subtotal** (labelled by count; a true XI only at a full
  4-man bench) — answering the ADR-012 caveat. **Pressure-tested on real data before
  writing:** declared Dubravka + Diop → forced in, `**`, sorted to the bottom; 13
  starters at 2337 pts vs squad 2464 pts (15). Added to the ADR index; Architecture §12
  changelog note. US-040 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the
  verification — run live against `data/fpl.db`.
* **Docs touched:** ADR-013 (new) + index, Architecture changelog, Sprint12 board.
* **Issues / Blockers:** None. (Data unchanged since Sprint 011; mechanism proven live.)
* **Next Steps:** US-041 — the `--bench` CLI + `select_squad` tag + `render_squad` section.

#### Session 2 — 2026-08-02 (US-041: the `--bench` command)
* **Completed:** `squad --bench` declares a bench. **No optimiser model change** —
  `select_squad` gained a `bench_ids` set (forced in via `include_set | bench_set`), a
  `bench=True` tag per row, and `bench` as the primary sort key (bench rows to the end;
  constant-False with no bench, so existing order is unchanged). CLI: `--bench` flag; a
  pure `validate_bench()` (cap 4 + bench∩include / bench∩exclude); `full = args.full or
  bool(args.bench)` (implies `--full`). `render_squad`: a "Bench:" heading, `**` marker,
  a **starters' subtotal**, a marker legend, and the ADR-013 caveat (softened to
  "Starters (11) is your XI" at a full 4-man bench). Docs: `--help`/epilog, README,
  Handbook Ch20 + Ch22. **+11 tests → 134 total, all green.** US-041 **complete**.
* **Manual smoke test:** ✅ `squad --bench Dubravka Diop` (implies `--full`) → 13
  starters + a "Bench:" section, `**`, `Starters (13): 2337 pts`; a full 4-man bench →
  `Starters (11): 2063 pts` "is your XI"; 5 valid names → cap-4 error; `--include Raya
  --bench Raya` and `--bench X --exclude X` → clear conflict errors; plain `squad` XI
  unchanged (no bench section); `--help` shows `--bench`.
* **Docs touched:** README, Handbook Ch20 + Ch22, Sprint12 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 012 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories — US-040 (ADR-013, the declared-bench design) and US-041
  (`squad --bench`). The manager can now declare a bench (1–4 players, marked `**`,
  sorted to the end), and the output shows a **starters' points subtotal** — the honest
  weekly number. Tests grew 123 → **134**. **No optimiser model change**, no new
  dependency.
* **Carried Forward:** None. Backlog: flexible formations, bench *order*, a saved squad,
  FBref xG/xA, plus season-dependent FPL work.
* **Key Artifacts / Decisions:** ADR-013 (declared bench; force-in + tag + `**`/sort;
  implies `--full`; cap 4; starters' subtotal by count); `select_squad(bench_ids=…)`;
  pure `validate_bench()`; `render_squad` bench section + subtotal.

#### Retrospective
* **What Went Well?**
  - **Tony's idea drove the sprint** — the whole feature came from his Sprint 011
    reflection, and it landed almost exactly as he sketched it (`**`, sort to the end,
    1–4 named). The retro loop is now genuinely steering the roadmap.
  - **Visibility and honesty turned out to be one fix.** Declaring the bench gave the
    clearer view *and* let the points total stop lying (the starters' subtotal answers
    ADR-012's caveat). A rare two-birds result.
  - **The pattern held a third straight sprint** — benching reuses the forcing logic;
    the new work was a tag, a marker, a sort key, and a subtotal. Core untouched.
  - The gate proved the tag/sort/subtotal on real data before code; the 3-part DoD held
    (12th sprint); the smoke test covered every path incl. the error cases.
* **What Could Be Improved?**
  - `--bench` silently enabling `--full` is convenient but implicit — fine here (the
    header shows the mode), but worth watching as flags accumulate.
  - Two forcing mechanisms now exist (`--include`, `--bench`) — clear in intent, but the
    squad command's surface is growing; a future tidy-up may help.
* **Lessons Learned?**
  - A good retro reflection *is* the next sprint plan — capturing the "why" in the
    manager's words made the build straightforward.
  - Intellectual honesty can be an *output*, not just a caveat — showing the starters'
    subtotal beats apologising for the squad total.
  - Extracting a pure helper (`validate_bench`) keeps DB-bound handlers testable — the
    same move as `resolve_squad_budget`.
* **Action Items for Next Sprint (013):**
  - [ ] Consider: flexible formations, bench order / a saved squad, FBref xG/xA, or
    season-dependent FPL work once it starts — check data first, as always.
  - [ ] Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

**Proposed follow-on (Sprint 013):** flexible formations for the XI, bench *order* or a
saved/persistent squad, FBref xG/xA (spike-first), or data-dependent FPL work once the
season starts.

**Completion Date:** 2026-08-02
**Final Notes:** The bench became explicit — clearer to read, and honest about what
scores. Straight from Tony's Sprint 011 reflection. Sprint outcome: **Successful** — 2/2
stories, zero roll-over, DoD held.
