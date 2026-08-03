# Sprint 022: Player Availability (don't pick injured players)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~3 working sessions (a full-stack slice: ingest → storage → optimiser → display)
**Carried Over:** None (Sprint 021 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

Tony's availability question surfaced a real gap — a probe confirmed it's live:

- **The optimiser currently picks an injured player.** `squad` (XI and `--full`) both select
  **Garner (status 'i', injured)** — based on last-season points, ignoring that he can't play.
  Tempting unavailable high-scorers abound: Garner, J.Timber, Saliba, Ekitiké (injured),
  Andersen (suspended).
- **FPL provides the data.** `status` (a/d/i/s/u — already stored since Sprint 005) plus
  `chance_of_playing_next_round` (0/25/…/100) and `news` (e.g. "Back injury"). Current split:
  **509 available · 19 doubtful · 29 injured · 3 suspended · 7 unavailable**.

So availability is **reference data** (live FPL attributes), the fix is data-supported, and it
closes a genuine correctness hole. **No new dependency.**

This sprint is Tony's Sprint 021 pick (via his availability question) — a real correctness
closer toward completing the phase.

---

### 🧭 Architecturally, what's new — the optimiser respects who can actually play

Until now `select_squad` maximises a score over *every* player, injured or not. Availability
adds a filter *at the edge* (the CLI), keeping the optimiser generic:

```
unavailable = status in {i, s, u, n}   (injured / suspended / unavailable / not-in-squad)
available   = status a (fit) or d (doubtful — might play; kept, but flagged)
```

- **By default, `squad` optimises over available players only** — no more injured Garner in
  your XI. `--include-unavailable` opts back in to the theoretical best.
- **Doubtful (d) players stay** (they might play) but are **flagged** in the output with their
  chance (e.g. "Kamara (d 75%)").
- **`--include <injured>` still forces them in** (your override) but **warns** — the tool
  informs, doesn't silently obey (the warn-not-block spirit of ADR-022).

The optimiser stays a pure "maximise these scores"; *availability is a policy at the edge*,
like the objective and the formation before it.

---

### 🎯 Sprint Goal

**Objective:** Make the tool honest about who can actually play — the optimiser skips
unavailable players by default (with an opt-out), doubtful players are flagged, and forcing in
an unavailable player warns — using FPL's `status` / `chance` / `news`.

#### Success Criteria
- [x] Approach agreed (**ADR-023**) before code
- [x] `Player.from_api` parses `chance_of_playing_next_round` and `news` (status already stored)
- [x] `refresh` stores them; a schema **migration** adds the columns to existing DBs
- [x] `squad` excludes unavailable players by default; **`--include-unavailable`** opts back in
- [x] The output reports what was left out (e.g. "39 unavailable excluded: Garner (i), …")
- [x] Doubtful players in the squad are flagged with their chance ("(d 75%)")
- [x] `--include <unavailable player>` keeps them (override) but **warns** + shows "(inj)"
- [x] Existing views/objectives unchanged; a `refresh` re-run is idempotent
- [x] Tests cover parsing, the migration, the availability filter, and the warnings (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-064 | Agree the approach (**ADR-023**): what counts as unavailable (status i/s/u/n; keep a + doubtful d), optimiser excludes-by-default + `--include-unavailable`, forced-in unavailable warns, doubtful flagged, ingest `chance`/`news` — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-065 | Ingest & store: `Player.from_api` gains `chance` / `news`; `storage` migration + save + `get_players`. Tests (parse + migration) | High | ✅ Complete | 1 session |
| US-066 | Apply availability: a pure `is_unavailable` helper; `cmd_squad` filters + reports + warns on forced-in; `render_squad` flags doubtful picks. Tests + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-023 recorded + added to the ADR index — _US-064_
- [ ] Update Architecture doc (players gain chance/news; availability policy; changelog) — _US-065_
- [ ] Update `README.md` / `--help` with `--include-unavailable` + the availability behaviour — _US-066_
- [ ] Handbook — a short section on availability (status codes, the default) — _US-066_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for twenty-one sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Optimiser excludes unavailable (default) + opt-out | Availability flags across every view (table/xg/…) — follow-on |
| Ingest `chance` + `news` | Deprioritising (vs excluding) by `chance` % |
| Flag doubtful picks; warn on forced-in | A saved squad's availability-on-reload (later) |
| The `status i/s/u/n` = unavailable rule | Predicting return dates |

**External Dependencies:**
- [ ] FPL API (already used) + PuLP; **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Excluding too much (e.g. doubtful) | Med | Only exclude definitely-out (status i/s/u/n); doubtful (d) stays, flagged |
| Preseason `status`/`news` may be stale | Low | Same caveat as all FPL data; auto-updates on refresh — stated |
| A forced-in injured pick silently obeyed | Low | Keep the override but **warn** (ADR-022 spirit) |
| Excluding makes a squad infeasible | Low | 509 available players — never binds; the existing "no legal squad" message backstops |
| Availability filter buried in the optimiser | Low | Filter at the CLI edge; `select_squad` stays generic |

---

### 🗝️ Gating decision (US-064 → ADR-023)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **Unavailable = status in {i, s, u, n}** (injured / suspended / unavailable / not-in-squad,
   all chance 0). **Available = a** (fit); **doubtful = d** (kept — might play — but flagged).
2. **Default exclude.** `squad` optimises over available players only; **`--include-unavailable`**
   opts back in to the theoretical best. The output reports the exclusions.
3. **Forced-in override warns.** `--include <injured>` keeps them (your call) but warns.
4. **Flag doubtful** picks with status + chance ("Kamara (d 75%)").
5. **Ingest** `chance_of_playing_next_round` and `news` via the model + the generic migration.

**Worked example to verify at the gate:** on real data — default `squad` no longer picks
**Garner (i)** (replaced by an available player); `--include-unavailable` brings the injured
options back; `--include Garner` forces him in *with a warning*; a doubtful pick shows
"(d 75%)". Confirms the policy before any code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-064: ADR-023 — player availability)
* **Completed:** Recorded **ADR-023**: unavailable = `status in {i,s,u,n}` (injured/suspended/
  unavailable/not-in-squad); available = `a`; **doubtful `d` kept but flagged**. `squad`
  excludes unavailable by default (policy at the CLI edge — `select_squad` stays generic);
  `--include-unavailable` opts back in; a forced-in unavailable pick **warns**; doubtful picks
  flagged with chance; ingest `chance`/`news`. **Pressure-tested on real data:** default
  `squad` drops **Garner (injured)** (2024 → 2020 pts, a 4-pt cost); `--include-unavailable`
  restores him; 564 → 527 available. Added to the ADR index; Architecture §12 changelog.
  US-064 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the verification.
