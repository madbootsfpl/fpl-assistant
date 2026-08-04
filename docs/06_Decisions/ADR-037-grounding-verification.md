# Architectural Decision Record: Grounding verification (prove the narration is faithful)

**Decision ID:** ADR-037
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Extends ADR-034 (`ask`) — closes the grounding loop
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Phase 4's thesis is **the analytics decide; the LLM only narrates** — the honest, transparent
counterpart to a black-box AI companion. But today `ask` only *instructs* the model not to invent
numbers; it doesn't *verify* it. The owner chose to deepen the **trust**: check the narration against
the facts and show the result, so grounding is **provable and visible**, not just promised.

A planning probe validated the core check — *"every number in the prose must appear in the facts"* —
on real data:

- **Grounded** (real `llama3.2`): prose numbers `{7.4}`, all in the facts → **0 unverified**.
- **Fabricated** ("…scored 22 goals and carries 9.8 xP…"): prose numbers `{22, 9.8}`, neither in the
  facts → **flagged**.

Cheap, robust, no new dependency.

#### Decision Drivers
- **Provable grounding** — verify, don't just instruct.
- **Visible** — the manager should *see* that the answer was checked.
- **Honest** — say exactly what's checked (numbers + names, not full meaning).

---

### 💡 Decisions

**1. Two checks, in a pure `verify_grounding(text, facts, *, known_names=(), subjects=())`.**
- **Numbers** — every number in the narration must appear in the facts (proven). Unbacked numbers are
  flagged.
- **Names** — a **known FPL player** (from the DB's player names) named in the narration who **isn't a
  subject** of this answer is flagged. Matching only against real player names keeps false positives
  down; each decision provides its `subjects` (the players the answer is about — the captain pick, the
  in/out of a transfer, the plan's players, the analyser's weakest/top).

**2. A visible trust line, soft.** After narration `ask` shows either
✓ *"Checked: all figures trace to the data."* or ⚠ *"This explanation mentions figures/names not in
the source data: …"* — and the **facts/table are always shown** regardless. Verification **never
blocks or regenerates** this sprint; it *informs*. (Regenerate-on-fail is a possible later step.)

**3. Optional, like the LLM.** No narration (Ollama absent) → nothing to verify; the tool is
unaffected. The verifier is pure string work — negligible latency, runs only when there's prose.

**4. Honest scope.** It checks **numbers + names**, not full semantic meaning — stated plainly so
"verified" doesn't over-promise. The facts/table remain the source of truth.

**Not in scope:** full claim/semantic verification (e.g. a second-LLM judge); blocking or regenerating
on a fail; verifying output outside `ask`; a new dependency.

---

### 🧪 Worked example (pressure-testing — real data, before code)

Number check, run at planning:

| Narration | Prose numbers | Unverified | Trust line |
|---|---|---|---|
| Real `llama3.2` (grounded) | `{7.4}` | none | ✓ checked |
| Fabricated ("22 goals, 9.8 xP") | `{22, 9.8}` | `22, 9.8` | ⚠ unverified: 22, 9.8 |

Confirms the check passes genuine output and catches invention before code. (The name check is the
companion — e.g. a narration naming "Salah" when he isn't a subject would be flagged.)

---

### ⚖️ Consequences & Trade-offs

* **Positive:** grounding becomes *provable and visible* — the distinctive, honest feature vs a
  black-box companion; a strong learning artifact (verifying an LLM's own output). Reuses the facts
  (+ DB names) we already have; no new dependency; soft so it can't break `ask`.
* **Negative / Trade-offs:** possible false positives (an incidental number; a name that's also a
  word) — mitigated by matching names only against the DB and keeping the ⚠ a *soft* note; it checks
  numbers + names, not full meaning (stated).
* **Risks & Mitigations:**
  - *Number false positives* → facts carry horizons/counts; the tightened prompt drops preamble; ⚠ is soft.
  - *Name false positives* → match only real player names; compare to the decision's `subjects`.
  - *Over-promising "verified"* → say exactly what's checked; the facts/table are the truth.

---

### 🛠 Implementation & Migration
* **Components Affected:** a pure `verify_grounding` in `src/ask.py` (the grounding contract); each
  decision gains a `subjects` list; `answer` runs the verifier after narration and carries the result
  on `AskResult`; `render_ask` shows the ✓/⚠ trust line. `known_names` comes from the store (player
  web_names). No new data/dependency; existing analytics untouched.
* **Action Items:**
  - [x] Record the design + the proven number check (US-104)
  - [ ] `verify_grounding` (numbers + names) + tests (US-105)
  - [ ] Wire into `ask` — the trust line; `AskResult` carries the result (US-106)
  - [ ] (Backlog) regenerate-on-fail; a stricter semantic/second-model check

---

### 🔄 Review & Reconsideration
* **Review Date:** If false positives annoy in real use, or a stronger guarantee is wanted.
* **Triggers for Reconsideration:**
  - [ ] Frequent false positives → tune the number/name heuristics.
  - [ ] A hard guarantee wanted → regenerate-on-fail, or a second-model claim check.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-104 (this), US-105, US-106
- **External Docs:** [ADR-034 (`ask` — analytics decide, LLM narrates)](./ADR-034-ask-command-grounded-nl.md) · [ADR-033 (the spike — anti-hallucination)](./ADR-033-llm-grounded-narration-spike.md) · [Sprint 035](../05_Sprints/Sprint35.md)
