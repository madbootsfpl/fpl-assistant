# Sprint 038: two new `ask` intents — start/bench + compare

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a gate + two grounded NL intents)
**Carried Over:** None (Sprint 037 closed clean)

> **Direction (owner's choice):** grow the natural-language layer (Phase 4) with the two most-asked
> weekly questions — *"who should I start/bench?"* and *"A or B?"* — both **grounded** and both
> showcasing the new **xMins** (a lineup decision *is* a minutes decision). The full probabilistic
> xMins and Data Hardening stay blocked until GW1 (2026-08-21, 17 days out).

---

### 🔎 Verified at planning (the standing lesson — two findings that shape the stories)

- **start/bench — TS is *already* optimal.** The xMins-weighted best-legal XI for TS **equals its
  declared XI** (bench = Dubravka/Diop/Slater/Kusi-Asare, clearly the four weakest) → **no swap to
  recommend today**. So the intent must answer *"your XI is already the best legal XI"* gracefully (and
  still show the ranked XI/bench + the closest call). Its value **grows in-season** when injuries/xMins
  force changes. Cleanly composable: `select_squad` (xMins-weighted `xp_by_id`) vs the declared XI.
- **compare — name-matching needs care.** A substring probe matched real players but exposed wrinkles:
  `"Haaland or B.Fernandes?"` also matched **`Fernandes`** (a *different* player — substring overlap),
  and `"compare Saka and Palmer"` matched **two** players named `Palmer` (ambiguity). So the gate must
  settle: **longest-match-wins + drop matches that are substrings of another**, **not-found** handling,
  and **ambiguity** (same web_name → ask to disambiguate, or take the higher-owned). `"Isak or
  Watkins"` matched cleanly.
- Still preseason (0 GWs); ClubElo up (intermittent). Both intents work preseason (xP is baseline-driven).

---

### 🧭 What's new — the weekly questions, grounded

Phase 4 answers captain/transfer/analyse today. This sprint adds the two questions a manager actually
asks each week: **start/bench** (the lineup decision — the best legal XI this week, xMins-weighted, and
the change vs your saved bench) and **compare** (A vs B — side-by-side xP, xMins, fixture, penalties,
with the analytics deciding which is stronger and the LLM only narrating). Both reuse the grounding
verifier (the ✓/⚠ trust line) and the structured-detail pattern (a table above the narration).

---

### 🎯 Sprint Goal

**Objective:** Two new grounded `ask` intents — **start/bench** (best legal XI vs the declared one,
xMins-weighted; graceful "already optimal") and **compare** (match N named players; a side-by-side
table; analytics decide the ranking, LLM narrates) — each with a structured detail table, `subjects`
for grounding, and the ✓/⚠ trust line.

#### Success Criteria
- [ ] Approach agreed (**ADR-039**) before code — routing keywords; the two decisions; **name-matching
      rules** (longest-match, dedupe substrings, not-found, ambiguity); grounding subjects; detail tables
- [ ] **start/bench** — `ask "who should I start from <squad>?"`: the xMins-weighted best legal XI, the
      swap(s) vs the declared bench (or "already optimal"), a ranked XI/bench detail table + ✓ line
- [ ] **compare** — `ask "A or B?"` / `"compare A and B"`: match the named players; a side-by-side table
      (xP, xMins, next fixture, penalty); the analytics state who's higher-xP; LLM narrates + ✓ line
- [ ] Name-matching is robust (the probe's wrinkles handled); a clear message on not-found / ambiguous
- [ ] Reuses `verify_grounding` (subjects = the players named) and the structured-detail pattern
- [ ] Optional LLM (degrades to decision + facts); existing intents unchanged; existing 343 stay green
- [ ] Tests (routing; name-matching edge cases; start/bench swap + no-swap; compare ordering) + live smoke
- [ ] Docs: ADR-039 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-112 | **Gate.** Both intents' design (**ADR-039**): routing; the start/bench decision (best legal XI vs declared, xMins-weighted, "already optimal" path) + the compare decision (**name extraction/matching** — longest-match, dedupe substrings, not-found, ambiguity — + side-by-side facts, analytics-decide ranking); grounding subjects; detail tables. Pressure-test name-matching + both paths on real data | Critical | ✅ Done | 0.5–1 session |
| US-113 | **start/bench intent** — route it; decide the best legal XI (xMins-weighted) and the change vs the declared bench (graceful "already optimal"); a ranked XI/bench detail table; `subjects` + ✓ line. Tests + smoke | High | ✅ Done | 1 session |
| US-114 | **compare intent** — extract & match N player names (robust per the gate); a side-by-side detail table (xP, xMins, fixture, penalty); analytics state the higher xP; `subjects` + ✓ line; not-found/ambiguous messaging. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-039 recorded + added to the ADR index — _US-112_
- [ ] Update Architecture changelog (two new `ask` intents) — _US-113/114_
- [ ] Update Handbook/README (the new questions) — _US-114_
- [ ] Update PROJECT_STATUS — _US-114_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — routing; name-matching edge cases (overlap, not-found, ambiguity);
   start/bench swap + no-swap; compare ordering; existing **343** stay green; no new dependency.
2. **Manual smoke test done** — `ask "who should I start from TS?"` (shows the XI/bench + the change or
   "already optimal" + ✓); `ask "Haaland or B.Fernandes?"` (side-by-side + who's higher + ✓); a
   not-found and an ambiguous name give a clear message.
3. **Documentation updated & checked** — ADR-039 + index, Architecture, Handbook, README, sprint board
   + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| start/bench + compare `ask` intents (grounded, xMins-weighted) | A multi-turn chat/REPL mode |
| Robust player-name extraction/matching | Fuzzy/spell-corrected names (exact/substring only, this sprint) |
| Reuse `verify_grounding` + structured detail | New verification modes (regenerate-on-fail is later) |
| Reuse `select_squad`, xMins, xP | Changing the existing captain/transfer/analyse intents |

**External Dependencies:** None beyond stored FPL data + the (optional) local LLM.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **Name-match overlap** ("Fernandes" ⊂ "B.Fernandes") | High | Longest-match-wins + drop matches that are substrings of another (gate rule; tested) |
| **Ambiguous names** (two "Palmer") | Med | Detect duplicates → ask to disambiguate (or take higher-owned); a clear message, never a silent wrong pick |
| **start/bench often "no change"** (well-built squad) | Med | Treat "already optimal" as a first-class, honest answer; still show the ranked XI/bench + closest call; value grows in-season |
| Overlap with `analyse` | Low | start/bench is the *lineup decision* (the swaps), not the health check; distinct framing |
| LLM invents a comparison verdict | Med | Analytics decide the ranking (higher xP stated as a fact); the LLM only narrates; ✓ verifies numbers + names |

---

### 🗝️ Gating decision (US-112 → ADR-039)

Settle before code — the risks are already probed. Proposed (confirm/redirect at "start US-112"):

1. **Routing.** Add two intents to `_INTENT_KEYWORDS`: **start/bench** (`start`, `bench`, `lineup`,
   `line-up`, `who should I play`) and **compare** (`compare`, ` or `, ` vs `, `versus`, `better`).
   First-match order matters; captain/transfer/analyse keep priority where they'd collide.
2. **start/bench decision.** Best legal XI for the saved 15 via `select_squad` on the **xMins-weighted**
   `xp_by_id`; diff against the declared XI → the swap(s) (bench→XI, XI→bench). No diff → "already the
   best legal XI." Subjects = the swapped players (or the XI when none). Detail = a ranked XI/bench table.
3. **compare decision.** Extract player names from the question by matching stored web_names
   (**longest-match-wins; drop a match that is a substring of another**); **not-found** → a clear
   message; **ambiguous** (duplicate web_name) → ask to disambiguate. For ≥2 matched players: a
   side-by-side table (xP over the horizon, xMins, next fixture, penalty) and a **fact** stating which
   has the higher xP (analytics decide; the LLM only explains). Subjects = the compared players.
4. **Grounded + optional, like the rest.** Both run `verify_grounding` (subjects supplied) and show the
   ✓/⚠ line; both degrade to decision + facts without the LLM; the facts/table are always shown.

**Worked examples (to run at the gate):** `"who should I start from TS?"` → "already optimal" +
ranked XI/bench; `"Haaland or B.Fernandes?"` → side-by-side, B.Fernandes higher xMins-weighted xP;
`"compare Saka and Palmer"` → ambiguity handled; `"Isak or Watkins"` → clean two-way compare.

---

### 📝 Session Progress Log

- **US-112 (gate) ✅** — Recorded **ADR-039**, design **pressure-tested on the live DB first**:
  - **Robust name-matching** (bounded substring + drop-substring-overlap + ambiguity + not-found)
    returned `[Haaland, B.Fernandes]` (dropping the spurious `Fernandes`), flagged `Palmer` ambiguous
    ×2, handled `Isak or Watkins` cleanly, and reported `foo and bar` as not found.
  - **start/bench** = `select_squad` on xMins-weighted xP **diffed against the declared XI**: TS →
    *already optimal* (a first-class answer); Haaland force-benched → *bring in Haaland, drop Diop*.
  Settled: routing (both after captain/transfer/analyse; **compare needs ≥2 matched players** so a stray
  " or " never forces a bogus compare); the two decisions carry `subjects` + a structured detail table;
  the analytics decide the compare ranking (higher xP as a fact), the LLM only narrates; both reuse
  `verify_grounding` + degrade without the LLM. ADR-039 added to the index.
- **US-113 (start/bench intent) ✅** — Routed `start_bench` (keywords `start`/`bench`/`lineup`), needs a
  squad like transfer/analyse. `_decide_start_bench` picks the best legal XI via `select_squad` on
  **xMins-weighted** xP, diffs it against the declared XI, and reports the swap(s) via `_lineup_change`
  (or "already the best legal XI" / "no saved bench"). New focused renderer `src/ui/startbench.py`
  (XI + bench, **xMins** + xP columns) as the structured detail; `subjects` = the whole squad (the
  lineup is about all of it); reuses `verify_grounding`. **+6 tests** (routing; the three `_lineup_change`
  branches; the no-squad message; the renderer) → suite **343 → 349**; ruff clean; no new dependency.
  **Live smoke** (`ask "who should I start from TS?"`): shows the recommended XI + bench with expected
  minutes, *"Change: none — already the best legal XI"*, grounded narration, and the ✓ trust line.
  (Swap detection proven at the gate: Haaland force-benched → "start Haaland — bench Diop".)
- **US-114 (compare intent) ✅** — Routed `compare` (`compare`/`versus`/` vs `/`better`/` or `, checked
  last so a stray "or" never steals a captain/transfer question). `_match_players` (bounded substring +
  drop-substring overlap + ambiguity, original-case keys for display) → `_decide_compare` ranks the
  named players by **xMins-weighted** xP and states the higher as a fact (analytics decide; the LLM
  only narrates). New `src/ui/compare.py` side-by-side table (xMins, xP, fixture, penalty).
  Not-found / ambiguous / <2 return a **soft, specific `message`** via a new `assemble` short-circuit —
  never a silent wrong pick. **+8 tests** (routing precedence; matcher overlap/ambiguity/bounded; the
  two message branches; the assemble short-circuit; the renderer ordering) → suite **349 → 357**; ruff
  clean; no new dependency. **Live smoke:** `ask "Haaland or B.Fernandes?"` → side-by-side (Haaland 29.0
  first), grounded narration, ✓ line; `"compare Saka and Palmer"` → ambiguity message; `"foo and bar"`
  → not-found message.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories. **US-112** — ADR-039, with the name-matcher + both start/bench paths
  pressure-tested on live data. **US-113** — the **start/bench** intent (best legal XI vs declared,
  xMins-weighted; graceful "already optimal"; `ui/startbench.py`). **US-114** — the **compare** intent
  (robust `_match_players`; side-by-side `ui/compare.py`; analytics decide the ranking; soft not-found /
  ambiguous messages). Tests 343 → **357**; one ADR; **no new dependency**. `ask` now answers five
  weekly questions.
* **Carried Forward:** None.
* **Key Artifacts / Decisions:** ADR-039; `_decide_start_bench` + `_lineup_change`; `_match_players` +
  `_decide_compare`; `ui/startbench.py` + `ui/compare.py`; the `assemble` soft-`message` short-circuit.

#### Retrospective
* **What Went Well?**
  - **The gate probe pre-solved the hard part.** Name-matching *looked* trivial and wasn't — the probe
    exposed the `Fernandes` ⊂ `B.Fernandes` overlap and the duplicate `Palmer` before any code, so
    US-114 implemented settled rules instead of discovering them mid-build.
  - **Pure composition again.** Both intents are `select_squad` / xP / xMins / the verifier / the shared
    table — no new analytics. The whole sprint added two renderers and some glue.
  - **Honest edge-cases as first-class answers** — "already optimal" (start/bench) and a specific
    not-found / ambiguous *message* (compare) beat a silent wrong pick or a generic error.
  - **The grounding held for free** — both intents reuse `verify_grounding`; the ✓ line just works, and
    "analytics decide, LLM narrates" kept the compare verdict honest.
* **What Could Be Improved?**
  - **start/bench often says "no change"** on a well-built squad (TS is already optimal); its punch
    lands **in-season** when injuries force lineup changes. Deliberate, but worth remembering.
  - **Routing "or" is broad** — `start X or Y` routes to start/bench (has "start") not compare. Rare;
    compare needs ≥2 players and bails gracefully. A smarter router could reconcile the two later.
  - **The no-history → 90-xMins quirk shows through** — a benched no-baseline player reads "90 mins,
    0.0 xP". Honest (correctly benched) but visually odd; the Phase-5 model resolves it.
* **Lessons Learned?**
  - Probe the deceptively-simple bit (string matching on real names) — that's where the bugs hide.
  - Give every intent a graceful, *specific* answer for its failure modes, not a generic fallback.
  - When two surfaces answer overlapping questions, keep them distinct (lineup decision vs health check)
    and let routing order + a required-signal (≥2 players) disambiguate.
* **Action Items for Next:**
  - [ ] (Backlog) a smarter router (reconcile "start X or Y" → compare when no squad + 2 players).
  - [ ] The full probabilistic xMins (Phase 5, post-GW1) resolves the no-history quirk.
  - [ ] Keep the gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4 (further intents / a chat mode / stronger
verification), the web UI (Phase 2), or wait for GW1 to do Data Hardening + the full Phase-5 xMins.

**Completion Date:** 2026-08-04
**Final Notes:** `ask` now covers the five weekly questions — captain, transfer, analyse, start/bench,
compare — all grounded, xMins-aware, and optional. The gate's real-data probe turned the sprint's one
genuine risk (name-matching) into a solved problem before code. Sprint outcome: **Successful** — 3/3
stories, zero roll-over, DoD held (38th).
