# Sprint 024: Shared Table Renderer (tech-debt closer)

**Dates:** 2026-08-03
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a pure refactor — output unchanged)
**Carried Over:** None (Sprint 023 closed clean; the build phase is feature-complete)

---

### 🔎 Verified at planning (per the standing lesson)

The duplication is real and the refactor is provably safe:

- **~271 lines across five renderers** — `table` (65), `xg` (49), `overperf` (61), `defcon`
  (49), `cleansheet` (47) — all build the *same* shape: a header line + a divider + rows of
  fixed-width, aligned columns. Only the **columns** differ (headers, widths, alignment, number
  formatting).
- **The output can be preserved exactly.** The one risk — that a generic "format the value, then
  pad to width" differs from the originals' combined specs (`{v:>6.1f}`) — was checked: for
  plain, negative, and **signed** (`+.1f`) numbers, `format(v, '.1f')` then `{s:>6}` is
  **byte-identical** to `{v:>6.1f}`. So the existing view tests will pin the refactor.

**No new dependency.** This sprint is Tony's Sprint 023 pick — the tech-debt capstone for a
feature-complete phase, leaving the code clean and the next view trivial to add.

---

### 🧭 Architecturally, what's new — a column spec instead of five copies

Every ranking view repeats the same three-part table by hand. We replace that with a tiny,
declarative renderer: a view *describes its columns*, and one helper builds the table.

```python
# src/ui/_table.py
class Col:  # header, width, align ("<" | ">"), fmt(row) -> str
    ...
def render_rows(rows, columns, rank=False) -> list[str]:
    "[header, divider, *row lines] — same output the views build by hand today."
```

A view then becomes its **title + `render_rows(rows, COLUMNS)` + footer note** — the columns
are data, not repeated f-strings. Widths/alignment/formatting live in the `Col` specs. Output
is **identical** (tests pin it); the win is ~5 near-duplicate loops collapse to one helper, and
the *next* ranking view (or a status flag added to all of them) is a one-line change.

**Scope: the five ranking views only.** The squad renderers (`render_squad` /
`render_loaded_squad`) are structurally different (position groups, bench sections, markers) and
stay as they are — a separate, smaller dedup left on the backlog.

---

### 🎯 Sprint Goal

**Objective:** Extract one shared table renderer (`Col` + `render_rows`) and migrate the five
ranking views to it — **with byte-identical output** — paying down ~271 lines of duplication and
making the next view trivial.

#### Success Criteria
- [ ] Approach agreed (**ADR-025**) before code
- [ ] `src/ui/_table.py` — a `Col` spec + `render_rows(rows, columns, rank=…)` returning
      `[header, divider, *rows]`, with its own unit tests
