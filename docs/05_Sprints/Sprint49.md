# Sprint 049: Squad-scoped fixtures — "which of my players have good fixtures?"

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2 working sessions (a gate + a third fixtures mode + a small renderer + chat/docs)
**Carried Over:** None (Sprint 048 closed clean)

> **Direction (owner):** the piece deferred from Sprint 048 — a **squad-scoped** fixtures answer. Today
> `ask "fixtures…"` does the league ranking and a single team's schedule; add *"which of my (TS's)
> players have good fixtures?"* — rank the teams **your squad has players at** by their fixture
> difficulty, so you see whose runs are kind (and how many of your players each affects).

---

### 🔎 Verified at planning (the standing lesson — the mode is a filter + a join)

- **A saved squad maps cleanly to teams.** TS's 15 players span **11 teams**; ranking those teams by
  their own FDR (next 5) reads: *LIV 2.6 (×2) · LEE/MCI/MUN/TOT 2.8 · … · BOU/FUL 3.6 (×1)*. So the mode
  is a **filter** (the league FDR restricted to the squad's teams) **+ a join** (a player-count per team)
  — no new analytics.
- **The player-count is the point.** *"3 of your players are at City, and City have a good run"* is the
  signal squad-scoping adds over the plain league ranking — worth a column.
- **It's a third mode of the existing intent.** Precedence: a **specific team** named → its schedule; else
  a **saved squad** named → squad-scoped ranking; else → the league ranking. Squad names ("TS") never
  collide with team codes/names.
- **Chat comes free.** `_dispatch` already threads the routed `squad` to `_decide_fixtures`, so a
  squad-scoped fixtures turn works in `chat` with no extra wiring.
- **Needs a named squad.** Like `analyse`/`transfer` (no auth), "my players" is only knowable when a
  saved squad is named; no name → the league ranking (a fine answer), not a forced prompt.
- FPL difficulty (ClubElo deferred, intermittent); still preseason (GW1 deadline 2026-08-21).

---

### 🧭 What's new — fixtures through the lens of your squad

The `fixtures` intent gains a third mode: name a saved squad and it ranks **that squad's teams** by their
upcoming fixture difficulty, each with a **player-count**. Same discipline (grounded + verified), same
intent, works in `ask` and `chat`.

---

### 🎯 Sprint Goal

**Objective:** a squad-scoped mode in `_decide_fixtures` — a saved squad named (and no specific team) →
rank the squad's teams by FDR (easiest default, hardest on a cue), each showing how many of the squad's
players it holds; a small renderer with a Players column; grounded facts + the ADR-037 verifier; working
in `ask` + `chat`. A gate settles the ranking lens.

#### Success Criteria
- [ ] Approach agreed (**ADR-049**) — the trigger + precedence (team → squad → league); the **ranking
      lens** (team-level with counts vs player-level); the renderer; needs-a-named-squad; horizon; how it
      flows through `ask` + `chat`
- [ ] `_decide_fixtures` gains the squad mode — squad → player teams (+counts) → league FDR filtered to
      those teams → ranked; easiest default, hardest on a cue; horizon parsed
- [ ] A small renderer (a Players column) — reused/extended, not a bent player table
- [ ] Grounded facts (teams, avg difficulty, player-count, opponents) + subjects; verifier each turn
- [ ] Works in **both** `ask` and `chat` (squad already threaded via `_dispatch`)
- [ ] Tests (squad mode ranks the squad's teams with counts; precedence — a team still wins, no squad →
      league; easiest/hardest; a squad with no current players / unknown squad) + smoke
- [ ] Docs: ADR-049 + index, Architecture, Handbook, README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-145 | **Gate.** Squad-scoped design (**ADR-049**): trigger + precedence (team → squad → league); the **ranking lens — team-level (with counts) vs player-level** (the owner call); the renderer; needs-a-named-squad; horizon; how it flows to `ask` + `chat`. Pressure-test (done: TS → 11 teams ranked by FDR + counts on real data) | Critical | ✅ Done | 0.5 session |
| US-146 | **The squad mode** — squad → players → each player's team FDR, ranked, in `_decide_fixtures`; a small `render_squad_fixtures`; the possessive-aware `_squad_name` fix; grounded facts; thread `squad` into the fixtures dispatch. Tests | High | ✅ Done | 1 session |
| US-147 | **Chat + docs** — verify it in `converse`/`chat`; a smoke across both surfaces; docs (Architecture, Handbook, README, PROJECT_STATUS) | High | ✅ Done | 0.5–1 session |

#### Technical Tasks & Maintenance
- [x] ADR-049 recorded + added to the ADR index — _US-145_
- [x] Update Architecture changelog (squad-scoped fixtures) — _US-146_
- [x] Update Handbook (a lesson) + README (the mode) — _US-147_
- [x] Update PROJECT_STATUS — _US-147_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — squad mode ranks the squad's teams with player-counts; precedence (a named
   team still gives its schedule; no squad → league ranking); easiest/hardest; a squad with no current
   players → a message; existing **416** stay green; no new dependency.
