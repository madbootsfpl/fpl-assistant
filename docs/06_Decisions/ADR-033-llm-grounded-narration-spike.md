# Architectural Decision Record: LLM grounded-narration spike (local Ollama)

**Decision ID:** ADR-033
**Date:** 2026-08-04
**Status:** Accepted (spike). **Outcome: ✅ COMMIT to Phase 4** — the grounded-narration pattern
works; see [spikes/031-llm/FINDINGS.md](../../spikes/031-llm/FINDINGS.md). Key added finding:
**pre-humanise the facts** (the model mis-read `venue "A"` as "home" and expanded `HUL` to the wrong
club until the facts were passed as unambiguous phrases).
**Superseded By / Replaces:** N/A (first Phase 4 exploration)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Phase 4 is an **AI / natural-language layer**. With the season-gated work parked until GW1, the
owner chose to **spike** it now — cheaply prove whether a local LLM can answer FPL questions in
plain English *grounded in our analytics*, before committing to build it. FPL launched an official
"Companion" (CoPilot); we can't leverage that closed tool, but the concept is sound and ours can be
**better-grounded** — every answer backed by our transparent xP/analytics, with the LLM forbidden
from inventing numbers.

A planning probe settled the crux:

- **Local Ollama is viable.** `llama3.2` (3B, 2 GB) explained a real `captain_picks` result in
  **5.4s**, stayed on the given facts, invented no players.
- **⚠️ But asked to *decide*, it hallucinated the decision** — it picked Saka (xP 7.2) over
  B.Fernandes (xP 7.4) and justified it with a **false** claim ("higher xP"). A small model cannot
  be trusted to rank numbers.

So the design writes itself (and it *is* the Phase-4 anti-hallucination rule): **the analytics
decide; the LLM only narrates the decision we already made.**

#### Decision Drivers
- **Grounding first** — the value is a *trustworthy* explanation, not fluent guessing.
- **Cheap & reversible** — a spike, boxed, ending in a commit/defer decision (like ADR-016).
- **Lightweight** — local, private, free; no new pip dependency in `src/`.

---

### 💡 Decisions

**1. Local Ollama (`llama3.2`), via stdlib HTTP.** Call `http://localhost:11434/api/generate` with
`urllib` — **no new pip dependency**, private, free. `llama3.2` is the model already pulled; using a
small model is deliberate — if a 3B model narrates *faithfully*, that's a strong result. (Model /
cloud choice becomes a Phase-4 question, not a spike blocker.)

**2. Analytics decide; the LLM narrates.** The `ask` flow routes the question to the analytics
(`captain_picks`), which **makes the decision** (its #1 is the pick). The LLM receives the
**pre-made pick + the supporting facts** and explains it — instructed **not to rank, compare,
compute, or mention any player/number not in the data**. The LLM never touches the decision, only
the words. (The probe proved that letting it decide produces a wrong, fabricated answer.)

**3. Scope: one intent (`captain` from a saved squad).** A single grounded
`ask "who should I captain from <squad>?"` — enough to prove the pattern. No general intent-router,
no chat loop (that's Phase 4 proper).

**4. Boxed as a spike — not production.** A runnable script under **`spikes/031-llm/`** (e.g.
`python spikes/031-llm/ask_spike.py "..."`), **not wired into `app.py`** and not in `src/`.
Production stays green (279 tests) with zero commitment. Ollama-down is handled gracefully (a clear
message, not a crash).

**5. The evaluation rubric → a written decision.** Judge on: **grounding faithfulness** (the
headline — does it stay on the given facts, name the *analytics-chosen* pick, invent nothing?),
narration quality (readable, useful), and effort/latency. Output: **commit** to Phase 4 (build a
real, structured `ask` command) or **defer** (with evidence), recorded like the soccerdata spike
(ADR-016).

**Not in scope:** a production `ask` command; a multi-intent router / chat UI; a cloud LLM or API
keys; any new dependency in `src/`; letting the LLM compute or rank anything.

---

### 🧪 Worked example (pressure-testing — already run at planning)

Given the real top-3 and asked to *recommend*, `llama3.2` produced:

> "I recommend **Saka** as captain… he has a **higher expected points total** than B.Fernandes and
> Haaland."

— which is **false** (Saka 7.2 < B.Fernandes 7.4). That failure *is* the design input: the spike
will run the **constrained** pattern instead — hand the LLM the analytics' pick (B.Fernandes) and
the facts, and confirm it **narrates that decision faithfully without re-ranking or inventing**. Two
runs, low temperature, checked by eye + a simple grounding check (correct name present; no unlisted
figures).

---

### ⚖️ Consequences & Trade-offs

* **Positive:** a cheap, honest read on whether grounded local-LLM narration is worth a Phase 4 —
  differentiated from FPL's black-box Companion by transparency. No new dependency, no production
  risk, reversible.
* **Negative / Trade-offs:** a 3B model may narrate blandly or occasionally slip (the spike will
  say); the constrained pattern means the LLM adds *explanation*, not *intelligence* — by design.
* **Risks & Mitigations:**
  - *Hallucination* → analytics decide, LLM narrates; pass only facts; verify the output.
  - *Weak model* → narration is the constrained job; if it's not enough, that's the finding.
  - *Scope creep* → one intent, boxed in `spikes/`, a written decision — not a build.

---

### 🛠 Implementation & Migration
* **Components Affected:** **none in `src/`.** A new `spikes/031-llm/` (a script that reuses the
  existing analytics read-only + a small stdlib Ollama call) + a written evaluation. `app.py` and
  production tests untouched.
* **Action Items:**
  - [x] Record the spike design + the probe evidence (US-093)
  - [ ] `spikes/031-llm/` grounded `ask` (narrate a captain decision); evaluate; write the decision (US-094)
  - [ ] (On "commit") Phase 4: a real `ask` command + an intent router + the grounding contract as `src/`

---

### 🔄 Review & Reconsideration
* **Review Date:** At the spike's end — the commit/defer decision.
* **Triggers for Reconsideration:**
  - [ ] Grounding proves unreliable even when narrating → defer; revisit with a bigger/cloud model or a stricter contract.
  - [ ] Grounding is faithful + useful → commit; design the production `ask` (router, contract, tests).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-093 (this), US-094; US-092 (Phase 3 docs celebration)
- **External Docs:** [ADR-016 (soccerdata spike — the evaluate/defer pattern)](./ADR-016-soccerdata-evaluation.md) · [ADR-029 (captain — the module being narrated)](./ADR-029-captain-suggestions.md) · [Roadmap — Phase 4](../04_Roadmap/Roadmap.md) · [Sprint 031](../05_Sprints/Sprint31.md)
