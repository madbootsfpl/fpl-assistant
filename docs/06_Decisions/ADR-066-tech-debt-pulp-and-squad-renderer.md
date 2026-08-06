# Architectural Decision Record: Tech-debt — PuLP API + squad renderer

**Decision ID:** ADR-066
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** revises two Backlog "tech debt" items in light of real behaviour — the naive
"migrate to the PuLP 4.0 API" and "fold the squad renderers into `render_rows`". No behaviour/output change.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Two standing tech-debt items: (1) `optimizer.py` uses PuLP's `LpVariable` + `PULP_CBC_CMD` inside a blanket
`warnings.simplefilter("ignore", DeprecationWarning)`; (2) `render_squad` / `render_loaded_squad` hand-format
similar console tables while the ranking views share `ui/_table.py`.

**Verified on real behaviour (PuLP 3.3.2):**
- `LpVariable(name, …)` deprecates → **`prob.add_variable(name, …)` works cleanly** (returns the variable,
  registers it with the problem).
- `PULP_CBC_CMD` deprecates → *"use `COIN_CMD`"* — but **`COIN_CMD` fails: "cannot execute cbc"** (it needs
  an external CBC binary; `PULP_CBC_CMD` bundles one). Switching would break the optimiser and the read-only
  **Cloud deploy** unless a CBC dependency is added.
- `render_rows` is a flat, single-space-joined ranked table; the squad views have a **mid-table "Bench:"
  heading**, **`**`/`*` markers glued without the join space**, and totals/notes — folding them in **changes
  the bytes**. The two squad renderers also **legitimately differ** (`render_loaded_squad` prints an
  unpadded `£X.Xm`; `render_squad` pads price to width 6).

#### Decision Drivers
- **Do no harm** — a refactor must not change behaviour or CLI output (tests pin both).
- **Don't hide real warnings** — a blanket ignore can mask *future* deprecations.
- **Simplicity over churn** — migrate what's clean; don't force a fit that costs bytes for little gain.

---

### ✅ Decision

**1. PuLP: migrate variables, keep the bundled solver (US-211).** `pick`/`start` are created with
`problem.add_variable(f"…", cat="Binary")` (silences the `LpVariable` deprecation). **Keep
`PULP_CBC_CMD`** — `COIN_CMD` needs an external CBC (`pip install pulp[cbc]`) and fails here, so the bundled
solver stays (works locally + on the Cloud). Replace the blanket
`warnings.simplefilter("ignore", DeprecationWarning)` with a **targeted**
`warnings.filterwarnings("ignore", message=".*PULP_CBC_CMD.*", category=DeprecationWarning)` inside the same
`catch_warnings()` scope — so the one accepted notice is silenced and any *other* future deprecation
surfaces. Optimiser results are **identical** (65 behavioural tests pin them).

**2. Squad renderer: share the byte-safe pieces, don't force `render_rows` (US-212).** Extract the shared
**header/divider** builder (identical Pos/Player/Team/Price + value header in both) and the **"Bench:"**
section-heading; both `render_squad` and `render_loaded_squad` call them. The **row bodies stay
per-renderer** — their price/value cell layouts genuinely differ, and changing either would alter CLI
output. **The `render_rows` fold is not pursued** (documented in the Backlog): its flat single-space join
can't reproduce the mid-table heading, the glued markers, or the divergent price cells byte-for-byte.

---

### 🔀 Alternatives Considered

- **Switch to `COIN_CMD`** (the deprecation's suggestion). Rejected — it can't find CBC here; would need a
  new CBC dependency and risks the Cloud deploy, for no functional gain (the bundled CBC solves fine).
- **Keep the blanket `DeprecationWarning` ignore.** Rejected — it hides *any* future deprecation; a targeted
  filter keeps the codebase honest.
- **Fold the squad renderers into `render_rows`.** Rejected — not byte-identical-feasible (heading/markers/
  price divergence); would either change output or need so many knobs it stops being a shared renderer.
- **Unify the two squad row layouts (accept a cosmetic output change).** Rejected — `squad --load`'s output
  would visibly shift; not worth it for a refactor.

---

### 🧭 Consequences

**Positive**
- The `LpVariable` deprecation is gone; the remaining one is **narrowly** suppressed (future deprecations
  now surface).
- The squad renderers share their header/divider/bench-heading — less duplication, same bytes.
- Zero behaviour/output change; the Cloud solver is untouched.

**Negative / risks (mitigations)**
- **`PULP_CBC_CMD` is still deprecated** → accepted + documented; revisit if/when we adopt `pulp[cbc]` or
  PuLP 4.0 actually lands and CBC packaging settles. The targeted filter keeps it quiet meanwhile.
- **The row bodies stay duplicated-ish** → a conscious call (their layouts differ); the shared header/
  divider captures the safe win, and the Backlog records why the rest isn't pursued.

---

### 📊 Validation

Verified: `add_variable` returns a usable var; `COIN_CMD` raises "cannot execute cbc"; `render_rows` can't
reproduce the squad layout byte-for-byte. Acceptance: `optimizer.py` uses `add_variable` + keeps
`PULP_CBC_CMD` with a targeted filter; the 65 optimizer tests pass **unchanged** (identical picks); the
squad renderers share the header/divider/bench-heading with the 19 render assertions passing **unchanged**
(byte-identical); no `DeprecationWarning` leaks from a build except the targeted PULP_CBC_CMD one; the
existing 580 tests stay green.