2. **Manual smoke test done** — `ask "which of TS's players have the best fixtures?"` (and in `chat`),
   with the ✓/⚠ trust line; a named team still returns its schedule; no squad still gives the league
   ranking.
3. **Documentation updated & checked** — ADR-049 + index, Architecture, Handbook, README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A squad-scoped FDR ranking (team-level, player-counts) in `ask` + `chat` | Per-player xP × fixtures (that's closer to `analyse`) |
| Reuse the league FDR; a small Players-column renderer | The custom (ClubElo) difficulty in `ask` — still deferred |
| Needs a named saved squad (else the league ranking) | Auto-detecting "my" squad without a name |

**External Dependencies:** None.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Precedence confusion (team vs squad vs league) | Med | A clear order — specific team wins, then squad, then league; tests pin each |
| The lens overlaps `analyse` | Low | Team-level FDR + counts (a fixtures view), not per-player xP; `analyse` stays the squad-health tool |
| A squad with departed players / unknown squad | Low | Filter to current players; empty → a clear message (the saved-squad pattern) |
| Grounding of a new fact shape | Low | Same discipline — self-describing facts + the ADR-037 verifier every turn |

---

### 🗝️ Gating decision (US-145 → ADR-049)

Settle before code — the mode is a filter+join, proven on real data. Proposed (confirm/redirect at
"start US-145"):

1. **Trigger + precedence.** A fixtures question naming a **saved squad** (and no specific team) → the
   squad mode. Order: a specific **team** → its schedule; else a **squad** → squad-scoped ranking; else →
   the league ranking. No named squad → league (not a forced prompt).
2. **The ranking lens — the owner call.** *Propose team-level:* rank the squad's **teams** by FDR, each
   with a **player-count** (concise; the count is the signal). *Alternative:* one row **per player** (15
   rows) — more granular but noisier and overlapping `analyse`.
3. **Renderer.** A small dedicated render (or extend `render_fdr_table`) adding a **Players** column;
   easiest default, hardest on a cue; "next N" horizon (default 5); FPL difficulty.
4. **Surfaces.** `ask` + `chat` via `_dispatch` (squad already threaded); grounded + verified.

**Worked example (probed):** *"which of TS's players have the best fixtures?"* → LIV 2.6 (×2) · LEE/MCI
(×3)/MUN/TOT 2.8 · … · BOU/FUL 3.6 — the squad's 11 teams, ranked, with counts.

---

### 📝 Session Progress Log

- **US-145 (gate) ✅** — Recorded **ADR-049**. Settled: a **third `fixtures` mode** by precedence
  (specific **team** → schedule; else **saved squad** → squad-scoped ranking; else **league**); the
  owner's lens call — **player-level** (one row per squad player: Player · Team · Avg FDR · Next
  opponents, ranked by the player's team FDR; easiest default, hardest on a cue) over team-level-with-
  counts; a small dedicated `render_squad_fixtures`; needs a **named squad** (else league); "next N"
  horizon; FPL difficulty; `ask` + `chat` via `_dispatch` (squad already threaded); grounded + verified.
  - **Bug caught at the gate:** *"which of **TS's** players…"* routed with **squad None** — the
    possessive "TS's" is one token, so `_squad_name` (whitespace split) never matched "TS". Fix (US-146):
    make **`_squad_name` possessive-aware** (strip a trailing `'s`), a general win for every squad-scoped
    intent. Worked example (probed): TS players rank *Virgil/Szoboszlai (LIV) 2.6 … Truffert (BOU)/
    Kusi-Asare (FUL) 3.6*. ADR-049 indexed.
- **US-146 ✅** — The squad mode. **`_squad_name` is now possessive-aware** (strips a trailing `'s`, so
  *"TS's players"* → TS) — a general fix. Added **`_decide_squad_fixtures`** (squad → current players →
  each player's team `team_fdr` → sorted, easiest default / hardest on a cue; grounded per-player facts),
  the precedence in `_decide_fixtures` (team → squad → league), and a small **`render_squad_fixtures`**
  (Player · Team · Avg FDR · Next opponents). Threaded the routed `squad` through the fixtures
  `_dispatch`.
  - **Tests (421 total, +5; in `test_ask_fixtures.py`):** `_squad_name` resolves the possessive; the
    squad mode ranks players by their team (easiest, then hardest reverses); a named **team beats a
    squad** (precedence); a squad with no current players → a message.
  - **Smoke (live DB):** `ask "which of TS's players have the best fixtures?"` ranks the 15 — *Virgil/
    Szoboszlai (LIV) 2.6 → … → Truffert (BOU)/Kusi-Asare (FUL) 3.6*; the possessive now routes to the
    squad mode.
  - **Docs:** Architecture §12 changelog (Sprint 049). _Chat verification + Handbook/README/PROJECT_STATUS
    are US-147._
- **US-147 ✅** — Verified the squad mode in `chat` and finished the docs. No new code — the `_dispatch`
  threading (US-146) already made it live in `converse`/`chat`.
  - **Smoke (live DB + Ollama, `chat`):** *which of TS's players have the best fixtures? → why? → …
    hardest fixtures?* — the squad mode answered all three (the **"why?"** follow-up re-narrated Virgil,
    and hardest reversed the order), each with a ✓ trust line; the possessive routed correctly.
  - **Docs:** README (a squad-scoped example), Handbook §21 ("a third mode, chosen by precedence" + the
    verify-the-real-phrasing lesson), PROJECT_STATUS (three fixtures modes + Tests 421 / ADRs 49 + the
    possessive note).
  - No tests changed (US-146 covered the mode, precedence and possessive; the chat path reuses the
    already-tested `_dispatch`).

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — all three stories delivered under the gate (US-145 / ADR-049). The `fixtures`
intent gained a **third mode**: name a saved squad and it ranks that squad's **players** by their team's
fixture run — the squad-relative view a manager reads before a move. **421 tests** (was 416, +5), **49
ADRs**, ruff clean, no new analytics.

**Delivered**
- **US-145 (gate)** — ADR-049: the precedence ladder (team → squad → league); the owner's lens call
  (**player-level**); the possessive-`_squad_name` fix; needs-a-named-squad.
- **US-146** — `_decide_squad_fixtures` (player → team FDR → sort), the possessive-aware `_squad_name`, a
  small `render_squad_fixtures`, and threading `squad` through the fixtures `_dispatch`.
- **US-147** — verified in `chat`; docs across README, Handbook, PROJECT_STATUS.

**What went well**
- **A new mode as a join, not an engine** — squad-scoped fixtures is *player → its team's `team_fdr` →
  sort* plus a small renderer; the cheapest feature was again the one that reused what existed.
- **The gate probe caught a real routing bug** — *"which of **TS's** players…"* resolved to no squad
  (the possessive is one token). A one-line fix (strip a trailing `'s`) rescued the natural phrasing
  *and* every other squad-scoped intent (captain/analyse/transfer).
- **Live in `chat` for free** — the shared `_dispatch` threading meant no chat wiring, and the *"why?"*
  follow-up re-narrates a squad-fixtures answer.

**Challenges / how they were handled**
- **Precedence (team vs squad vs league)** — settled as a clear ladder in one decision function; tests
  pin each branch (a named team still beats a squad).
- **Overlap with `analyse`** — kept this a *fixtures* lens (team difficulty per player), not xP, so
  `analyse` stays the squad-health tool.

**Carried forward:** None.
