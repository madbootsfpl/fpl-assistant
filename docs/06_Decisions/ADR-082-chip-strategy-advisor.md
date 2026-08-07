# Architectural Decision Record: Chip-strategy advisor (an assembler + a grounded intent)

**Decision ID:** ADR-082
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** new decision-support. Mirrors the **gameweek plan** (ADR-070): an *assembler*
over existing primitives, surfaced as a grounded, verified `ask` intent + a Squads view. Triggered by an owner
feature request (the "Chip Strategy Guidance" intake item, made buildable-now).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner request: *"AI advice on **when** to use **Wildcard · Free Hit · Bench Boost · Triple Captain** from your
squad, fixtures, and mini-league position."* Chip timing is a season-shaping decision the tool doesn't help
with yet.

**Verified in code (the live DB):** `decision_xp(..., horizon=N)` already returns each player's
**`by_gameweek`** = `{gw → xP}` (ADR-032; sums to the horizon total). So "which GW scores most" — for one
player (Triple Captain) or all 15 (Bench Boost) — is a **decomposition of numbers we already compute**, no new
analytics. `team_fdr`/`team_schedule` give the fixture-run framing (today's next-5 spread LIV 2.60 → FUL 3.60
is real). **No DGW/BGW preseason** (every GW has exactly 10 fixtures — checked) and **no stored deadline** (no
`events` table), so the v0 signal is **fixture-run + xP based**, framed honestly.

#### Decision Drivers
- **When, per chip** — a best GW (or window) for each of the four chips, from the squad's own projections.
- **Reuse, don't reinvent** — the per-GW xP (`by_gameweek`) + `best_legal_xi` already exist; this is an
  assembler (the ADR-070 shape), so the chip answer can't drift from the standalone tools.
- **Grounded + honest** — analytics decide, the LLM only narrates + is **verified** (ADR-037); a caption says
  what sharpens in-season (DGW/BGW) and at GW1 (mini-league position, live minutes/form).

---

### ✅ Decision

**1. A pure `chip_advisor` assembler (US-251).** `src/analytics/chips.py::chip_advisor(owned,
by_gameweek_by_id, gameweeks)` reduces the per-GW xP the caller already computed into one recommendation per
chip — each a **decomposition of `by_gameweek`** + `best_legal_xi`:

| Chip | Signal (per GW, over the squad's 15) | Best GW = |
|------|--------------------------------------|-----------|
| **Triple Captain** | the max **single starter's** GW xP (a starter in that GW's best legal XI) | argmax |
| **Bench Boost** | the **all-15** GW total (surface the bench's share) | argmax |
| **Free Hit** | the **best-legal-XI** GW xP | **argmin** (your weakest single week — a one-off cover) |
| **Wildcard** | the lowest **rolling window** of legal-XI xP (default 3 GW) | the weakest stretch → reset *before* it |

Pure (no I/O); unit-tested offline with a crafted `by_gameweek` that makes each chip's best GW deterministic.

**2. A grounded `chips` `ask`/`chat` intent (US-251).** `_decide_chips` reuses `_squad_xp` (the same horizon
xP the transfer/analyse/gameweek tools use), calls `chip_advisor`, and returns **self-describing facts** (chip
· GW/window · the value · the player) so the LLM narrates without inventing numbers; **verified** (✓/⚠). A new
`_INTENT_KEYWORDS["chips"]` entry placed so it **can't** hijack existing routes: it matches distinctive phrases
(`chip`/`chips`/`chip strategy`/`which chip`/`triple captain`/`free hit`/`use my bench boost`/`use my
wildcard`), **not** bare `bench boost` / `wildcard` (which stay with `build_squad` — `"build me a squad for a
bench boost"` must still build), and not bare `captain`/`bench`. A shared `src/ui/chips.py::render_chip_advice`
block (CLI + web reuse it).

**3. A Squads "Chips" view (US-252).** A **"Chips"** option on the Squads segmented control that routes through
`ask.answer(active_squad=…, horizon=…)` + `render_ask` (degrades to the plain advice without Ollama), using the
tab's *Gameweeks ahead* horizon; honest captions.

---

### 🔀 Alternatives Considered

- **A new per-chip scoring metric.** Rejected — the per-GW xP (`by_gameweek`) already ranks GWs; a reduction is
  enough and can't drift from the other tools.
- **DGW/BGW-driven timing** (the classic chip logic). Deferred — double/blank GWs are announced **in-season**;
  preseason every GW has 10 fixtures. The fixture-run + xP signal works now; DGW/BGW sharpens it later.
- **Mini-league-position input** (the owner asked for it). Deferred — needs the leagues API + per-manager picks,
  **public only from the GW1 deadline (2026-08-21)**. A later, gated enhancement.
- **A season-long (38-GW) scan.** Deferred — v0 uses the tab horizon (≤8); `decision_xp` over 38 GWs is heavy
  and preseason-flat. Enough to demo the shape now.
- **A standalone CLI `chips` command.** Deferred — surface via `ask` + the Squads view first (the ADR-070
  pattern); a command is a trivial later add.

---

### 🧭 Consequences

**Positive**
- Chip timing guidance from the squad's own projections, reusing the unified xP — no new metric, no drift.
- The assembler is pure → unit-tested offline; the intent is grounded + verified like every other.
- Degrades without Ollama (the block is the truth); no server writes.

**Negative / risks (mitigations)**
- **Preseason-flat fixtures** → the windows are close together now; a caption frames it as *guidance that
  sharpens in-season*. The mechanism (argmax/argmin over per-GW xP) is correct and lights up as fixtures spread.
- **No DGW/BGW / mini-league yet** → explicitly deferred + captioned; the honest scope is fixture-run + xP.
- **Routing collisions** (`triple captain` ⊃ "captain", `bench boost` ⊃ "bench", `wildcard` ∈ build) →
  handled by distinctive multi-word chip phrases + placement; a routing test pins the existing intents.

---

### 📊 Validation

Verified (live DB): `decision_xp(horizon=8)` returns `by_gameweek` per player summing to the total; `team_fdr`
gives a usable next-5 spread; every GW has 10 fixtures (no DGW/BGW); no `events` table. Acceptance: `chip_advisor`
picks the deterministic best GW for each chip on a crafted `by_gameweek` (TC = the ceiling GW, BB = the all-15
GW, FH = the weakest XI GW, WC = the weakest window); the `chips` intent is grounded + verified (every narrated
number is a fact) and routes on the chip phrases without breaking the `build_squad`/`captain`/`start_bench`
routing tests; the Squads "Chips" view renders + degrades without Ollama; `decision_xp`/the analytics + the
existing 647 tests are unchanged (new tests added).
