# Sprint 048: A fixtures / FDR `ask` intent — "who has the best fixtures?"

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2–3 working sessions (a gate + the intent + wiring/chat/docs)
**Carried Over:** None (Sprint 047 closed clean)

> **Direction (owner):** *more Phase 4* → a **fixtures / FDR `ask` intent**. A routing probe showed
> every fixtures question falls straight through to the help message today — *"who has the best fixtures
> over the next 5?"*, *"when does Arsenal play?"* — **even though the analytics already exist**
> (`team_fdr`, `team_schedule`). Close the single biggest visible gap by wiring them into `ask`/`chat`.

---

### 🔎 Verified at planning (the standing lesson — the analytics + renderers already exist)

- **Both engines produce grounded output on the live DB.** `team_fdr(upcoming, next_n=5, source="fpl")`
  ranks the league (easiest: *LIV 2.6 · TOT 2.8 · MUN 2.8*; hardest: *BOU/FUL 3.6*), each row carrying
  `avg_difficulty` + the `opponents` list. `team_schedule(upcoming, "ARS")` gives *GW1 COV (H) diff 2,
  GW2 AVL (A) diff 4, …*. No new analytics needed — this is pure Phase-4 wiring.
- **The renderers exist too** — `render_fdr_table` and `render_team_fixtures` — so the `ask` detail
  table is a reuse, exactly like the transfer plan / shortlist.
- **A clean routing slot.** Every fixtures phrasing (*"best fixtures"*, *"when does Arsenal play?"*,
  *"who does Man City play?"*, *"next opponents for Spurs"*) routes to **None** today — so a new
  `fixtures` intent collides with nothing.
- **Team names resolve.** Teams carry a full `name` + a `short_name` (ARS, MCI, TOT). A couple are
  colloquial (*Spurs*=TOT, *Man City*=MCI, *Man Utd*=MUN) and users may type *Tottenham* / *Man United*
  — so team matching needs the name, the code, and a small alias set (gate to pin the extent).
- **FPL difficulty is the safe default.** ClubElo (the `custom` source) is intermittent; the `ask`
  layer stays simple — FPL default, custom deferred.
- Still preseason (0 GWs; GW1 deadline 2026-08-21).

---

### 🧭 What's new — ask about fixtures in plain English

One `fixtures` intent, two modes: a **league FDR ranking** (*"who has the best / hardest fixtures over
the next N?"*) and **one team's schedule** (*"when does Arsenal play?"*, *"who does City play?"*). Both
reuse the existing analytics + renderers, both grounded + verified (ADR-037), and both work one-shot
(`ask`) and in a conversation (`chat`).

---

### 🎯 Sprint Goal

**Objective:** a `fixtures` `ask` intent that answers league-FDR *and* single-team-schedule questions,
grounded on the existing `team_fdr` / `team_schedule` (FPL difficulty), reusing the existing renderers;
routed deterministically; working in both `ask` and `chat`. A gate settles the modes + the scope.

#### Success Criteria
- [ ] Approach agreed (**ADR-048**) — the two modes; team resolution (name/code/alias extent);
      easiest-vs-hardest default; the horizon; FPL-default source; the owner's scope call (squad-scoped
      fixtures in or out); how it flows through `ask` + `chat`
- [ ] Routing — a `fixtures` intent + keywords, placed to avoid collisions (proven: they fall through
      today)
- [ ] `_match_team(question, teams)` — resolve a team by full name / short code / a small alias set;
      ambiguity + not-found handled (a clear message, never a wrong guess)
- [ ] `_decide_fixtures(store, question)` — team named → schedule mode; else → league FDR ranking
      (easiest default, hardest on "hard/tough/avoid"); horizon parsed (default 5); grounded facts +
      the reused renderer as `detail`
- [ ] Wired through `_dispatch` so it works in **both** `ask` and `chat`; grounding verified each turn
- [ ] Tests (routing; team match incl. alias + ambiguity; FDR-ranking mode; team-schedule mode;
      hardest keyword; a no-team-found message) + smoke
- [ ] Docs: ADR-048 + index, Architecture, Handbook, README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-142 | **Gate.** Fixtures-intent design (**ADR-048**): the two modes (league FDR / team schedule); team resolution (name/code/alias extent); easiest-vs-hardest default; horizon; FPL-default source; **squad-scoped fixtures — in or out** (the owner call); how it flows to `ask` + `chat`. Pressure-test (done: both engines + renderers + team names on real data) | Critical | ✅ Done | 0.5–1 session |
| US-143 | **The intent** — `_match_team`; `_decide_fixtures` (both modes; grounded facts; reuse `render_fdr_table` / `render_team_fixtures`); routing keywords; the `_dispatch` branch. Tests | High | ✅ Done | 1 session |
| US-144 | **Chat + CLI + docs** — verify it in `converse`/`chat`; a smoke across both surfaces; docs (Architecture, Handbook, README, PROJECT_STATUS) | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-048 recorded + added to the ADR index — _US-142_
- [x] Update Architecture changelog (fixtures `ask` intent) — _US-143_
- [x] Update Handbook (a lesson) + README (the intent) — _US-144_
- [x] Update PROJECT_STATUS — _US-144_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — routing to `fixtures`; `_match_team` (name/code/alias, ambiguity,
   not-found); the FDR-ranking mode; the team-schedule mode; the hardest keyword; grounded facts;
   existing **407** stay green; no new dependency.
