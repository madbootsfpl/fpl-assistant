# Architectural Decision Record: The `ask` command — grounded natural-language answers

**Decision ID:** ADR-034
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Productionises the ADR-033 spike (which returned **commit**)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The Sprint 031 spike (ADR-033) proved a local LLM can answer FPL questions in plain English
**grounded** in our analytics — *if* the analytics decide and the LLM only narrates *pre-humanised*
facts. It returned **commit**. This ADR is the production design: a real `ask` command over the
three decision-support intents (captain / transfer / analyse).

Two findings from the spike + a planning probe shape it:

- **The LLM must never decide.** Asked to *recommend*, it re-ranked and fabricated a justification.
- **It must not decode data.** It read `venue "A"` as "home" and expanded team codes wrongly; and in
  a multi-fact summary (analyse) it **conflated** fields (implied availability concerns when there
  were none). Fix: pass **pre-humanised, self-describing facts** and forbid merging.

The tool must also not *depend* on the LLM — the analytics are the product; narration is a bonus.

#### Decision Drivers
- **Grounding by construction** — the LLM can't invent what it never computes.
- **The LLM is optional** — degrade to the structured decision when it's absent.
- **Lightweight & testable** — no new dependency; the real model out of the unit suite.

---

### 💡 Decisions

**1. Module shape.**
- `src/llm.py` — a tiny Ollama client: `narrate(prompt) -> str | None`, stdlib HTTP, injectable,
  **returns `None` when Ollama is unavailable** (timeout / not running) instead of raising — this is
  what makes degradation clean.
- `src/ask.py` — orchestration, mostly pure: `route(question) -> (intent, squad)`; per-intent
  humanisers (`_captain_facts` / `_transfer_facts` / `_analyse_facts`); a prompt builder; and
  `answer(question, store, narrator)` tying it together.
- `src/ui/ask.py` — render the result (decision line + explanation, or the degraded note).
- `cli.py` `cmd_ask` + an `ask` subparser; `OLLAMA_URL` / `OLLAMA_MODEL` in `config`.

**2. The grounding contract (per intent).** Analytics **decide** the answer and emit
**pre-humanised, self-describing facts** (e.g. `"fixture": "away against HUL"`,
`"availability_problems": "0 (none)"`); a prompt builder enforces **narrate-not-decide, invent
nothing, don't merge fields, don't expand codes**; the LLM returns prose only. It never sees a
decision to make. (The analyse summary gets the tightest framing — it's the one that conflated.)

**3. Keyword intent routing.** Map the question to captain / transfer / analyse by keywords, and
extract the squad name. **Deterministic — the LLM decides nothing, including the route.** An
unrecognised question returns a helpful *"I can answer about captaincy, transfers, or your squad's
health"* message.

**4. The LLM is optional (graceful degradation).** When Ollama is absent/down (`narrate` → `None`),
`ask` still returns the **analytics decision + facts** with a note *"(start Ollama for a written
explanation)"*. The tool is fully usable without the model — narration is additive, never load-bearing.

**5. Testable without a live model.** The `narrator` is **injectable**; unit tests pass a fake
(canned string, or `None` for the degradation path) so routing, humanising, and the full flow run
**offline**. `route()` and the humanisers are pure. The real Ollama call is **smoke-only**. **No new
pip dependency** (stdlib HTTP).

**Not in scope:** a conversational multi-turn chat; LLM-based routing; a cloud LLM / API keys; the
LLM ranking / computing / recommending anything.

---

### 🧪 Worked example (pressure-testing — spike + planning probe, real data)

All three intents narrated grounded on the live squad "TS":
- **captain** (spike) → "B.Fernandes… away at HUL… penalty taker" ✅
- **transfer** → "replacing Kelleher with Benitez… +15.4 expected points" ✅
- **analyse** → "278.1 projected XI points… weakest Ampadu, Kelleher, Truffert" ✅ — but it
  **conflated** availability into the weakest-starters point, which drove Decision 2's
  self-describing-facts rule.

And the degradation path is trivial to verify: stop Ollama → `ask` prints the decision + facts + the
note, no crash.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the first natural-language interface — grounded, transparent (backed by *our* numbers,
  unlike a black-box Companion), and *optional*. No new dependency; the analytics/tests untouched.
* **Negative / Trade-offs:** a 3B model's prose is faithful but plain; grounding is only as good as
  the humanised facts (so the humanisers carry the weight, not the prompt alone).
* **Risks & Mitigations:**
  - *Invents / re-ranks* → decide/humanise/narrate-not-decide; verify the pick name appears.
  - *Summary conflation* → self-describing facts + "don't merge fields".
  - *Depends on the LLM* → optional; degrade to the decision.
  - *Misroute* → deterministic keywords + a helpful fallback.

---

### 🛠 Implementation & Migration
* **Components Affected:** new `src/llm.py`, `src/ask.py`, `src/ui/ask.py`; `cli.py` (`ask`);
  `config` (`OLLAMA_URL`/`OLLAMA_MODEL`). Reuses `captain_picks` / `suggest_transfers` /
  `analyse_squad` read-only. Existing analytics/views/tests untouched.
* **Action Items:**
  - [x] Record the production design + the spike/probe evidence (US-095)
  - [ ] `llm.py` + grounding contract + router + `ask` (captain) + degradation + tests (US-096)
  - [ ] Extend `ask` to transfer + analyse (explicit fact-framing) + tests + smoke (US-097)
  - [ ] (Backlog) a conversational mode; a larger/cloud model option; more intents

---

### 🔄 Review & Reconsideration
* **Review Date:** After a season of real use, or if grounding proves fragile in practice.
* **Triggers for Reconsideration:**
  - [ ] Prose quality matters more → a larger/cloud model behind the same contract.
  - [ ] Users want conversation → a multi-turn mode (still analytics-grounded).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-095 (this), US-096, US-097
- **External Docs:** [ADR-033 (the spike → commit)](./ADR-033-llm-grounded-narration-spike.md) · [ADR-029/030/031 (the intents narrated)](./ADR-029-captain-suggestions.md) · [spikes/031-llm/FINDINGS.md](../../spikes/031-llm/FINDINGS.md) · [Sprint 032](../05_Sprints/Sprint32.md)
