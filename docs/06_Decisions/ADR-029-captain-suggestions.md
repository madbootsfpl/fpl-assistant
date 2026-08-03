# Architectural Decision Record: Captain suggestions (recommend + explain)

**Decision ID:** ADR-029
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (first Phase 3 / decision-support feature)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Phase 3 (decision support) opens with **captain suggestions** — "who do I give the armband to?".
The captain scores double, so the question is: who is most likely to haul next gameweek, among
players I can actually pick?

Everything needed is already in the app, which a planning probe confirmed on live data:

- **The enriched xP** (ADR-028) already ranks players by expected next-GW points, and its top is a
  sensible captain shortlist (B.Fernandes, Saka, Haaland…).
- **`penalties_order`** is populated (20 first-choice takers) — a real ceiling signal.
- **Opponent + home/away** derive from stored fixtures (`team_h`/`team_a` + a player's `team_id`).
- **Availability** (`is_unavailable`, ADR-023) and **saved squads** (`SquadStore`, ADR-024) exist.

So captaincy is a **decision-support layer on xP**, not new modelling. But the probe surfaced two
decisions that theory alone would have missed (see Decisions 2 and 3).

#### Decision Drivers
- **Recommend, and explain why** — the first feature that advises, not just ranks.
- **Reuse, don't reinvent** — xP is the metric; availability and saved squads compose in.
- **Be honest about the metric** — xP is a *mean*; captaincy also cares about *ceiling*.

---

### 💡 Decisions

**1. Metric: next-GW xP (horizon 1), availability-filtered.** Rank candidates by the enriched xP
(ADR-028) for the next gameweek — captaincy is a one-week call. **No new score is invented.**
*Rejected:* a bespoke captain model or a ceiling/variance metric — there's no form/variance data
yet, and it would be over-engineering. (Ceiling / "differential" captaincy → Backlog.)

**2. Exclude goalkeepers (a probe finding).** On live data a **GK (Benitez) ranked 3rd by mean
xP** — the "xP is a mean, not a ceiling" caveat made concrete. A keeper has a high floor
(appearances, saves, clean sheets) but **no ceiling** — you can't get the 15–20-point haul
captaincy is for, and virtually no one captains a keeper. So captain candidates are **outfield
only** (policy at the edge; GKs remain in the normal `xp` view).

**3. Include doubtful players (flagged); exclude the hard-out.** Captain availability uses ADR-023's
`is_unavailable` (exclude `i/s/u/n`) — but **includes doubtful (`d`) players with a flag**, because
a doubtful premium (e.g. a 75%-chance star) is still a legitimate, risky captain the human should
weigh. Note this differs from `player_xp`, which zeroes anything not `status == "a"`; captain
computes xP for doubtful players and flags them rather than dropping them.

**4. Penalties are context, not a multiplier.** A penalty taker's returns are **already in their
xP** — adding a bonus would double-count. Show a penalty flag so the human can break ties between
close candidates; it does not change the ranking.

**5. Two modes.** `captain` (global top-N — planning, differentials) and `captain --squad <name>`
(candidates drawn from a saved squad — the real weekly question, reusing `SquadStore`; departed
players handled per ADR-024).

**6. Explain the pick.** Show opponent, home/away, fixture difficulty, penalty duty, and xP — a
recommendation states *why*, so the manager can trust or overrule it.

**Not in scope:** ceiling/variance captaincy (needs variance data — Backlog); triple-captain chip
timing (Phase 5); transfer suggestions / team analyser (later Phase 3); xMins weighting (later).

---

### 🧪 Worked example (pressure-testing — live data, before code)

Ranking available outfield players by next-GW xP, annotated:

```
 7.4  B.Fernandes  MUN  PEN  vs HUL (A)
 7.2  Saka         ARS  PEN  vs COV (H)
 6.8  Haaland      MCI  PEN  vs BOU (H)
 6.4  Wilson       BRE       vs TOT (H)
 6.1  Palmer       CHE  PEN  vs FUL (A)
```

Confirms: xP gives a sensible shortlist; penalty flags + opponent + venue derive from stored data;
and **excluding GKs** removes the odd Benitez-at-#3 that pure mean-xP produced. (No unavailable
player sat in the top 40 — preseason — so the availability filter couldn't be shown live, but it's
built and unit-tested; it guards in-season.)

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the app's first *recommendation with a reason*; composes xP + availability + saved
  squads into the real weekly decision. FPL-native; no new dependency.
* **Negative / Trade-offs:** xP is a mean, so a genuine high-ceiling differential punt won't stand
  out (honest caveat; the GK exclusion is the one place we hard-code around it). Doubtful players are
  suggested-with-a-flag, which is a judgement the human must make.
* **Risks & Mitigations:**
  - *Double-counting penalties* → context flag only, never added to the score.
  - *Recommending someone who won't start* → hard `is_unavailable` filter; doubtful flagged.
  - *"It's just `xp --limit 5`"* → the availability filter + GK exclusion + `--squad` + the
    explained pick make it a recommendation, not a ranking.

---

### 🛠 Implementation & Migration
* **Components Affected:** `players.penalties_order` (migration) + `Player.from_api`; a
  `captain_picks()` analytics fn (rank outfield-available by next-GW xP, annotate opponent/venue/pen,
  compute xP for doubtful); the `captain` command + `--squad` mode + an explain-why view. `refresh`
  already fetches the source. The optimiser and existing views are untouched.
* **Action Items:**
  - [x] Record the design + the two probe findings (GK, doubtful) (US-080)
  - [ ] `penalties_order` ingest; `captain_picks`; `captain` command + view (US-081)
  - [ ] `captain --squad <name>` (reuse `SquadStore`) (US-082)
  - [ ] (Backlog) ceiling/variance ("differential") captaincy; triple-captain timing (Phase 5)

---

### 🔄 Review & Reconsideration
* **Review Date:** Once in-season variance/form data exists (revisit mean-vs-ceiling) or when the
  transfer/team-analyser features arrive (share the candidate-scoring code).
* **Triggers for Reconsideration:**
  - [ ] Variance/ceiling data available → a differential-captain mode alongside the mean.
  - [ ] xMins model exists → weight candidates by expected minutes (retire the doubtful judgement).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-080 (this), US-081, US-082
- **External Docs:** [ADR-028 (enriched xP)](./ADR-028-xp-historical-baseline.md) · [ADR-023 (availability)](./ADR-023-player-availability.md) · [ADR-024 (saved squads)](./ADR-024-saved-squad.md) · [ADR-006/007 (xP)](./ADR-006-expected-points-v0.md) · [Sprint 027](../05_Sprints/Sprint27.md)