- [ ] `table`, `xg`, `overperf`, `defcon`, `cleansheet` migrated to it
- [ ] **Output is unchanged** — every existing view test passes untouched
- [ ] Titles/footers/section logic (e.g. `overperf`'s two ends) stay per-view
- [~] The **duplicated logic** is gone (each view shrank ~12%; padding written once, not 5×).
      _Raw line total is ~flat (271 → 298, +27): the well-documented shared module offsets the
      per-view savings. The win is maintainability, not fewer lines — recorded honestly._
- [ ] The squad renderers are left as-is (out of scope; noted)
- [ ] Tests: `render_rows` unit tests + all existing view tests green (offline)
- [ ] **Manual smoke test** — each view's real output eyeballed as unchanged (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-070 | Agree the shared-renderer design (**ADR-025**): the `Col` spec + `render_rows`, format-then-pad reproduces the originals exactly, scope = the 5 ranking views, output-preserving — pressure-test with a worked example | Critical | ✅ Done | 0.5 session |
| US-071 | Build `src/ui/_table.py` (`Col` + `render_rows`) with unit tests; migrate **table + xg** as proof (output unchanged; their tests green) | High | ✅ Done | 1 session |
| US-072 | Migrate **overperf + defcon + cleansheet** (incl. `overperf`'s two-section layout); confirm all view tests green + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-025 recorded + added to the ADR index — _US-070_
- [ ] Update Architecture doc (a shared UI renderer; changelog) — _US-070_
- [x] Update Handbook Ch 20 (CLIs) with the shared renderer (DRY + safe-refactor lesson) — _US-072_
- [x] Backlog: no formal Roadmap entry existed (it was tracked informally in Sprint 023's
      lessons); closed here by completing the work — _US-072_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for twenty-three sprints — a story isn't done until:
1. **Automated tests pass** (existing view tests **unchanged** — they pin the output).
2. **Manual smoke test done** — each view's real output eyeballed as identical to before.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, sprint board +
   PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A `Col` + `render_rows` shared renderer | The squad renderers (grouped/bench — different shape) |
| Migrate the 5 ranking views, output-identical | Any output/behaviour change (a pure refactor) |
| `overperf`'s two-section reuse of the helper | Adding new columns / availability flags (a follow-on) |
| Unit tests for the renderer | New views or metrics |

**External Dependencies:**
- [ ] None beyond stdlib; **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Subtle output change (spacing/format) | High | Verified format-then-pad == the originals; existing view tests pin every line; smoke-eyeball each |
| A view has a quirk the abstraction misses (`overperf` two ends, `table`'s "—") | Med | Keep titles/footers/sections per-view; the renderer does only the table body; specs carry the value fns |
| Over-abstracting | Low | Minimal `Col` (header/width/align/fmt) + one function — no config framework |
| Refactor churn touches many files | Med | Migrate 2 views first (US-071) as a checkpoint, then the rest (US-072); tests green at each step |

---

### 🗝️ Gating decision (US-070 → ADR-025)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **The abstraction.** `Col(header, width, align, fmt)` — `fmt(row)` returns the cell *string*;
   `render_rows(rows, columns, rank=…)` joins padded cells into a header, a divider, and rows.
   An optional leading `#` rank column.
2. **Output-preserving.** `format(v, '.1f')` then `{s:>W}` is byte-identical to `{v:>W.1f}`
   (verified for plain / negative / signed). So the migration changes no output.
3. **Scope.** The five ranking views. Titles, footers, and section logic (`overperf`'s
   over/under) stay in the view; the renderer builds only the table body. The squad renderers
   are out of scope.
4. **Verification.** Existing view tests are the safety net — they must pass **untouched**; a
   smoke test eyeballs each view.

**Worked example to verify at the gate:** define the `xg` columns as `Col` specs and show
`render_rows` produces the *exact* current `xg` header/divider/rows for a sample — proving the
abstraction reproduces a real view before migrating anything.

---

### 📝 Session Progress Log

- **US-070 (gate) ✅** — ADR-025 written. Pressure-tested a prototype `Col` + `render_rows`
  against the **real** xg/defcon/overperf functions — byte-identical across all three structural
  variants (incl. overperf's two-section/no-divider layout). Rejected a general table framework
  (keep widths explicit).
- **US-071 ✅** — Built `src/ui/_table.py` (`Col` + `render_rows(rows, columns, rank=, divider=)`);
  the seam is `fmt` formats / `render_rows` only pads. Migrated `table` + `xg`. Verified **byte-
  identical** vs a frozen baseline (4 cases: all/limit, incl. the ellipsis-vs-slice truncation
  quirk + the `—` fallback). Added 7 renderer unit tests. Suite **227 passed** (was 220); the
  table/xg tests passed **untouched**. Smoke-tested `table`/`xg` on live data — output unchanged.
- **US-072 ✅** — Migrated `overperf` (two sections, no divider, rank restarts each call),
  `defcon`, and `cleansheet`. Verified **byte-identical** vs a frozen baseline (9 cases: all /
  limit / **empty** for each). All 20 of their view tests passed **untouched**; full suite **227
  passed**. Smoke-tested all three on live data — output unchanged. **All five ranking views now
  share `ui/_table.py`.** Line-count noted honestly (duplication gone, raw total ~flat, +27).

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-070 (gate → ADR-025), US-071 (`ui/_table.py` + `table`/`xg`),
  US-072 (`overperf`/`defcon`/`cleansheet`). **All five ranking views now share one renderer** —
  a `Col` spec + `render_rows(rows, columns, rank=, divider=)`. A **pure refactor**: output is
  byte-identical (verified against frozen baselines; every existing view test passed **untouched**).
  Tests grew 220 → **227** (+7 renderer unit tests). No new dependency. *The last real duplication
  in a feature-complete build phase is paid down.*
* **Carried Forward:** None. Remaining backlog (all small): availability flags in the ranking
  views; a shared renderer for the *squad* views (`render_squad`/`render_loaded_squad` — a
  different shape, deliberately out of scope); combined defensive value; `xp` per-GW; PuLP 4.0.
* **Key Artifacts / Decisions:** ADR-025 (the `Col` + `render_rows` design; the *fmt-formats /
  render_rows-only-pads* seam; rejected a general table framework — keep widths explicit);
  `src/ui/_table.py`; `tests/test_table_renderer.py`.

#### Retrospective
* **What Went Well?**
  - **Provably output-preserving, not hopefully.** The risk was a single changed byte. It was
    retired *before* code: `format(v,'.1f')` then `{s:>6}` is byte-identical to `{v:>6.1f}`, and a
    prototype was diffed against the **real** xg/defcon/overperf at the gate. Then each migration
    was diffed against a frozen baseline (13 cases total, incl. every empty state).
  - **The right seam.** `fmt` produces the finished cell string; `render_rows` only pads. Every
    per-view quirk — table's ellipsis, cleansheet's `.2f`, overperf's signed `+.1f` and its
    two-section/no-divider layout — stayed in the view; the core carries none. Two flags
    (`rank`, `divider`) covered all the structural variation.
  - **Existing tests as the safety net.** All 28 view tests passed **unedited** — the definition
    of a clean refactor. A refactor that needs its tests changed isn't one.
  - DoD held (24th sprint): byte-diff + tests + live smoke on every view.
* **What Could Be Improved?**
  - **The line count didn't drop** (271 → 298, +27) — the well-documented shared module offsets
    the per-view savings. The *duplication* is gone and each view shrank ~12%, but "fewer lines"
    was the wrong success metric; "one place to change" is the real one. Recorded honestly rather
    than spun.
  - The squad renderers were left out (genuinely a different shape) — the smaller dedup noted in
    Sprint 023 is still open.
* **Lessons Learned?**
  - To refactor without fear: freeze a baseline, migrate, diff byte-for-byte, keep tests untouched.
  - Push the variation to the edge (a `fmt` per column) and the shared core stays trivial.
  - Measure the right thing: maintainability (one edit point), not raw line count.
* **Action Items for Next Sprint (025):**
  - [ ] The build phase is feature-complete and the tech debt is paid down — decide the next
        phase (web UI? a shared *squad* renderer? live/current-season data?) or pause. Check first.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down — 502s as of 2026-08-03).

---

**Proposed follow-on (Sprint 025):** the build phase is clean and feature-complete — either open a
new phase (e.g. a web view per ADR-002's long-term intent, or live current-season data) or take the
remaining small closers (availability flags in views, a shared squad renderer). Owner to steer.

**Completion Date:** 2026-08-03
**Final Notes:** A disciplined tech-debt closer — five near-duplicate renderers collapsed to one,
with output proven byte-identical and every test green untouched. Sprint outcome: **Successful** —
3/3 stories, zero roll-over, DoD held. The line-count non-win recorded honestly.
