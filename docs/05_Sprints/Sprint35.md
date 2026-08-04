# Sprint 035: Phase 4 — grounding verification (prove the narration is faithful)

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a verification layer + a visible trust line)
**Carried Over:** None (Sprint 034 closed clean)

> **Direction (owner's choice):** deepen Phase 4's *trust*. Today `ask` **instructs** the LLM not to
> invent numbers; this sprint **verifies** it didn't — checking the narration against the facts and
> showing the result. It makes *"grounded, not a black box"* **provable**, not just promised.

---

### 🔎 Verified at planning (the standing lesson — the check works)

Prototyped the core check — *"every number in the prose must appear in the facts"* — on real data:

- **Grounded** (real `llama3.2` captain narration): prose numbers `{7.4}`, all in the facts →
  **0 unverified**. Passes.
- **Fabricated** ("…scored 22 goals and carries 9.8 xP…"): prose numbers `{22, 9.8}`, neither in the
  facts → **flagged**.

So the number check passes genuine output and catches invention — cheap, robust, no new dependency.
A **name check** (a known FPL player named in the prose who isn't a subject of the answer) is the
natural companion. ClubElo intermittent; still preseason — neither is material here.

---

### 🧭 What's new — the grounding becomes *visible and checked*

Phase 4's whole thesis is *the analytics decide; the LLM only narrates* — the honest, transparent
counterpart to a black-box AI companion. This sprint closes the loop: after narration, a
**verifier** checks that every **number** and **player name** in the prose traces to the facts, and
`ask` shows a **trust line** (✓ checked, or ⚠ with the unverified bits) — with the exact facts/table
always present. Verification is *soft* (it informs, never blocks) and, like the LLM, entirely optional.

---

### 🎯 Sprint Goal

**Objective:** A pure `verify_grounding` that flags **numbers** and **player names** in the LLM's
narration that aren't backed by the facts; wire it into `ask` as a **visible trust line** (✓ / ⚠),
with the facts/table always shown. Soft — informs, never blocks.

#### Success Criteria
- [ ] Approach agreed (**ADR-037**) before code — number + name checks; a visible trust line; soft/optional
- [ ] `verify_grounding(text, facts, *, known_names, subjects)` — returns unverified numbers + names
- [ ] **Number check:** every number in the prose appears in the facts (proven at planning)
- [ ] **Name check:** a known FPL player named in the prose who isn't a subject of the answer → flagged
      (uses the DB's player names; false-positive-averse)
- [ ] `ask` shows a **trust line** — ✓ "checked against the data", or ⚠ with the unverified items;
      the facts/table are always present
- [ ] Soft + optional — never blocks; absent LLM (no narration) → no check needed
- [ ] Tests (grounded passes; fabricated numbers/names flagged; edge cases) + live smoke
- [ ] Docs: ADR-037 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-104 | **Gate.** Grounding-verification design (**ADR-037**): number check (proven) + name check; a visible ✓/⚠ trust line; soft/optional; where it lives (the grounding contract). Pressure-test on real + fabricated narration | Critical | ✅ Done | 0.5 session |
| US-105 | **`verify_grounding`** (pure) — unverified numbers (prose ∉ facts) + unverified names (known FPL player named, not a subject). Each decision provides its `subjects`; `known_names` from the DB. Unit-tested | High | ✅ Done | 1 session |
| US-106 | **Wire into `ask`** — run the verifier after narration; a ✓/⚠ trust line in `render_ask` (facts/table always shown); carry the result on `AskResult`. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-037 recorded + added to the ADR index — _US-104_
- [x] Update Architecture changelog (a verification layer closes the grounding loop) — _US-105_
- [x] Update Handbook/README (the trust line; grounded *and verified*) — _US-106_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — grounded passes, fabricated numbers/names flagged, edge cases; existing
   304 stay green; no new dependency.
2. **Manual smoke test done** — `ask` on live data shows a ✓ trust line for grounded output; a
   contrived fabrication shows ⚠ with the offending items.
3. **Documentation updated & checked** — ADR-037 + index, Architecture, Handbook, README, sprint
   board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Number + player-name verification of the narration | Full semantic/claim verification (a second LLM judge) |
| A visible ✓/⚠ trust line; facts/table always shown | Blocking/regenerating on a fail (soft only, this sprint) |
| Reuse the facts (+ DB names) we already have | New data / dependency |
| Soft, optional (like the LLM itself) | Verifying non-`ask` output |

**External Dependencies:** None beyond stored FPL data.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Number-check false positives (incidental numbers) | Med | Facts include the horizon/counts; the tightened prompt drops preamble; a ⚠ is a *soft* note, not a block |
| Name-check false positives (a name that's a common word) | Med | Match only against the DB's known player names; require a subject-set to compare against |
| Over-promising "verified" | Low | It checks numbers + names, not full meaning — say exactly that; the facts/table are the truth |
| Verifier adds latency | Low | Pure string work — negligible; runs only when there's narration |

---

### 🗝️ Gating decision (US-104 → ADR-037)

Settle before code — the number check is pressure-tested. Proposed (confirm/redirect at "start US-104"):

1. **Two checks.** (a) **Numbers** — every number in the prose must appear in the facts (proven).
   (b) **Names** — a known FPL player named in the prose who isn't a *subject* of the answer is
   flagged (uses the DB's player names; the decision provides its `subjects`).
2. **A visible trust line, soft.** `ask` shows ✓ *"checked: all figures trace to the data"* or ⚠
   *"mentions unverified figures/names: …"* — and the **facts/table are always shown**. Verification
   **never blocks or regenerates** (this sprint); it informs.
3. **Optional, like the LLM.** No narration (Ollama absent) → nothing to verify; the tool is
   unaffected.
4. **Honest scope.** It verifies numbers + names, not full semantics — stated plainly.

**Worked example (already run):** grounded → 0 unverified (✓); a fabrication ("22 goals, 9.8 xP")
→ ⚠ [22, 9.8].

---

### 📝 Session Progress Log

- **US-104 (gate) ✅** — Recorded **ADR-037**: a pure `verify_grounding(text, facts, *, known_names,
  subjects)` with two checks — **numbers** (every prose number must be in the facts; proven at
  planning: grounded → 0 unverified, "22 goals/9.8 xP" → flagged) and **names** (a known FPL player
  named who isn't a `subject` of the answer). `ask` shows a **soft, visible ✓/⚠ trust line** with the
  facts/table always present; verification never blocks/regenerates (this sprint) and is optional
  (no LLM → nothing to check). Honest scope stated: numbers + names, not full semantics.
- **US-105 (`verify_grounding`) ✅** — Pure fn in `src/ask.py`: `_numbers` (prose numbers ∉ facts) +
  a **conservative** name check (`_significant_tokens` — ≥4-letter whole words, so "ward" ≠ "forward"
  and short names like "Son"/"Sá" don't collide; flags a known player who isn't a `subject`).
  **6 tests** (grounded passes, fabricated numbers flagged, non-subject player flagged, subject not
  flagged, no false-positives on short/common words, empty text) → suite **304 → 310**; ruff clean;
  no new dependency.
- **US-106 (wire into `ask`) ✅** — Each decision now carries `subjects` (the players it's about);
  `answer` supplies the DB's `known_names`; `assemble` runs `verify_grounding` after narration and
  carries the result on `AskResult.trust`; `render_ask` shows a **✓/⚠ trust line** (facts/table
  always present; no line when there's no narration). **+2 tests** → suite **310 → 312**; ruff clean.
  Live smoke: grounded `ask` shows *"✓ Checked: every figure and name… traces to the data"*; degraded
  (no LLM) shows facts + no line. **Grounding is now visible and verified.**

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-104 (ADR-037), US-105 (`verify_grounding`), US-106 (wire into
  `ask` + trust line). Phase 4's grounding is now **verified and visible**: every `ask` answer checks
  its narration against the facts and shows a ✓/⚠ line. Tests 304 → **312**; one ADR; **no new
  dependency**.
* **Carried Forward:** None. Regenerate-on-fail and a stricter semantic check are on the Backlog.
* **Key Artifacts / Decisions:** ADR-037 (verify numbers + names; a soft, visible trust line);
  `verify_grounding`, `AskResult.trust`, the `_trust_line` renderer, `subjects` on each decision.

#### Retrospective
* **What Went Well?**
  - **Instruction became proof.** We'd *told* the LLM not to invent numbers; now we *verify* it — the
    honest completion of Phase 4's anti-hallucination story.
  - **The self-check is itself trustworthy** — the name check is deliberately conservative (≥4-letter
    whole words), so it doesn't cry wolf. A soft trust line is only useful if it's rarely wrong.
  - **Proven before built** — the planning probe showed the number check passes real output and
    catches a fabrication; a test locks it in.
  - **Grounding is now *visible*** — the ✓ line is the transparent thing that separates this from a
    black-box companion. Pure string work; the analytics untouched. DoD held (35th).
* **What Could Be Improved?**
  - **It checks numbers + names, not full meaning** — a false comparison in words (not numbers) could
    slip through. Stated honestly; a semantic/second-model check is a later option.
  - **Rounding edge** — if the model rounds a figure (7.4 → 7), the number check flags it. Rare with a
    verbatim-copying small model, and only a soft ⚠; noted.
* **Lessons Learned?**
  - Instructing an LLM is hope; verifying its output is proof — check, don't just prompt.
  - A safety check must itself be trustworthy — bias it against false positives.
  - Make the guarantee *visible* (the ✓ line) — trust you can see beats trust you're asked to take.
* **Action Items for Next:**
  - [ ] (Backlog) regenerate-on-fail; a semantic/second-model claim check; tune heuristics if needed.
  - [ ] **Data Hardening** at ~GW1 (2026-08-21); or more Phase 4 / the web UI — owner to steer.
  - [ ] Keep gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4 (a stronger check, more intents, chat), the web
UI (Phase 2), or wait for GW1 to do Data Hardening. All live.

**Completion Date:** 2026-08-04
**Final Notes:** Phase 4's through-line is complete — instruct (ADR-034), prove (ADR-033), *verify and
show* (ADR-037). The grounding is now provable and visible, and the check is honest about its own
limits. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
