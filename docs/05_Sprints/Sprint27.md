# Sprint 027: Captain Suggestions (Phase 3 begins)

**Dates:** 2026-08-03
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~3 working sessions (the first Phase 3 / decision-support feature)
**Carried Over:** None (Sprint 026 closed clean)

---

### 🔎 Verified at planning (the standing lesson — probed the live API first)

Captain suggestions lean on penalty duties + fixtures, so I checked what's actually available:

- **`penalties_order` is populated preseason** — **20** first-choice penalty takers (one per club:
  Haaland, B.Fernandes, Saka, Thiago…). A real captaincy signal (penalty takers carry a higher
  ceiling). Also present: `direct_freekicks_order`, `corners_and_indirect_freekicks_order` (set-piece
  involvement) — penalties is the one that matters most.
- **Opponent + home/away are derivable** from fixtures we already store (`team_h`/`team_a` +
  short names via `get_upcoming_fixtures`), keyed off a player's `team_id`. **No new data needed**
  for the "who/where" context.
- **The enriched xP already surfaces sensible captain candidates** — next-GW `xp` tops out at
  B.Fernandes, Saka, Haaland (the multi-season baseline, ADR-028). Captaincy is a *one-week*
  decision, so **horizon = 1** is the natural default.
- **We already own the pieces this composes:** availability (`is_unavailable`, ADR-023) and saved
  squads (`SquadStore`, ADR-024).

**What this means:** captaincy is a **decision-support layer on the xP we just enriched**, not new
modelling — rank by next-GW xP, filter to who'll actually play, and *explain the pick*. FPL-native;
**no new dependency**. ClubElo re-checked — still down (timeout).

---

### 🧭 What's new — the app starts *recommending*, not just *ranking*

Every feature so far ranks or optimises; this one gives a **recommendation with a reason** — the
first Phase 3 step. The headline use case composes two Phase 1/2 features: **"who do I captain from
*my* squad this week?"** — captain candidates drawn from a **saved squad** (ADR-024), scored by the
**enriched xP** (ADR-028), filtered to the **available** (ADR-023), and annotated with the opponent,
venue, and penalty duty so the human sees *why*.

