# Architectural Decision Record: Shared table renderer (`Col` + `render_rows`)

**Decision ID:** ADR-025
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (a pure refactor; no behaviour change)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Five ranking views — `table`, `xg`, `overperf`, `defcon`, `cleansheet` — each hand-build the
**same** three-part console table: a header line, a `---` divider, then rows of fixed-width,
aligned cells. That's ~271 lines with the padding/alignment logic copied five times. Adding a
sixth view, or a column to all of them (e.g. an availability flag), means editing five files the
same way.

This is the last real duplication in a feature-complete build phase, and Tony's chosen Sprint 024
closer. The task is a **pure refactor**: extract the shared shape **without changing a single byte
of output** — the existing view tests are the safety net.

Reading the five files (not memory) surfaced the quirks any abstraction must survive or it will
silently change output:

- **No divider** — `overperf` prints header→rows with no `---` line.
- **Two sections, rank restarting at 1** — `overperf` shows over- and under-performers.
- **Truncation differs** — `table` truncates names/teams with an ellipsis (`…`); the others
  plain-slice (`str(x)[:W]`).
- **Number formats vary** — `.1f`, `.2f`, `+.1f` (signed), `£{}m`, plain int, and a `—` fallback.
- **Widths vary** — name is 17 (table/xg) vs 16 (overperf/defcon/cleansheet); the number column
  is 6, 7, or 8.

#### Decision Drivers
- **Output must be byte-identical** — tests pin every line; no test should need editing.
- **Keep it simple** (Charter) — five fixed-width console tables, not a general table framework.
- **Absorb the quirks at the edge** — the shared core stays dumb; each view keeps its own idioms.

---

### 💡 Decisions

**1. A column spec + one renderer, in `src/ui/_table.py`.**

```python
class Col:            # header, width, align ("<" | ">"), fmt(row) -> str
def render_rows(rows, columns, *, rank=False, divider=True) -> list[str]
    # returns [header, (divider), *row lines]
```

A view declares its columns as **data** and calls `render_rows`; its **title and footer stay in
the view**.

**2. The seam that makes it safe — `fmt` formats, `render_rows` only pads.** Each column's
`fmt(row)` returns the *finished* cell string — including any truncation and any number format.
`render_rows` does nothing but pad each string to its column width and join with a single space.
It **never truncates and never formats numbers.** So every per-view quirk (table's ellipsis,
cleansheet's `.2f`, overperf's `+.1f`) lives in that view's `Col` specs, and the core carries none
of them.

Why this is output-preserving: the originals combine format-and-pad in one spec, e.g.
`f"{v:>6.1f}"`. Formatting first and padding after — `f"{format(v, '.1f'):>6}"` — is
**byte-identical** for plain, negative, and signed numbers (verified). So splitting the two steps
changes nothing.

**3. `rank` and `divider` are flags, not special views.** `rank=True` prepends a left-aligned `#`
column (width 3) whose value is the 1-based row index — and it **restarts at 1 on each call**, so
`overperf` gets correct numbering by calling `render_rows` once per section. `divider=False` omits
the `---` line, which is how `overperf` renders.

**4. Scope: the five ranking views only.** The squad renderers (`render_squad` /
`render_loaded_squad`) are a different shape (position groups, bench sections, in-line markers) and
are **out of scope** — a separate, smaller dedup left on the backlog.

**Rejected alternative — a general table framework** (auto-computed widths, borders, wrapping,
config objects). Over-engineered for five small fixed-width tables; it would add complexity the
Charter tells us to avoid, and risk output drift (auto-width ≠ the hand-tuned constants). We keep
the widths explicit in the specs.

---

### 🧪 Worked example (pressure-testing — run against the real renderers)

Before approving, a prototype `Col` + `render_rows` was run against the **real** view functions and
compared byte-for-byte, covering all three *structural* variants:

| View | What it stress-tests | Result |
|---|---|---|
| `xg` | `None → 0.0` coercion; a name overflowing 17 chars; four `.1f` columns | **byte-identical** |
| `defcon` | signed `+.1f` Margin; integer `Thr`; name width 16 | **byte-identical** |
| `overperf` | **two sections, no divider, rank restarting at 1**; signed Diff | **byte-identical** |

`table` (ellipsis truncation) and `cleansheet` (`.2f`, width 8) ride the same seam — a different
`fmt` and different `Col` params — and are proven in build by keeping their tests green untouched.

This confirms the abstraction reproduces every quirk *before* any production code was migrated.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** ~271 lines of near-duplicate rendering collapse to one small helper + thin per-view
  specs. A new ranking view, or a column added to all of them, becomes a one-line change. Output is
  unchanged (tests pin it). No new dependency.
* **Negative / Trade-offs:** one more indirection to read (a view's shape is now "its column specs"
  rather than an inline f-string). Accepted — the specs are declarative and short.
* **Risks & Mitigations:**
  - *A subtly different byte breaks output* → format-then-pad proven identical; existing view tests
    pin every line; smoke-eyeball each view during migration.
  - *A view quirk the core doesn't cover* → the `fmt` seam keeps quirks in the view; `rank` /
    `divider` flags cover the structural variants (proven).
  - *Scope creep into the squad renderers* → explicitly out of scope; left on the backlog.

---

### 🛠 Implementation & Migration
* **Components Affected:** a new `src/ui/_table.py` (`Col` + `render_rows`); the five view modules
  (`table`, `xg`, `overperf`, `defcon`, `cleansheet`) migrated to use it. Analytics, CLI, storage,
  and the squad renderers are **untouched**. Existing view tests should pass **unedited**.
* **Action Items:**
  - [x] Record the design + worked example (US-070)
  - [ ] Build `src/ui/_table.py` (`Col` + `render_rows`) + unit tests; migrate `table` + `xg` (US-071)
  - [ ] Migrate `overperf` + `defcon` + `cleansheet` (incl. the two-section layout) (US-072)
  - [ ] (Backlog) a shared renderer for the squad views; availability flags in the ranking views

---

### 🔄 Review & Reconsideration
* **Review Date:** If a view needs something the spec can't express (multi-line cells, colour,
  variable widths).
* **Triggers for Reconsideration:**
  - [ ] A view needs auto-computed widths or wrapping → revisit the "keep widths explicit" stance.
  - [ ] The squad renderers are folded in → the spec may need groups/section support.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-070 (this), US-071, US-072
- **External Docs:** [ADR-002 (UI approach)](./ADR-002-ui-approach.md) · [ADR-003 (CLI)](./ADR-003-cli-approach.md) · [Sprint 024](../05_Sprints/Sprint24.md)
