# Sprint 031: Phase 3 Wrap-up + Phase 4 LLM Spike

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a docs task + an evaluation spike)
**Carried Over:** None (Sprint 030 closed clean)

> **Direction (owner's Sprint-30 retro + choice):** celebrate Phase 3 in the docs, then — with the
> season-gated Data Hardening parked until GW1 — **spike Phase 4 (an LLM/chat layer)** to prove
> grounded natural-language answers with local Ollama before committing. A spike in the spirit of
> Sprint 015 (soccerdata): evaluate, decide, minimal throwaway code.

---

### 🔎 Verified at planning (the standing lesson — and it found the crux)

Probed the local Ollama setup *before* designing:

- **Ollama is live and viable.** `llama3.2` (a 3B model, 2 GB) is pulled; the server answers on
  `localhost:11434`; it explained a real `captain_picks` result in **5.4s** — local, private, free,
  no install. It stayed grounded (named Saka, penalty taker, home vs COV — all from the data) and
  invented no players.
- **⚠️ But asked to *decide*, it hallucinated the decision.** Given the top-3 and asked to
  *recommend* a captain, it picked **Saka (xP 7.2)** over **B.Fernandes (xP 7.4)** and justified it
  with a **false claim** — *"he has a higher expected points total"* — contradicting the data. A
  small model can't be trusted to rank numbers.

**The design consequence (the whole point of Phase 4's anti-hallucination rule, proven live):** the
**analytics decide; the LLM only *narrates* the decision we already made.** We never ask the LLM
"who should I captain?" (it re-ranks and fabricates); we hand it *"the pick is B.Fernandes — here
are the facts — explain why, and don't compare or invent numbers."* This is the spike's central
constraint, not an afterthought.

**Also:** still preseason (0 GWs, GW1 = 2026-08-21) — Data Hardening stays parked, as expected.

---

### 🧭 What's new — the first LLM component, kept on a tight leash

Every layer so far is deterministic. Phase 4 introduces a *language* layer — but on strict terms:
it **explains**, it does not **compute**. The analytics remain the single source of truth (xP,
captain, transfer, analyse all emit structured data); the LLM turns a *pre-made, structured
decision* into a readable sentence, forbidden from ranking, comparing, or inventing numbers. The
spike proves whether that discipline holds with a small local model — and whether it's worth
committing to a full Phase 4.

---

### 🎯 Sprint Goal

**Objective:** (1) Make the docs reflect Phase 3 completion; (2) **spike** a grounded `ask` that has
local Ollama *narrate* a captain decision made by our analytics — evaluate grounding + quality +
effort, and **decide** commit-to-Phase-4 or defer (evidence, not vibes).

#### Success Criteria
- [ ] **Docs celebrate Phase 3** — README (captain/transfer/analyse are *built*, not "planned"),
      Roadmap (Phase 3 substantially complete), a Phase-3 milestone note
- [ ] Spike approach agreed (**ADR-033**) — Ollama; **analytics-decide / LLM-narrate**; grounding
      rules; the evaluation rubric; commit/defer framing
- [ ] A grounded `ask` **spike** — routes a captain question to `captain_picks`, hands the LLM the
      *pre-made decision + facts*, gets an explanation; **no new pip dependency** (HTTP to Ollama via stdlib)
- [ ] **The anti-hallucination test is the headline** — verify the LLM narrates only the given facts,
      never re-ranks or invents numbers (the probe showed it *will* if asked to decide)
- [ ] Boxed as a spike (throwaway/experimental; `spikes/031-llm/` or a clearly-flagged `ask`); no
      production commitment beyond the decision
- [ ] **A written decision** — commit to Phase 4 (and how) or defer (why), with the probe evidence
- [ ] Docs: ADR-033 + index, PROJECT_STATUS; the spike's evidence recorded

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-092 | **Phase 3 docs celebration** — README (`captain`/`transfer`/`analyse` are built; move them out of "planned"), Roadmap (Phase 3 ≈ complete), a `01_Journal` Phase-3 milestone note | High | ✅ Done | 0.5 session |
| US-093 | **Gate.** LLM spike design (**ADR-033**): local Ollama; the **analytics-decide / LLM-narrate** grounding pattern (the probe proved the LLM mis-ranks if asked to decide); scope = one module (`captain`); anti-hallucination rules + the evaluation rubric; commit/defer framing. Pressure-tested (the probe) | Critical | ✅ Done | 0.5 session |
| US-094 | **The spike** — a grounded `ask` that narrates a `captain_picks` decision via Ollama (stdlib HTTP, no new dep); evaluate grounding (does it stay faithful?), quality, and effort; **write the commit/defer decision** with evidence. Boxed | High | ✅ Done | 1.5 sessions |

#### Technical Tasks & Maintenance
- [x] ADR-033 recorded + added to the ADR index — _US-093_
- [x] Update PROJECT_STATUS (Phase 3 celebrated; Phase 4 spiked → commit) — _US-094_
- [x] Record the spike's evidence + decision (spikes/031-llm/FINDINGS.md + ADR-033 outcome) — _US-094_

---

### ✅ Definition of Done (this sprint — adapted: a spike + docs)

The 3-part DoD, adapted (as for the Sprint 015 spike):
1. **Verified, not unit-tested** — the spike demonstrates grounded narration on real data, and the
   anti-hallucination behaviour is explicitly checked (the model does *not* re-rank/invent). Any
   throwaway spike code isn't held to production test standards; **production `src/` stays green (279)**.
2. **Read-through check** — the docs read correctly (Phase 3 accurately reflected); the spike's
   evidence + decision are legible.
3. **Documentation updated & checked** — README/Roadmap/milestone, ADR-033 + index, PROJECT_STATUS,
   sprint board (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Phase 3 docs celebration | New analytics/features |
| A grounded `ask` **spike** over ONE module (captain) | A full chat interface / multi-intent router |
| Local Ollama via stdlib HTTP (no new dep) | A cloud LLM / API keys / new pip deps in `src/` |
| The anti-hallucination evaluation + a commit/defer decision | Committing to build Phase 4 (that's the *decision's* outcome) |

**External Dependencies:**
- [ ] Local Ollama running (`llama3.2` pulled — verified at planning); reachable at `localhost:11434`.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| LLM invents/wrong numbers (proven it will if asked to decide) | High | **Analytics decide, LLM narrates**; pass only pre-made facts; forbid ranking/compare; verify explicitly |
| A small 3B model is too weak | Med | It's fine for *narration* (the constrained job); if not, note it — the pattern (not the model) is the finding |
| Scope creep into a full Phase 4 | Med | It's a **spike**: one module, throwaway, a written decision — not a build |
| A new heavy dependency | Low | Stdlib HTTP to Ollama; no new pip dep in `src/`; local/private/free |
| The season not started limits realism | Low | Captaincy works preseason (xP projections); grounding discipline is season-agnostic |

---

### 🗝️ Gating decision (US-093 → ADR-033)

Settle before the spike — the probe already pressure-tested it. Proposed (confirm/redirect at
"start US-093"):

1. **Local Ollama** (`llama3.2`), via **stdlib HTTP** to `localhost:11434` — no new pip dependency,
   private, free. (A cloud LLM is a later option if quality demands it.)
2. **Analytics decide, LLM narrates.** The `ask` flow routes a question to the analytics
   (`captain_picks`), which *makes the decision*; the LLM receives the **pre-made decision + the
   supporting facts** and explains it — explicitly told **not to rank, compare, or invent numbers**.
   (The probe proved that asking it to decide produces a wrong, fabricated answer.)
3. **Scope = one module (`captain`).** A single grounded `ask "who should I captain from <squad>?"`
   — enough to prove the pattern. A multi-intent router / full chat is deferred to Phase 4 proper.
4. **The rubric.** Grounding (never invents/contradicts), faithfulness (explains *our* decision, not
   its own), quality (readable/useful), effort/latency. Output: **commit to Phase 4 or defer**, with
   evidence — like the soccerdata spike (ADR-016).

**Worked example (already run at planning):** asked to *recommend*, `llama3.2` wrongly picked Saka
over B.Fernandes and fabricated a justification. The spike will show the *constrained* pattern
(narrate the analytics' B.Fernandes pick) stays faithful — the core hypothesis to confirm.

---

### 📝 Session Progress Log

- **US-092 (Phase 3 docs celebration) ✅** — Fixed the stale front door: the **README** now lists
  `captain`/`transfer`/`analyse` (+ `history`, per-GW xP) under *What it does today* — they'd been
  wrongly left under "Planned" — and the status line marks Phase 3 complete; commands section
  updated. The **Roadmap** Phase 3 section marked **✅ substantially complete** (captain/transfer/
  analyser done; xMins/live-layer/multi-move deferred). Added a **Phase-3 milestone** to
  `01_Journal` (the trio, the composability dividend, the honest boundaries). No code touched
  (production suite stays 279).
- **US-093 (gate) ✅** — Recorded **ADR-033**: local Ollama (`llama3.2`) via stdlib HTTP (no new
  dep); the **analytics-decide / LLM-narrate** pattern (the probe proved the LLM mis-ranks + invents
  a justification if asked to *decide*); scope = one intent (`captain` from a squad); boxed as a
  runnable script in `spikes/031-llm/` (not production); rubric = grounding faithfulness (headline) +
  quality + effort → commit/defer. Confirmed: script-in-spikes + `llama3.2` as-is.
- **US-094 (the spike) ✅** — Built `spikes/031-llm/ask_spike.py` (analytics decide → LLM narrates;
  stdlib HTTP; no new dep; Ollama-down handled). Ran it: the **constrained pattern fixed the
  catastrophic failure** — every run named the analytics' pick (B.Fernandes), no re-ranking, no
  invented players. **New finding:** the 3B model mis-read coded fields (`venue "A"` → "home"; `HUL`
  → "Huddersfield") — fixed by **pre-humanising the facts** ("away against HUL") + forbidding code
  expansion (verified). **Decision: ✅ COMMIT to Phase 4** — real value, low cost, clear design
  (contrast: soccerdata → defer). Evidence in `spikes/031-llm/FINDINGS.md`. Production untouched
  (ruff clean, 279 green; `spikes/` excluded from lint).

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-092 (Phase 3 docs celebration), US-093 (ADR-033), US-094 (the
  LLM spike). The docs now tell the truth (Phase 3 built, not "planned"); and a boxed spike proved
  **grounded local-LLM narration works**, ending in a clear **COMMIT to Phase 4**. Production
  untouched (279 tests, ruff clean); **no new dependency** (stdlib HTTP to Ollama); the LLM code
  lives in `spikes/`, not `src/`.
* **Carried Forward:** None. Phase 4 (a real `ask`) is green-lit for when it's prioritised; Data
  Hardening still waits on GW1.
* **Key Artifacts / Decisions:** ADR-033 (analytics-decide / LLM-narrate; local Ollama; spike →
  commit); `spikes/031-llm/ask_spike.py` + `FINDINGS.md`; refreshed README/Roadmap; a Phase-3
  milestone note.

#### Retrospective
* **What Went Well?**
  - **The spike answered the real question cheaply.** ~1.5 sessions, no new dependency, no production
    risk — and a decisive, evidence-backed **commit** (vs the soccerdata spike's defer).
  - **Verify-on-real-data earned it twice.** The planning probe proved the LLM *fabricates if asked
    to decide* (→ analytics-decide/LLM-narrate); running the spike proved it *mis-reads coded fields*
    (→ pre-humanise the facts). Two design rules the theory wouldn't have handed us.
  - **The grounding discipline is engineered, not hoped.** The LLM is structurally unable to invent
    the numbers — the honest, transparent contrast to FPL's black-box Companion.
  - **Honest docs first.** Fixing the README (which listed *built* features as "planned") before
    showing off a new capability.
  - DoD held (adapted for a spike + docs): evidence + a written decision; production stays green.
* **What Could Be Improved?**
  - **3B-model prose is a little generic** — faithful but not eloquent. Fine for explanation; a
    bigger model would improve fluency (a Phase-4 option, not a blocker).
  - **The spike is one intent (captain).** Enough to prove the pattern, but transfer/analyse
    narration + an intent router are unproven until Phase 4 proper.
* **Lessons Learned?**
  - Never let an LLM make a numeric decision — hand it the *decision* and *pre-humanised facts*, and
    it narrates honestly.
  - A spike's job is a *decision with evidence* — running it (not just designing it) surfaced the
    second rule.
  - Keep the front door honest; and keep experiments boxed (no production commitment until decided).
* **Action Items for Next:**
  - [ ] **Phase 4 (green-lit):** a real `ask` command — intent router (captain/transfer/analyse) + a
        grounding-contract module (pre-humanised facts, narrate-not-decide, a verify check) + graceful
        Ollama-absent handling + tests. Owner to prioritise vs other work.
  - [ ] **Data Hardening** still queued for ~GW1 (2026-08-21).
  - [ ] Keep gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — **Phase 4** (build the real `ask`, not blocked) or wait for
GW1 to do **Data Hardening**. Both are live options.

**Completion Date:** 2026-08-04
**Final Notes:** Honest docs + a decisive spike. The LLM path is real and differentiated *because*
it's grounded — analytics decide, the model narrates pre-humanised facts, and it can't invent the
numbers. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held (spike + docs).