* **Docs touched:** ADR-023 (new) + index, Architecture changelog, Sprint22 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Gap confirmed live: the optimiser was picking injured Garner.)
* **Next Steps:** US-065 — ingest & store `chance` + `news` + the migration.

#### Session 2 — 2026-08-03 (US-065: ingest & store chance + news)
* **Completed:** `Player` gained `chance` (`int|None`) + `news` (`str|None`); `from_api` reads
  `chance_of_playing_next_round` + `news` via `raw.get()` (`status` already stored). Storage:
  the two added to `_MIGRATIONS`, `CREATE_PLAYERS`, `UPSERT_PLAYER`, `save_players`;
  `get_players` unchanged. **4 new tests → 206 total, all green** (from_api parse + absent;
  save/get round-trip; migration). US-065 **complete**.
* **Manual smoke test:** ✅ On the real `data/fpl.db`: opening Storage migrated it; `refresh`
  populated them — Garner (i, chance 0, "Groin injury"), Timber, Saliba, Ekitiké all flagged.
* **Docs touched:** Architecture §6 data model (players +2 availability columns), Sprint22
  board, PROJECT_STATUS. (README/Handbook come with the behaviour in US-066.)
* **Issues / Blockers:** None.
* **Next Steps:** US-066 — the availability filter + reporting + doubtful flags.

