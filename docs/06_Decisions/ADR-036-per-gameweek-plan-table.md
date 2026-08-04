# Architectural Decision Record: Per-gameweek transfer-plan table + a structured detail in `ask`

**Decision ID:** ADR-036
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Composes ADR-035 (plan) × ADR-032 (per-GW xP); extends ADR-034 (`ask`)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The multi-transfer plan (ADR-035) shows *which* transfers to make, but only a total gain — the owner
asked (Sprint-33 retro) for *"a table with a list of transferred-in players and points per week"*,
and noted the `ask` plan output is **prose only** (no structured table).

Both are a **composition of features we already have**: `player_xp` returns `by_gameweek` (ADR-032),
and the plan already names the incoming players (ADR-035). A planning probe joined them on the TS
5-plan:

```
In             GW1  GW2  GW3  GW4  GW5    xP
Benitez        7.0  6.3  7.0  7.7  7.0   35.0
Dasilva        5.3  5.3  5.8  5.3  4.8   26.6
...
```

Reads well; shows *when* each incoming player's points land. No new modelling.

#### Decision Drivers
- **Show the weekly shape**, not just a total.
- **Give `ask` the exact data** alongside the narration.
- **Reuse, don't re-model** — the plan engine and grounding contract stay untouched.

---

### 💡 Decisions

**1. Per-gameweek columns in the plan table.** `render_transfer_plan` gains **GW1…GWN** columns
showing the **incoming player's** per-GW xP (from `by_gameweek`, ADR-032), plus the gain. The Bank
column moves to the footer (with the total + caveats) to keep width reasonable. Each row keeps the
OUT for context. Applied to both surfaces (`transfer --count` and `ask`). Built on the shared
renderer (ADR-025) with dynamic GW columns, as `analyse`/`xp` already do.

**2. `ask` returns a *structured detail*.** The plan decision carries a **pre-rendered table**
(`detail`); `AskResult` gains a `detail: str | None`, and `render_ask` shows **headline → detail
(table) → narration (prose)**. This is a small evolution of the ADR-034 result shape — the LLM still
narrates only from the self-describing facts (unchanged); **the table is the exact truth, the prose
is the readable summary**. The coupling is minimal: the decision hands `render_ask` a finished string.

**3. Tighten the plan-narration prompt.** The 3B model echoes the instruction (*"Here is a summary…"*).
Adjust the prompt to suppress the preamble. Best-effort — the table is authoritative regardless.

**Not in scope:** new plan logic (ADR-035 unchanged); a general structured-output framework for every
intent; per-GW *actuals* (needs GW1 — Data Hardening); a bigger/cloud model.

---

### 🧪 Worked example (pressure-testing — real data, before code)

The TS 5-plan's incoming players with GW1–GW5 xP (Benitez 7.0/6.3/7.0/7.7/7.0 = 35.0; Dasilva
5.3/5.3/5.8/5.3/4.8 = 26.6; …) — a clean join of `by_gameweek` (ADR-032) and the plan's incoming
players (ADR-035). Confirms the table before code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** a manager sees the weekly shape of each incoming player; `ask` shows the exact data
  under the prose. Pure composition — the engine and grounding contract are untouched; no new dependency.
* **Negative / Trade-offs:** a wider table (per-GW columns) — narrow columns cope with the default
  5-GW horizon; a soft cap for larger N is a noted refinement. `ask` output is busier (table + prose)
  — but clearly separated and both useful.
* **Risks & Mitigations:**
  - *Wide table* → narrow GW columns; default 5.
  - *Coupling `ask` to a rendered detail* → the decision hands over a finished string; `render_ask`
    just prints it.
  - *Per-GW rounding vs total* → the known ADR-032 artifact; the total is authoritative; footnoted.

---

### 🛠 Implementation & Migration
* **Components Affected:** `src/ui/transfer.py` (per-GW columns in `render_transfer_plan`, threading
  `by_gameweek`); `cli.py` `cmd_transfer` (pass `by_gameweek`); `src/ask.py` (plan decision carries a
  rendered `detail`; a tighter prompt) + `src/ui/ask.py` (show `detail`); `AskResult` gains `detail`.
  The plan engine (`suggest_transfer_plan`) and `player_xp` are unchanged.
* **Action Items:**
  - [x] Record the composition + probe evidence (US-101)
  - [ ] Per-GW columns in `render_transfer_plan` + `transfer --count` (US-102)
  - [ ] `ask` carries + shows the `detail` table; tighten the prompt (US-103)
  - [ ] (Backlog) a soft cap / compact form for large horizons

---

### 🔄 Review & Reconsideration
* **Review Date:** If per-GW columns overflow in real use, or `ask` needs structured detail for more intents.
* **Triggers for Reconsideration:**
  - [ ] Large horizons overflow → a compact form / cap.
  - [ ] More intents want structured detail → a small shared detail-render helper.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-101 (this), US-102, US-103
- **External Docs:** [ADR-035 (plan)](./ADR-035-multi-transfer-plan.md) · [ADR-032 (per-GW xP)](./ADR-032-per-gameweek-xp.md) · [ADR-034 (`ask`)](./ADR-034-ask-command-grounded-nl.md) · [ADR-025 (shared renderer)](./ADR-025-shared-table-renderer.md) · [Sprint 034](../05_Sprints/Sprint34.md)
