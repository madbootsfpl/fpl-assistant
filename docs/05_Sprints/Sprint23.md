# Sprint 023: Saved / Persistent Squad (user state)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~3 working sessions (a new persistence layer + save/load)
**Carried Over:** None (Sprint 022 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

A probe confirmed the whole flow works with no new dependency:

- **Save/load round-trips** — capturing a squad's player ids (+ bench) and JSON round-tripping
  them is trivial (15 ids in, 15 out).
- **Reload is the valuable bit** — looking the ids up in *current* data re-prices (£100.0m)
  **and flags who's now unavailable** (Garner is injured now) and **notes departures** (an id
  no longer in the game). Reuses Sprint 022's `is_unavailable`.
- **Storage boundary** — `.gitignore` covers `data/*.db` (the reference *cache*) but **not**
  `data/*.json`; a saved squad is **user state**, so it needs its own store *and* its own
  gitignore rule (never committed).

**No new dependency** (stdlib `json`). This sprint is Tony's Sprint 022 pick — the last big
feature, closing the phase.

---

### 🧭 Architecturally, what's new — user state, separate from the reference cache

Every byte we've stored so far is **reference data** — FPL's players/teams/fixtures, cached in
`data/fpl.db` and *overwritten* on every `refresh`. A saved squad is different: it's **the
user's own state** (your picks), and it must **survive a refresh**. So it gets its own home:

```
data/fpl.db      ← reference cache (refreshed, disposable)     [gitignored: data/*.db]
data/squads.json ← user state (your saved squads, persistent)  [gitignore: add data/squads.json]
```

That separation *is* the new concept. A small `SquadStore` (JSON-backed, injectable path, like
`Storage`) owns it — kept apart from `Storage` so the two lifecycles never mix.

**Save the picks, not the numbers.** We store player **ids** (+ which are bench) — *not* prices
or availability, because those are reference data that goes stale. On **load**, we look the ids
up in *current* data and derive everything fresh: re-price, flag injuries, note who's left.
That's the payoff — "reload my team, see what's changed".

---

### 🎯 Sprint Goal

**Objective:** Let a manager save their chosen squad and reload it later — `squad --save <name>`
persists the picks; `squad --load <name>` reconstructs them against current data, re-prices,
flags availability, and notes anyone who's left the game.

#### Success Criteria
- [x] Approach agreed (**ADR-024**) before code
- [x] A `SquadStore` (JSON, injectable path) with `save` / `load` / `names`; user data kept
      separate from the `data/fpl.db` cache and **gitignored**
- [x] `squad … --save <name>` stores the computed squad's player ids + names + bench (+ cost/date)
- [x] `squad --load <name>` reconstructs the squad from current data and displays it
- [x] On load: **re-priced** against current prices (saved cost shown for comparison)
- [x] On load: **availability flags** (reusing Sprint 022) — injured/doubtful picks marked
- [x] On load: **departed players** (ids no longer in the game) are noted by name, not dropped
- [x] Loading an unknown name errors clearly and lists the saved names
- [x] Tests cover save/load round-trip, re-pricing, availability, departed, unknown name (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-067 | Agree the approach (**ADR-024**): store ids + bench (not prices/status), a separate JSON `SquadStore` (user state ≠ cache), `--save`/`--load`, on-load re-price + availability + departed handling — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-068 | `SquadStore` (JSON, injectable path — `save`/`load`/`names`) + `squad --save <name>`; gitignore user data. Tests (round-trip, overwrite, list) | High | ✅ Complete | 1 session |
| US-069 | `squad --load <name>`: reconstruct from current data, re-price (vs saved), flag availability, note departed, display; unknown-name error. Tests + smoke test | High | ✅ Complete | 1–1.5 session |

#### Technical Tasks & Maintenance
- [ ] ADR-024 recorded + added to the ADR index — _US-067_
- [ ] Update Architecture doc (user state vs reference cache; changelog) — _US-067_
- [ ] `config.SQUADS_PATH` + a `.gitignore` rule for `data/squads.json` — _US-068_
- [ ] Update `README.md` / `--help` + Handbook (persistence, user vs reference data) — _US-069_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for twenty-two sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Save/load a squad by name (user state) | Multiple users / accounts |
| Re-price + availability + departed on load | Editing a saved squad in place |
| A JSON `SquadStore`, gitignored | Syncing to the real FPL account/API |
| Store ids + bench (+ saved cost/date) | Storing prices/status (looked up fresh) |

**External Dependencies:**
- [ ] Stdlib `json`; the FPL data already cached; **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| User data committed / wiped by refresh | High | Separate `data/squads.json`, **gitignored**; `refresh` only touches `fpl.db` |
| A saved player has left the game | Med | Detect (id not in current data) and **note** it; don't crash or silently drop |
| Corrupt/missing JSON file | Low | Read → empty dict on missing/invalid; save writes atomically |
| Stale numbers if we stored them | Low | Store ids only; derive price/availability fresh on load |
| `--save` + `--load` used together | Low | `--load` is a distinct mode; guard/erroring if combined |

---

### 🗝️ Gating decision (US-067 → ADR-024)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **Store the picks, not the numbers.** Player **ids** + bench ids (+ saved cost/date for
   comparison) — *not* prices/status, which are reference data derived fresh on load.
