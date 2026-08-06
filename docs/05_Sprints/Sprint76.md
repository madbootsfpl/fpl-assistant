# Sprint 076: Tech-debt sweep — PuLP API + squad renderer

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (refactors — behaviour/output preserved, pinned by existing tests)
**Carried Over:** none

> **Direction (owner):** clear the two standing tech-debt items — the PuLP 4.0 deprecations (currently
> blanket-suppressed) and the duplicated squad renderers.

---

### 🔎 Verified at planning (real behaviour — this re-scoped both items)

- **PuLP is 3.3.2**; the current code uses `LpVariable(...)` + `PULP_CBC_CMD` inside a blanket
  `warnings.simplefilter("ignore", DeprecationWarning)`. Two real deprecations fire:
  1. `LpVariable(name, …)` → *"use `prob.add_variable(name, …)`"* — **migrates cleanly** (`add_variable`
     exists in 3.3.2 and returns the variable).
  2. `PULP_CBC_CMD` → *"use `COIN_CMD`"* — but **`COIN_CMD` fails: "cannot execute cbc"** (it needs an
     external CBC binary; `PULP_CBC_CMD` bundles one). Switching would **break the optimiser + the Cloud
     deploy** unless we add a CBC dependency. → **Keep `PULP_CBC_CMD`.**
- **Squad renderer:** `ui/_table.py`'s `render_rows` is a flat, single-space-joined ranked table. The squad
  views have a **mid-table "Bench:" heading**, **trailing `**`/`*` markers glued without the join space**,
  and totals/notes — so folding them in **changes the bytes** (breaks the golden tests) for little gain.
  The two squad renderers also **legitimately differ** (`render_loaded_squad` prints an unpadded `£X.Xm`;
  `render_squad` pads price to 6). So: extract the genuinely-shared, byte-safe pieces; **don't** force
  `render_rows`.
- **Safety net:** 65 behavioural optimizer tests + 19 squad-render assertions pin behaviour + **byte output**.

---

### 🎯 Sprint Goal

**Objective:** reduce the debt honestly — migrate what's safe, keep what the naive migration would break,
and document the revised decisions — with **no behaviour or output change** (the tests are the proof).

#### Success Criteria
- [ ] Approach agreed (**ADR-066**) — migrate `LpVariable` → `add_variable`; **keep `PULP_CBC_CMD`**
      (COIN_CMD needs external CBC — verified); replace the blanket DeprecationWarning ignore with a
      **targeted** suppression of just the `PULP_CBC_CMD` notice; a shared squad header/divider helper
      (not `render_rows` — documented why); backlog updated
- [x] **US-211 (PuLP tidy)** — `problem.add_variable(...)` for `pick`/`start`; the blanket
      `simplefilter("ignore", DeprecationWarning)` → `filterwarnings("ignore", message=".*PULP_CBC_CMD.*")`
      (so other deprecations surface); optimiser results **identical** (65 tests green, no warning leak)
- [x] **US-212 (squad renderer de-dup)** — extracted the shared **header** builder + the **"Bench:"
      section-heading** used by `render_squad` + `render_loaded_squad`; **byte-identical output** (the 19
      render assertions pin it); the divider/rows stay per-renderer; `render_rows` fold **closed with a
      rationale** in the Backlog
- [x] **No behaviour/output change** — existing **580** stay green; ruff clean
- [ ] Docs: ADR-066 + index ✅, Backlog ✅; Architecture, PROJECT_STATUS _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-211 | **PuLP API tidy** — `LpVariable`→`add_variable`; keep `PULP_CBC_CMD` (COIN_CMD needs external CBC); narrow the warning suppression to the one remaining deprecation. ADR-066. | High | ✅ Done | ~½ session |
| US-212 | **Squad renderer de-dup** — a shared header + bench-heading for `render_squad`/`render_loaded_squad` (byte-identical); close the `render_rows`-fold idea with a rationale. ADR-066. | Medium | ✅ Done | ~½ session |

---

### 🧭 Design sketch (to settle in ADR-066)

**US-211.** In `optimizer.py`: `pick = {id: problem.add_variable(f"pick_{id}", cat="Binary") …}` (same for
`start`) — `add_variable` registers the var with the problem and returns it, so the constraint/objective
code is unchanged. Keep `problem.solve(pulp.PULP_CBC_CMD(msg=False))`. Replace
`warnings.simplefilter("ignore", DeprecationWarning)` with
`warnings.filterwarnings("ignore", message=".*PULP_CBC_CMD.*", category=DeprecationWarning)` — a **targeted**
suppression, with a comment: COIN_CMD needs a separate CBC (`pip install pulp[cbc]`) so we keep the bundled
solver; the narrow filter means any *other* future deprecation isn't hidden.