2. **Manual smoke test done** — `ask "who has the best fixtures over the next 5?"`, `ask "when does
   Arsenal play?"`, and the same inside `chat`, each with the ✓/⚠ trust line.
3. **Documentation updated & checked** — ADR-048 + index, Architecture, Handbook, README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| League FDR ranking + single-team schedule, in `ask` + `chat` | A `next` rank-offset follow-up for fixtures — not a natural "Nth pick" |
| Team resolution (name / code / a small alias set) | Full fuzzy team matching / every nickname — a pragmatic set only |
| FPL difficulty (the default source) | The custom (ClubElo) difficulty in `ask` — deferred (intermittent) |
| The owner's squad-scoped decision at the gate | (If deferred) "which of my players have good fixtures?" |

**External Dependencies:** None (ClubElo not required; FPL difficulty is built in).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Team name mis-resolves (wrong or ambiguous) | Med | Match name/code/alias; on ambiguity or none, a clear message — never a silent wrong guess (the `compare` lesson) |
| Routing collision as intents grow | Low | Proven the phrasings fall through today; place the keywords carefully; a routing test |
| A fixtures answer the LLM embellishes | Low | Same discipline — grounded facts + the ADR-037 verifier every turn |
| "best fixtures" ambiguous (easiest vs hardest) | Low | Default easiest (who to target); "hard/tough/avoid/worst" → the hard end; state which in the header |

---

### 🗝️ Gating decision (US-142 → ADR-048)

Settle before code — the analytics, renderers and team names are probed. Proposed (confirm/redirect at
"start US-142"):

1. **The two modes.** A **team named** → its schedule (`team_schedule`, reuse `render_team_fixtures`);
   **no team** → the league FDR ranking (`team_fdr`, reuse `render_fdr_table`), **easiest** by default,
   **hardest** when the question says hard/tough/avoid/worst.
2. **Team resolution.** `_match_team` on the full name + short code + a small alias set (*Tottenham*→TOT,
   *Man United/Man Utd*→MUN, *Man City*→MCI); ambiguity / not-found → a clear message.