#### Session 3 — 2026-08-03 (US-066: apply availability)
* **Completed:** `optimizer.is_unavailable(p)` (status i/s/u/n) + `available_players(players,
  keep_ids)` (drop unavailable, keep forced) — pure, tested. `cmd_squad` filters the pool by
  default (`--include-unavailable` opts in, keeping `select_squad` generic), reports the
  exclusions, and warns on any forced-in unavailable pick. `render_squad` flags each pick's
  status inline (`(d 75%)`, `(inj)`). **+4 tests → 210 total, all green** (is_unavailable;
  available_players keeps forced; render flags doubtful/injured; `--include-unavailable`
  parses). US-066 **complete** — Sprint 022 done.
* **Manual smoke test:** ✅ Default `squad --full` **excludes injured Garner** (was picked);
  report "(39 unavailable excluded: Garner (i)…)"; `--include-unavailable --full` → Garner back
  as `159 (inj)`; `--include J.Timber` → forced in `* (inj)` + "⚠ J.Timber is injured (0%) —
  forced in."; `--help` shows the flag. (Diagnosed a non-bug: the flexible XI omits Garner
  regardless because Rice (184) > Garner (159) — availability is clearest in `--full`.)
* **Docs touched:** README, Handbook Ch22 (availability section + ADR link), cli `--help`,
  Sprint22 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 022 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-064 (ADR-023), US-065 (ingest `chance`/`news`), US-066
  (the availability filter + flags). `squad` no longer picks injured players by default; a
  forced-in unavailable pick warns; doubtful picks are flagged. Tests grew 202 → **210**. **No
  new dependency.**
* **Carried Forward:** None. Backlog: availability flags in the other views (table/xg/…); a
  saved-squad availability reload; weight-by-`chance` instead of a hard exclude.
* **Key Artifacts / Decisions:** ADR-023 (availability policy at the edge; warn-not-block);
  `players` +`chance`/`news`; `is_unavailable` / `available_players`; the inline flags; Handbook
  Ch22 section.

#### Retrospective
* **What Went Well?**
  - **Made the optimiser trustworthy.** It was silently recommending injured Garner as
    "optimal"; now it respects who can actually play — a real correctness fix, from Tony's
    availability question.
  - **Policy at the edge, again.** Availability filters at the CLI; `select_squad` stayed a
    pure "maximise these scores" — the fifth feature to slot in that way.
  - **The double-check habit paid off.** A suspicious smoke result (`--include-unavailable`
    not showing Garner in the XI) was chased down to a *non-bug* (flexible formation prefers a
    better MID) rather than shipped or "fixed" wrongly.
  - Full-stack slice absorbed by the existing seams a *fifth* time; DoD held (22nd sprint).
* **What Could Be Improved?**
  - Availability is only surfaced in the *squad* — the other views (table/xg/…) don't flag it
    yet (a natural follow-on).
  - A hard exclude is blunt; a doubtful player is kept-and-flagged, but weighting by `chance`
    would be more nuanced (deferred).
* **Lessons Learned?**
  - An "optimal" answer is only as good as its inputs — filter out what can't happen.
  - The generic-core / policy-at-edge pattern keeps absorbing features cleanly (5th time).
  - Chase a surprising result to its cause before calling it a bug or a fix.
* **Action Items for Next Sprint (023):**
  - [ ] Consider: availability flags across the views; a saved squad; combined defensive value;
    or another closer — check first.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 023):** availability flags in the other views, a saved squad,
combined defensive value, or another backlog closer — toward completing the phase.

**Completion Date:** 2026-08-03
**Final Notes:** The optimiser is honest about who can play — from Tony's availability
question, a real correctness fix. Sprint outcome: **Successful** — 3/3 stories, zero roll-over,
DoD held.