**US-212.** In `ui/squad.py`, extract `_header(value_head)` + `_divider(value_rule)` (the Pos/Player/Team/
Price + value header, identical in both) and a tiny `_bench_heading` insert; both renderers call them. The
**row bodies stay per-renderer** (their price/value layouts genuinely differ — changing either would alter
CLI output). Add a one-line note in `docs/Backlog.md`: the `render_rows` fold is **not pursued** (shape
mismatch — mid-table heading, glued markers, divergent price cells; would change bytes for little gain).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the 65 optimizer tests (behaviour) + the 19 squad-render assertions (byte output) stay
   green **unchanged**; a quick check confirms no `DeprecationWarning` leaks from a squad build except the
   (targeted-suppressed) PULP_CBC_CMD one. Existing **580** stay green; ruff clean.
2. **Manual smoke** — `python app.py squad --full` and `--load` render exactly as before; a build runs with
   no visible deprecation noise.
3. **Docs updated** — ADR-066 + index, Architecture, PROJECT_STATUS, Backlog (both items closed).

---

### 📝 Session Progress Log

- **US-211 ✅ (gate + build)** — Recorded **ADR-066** (+ index; covers US-212). In `optimizer.py`: `pick`
  and `start` now use `problem.add_variable(f"…", cat="Binary")` (silences the `LpVariable` deprecation).
  **Kept `PULP_CBC_CMD`** — `COIN_CMD` fails ("cannot execute cbc", needs an external CBC) so the bundled
  solver stays. Replaced the blanket `warnings.simplefilter("ignore", DeprecationWarning)` with a
  **targeted** `filterwarnings("ignore", message=".*PULP_CBC_CMD.*", …)` (so any *other* future deprecation
  surfaces). Optimiser results **identical** — the 65 behavioural optimizer tests pass **unchanged**; 580
  green, ruff clean. **Smoke (real DB):** a 15-man build is Optimal (£100.0m, 15 picked) with **no
  DeprecationWarning leaking** to the caller; `squad --full` renders normally. _US-212 (squad renderer
  de-dup) next._

- **US-212 ✅ (build)** — In `ui/squad.py`, extracted the byte-safe shared pieces: `_header(value_head)`
  (the Pos/Player/Team/Price + value column header, identical in both renderers) and `_BENCH_HEADING`
  (the `["", "Bench:"]` insert). `render_squad` and `render_loaded_squad` now call them; their **dividers
  and row bodies stay per-renderer** (they legitimately differ — a solid rule vs per-column dashes; an
  unpadded `£X.Xm` vs a width-6 padded price). **Closed the `render_rows` fold** with a rationale in
  `docs/Backlog.md`: its flat single-space join can't reproduce the mid-table "Bench:" heading, the glued
  `**`/`*` markers, or the divergent price cells byte-for-byte. **Output byte-identical** — the 77
  optimizer + analyse tests (incl. the 19 render assertions) pass **unchanged**; 580 green, ruff clean. No
  behaviour/output change.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — both tech-debt items cleared with **zero behaviour or output change** (the 65
optimizer + 19 render assertions passed unchanged throughout). The real value was **verifying before
migrating**: the naive backlog versions would each have caused harm.

**What went well** — probing the actual behaviour re-scoped the sprint honestly: `COIN_CMD` fails ("cannot
execute cbc"), so keeping the bundled `PULP_CBC_CMD` avoided breaking the optimiser + the Cloud; and
`render_rows` can't reproduce the squad layout byte-for-byte, so we shared only the safe pieces. Narrowing
the blanket `DeprecationWarning` ignore to a targeted filter is a genuine improvement — future deprecations
now surface instead of being hidden.

**What to watch / lessons** — "tech debt" phrased in a backlog can be **over-stated**: the migration target
(`COIN_CMD`) wasn't viable, and the "shared renderer" was smaller + more divergent than it read. The
disciplined move was to migrate what's safe, **keep** what a naive change would break, and **document the
close** (in the Backlog + ADR-066) rather than force a fit. `PULP_CBC_CMD` stays deprecated-but-bundled —
revisit only when `pulp[cbc]` / PuLP 4.0 packaging settles.

**Lessons captured:** `docs/05_Sprints/Sprint76_Lessons_Learnt.md`.