Architecturally it stays honest: the ranking metric is xP (no new score invented); penalties are
**context, not a multiplier** (a penalty taker's returns are already in their xP — double-counting
would be wrong). Availability is the one hard filter (a captain who doesn't start is a wasted week).

---

### 🎯 Sprint Goal

**Objective:** A `captain` command that recommends the top 3–5 captain picks for the next gameweek —
ranked by the enriched xP, filtered to available players, and **explained** (opponent, home/away,
penalty duty). Two modes: **global** (planning) and **`--squad <name>`** (captain from your own
saved squad — the real weekly question).

#### Success Criteria
- [ ] Approach agreed (**ADR-029**) before code — metric, modes, penalties-as-context, horizon
- [ ] `penalties_order` ingested (new column, generic migration) + on the `Player` model
- [ ] Captain analytics: rank available candidates by next-GW xP; annotate opponent + venue + pen duty
- [ ] `captain` command (global top-N) + a view that **explains each pick** (not just a number)
- [ ] `captain --squad <name>` — candidates drawn from a saved squad (reuses `SquadStore`)
- [ ] Unavailable players excluded (a captain must be nailed-on); penalty duty is **context, not a
      score multiplier** (no double-counting)
- [ ] Tests (ranking, availability filter, annotation, squad mode) + **manual smoke on live data**
- [ ] Docs: ADR-029 + index, Architecture changelog, Handbook, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-080 | **Gate.** Captain-suggestion design (**ADR-029**): metric = next-GW xP (availability-filtered); penalties as **context not a multiplier** (avoid double-counting); modes = global + `--squad`; horizon 1; the "explain the pick" principle. Pressure-test on real candidates | Critical | ✅ Done | 0.5 session |
| US-081 | **Captain analytics + command (global)** — ingest `penalties_order` (migration + model); a `captain_picks` analytics fn (rank by xP, filter unavailable, annotate opponent/venue/pen); the `captain` command + an explain-why view. Tests + smoke | High | ✅ Done | 1.5 sessions |
| US-082 | **`captain --squad <name>`** — draw candidates from a saved squad (reuse `SquadStore`); handle a missing squad / departed players gracefully. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-029 recorded + added to the ADR index — _US-080_
- [x] Update Architecture changelog (first Phase 3 feature) — _US-081_
- [x] Backlog: ceiling/variance ("differential") captaincy noted as a future enhancement — _US-081_
- [x] Update Handbook (Ch 21 — from ranking to recommending; reuse a metric + explain) — _US-082_
- [ ] Backlog: note ceiling/variance ("differential") captaincy as a future enhancement — _US-081_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — ranking, availability filter, annotations, squad mode; existing 242 green.
2. **Manual smoke test done** — `captain` and `captain --squad` on live data; the top picks are
   sensible and the reasons read correctly.
3. **Documentation updated & checked** — ADR-029 + index, Architecture, Handbook, sprint board +
   PROJECT_STATUS (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Rank captains by next-GW xP, availability-filtered | A new captain *score* (xP is the metric) |
| Explain the pick (opponent, venue, penalty duty) | Ceiling/variance ("differential") captaincy — a follow-on |
| Global + `--squad` (from a saved squad) modes | Transfer suggestions / team analyser (later Phase 3) |
| Ingest `penalties_order` | Live-lineup / rotation (xMins) weighting — a later phase |

**External Dependencies:**
- [ ] FPL bootstrap (`penalties_order`, verified populated) — already fetched by `refresh`.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Double-counting penalties (in xP *and* as a bonus) | Med | Rank by xP only; penalties are **shown as context**, not added to the score |
| Recommending an injured/doubtful player | High | Hard availability filter (`is_unavailable`); doubtful flagged, not captained blindly |
| "It's just `xp --limit 5`" | Med | The value is the availability filter + `--squad` mode + the *explained* pick — a recommendation, not a ranking |
| xP is a mean, not a ceiling | Low | Honest caveat: xP is expected points; ceiling/differential captaincy is a noted follow-on |
| A saved squad has departed players | Med | Reuse ADR-024's departed handling — skip/note, don't crash |

---

### 🗝️ Gating decision (US-080 → ADR-029)

Settle before code — pressure-test on real candidates. Proposed (confirm/redirect at "start US-080"):

1. **Metric.** Rank by **next-GW xP** (the enriched rate, ADR-028), availability-filtered. No new
   score. *Rejected:* a bespoke captain model or a ceiling/variance metric — no form/variance data
   yet; over-engineering. (Ceiling captaincy → Backlog.)
2. **Penalties = context, not a multiplier.** A penalty taker's returns are already in their xP;
   adding a bonus would double-count. Show a ⚽/"pen" flag so the human can break ties.
3. **Modes.** `captain` (global top-N, for planning) and `captain --squad <name>` (from your saved
   squad — the real weekly question, reusing `SquadStore`).
4. **Explain the pick.** Show opponent, home/away, fixture difficulty, penalty duty, and xP — a
   recommendation states *why*. Horizon = 1 (captaincy is a one-week call).

**Worked example to verify at the gate:** for a sample squad, show the top-3 captain picks with
reasons and confirm the availability filter drops a doubtful player who'd otherwise rank.

---

### 📝 Session Progress Log

- **US-080 (gate) ✅** — Pressure-tested a real captain board (players + upcoming + baselines →
  next-GW xP, annotated with penalty flag + opponent + venue). Top picks sensible (B.Fernandes,
  Saka, Haaland — all PEN). **Two probe findings shaped ADR-029:** (1) a **GK (Benitez) ranked #3
  by mean xP** — the mean-not-ceiling caveat made real → **exclude goalkeepers** from captain
  candidates; (2) `player_xp` zeroes doubtful (`status != "a"`), but captaincy should **include
  doubtful, flagged** (a 75% premium is still a call) → captain uses ADR-023's `is_unavailable` and
  computes xP for doubtful. Recorded ADR-029: metric = next-GW xP; penalties = context not a
  multiplier; global + `--squad` modes; explain the pick. ClubElo re-checked — still down (timeout).
- **US-081 (captain analytics + command) ✅** — Ingested `penalties_order` (migration + `Player`);
  a `is_available` seam on `player_xp` (so doubtful players get an xP instead of being zeroed); a
  new `captain_picks` analytics fn (rank available outfield by next-GW xP, annotate opponent/venue/
  penalty/doubtful) + `_next_opponent`; the `captain` command (`--limit`/`--type`) and a
  `render_captain_picks` view — **the shared renderer's first new consumer** (ADR-025 paying off).
  **5 tests** (rank+annotate, GK-excluded, injured-out/doubtful-kept, away venue, limit) → suite
  **242 → 247**; ruff clean. Live smoke: top 5 = B.Fernandes/Saka/Haaland (pen) / Wilson / Gabriel;
  the GK (Benitez, #3 by mean xP in the probe) is **correctly excluded**.
- **US-082 (`captain --squad`) ✅** — Added `--squad <name>` to `captain`: loads a saved squad
  (`SquadStore`, ADR-024), filters candidates to its players (departed ids simply don't match —
  handled), errors helpfully on an unknown name (lists saved squads). The view titles "from squad
  '<name>'". **2 parser tests** (defaults + `--squad`/`--limit`) → suite **247 → 249**; ruff clean.
  Live smoke: saved a squad → `captain --squad` showed its top 5 (Gabriel/João Pedro/Gibbs-White/
  Semenyo/Rice); unknown-name path lists saved squads; cleaned up the throwaway squad.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-080 (ADR-029), US-081 (captain analytics + command),
  US-082 (`captain --squad`). **Phase 3 (decision support) is open**: a `captain` command that
  *recommends and explains* the top picks for the next gameweek — global or from your saved squad.
  Built entirely by **composing** existing work (enriched xP + availability + saved squads + the
  shared renderer). Tests 242 → **249**; one ADR; **no new dependency**.
* **Carried Forward:** None. Ceiling/variance ("differential") captaincy is on the Backlog (needs
  variance data we don't have yet).
* **Key Artifacts / Decisions:** ADR-029 (metric = xP; exclude GKs; keep doubtful flagged;
  penalties as context not a multiplier; explain the pick); `captain_picks`, `captain` command,
  `render_captain_picks`; `players.penalties_order`; an `is_available` seam on `player_xp`.

#### Retrospective
* **What Went Well?**
  - **The app crossed from *ranking* to *recommending*.** The first feature that advises — top
    picks *with reasons* (opponent, venue, penalty duty) and decision-appropriate filters — not a
    bare list.
  - **It was mostly composition, not new code.** xP (ADR-028), availability (ADR-023), saved
    squads (ADR-024), and the shared renderer (ADR-025 — its first *new* consumer) clicked
    together. Well-separated layers paid a dividend a whole phase later.
  - **The probe drove two honest design calls.** A GK ranking 3rd by mean xP made the
    mean-not-ceiling caveat concrete → exclude GKs; and it exposed that `player_xp` zeroes doubtful
    players → an `is_available` seam so a doubtful premium is *suggested and flagged*, not dropped.
  - **Reused, didn't reinvent.** Captaincy ranks by xP + context rather than inventing a "captain
    rating" that would need its own validation; penalties are shown, not double-counted.
  - DoD held (27th sprint): tests + live smoke + docs each story.
* **What Could Be Improved?**
  - **xP is a mean, not a ceiling** — the one real limitation. GK exclusion papers over the worst
    case, but a genuine high-ceiling differential still won't top the list. Honest, and noted for
    when variance data exists.
  - Couldn't demo the **availability filter dropping a player** live (preseason, no injuries) — it's
    unit-tested, but a real in-season example would be more convincing.
* **Lessons Learned?**
  - A good recommendation reuses a trusted metric and **explains itself** — don't invent a score.
  - Decision features need decision-appropriate *policy* (exclude GKs, keep-but-flag doubtful) even
    when the underlying metric is shared.
  - Well-separated layers compound: this phase's feature was mostly wiring existing pieces together.
* **Action Items for Next Sprint (028):**
  - [ ] Pick the next Phase 3 feature — transfer suggestions or a team analyser (both build on xP +
        saved squads), or harden data (full backfill; per-GW + live-form blending once GW1 plays).
  - [ ] Once variance/form data exists: a ceiling/differential captain mode.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 028):** owner to steer — likely the next decision-support feature
(transfer suggestions / team analyser, composing xP + saved squads), or data hardening.

**Completion Date:** 2026-08-03
**Final Notes:** Phase 3 opened by *composition* — captaincy fell out of xP + availability + saved
squads + the shared renderer, with two probe-driven policy calls (GK exclusion, doubtful handling).
The app now recommends, not just ranks. Sprint outcome: **Successful** — 3/3 stories, zero
roll-over, DoD held.
