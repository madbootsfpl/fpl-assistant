# Sprint 100: The AI Chat Assistant — a grounded rules KB + a labelled free-form mode

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a curated FPL-rules KB + a grounded `rules` intent, then a labelled free-form tail)
**Carried Over:** none

> **Direction (owner intake):**
> *"Ask tab: an **AI Chat Assistant** — a 24/7 chatbot for FPL **rules**, squad questions, and **tactical
> advice** tailored to your team."*
>
> **Owner steer (this planning):** **Curated rules KB + labelled free-form.** Answer FPL-rules questions from
> a curated, **verified** knowledge base (✓); answer genuinely open tactical questions free-form but clearly
> tagged **ℹ general — not verified**. Grounded squad questions are unchanged.

---

### 🔎 Verified at planning

- **The trust model is the constraint.** Today `ask`/`chat` is a **grounded** router — analytics DECIDE, the
  LLM only **narrates**, and every number/name is **verified** (✓/⚠, ADR-034/037). A general "FPL rules /
  tactics" chatbot is partly **ungrounded** — so the design must keep the trust boundary explicit.
- **The LLM can't be trusted on rules facts.** This session the local Ollama **hallucinated chip facts** (it
  invented "45.5 xP" and miscounted) and `verify_grounding` flagged it (⚠). So FPL rules must come from a
  **curated KB**, not the model's memory — the model only phrases them.
- **There's one clean hook.** `route()` returns `intent=None` for an unrecognised question, and `_fresh`
  handles it at a single point (`if intent is None: return assemble(question, None, None, narrator)`,
  currently the `_FALLBACK` help text). That's where the **general handler** slots in — *after* every grounded
  intent, so squad questions still route grounded.
- **Degradation is already the pattern.** `narrate()` returns None without Ollama; grounded intents show their
  facts regardless. A **rules** answer degrades to its KB facts (the block is the truth); the **free-form**
  tail needs the LLM, so without it we fall back to the help message.
- **The trust line has two states** (✓ / ⚠); a **third (ℹ "general, not checked")** is needed for free-form.

---

### 🎯 Sprint Goal

**Objective:** the Ask tab answers **FPL-rules** questions from a curated, **verified** knowledge base (✓) and
open **tactical** questions free-form with a clear **ℹ not-verified** label — while every existing grounded
squad/player question is unchanged. A real assistant, with the trust boundary always visible.

#### Success Criteria
- [ ] **US-259 (curated rules KB + a grounded `rules` intent, ADR-085)** — a `src/fpl_rules.py` KB of
      authoritative FPL facts (scoring · chips · transfers/hits · deadlines · price changes · squad rules ·
      formations · autosubs · captaincy · DGW/BGW). A `rules` path that **matches a rules topic**, selects the
      relevant facts, narrates them, and **verifies** the prose against those facts (✓) — degrading to the raw
      facts without Ollama. Routing answers general *"how does X work / what are the rules"* **without stealing
      squad commands** (pinned by tests).
- [ ] **US-260 (the labelled free-form tail + wiring)** — when no grounded intent **and** no rules topic
      matches, a **free-form** LLM answer scoped to general FPL rules/tactics, tagged **ℹ general — not checked
      against your data** (a new `_trust_line` state); it **degrades to the help message** without Ollama, and
      **never** makes a specific squad/player *decision* (those stay grounded). Wired through `answer`/
      `converse` → the **Ask** tab + CLI `chat`; a couple of example prompts.
- [ ] **No drift** — the grounded intents + `decision_xp` unchanged; existing **663** stay green; ruff clean.
- [ ] Docs: ADR-085 + index, PROJECT_STATUS, Architecture, Roadmap, README, Help, Backlog.

---

### 🧭 Design sketch

