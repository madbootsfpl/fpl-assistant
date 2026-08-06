# Architectural Decision Record: Consistent number formatting in the web tables

**Decision ID:** ADR-072
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** new **display-only** convention. Adds a shared column-format layer over the
Streamlit tables (Pool ADR-057/063, stat boards ADR-063, squad tables Sprint 059, ratings ADR-071). No
analytics change. Triggered by tester request.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester feedback: *"Keep to xx.x — Value/£m shows 24.2345, prefer 24.2. Player cost to one decimal too:
6 should be 6.0 to keep the tables aligned."* The web tables don't pin decimals, so money/value columns
ragged: some cells show many decimals, some whole numbers show no decimal at all.

**Verified in code (real data):** `Val/£m` is `rank_players`' `value` — an **unrounded float** (e.g. Guéhi
`29.833333333333332`); and **299/572** prices are whole numbers (6.0, 8.0) that a mixed `st.dataframe`
column can render as `6`. So a money column can show `24.2345`, `5.5`, and `6` in three different shapes.
The **CLI** text tables already format to fixed decimals via their renderers, so `24.2345` cannot appear
there — this is a **web-only** problem. Affected surfaces: the **Pool**, the **four stat boards** (`_board`),
and the **squad tables** (`render_player_table`, used by Captain/Transfer/My Squad/…).

#### Decision Drivers
- **Aligned + scannable** — one shape per column (`6.0`, `24.2`), right-aligned.
- **Still numeric** — the column must stay sortable and keep its true value; formatting is *display*, not a
  round of the data.
- **One convention, one place** — the same rule everywhere, not per-table ad-hoc strings.
- **Right precision per metric** — money/% read best at 1dp; small expected-goal ratios need 2dp.

---

### ✅ Decision

**1. Format via `NumberColumn`, not pre-rounded strings.** `st.column_config.NumberColumn(label,
format="%.1f")` forces `6.0` / `24.2`, **right-aligns**, and keeps the column **numeric + sortable** — a
pre-formatted string would left-align and sort lexically ("10.0" < "9.0"). The underlying analytics value is
untouched (so sorting uses the real number; only the *display* is pinned).

**2. A shared convention module `src/web_streamlit/formats.py`.** A `FORMATS` map (`{column-label: printf}`)
encodes the policy once, plus `column_config(labels, *, help=None, images=…)` → a `{label: column-config}`
dict that returns a `NumberColumn` (with `format=` + optional `help=`) for a numeric label, an `ImageColumn`
for an image label, a plain `Column` for a text label that carries `help`, and nothing for other text
(default rendering). The **Pool**, `_board`, and `render_player_table` all build their `column_config`
through it — so the convention can't drift between tables and it composes with the ADR-071 tooltips.

**3. The decimal policy (owner's call).**
- **1 decimal** — money & rates: `£m` · `Val/£m` · `Own%` · `Form` · `ICT` · `xP` · `Actual` · `Exp` ·
  `DC/90` · `Thr`.
- **Integer** — counts: `Pts` · `Mins`.
- **2 decimals** — the expected-goals family: `xG` · `xA` · `xGI` · `xGC` · `xGC/90` (FPL-native precision;
  1dp would blur small ratios like 0.52 vs 0.55).
- **Signed 1 decimal (`%+.1f`)** — differences: `Diff` · `Margin` · `+xP`. The `_board` `Diff`/`Margin`
  cells move from a **pre-formatted string** back to the **raw number** so `NumberColumn` right-aligns them.

**4. Scope.** Web `st.dataframe` tables only. The CLI is unchanged (its renderers already align). No server
writes; analytics untouched.

---

### 🔀 Alternatives Considered

- **Round the values in the analytics** (e.g. `round(value, 1)`). Rejected — that corrupts the source number
  for everyone (CLI, sorting, xP math) to fix a display nit; formatting belongs at the display edge.
- **Pre-format each cell to a string** (`f"{v:.1f}"`). Rejected — left-aligns, and breaks numeric sorting
  (lexical order). `NumberColumn` gives alignment *and* correct sorting.
- **Strict 1dp everywhere** (incl. the xG family). Rejected by the owner — 1dp blurs the small xG/xGC values;
  the xG family keeps its 2dp.
- **Per-table inline column_config** (no shared module). Rejected — three tables would drift; one `FORMATS`
  map keeps them identical and is the single place to change the policy.

---

### 🧭 Consequences

**Positive**
- Every money/value/% column lines up (`6.0`, `24.2`); counts stay whole; the xG family keeps its precision.
- Columns remain numeric — sortable and truthful; the format is display-only.
- One convention module → no drift; composes with the ADR-071 tooltips (same `NumberColumn`).

**Negative / risks (mitigations)**
- **A new numeric column must be added to `FORMATS`** or it renders at the Streamlit default → a `formats`
  unit test + the visible convention make this obvious; an unlisted text column simply renders as-is.
- **`Diff`/`Margin` change from string to number** → the `+` sign is preserved via `format="%+.1f"`; a test
  pins the shape.
- **Mixed None/number columns** → `NumberColumn` renders blanks for `None`, unchanged behaviour.

---

### 📊 Validation

Verified: the offending value (`29.833333333333332`) and whole-number prices are real; `NumberColumn`
formats + right-aligns without touching the value. Acceptance: `FORMATS`/`column_config` return the right
config per column type (integer vs 1dp vs 2dp vs signed vs image vs text); the Pool shows `6.0` and `24.2`
(not `6` / `24.2345`) and xGI still `4.42`; the Pool, a stat board, and a squad table render through the
shared config with no crash; the analytics + existing 607 tests are unchanged (new tests added).