3. **Horizon + source.** "next N" parsed (default 5); FPL difficulty (custom/ClubElo deferred).
4. **Surfaces.** Both `ask` and `chat` (via `_dispatch`); grounded + verified. No `next`-offset follow-up
   for fixtures (it isn't a ranked-pick list); a fresh fixtures turn in `chat` just works.
5. **The owner call — squad-scoped fixtures?** *"which of my players have the best fixtures?"* (squad →
   player teams → FDR) is useful but more work and overlaps `analyse`. *Propose: two modes this sprint,
   squad-scoped deferred — confirm/redirect at the gate.*

**Worked example (probed):** *"best fixtures next 5"* → LIV 2.6 · TOT 2.8 · MUN 2.8; *"when does Arsenal
play?"* → GW1 COV (H), GW2 AVL (A), GW3 CHE (H)… — both grounded, straight from the existing engines.

---

### 📝 Session Progress Log

- **US-142 (gate) ✅** — Recorded **ADR-048**, the design settled off the planning probes + one owner
  decision. Settled: **one `fixtures` intent, two modes** — a **team named** → its schedule
  (`team_schedule`, reuse `render_team_fixtures`), **no team** → the **league FDR ranking** (`team_fdr`,
  reuse `render_fdr_table`; **easiest** default, **hardest** on hard/tough/avoid/worst); a `_match_team`
  on name/short-code/a small alias set (*Tottenham/Spurs*→TOT, *Man Utd*→MUN, *Man City*→MCI,
  *Forest*→NFO) that **never guesses** (the ambiguous bare *"City"* and out-of-league *"Wolves"* → a
  message, ≥2 teams → clarify); "next N" horizon (default 5); **FPL difficulty only** (ClubElo deferred);
  wired via the shared `_dispatch` so it works in **both `ask` and `chat`**, grounded + verified; **no
  `next`-offset** for fixtures (not a ranked-pick list). Owner's call: **two modes this sprint,
  squad-scoped fixtures deferred**. Worked example: *best fixtures next 5* → LIV 2.6 · TOT 2.8 · MUN 2.8;
  *when does Arsenal play?* → GW1 COV (H), GW2 AVL (A), GW3 CHE (H). ADR-048 indexed.
- **US-143 ✅** — The working `fixtures` intent in `src/ask.py`. Added `_match_team` (name / **case-
  sensitive** short code / alias set; never guesses), `_fixture_horizon` ("next N", default 5, capped
  38), `_decide_fixtures` (team named → `team_schedule` + `render_team_fixtures`; else `team_fdr` +
  `render_fdr_table`, easiest default / hardest on a cue), grounded facts (venue humanised, avg
  difficulty), a `fixtures` keyword tuple (placed last), and the `_dispatch` branch (so it's live in
  `ask` *and* `chat`). Extended `render_fdr_table` with a `hardest` flag for the footer (CLI default
  unchanged).
  - **Tests (416 total, +9; new `test_ask_fixtures.py`):** routing to fixtures + earlier intents still
    win; `_match_team` resolves name/code/alias and never guesses (the bare "new" ≠ code NEW; ≥2 teams →
    list; no team → None); `_fixture_horizon` parses/defaults/caps; the team-schedule mode (venue + avg
    facts); the league ranking (easiest, then hardest reverses); an ambiguous-team clarify; no-fixtures →
    None.
  - **Smoke (live DB + Ollama):** `ask "who has the best fixtures over the next 5?"` → LIV 2.6 · TOT/MUN
    2.8 …; `"which teams have the hardest fixtures?"` → FUL/BOU 3.6; `"when does Arsenal play next?"` →
    GW1 COV (H) … — each with a ✓ trust line. (The narrator once described a venue loosely; numbers/names
    still trace, so ✓ holds and the table is the stated truth.)
  - **Docs:** Architecture §12 changelog (Sprint 048). _Chat verification + Handbook/README/PROJECT_STATUS
    are US-144._
- **US-144 ✅** — Verified the intent in a **`chat`** conversation and finished the docs. No new code —
  the `_dispatch` branch (US-143) already made fixtures live in `converse`/`chat`.
  - **Smoke (live DB + Ollama, `chat`):** *best fixtures next 5 → when does Arsenal play? → who does Man
    City play? → why?* — each turn answered (both modes), and the **"why?"** follow-up re-narrated the
    last team's schedule for free (fixtures stores a decision with facts, so the why-family works).
    Every turn carried a ✓ trust line.
  - **Docs:** README (intent + two examples), Handbook §21 ("a new intent from analytics you already
    have"), PROJECT_STATUS (commands + Tests 416 / ADRs 48 + the fixtures line + "eight intents").
  - No tests changed (US-143 covered routing + both modes + resolution; the chat path reuses the
    already-tested `_dispatch`).

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — all three stories delivered under the gate (US-142 / ADR-048). `ask`/`chat`
now answer fixtures questions — a league **FDR ranking** and a **single team's schedule** — closing the
biggest routing gap the Sprint-047 probe found. **416 tests** (was 407, +9), **48 ADRs**, ruff clean,
**no new code in the analytics or UI layers** (pure reuse).

**Delivered**
- **US-142 (gate)** — ADR-048: the two modes; `_match_team` that never guesses; FPL-default source;
  the owner's scope call (two modes this sprint, **squad-scoped deferred**).
- **US-143** — `_match_team` + `_fixture_horizon` + `_decide_fixtures` (both modes, grounded facts,
  reusing `team_fdr`/`team_schedule` + their renderers), the routing keyword, the `_dispatch` branch;
  a `hardest` footer flag on `render_fdr_table`.
- **US-144** — verified in `chat`; docs across README, Handbook, PROJECT_STATUS.

**What went well**
- **The gap was tiny to close** — the analytics *and* the renderers already existed, so the whole
  feature was a decision function + one router keyword. Checking what's already built beat designing
  anything new.
- **It came live in `chat` for free** — the shared `_dispatch` (ADR-047) meant no chat wiring, and the
  **"why?"** follow-up even re-narrates a fixtures answer (it stores a decision with facts).
- **Team resolution never guesses** — the `compare` rule applied: the ambiguous bare "City" and the
  out-of-league "Wolves" get a message, ≥2 teams get a clarify, and a typed code matches without the
  common word "new" false-firing.

**Challenges / how they were handled**
- **"play" is a broad keyword** — needed to catch *"when does Arsenal play?"* without stealing other
  intents. Resolved by placing `fixtures` **last** in the routing order, so every more-specific intent
  matches first; a routing test pins it.
- **Case-sensitivity of short codes** — a lowercased match made "the **new** gameweek" resolve to NEW.
  Fixed by matching the code **case-sensitively** (typed codes are uppercase), with a test.
- **The "easiest" footer** — `render_fdr_table` hardcoded "easiest run"; added a `hardest` flag so the
  hardest-mode footer is honest (CLI default unchanged).

**Carried forward:** None.