2. **A separate store.** A JSON file `data/squads.json` via a small `SquadStore` (injectable
   path), distinct from the `data/fpl.db` cache — **user state ≠ reference data**. Gitignored.
3. **`--save`** persists the just-computed squad; **`--load`** is a display-only mode that
   reconstructs from current data (no optimising).
4. **On load** — re-price (show saved → now), flag availability (reuse Sprint 022), and note
   departed players (id not in current data). Unknown name → error + list saved names.

**Worked example to verify at the gate:** save a full squad → `data/squads.json` holds 15 ids;
load it → re-priced £100.0m, **Garner flagged injured** (became injured since), and a departed
id noted as "no longer in the game". Confirms the round-trip + the reload value before code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-067: ADR-024 — saved squad / user state)
* **Completed:** Recorded **ADR-024**: store the picks (player ids + bench + saved cost/date),
  *not* prices/status (derived fresh on load). A separate JSON `SquadStore` (`data/squads.json`,
  injectable path, **gitignored**) — **user state ≠ the `data/fpl.db` reference cache** — so it
  survives `refresh`. `squad --save` persists the computed squad; `--load` is a display-only
  reconstruct that re-prices (saved → now), flags availability (reuses ADR-023), and notes
  departed players; unknown name errors + lists names. Recorded the honest re-price note (a
  departed player makes saved-vs-now approximate). **Pressure-tested end-to-end on real data:**
  save 15 ids / £100.0m → load re-priced, a departed id noted, availability re-checked. Added to
  the ADR index; Architecture §12 changelog (first user-state layer). US-067 **complete** — no
  feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the verification.
* **Docs touched:** ADR-024 (new) + index, Architecture changelog, Sprint23 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Storage boundary confirmed: `data/*.json` not yet gitignored.)
* **Next Steps:** US-068 — the `SquadStore` + `squad --save` + the gitignore rule.

#### Session 2 — 2026-08-03 (US-068: SquadStore + squad --save)
* **Completed:** New `src/squads.py` — `SquadStore(path)` (JSON, injectable): `save`/`load`/
  `names`; `_read` → `{}` on missing/corrupt; `_write` is **atomic** (temp + `os.replace`).
  `config.SQUADS_PATH = data/squads.json`; **`.gitignore` gains `data/*.json`** (user state,
  never committed). `squad --save <name>` persists the computed Optimal squad's ids + bench +
  cost + date. **+7 tests → 217 total, all green** (round-trip, sorted names, unknown → None,
  overwrite, missing → empty, corrupt → empty/no-crash; `--save` parses). US-068 **complete**.
* **Manual smoke test:** ✅ `squad --full --save my-team` → "Saved as 'my-team' (15 players,
  £100.0m)"; `data/squads.json` holds 15 ids / bench / cost / saved_at; `git check-ignore`
  confirms it's **gitignored** and `git status` doesn't show it.
