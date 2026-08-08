# Sprint 110: Chat robustness — remembered context + a bigger rules KB

**Dates:** 2026-08-11 (planned)
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~1 session (a small persistence layer + curated content)
**Carried Over:** none

> **Direction (owner steer — no tester feedback this cycle):** make the Ask/chat assistant sturdier before wider
> testing: (1) **remember the conversation across runs** (the open half of ADR-080 — follow-ups only work
> within one process today), and (2) **grow the curated rules KB** so it answers more FPL-rules questions.

---

### 🔎 Verified at planning (on real data)

- **A `Context` serializes cleanly to JSON** — a real turn's `Context(intent, squad, question, count, rank,
  decision)` round-trips via `dataclasses.asdict` → `json.dumps` (1488 bytes; `decision` = detail/headline/
  facts/subjects/task, all JSON types). So persisting it to a local file is straightforward.
- **Follow-ups are process-local today.** The CLI `chat` REPL threads `Context` in memory; the one-shot `ask`
  is context-free (`cmd_ask` → `ask.answer`); the web threads it in `st.session_state`. So *"ask X"* then a
  separate *"ask why?"* can't work, and a chat restart forgets — exactly the gap.
- **The web must stay read-only.** The deploy is multi-user with **no server writes** (a guardrail test scans
  the web edges for `.save(`). So persistence is **CLI-only** (local, single-user); the web keeps
  `session_state` (per-session) untouched — the store is never imported by `web_streamlit`.
- **`data/*.json` is already git-ignored** (except `seed_squads.json`), so a `data/chat_context.json` needs no
  new ignore rule and won't be committed.
- **The rules KB is 13 entries** (`src/fpl_rules.py::RULES`) with a simple `match_rules` cue-matcher — easy to
  grow. Common gaps: player **flags/availability** (🔴/🟡 + 75/50/25% chance), **pre-season unlimited
  transfers**, **one chip per gameweek**, **bench points**, **wildcard timing**, **mini-leagues**, **overall
  vs gameweek rank**, **team value / selling price**.

---

### 🎯 Sprint Goal

**Objective:** the assistant *remembers* — a follow-up ("why?", "and the next?") works across separate CLI
invocations and a restarted chat — and it *knows more* — the curated rules KB answers a wider set of FPL-rules
questions, still grounded + verified (✓). The web stays read-only (session-only memory, unchanged).

#### Success Criteria
- [x] **US-281 (remember the conversation across runs)** — a small **`src/chat_context.py`** that saves/loads a
      `Context` ↔ a local JSON file (`config.CHAT_CONTEXT_PATH`, git-ignored) with a **timestamp + TTL** (a
      stale context is ignored, so an old "why?" doesn't resurface an ancient turn). The **CLI `ask`** loads the
      context → `converse` → saves the new one (so *"ask …"* then *"ask why?"* works); the **CLI `chat`** REPL
      **resumes** the saved context on start + saves each turn, and a **"forget"/"reset"** word clears it. The
      **web is unchanged** (session-only; the store is CLI-only, never imported by `web_streamlit`).
- [x] **US-282 (grow the rules KB)** — **~8 new** authoritative entries (player flags/availability · pre-season
      unlimited transfers · one chip per gameweek · bench points · wildcard timing · mini-leagues · overall vs
      gameweek rank · team value & selling price), each short + numeric where the number is the answer;
      `TOPIC_LABELS` extended. The `rules` intent picks them up and still **verifies** (✓, ADR-085/037).
- [x] **No drift** — the analytics + grounding untouched; `ask.answer`/`converse` stay pure (the persistence is
      in the CLI handler only, so the web + tests are unaffected); the read-only web guardrail holds; **726**
      green (716 → +10: chat-context store/resume/CLI, KB coverage); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Backlog, ADR index (a short **ADR-091** for persisted
      chat context — agreed at the gate).

---

### 🧭 Design sketch

**US-281 — persisted chat context (the gate writes ADR-091).**
- `src/chat_context.py`: `save_context(ctx, *, now=…)` writes `{saved_at, context: asdict(ctx)}` to
  `config.CHAT_CONTEXT_PATH`; `load_context(*, now=…, ttl=_TTL)` reads it back into a `Context`, returning
  `None` when the file is absent/corrupt **or older than the TTL** (a light guard against a stale follow-up).
  `clear_context()` removes the file. `now`-injected → deterministic tests.
- `cli.py::cmd_ask`: `ctx = load_context(); result, new = converse(question, ctx, …); save_context(new)` —
  so a follow-up-shaped line uses the last turn, a fresh question overwrites it. A `--forget` flag (or an
  `ask forget`) clears it.
- `cli.py::cmd_chat`: seed `chat_transcript` with the loaded context, persist after each turn; a **"forget"**
  line resets. (Small change to thread an initial context into the REPL loop.)
- **The web is out of scope for the file** — `web_streamlit` never imports `chat_context`; `st.session_state`
  keeps per-session memory (no server write). A test asserts the store isn't referenced in the web edge.

**US-282 — a bigger rules KB.** Append entries to `RULES` (same shape: `topic` · `cues` · a short `fact`),
extend `TOPIC_LABELS`, keep facts phrased for **2025/26** and numeric where the number is the answer (so the
verifier traces it). Avoid anything uncertain — only well-established rules. No matcher change needed.

**Deferred:** persisting context for the web across browser sessions (would need client storage / violates the
read-only server); a hosted LLM for the deploy's free-form tail; an LLM intent classifier.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-281 | **Remember the conversation across runs** — a local, TTL'd `chat_context` store; CLI `ask`/`chat` load+save; web session-only (ADR-091). | High | ✅ Done | ~½ session |
| US-282 | **Grow the curated rules KB** — 8 new grounded entries + routing + `TOPIC_LABELS`; still verified. | High | ✅ Done | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — a `Context` round-trips through `save_context`/`load_context`; a fresh load past the TTL
   returns `None`; `clear_context` clears; a two-call CLI sequence (*"who should I captain?"* then *"why?"*)
   resolves the follow-up via the store; a "forget" resets; the web Ask still uses `session_state` and never
   imports the store (guardrail). `match_rules` returns each new entry for its cues; the `rules` intent answers
   + verifies for a couple of the new topics; the existing matches are unchanged. Existing **716** stay green.
   No `.save(` in the web edges (guardrail holds).
2. **Manual smoke** — `python app.py ask "who should I captain from my-team?"` then `python app.py ask "why?"`
   (two separate commands) explains the last pick; `ask "how do player flags work?"` answers from the KB (✓).
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Backlog, ADR-091.

---

### 📝 Session Progress Log

**US-281 — remember the conversation across runs.** ✅ Done. **ADR-091** written first (the gate).
- New **`src/chat_context.py`**: `save_context` / `load_context` / `clear_context` persist one `Context` ↔ a
  local git-ignored JSON (`config.CHAT_CONTEXT_PATH = data/chat_context.json`) with a **timestamp + 2h TTL**
  (a stale "why?" past the TTL, a missing/corrupt file, or a shape drift → `None`, never a crash — saving is
  best-effort). `now`-injected → deterministic tests.
- **CLI `ask`** now loads the context → `converse` → saves the new one, so *"ask …"* then a **separate**
  *"ask why?"* resolves the follow-up (verified live). A `--forget` flag and asking *"forget"/"reset"* clear it.
- **CLI `chat`** resumes the saved context on start (prints "Resuming your last conversation") and persists
  each turn; a **"forget"** line drops it. `chat_transcript` gained a `context=` seed and now yields
  `(result, context)` so the caller can persist; a reset word yields a `None` context.
- **The web is untouched** — `web_streamlit` never imports the store; it keeps `st.session_state.chat_context`
  (per-session, no server write). The pure `ask.answer`/`converse` API is unchanged (persistence lives only in
  the CLI handler), so the web + tests are unaffected.
- **Tests (+8):** `chat_context` round-trip / TTL / clear / corrupt-safe; `chat_transcript` resume + forget;
  the CLI `--forget` flag + a two-run follow-up (*"captain"* → *"why?"* across invocations); a **guardrail**
  that no web edge imports/calls the store (distinct from the session_state key it happens to share the name
  with). **724** green, ruff clean.
- **Manual smoke:** `ask "who should I captain from all players?"` then a separate `ask "why?"` re-explains the
  pick; `ask "forget"` clears the file.

**US-282 — grow the curated rules KB.** ✅ Done.
- **8 new authoritative entries** in `fpl_rules.py::RULES` (13 → **21**): **flags** (🔴 unavailable / 🟡 75-50-25%
  doubt) · **preseason_transfers** (unlimited free before the GW1 deadline) · **chip_limits** (one chip per GW) ·
  **bench_points** (only the XI scores, except Bench Boost) · **wildcard_timing** (two per season, 2nd ~GW20) ·
  **leagues** (Classic total-points vs Head-to-Head 3/1/0) · **ranking** (Overall vs Gameweek rank) ·
  **team_value** (selling price = buy + ½ the rise). Each short + numeric where the number is the answer.
  `TOPIC_LABELS` extended to 21.
- **Routing extended too** — the new questions contain words that route to *squad* intents ("transfers",
  "wildcards", "bench"), so I added **specific** rules cues (`yellow flag`, `before gameweek`, `two chips`,
  `bench points`, `how many wildcards`, `head to head`, `overall rank`, `selling price`, … + `what does`) that
  win first **without hijacking** the imperative squad commands. All 8 now route to `rules` and answer
  **verified (✓)** from the KB, not the LLM's memory.
- **Only well-established rules** — nothing speculative (the KB exists precisely to avoid hallucinated rules).
- **Tests (+2):** each new topic answers its natural question; topic ids are unique. No routing regressions.
  **726** green, ruff clean.
- **Manual smoke:** *"what does the yellow flag mean?"*, *"how many wildcards do I get?"*, *"what is my selling
  price?"* etc. all answer from the KB with the ✓ trust line.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **716 → 726** (+10: chat-context store/resume/CLI +
the web guardrail, and KB coverage/uniqueness). Ruff clean; CI-parity green. **New ADR-091** (persisted chat
context). No analytics change — a CLI persistence layer + curated content; the grounding still verifies.

**Delivered**
- **US-281 — remember the conversation across runs (ADR-091).** A local, git-ignored, TTL'd `chat_context`
  store; the CLI `ask` loads→converse→saves (so *"ask …"* then a separate *"ask why?"* resolves) and `chat`
  resumes + persists per turn (a "forget" clears it). The pure `ask.answer`/`converse` API is untouched; the
  multi-user web keeps `session_state` (a guardrail test enforces it).
- **US-282 — grow the rules KB.** 8 new grounded entries (flags · preseason transfers · one-chip-per-GW · bench
  points · wildcard timing · leagues · ranking · team value) + the routing cues that make them verify ✓.

**What went well**
- **The pure core made the persistence a thin edge.** Because `converse` already takes an injected context and
  returns the next one, "persist across runs" was a small CLI wrapper (load → converse → save) — no change to
  the analytics or the web.
- **Designing around the read-only web.** Keeping the store CLI-only (and asserting the web never imports it)
  preserved the no-server-writes guarantee on the multi-user deploy — the constraint shaped a clean split.
- **Best-effort persistence.** Save/load swallow errors and a TTL bounds staleness, so a nice-to-have feature
  can never crash a turn or resurface an ancient answer.
- **Caught the real gap in US-282.** Growing the KB only helps if the question *routes* to the rules intent —
  spotting that "what does the yellow flag mean?" fell to free-form turned a content task into a content +
  routing task, so all 8 now verify ✓ instead of ℹ.

**Watch-outs / follow-ups**
- **A guardrail false-positive.** The web names a `session_state` key `chat_context`, so a naïve substring scan
  flagged it; the guardrail now targets the module import + its calls. A reminder that string-scan guardrails
  need precise anchors.
- **The rules routing is substring-based** — the new cues are specific enough not to hijack squad commands, but
  the cue list is growing; an LLM/intent classifier is the eventual answer (deferred).
- **Deferred:** web cross-session persistence (needs client storage; server-side would break read-only); a
  hosted LLM for the deploy's free-form tail; keep growing the KB as questions arrive.

See `Sprint110_Lessons_Learnt.md` for the detailed retro.