**US-259 (ADR-085).** `src/fpl_rules.py`: `RULES` — a list of `{topic, cues, facts}` entries (each `facts` a
short authoritative string, e.g. *"Bench Boost: your bench's points count for that gameweek. One use per half
of the season."*). A pure `match_rules(question) -> list[facts]` (cue keywords → the relevant entries). In
`ask.py`, a `_decide_rules(question)` builds a decision `{detail: the facts block, facts: {…}, subjects: [],
task: "answer using ONLY these FPL rules"}` → narrated + **verified** (same `assemble`/`verify_grounding`
path, ✓). Invoked from the `intent is None` fallback (so grounded intents win), **before** the free-form tail.

**US-260.** In the fallback: if `_decide_rules` matches → grounded rules answer; **else** a `_free_form(question,
narrator)` — a scoped prompt (*"You are an FPL assistant. Answer this general rules/tactics question briefly.
Do NOT recommend specific players or picks — those come from the tools."*) → an `AskResult` with the prose and
`trust={"free_form": True}`; `render_ask` renders **ℹ General FPL advice — not checked against your data**.
Without Ollama → the existing `_FALLBACK` help. Threaded through `answer`/`converse` unchanged (it's all in the
`intent is None` branch); the Ask tab already calls `converse`. Add example prompts + a Help note.

**Routing guard:** rules cues are **question-shaped + subjectless** (*how does / what is / what are / rules /
deadline / how many points / explain*), and only reached when no grounded intent matched — so *"how does bench
boost work"* → rules (not `start_bench`), *"which chip should I use for TS"* → chips, *"fix my bench"* →
start_bench. Pinned by tests.

**Deferred:** RAG / a bigger knowledge base; multi-turn free-form memory beyond the existing `Context`; a cloud
LLM for the deployed app (free-form needs a local/hosted model — the deploy degrades to rules + grounded).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-259 | **Curated rules KB + a grounded `rules` intent** — `fpl_rules.py` + `_decide_rules`, verified from the KB; routing that answers rules without stealing squad commands. ADR-085. | High | ⬜ To do | ~⅔ session |
| US-260 | **Labelled free-form tail** — open tactics → an LLM answer tagged **ℹ not-verified**, degrade without Ollama, never a squad decision; Ask-tab + `chat` wiring + examples. | High | ⬜ To do | ~⅓ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `match_rules` maps rules questions to the right facts; `_decide_rules` verifies clean (✓)
   when the narration restates only KB facts, and flags (⚠) an invented number; the free-form path returns
   `trust={"free_form": True}` → an **ℹ** line, and **degrades to the help message** without a narrator; the
   routing guard (rules vs start_bench/chips/analyse) is pinned; a grounded squad question is unchanged.
   Existing **663** stay green.
2. **Manual smoke** — *"how does bench boost work?"* → a ✓ rules answer; *"is it worth a −4 this week?"* → an
   **ℹ** free-form answer; *"who should I captain from RoboTS?"* → the grounded pick (unchanged); with Ollama
   off, rules still answers (facts) and free-form shows the help message.
3. **Docs updated** — ADR-085 + index, PROJECT_STATUS, Architecture, Roadmap, README, Help, Backlog.

---

### 📝 Session Progress Log

**US-259 — curated rules KB + a grounded `rules` intent (ADR-085).** ✅ Done.
- `src/fpl_rules.py`: a `RULES` KB of **13** authoritative entries (scoring · clean sheets/saves · bonus/BPS ·
  Defensive Contribution · chips · transfers/hits · price changes · squad rules · formations · captaincy ·
  auto-subs · deadline · double/blank GWs), each `{topic, cues, fact}`; a pure `match_rules(question)` →
  the `(topic, fact)` pairs whose cue appears (capped at 4), empty when nothing matches. `TOPIC_LABELS` for
  the "what I can explain" list.
- `ask.py`: a **`rules`** intent placed **first** in `_INTENT_KEYWORDS` with **question-shaped** cues
  (how does / how do / what is a / how many points / scoring / clean sheet / price change / when is the
  deadline …) that don't collide with squad commands; `_decide_rules` selects the KB facts → narrated +
  **verified** (✓, ADR-037), degrading to the raw facts block without Ollama; a rules-shaped question with no
  topic → a "here's what I can explain" message (US-260 makes it free-form). `src/ui/rules.py::render_rules`.
- **Tests (+8):** `match_rules` (right topic, multi-topic + cap, empty-safe, every fact non-empty); routing
  (rules questions → rules; `fix my bench`/`what transfer`/`how good is my squad`/`which chip`/`build … bench
  boost` unaffected); `_decide_rules` grounded (✓ on faithful narration, ⚠ on an invented number, facts block
  without a model) + the topics-list fallback. **671** green, ruff clean.
- **Real-LLM smoke (Ollama on):** `ask "how does bench boost work?"` → the model phrased the chip facts from
  the KB and the answer **verified ✓** ("every figure and name traces to the data").

**US-260 — the labelled free-form tail (ADR-085).** ✅ Done.
- `assemble` gains a **free-form** branch: a `{"free_form": True}` decision → a scoped LLM answer
  (`_free_form_prompt`: general rules/tactics only, **never** a specific player/pick), returned with
  `trust={"free_form": True}`; **no model → the `_FALLBACK` help message**. Both fallbacks now route here: an
  unrecognised question (`intent is None` → intent `"chat"`) and a rules-shaped question with no curated fact
  (`_decide_rules` no-match).
- `ui/ask.py`: `render_ask` shows a free-form answer (prose, no grounded decision), and `_trust_line` gains
  the **ℹ "General FPL advice — not checked against your data"** third state (alongside ✓ / ⚠).
- The **Ask tab + CLI `chat`** get this for free (they already call `converse`); added two rules example
  prompts + an intro caption naming the three answer types (✓ grounded · ✓ rules · ℹ tactics).
- **Tests (+2, 1 updated):** an unrecognised question → a free-form answer tagged ℹ, degrading to the help
  message without a model; `_decide_rules` no-match → the free-form decision; the one-shot unrecognised test
  updated (now intent `"chat"`, same help message). **672** green, ruff clean.
- **Real-LLM smoke:** `ask "any general advice for a first-time manager?"` → a helpful answer + the honest
  **ℹ not-verified** label; grounded/rules answers keep their ✓. Never makes a squad decision (those stay
  grounded).

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