* **Docs touched:** config, .gitignore, Sprint23 board, PROJECT_STATUS. (README/Handbook come
  with `--load` in US-069.)
* **Issues / Blockers:** None.
* **Next Steps:** US-069 — `squad --load` (reconstruct + re-price + availability + departed).

#### Session 3 — 2026-08-03 (US-069: squad --load)
* **Completed:** Extended `SquadStore.save` to also store `player_names` (so a departed player
  shows by name). `squad --load <name>` is a distinct display-only mode (`_load_squad`):
  reconstruct present players by id, re-price, flag availability (reuses ADR-023), collect
  departed by saved name; `--save`+`--load` together errors; unknown name errors + lists.
  `render_loaded_squad` shows the table (starters + bench, `**`, availability flags), the
  **saved → now** cost, an availability summary, and a departed note. **+3 tests → 220 total,
  all green** (save stores names; render re-prices/flags/departed; `--load` parses). US-069
  **complete** — Sprint 023 done.
* **Manual smoke test:** ✅ Save `--full --bench …` then `--load` → bench section, re-priced
  "was £100.0m → now £100.0m". `--include-unavailable --save risky` then `--load risky` →
  **`Garner … (inj)` + "⚠ 1 of your picks now flagged: Garner(inj)"** (the availability-on-reload
  value, live). Unknown name → "No saved squad 'nope'. Saved: …"; `--save --load` together →
  "Use --save or --load, not both."; `--help` shows both.
* **Docs touched:** README, Handbook Ch22 (saving-a-squad / user-state section + ADR link),
  cli `--help`, Sprint23 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 023 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-067 (ADR-024), US-068 (`SquadStore` + `--save`), US-069
  (`--load`). The first **user-state** layer: save your squad and reload it, re-priced with
  current availability and any departures. Tests grew 210 → **220**. **No new dependency**
  (stdlib JSON). *The last big feature — the phase is now feature-complete.*
* **Carried Forward:** None. Backlog (all small/tech-debt now): availability flags in the other
  views, combined defensive value, bench order, `xp` per-GW, a shared table renderer, PuLP 4.0.
* **Key Artifacts / Decisions:** ADR-024 (user state ≠ reference cache; store picks, derive
  numbers fresh); `src/squads.py` (`SquadStore`, JSON, atomic, gitignored); `render_loaded_squad`.

#### Retrospective
* **What Went Well?**
  - **A genuinely new concept, cleanly done.** User state gets its own file, its own store, its
    own lifecycle — separate from the disposable cache, gitignored. The boundary was the whole
    point, and it held (verified with `git check-ignore`).
  - **Store the picks, derive the numbers.** That single decision is what makes reload useful —
    re-price + injury flags — and it reused Sprint 022's availability work for free.
  - **The killer use case works live** — reload a squad and it flags a player who's since been
    injured, and names one who's left.
  - Robust by design: atomic write, corrupt/missing file → empty, departed player → noted not
    crashed. DoD held (23rd sprint).
* **What Could Be Improved?**
  - `render_loaded_squad` duplicates a little of `render_squad`'s row loop — the shared-renderer
    backlog item would fix it (deliberately deferred).
  - Re-price vs saved is approximate when a player has departed (noted honestly).
* **Lessons Learned?**
  - Not all data is the same: user state and reference cache need different homes and lifecycles.
  - Persist the minimum (ids + names); recompute the rest — it stays correct as data changes.
  - A tiny store that mirrors an existing one (`Storage`) is instantly testable (injectable path).
* **Action Items for Next Sprint (024):**
  - [ ] Only polish + tech debt remain — pick a closer (availability flags in views, shared
    renderer, combined defensive value) or call the phase done. Check first.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 024):** a final polish/tech-debt closer (availability flags across
views, a shared table renderer, combined defensive value) — or declare the build phase complete.

**Completion Date:** 2026-08-03
**Final Notes:** The last big feature — saved squads, a clean new user-state layer. The build
phase is feature-complete. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
