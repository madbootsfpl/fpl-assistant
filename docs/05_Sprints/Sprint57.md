# Sprint 057: Cloud squads — build, download & load (per-user, no server)

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2–3 working sessions (a gate + a session-squad model + download/upload + wiring + docs)
**Carried Over:** None (Sprint 056 shipped; the app is live)

> **Direction (owner):** the deployed app has no saved squads and can't make one (the DB is gitignored,
> the web is read-only, and Community Cloud's disk is ephemeral + multi-user). Let each tester **build a
> squad, save it, and manage transfers** — persisted as **their own downloadable file** (Path 1, chosen):
> zero server infra, no accounts, each user keeps their own squad.

---

### 🔎 Verified at planning (the mechanism is feasible; no server writes)

- **The squad format round-trips.** A saved squad is `{player_ids, player_names, bench_ids, cost}` — the
  same JSON the CLI's `SquadStore` uses, so a web-built/downloaded squad is **CLI-interoperable**.
- **Build can produce structured ids.** `select_squad` returns the selected 15 (+ `best_legal_xi` for the
  bench) → a squad dict → a `st.download_button`. Confirmed on the live DB (an Optimal 15).
- **The pages already take a squad dict.** `Transfer` builds `owned` from `squad["player_ids"]`; feeding
  it a session/uploaded squad just works. (`Analyse` will run the engine on the dict directly, not via
  `ask`-by-name, so an uploaded squad works too.)
- **No server writes — the architecture holds.** Persistence is the **user's downloaded file** +
  `st.session_state`; the DB and `SquadStore` stay **read-only** on the cloud. (Community Cloud's disk is
  ephemeral, so a server file wouldn't persist anyway — and would be shared across all users.)
- Preseason (GW1 2026-08-21).

---

### 🧭 What's new — your squad, in the browser

The Streamlit app gains a **session "active squad"**: **build** one (Build page) or **upload** a
`squad.json`, and it's used across **Transfer** and **Analyse** for your session. **Download** it to keep
it (that file *is* your save — re-upload next time). A committed **demo squad** means the pages aren't
empty on first visit. All per-user, no accounts, no server writes.

---

### 🎯 Sprint Goal

**Objective:** a session **active squad** on the Streamlit app — set by **building** (Build → Download) or
**uploading** a `squad.json` (SquadStore-compatible) held in `st.session_state`; **Transfer** and
**Analyse** consume it; a committed **demo seed squad** populates the pages. Persistence is the user's
file; the DB/`SquadStore` stay read-only (no server writes). A gate settles the model.

#### Success Criteria
- [ ] Approach agreed (**ADR-054**) — the session "active squad" model; the SquadStore-compatible download
      format; the committed **demo seed** (read-only, a `SQUADS_PATH` fallback); a unified "available
      squads" helper (demo + session); where upload lives; no server writes
- [ ] **Build → Download** — Build (engine-based `select_squad`) offers a **Download `squad.json`**
      (player_ids + bench + cost) and sets it as the active squad
- [ ] **Upload → active** — a `file_uploader` (sidebar) parses a `squad.json` → validates →
      `st.session_state["squad"]`
- [ ] **Transfer** + **Analyse** use the **active squad** (session) or a **demo** squad (a selector)
- [ ] A committed **`data/seed_squads.json`** (demo) + a `SQUADS_PATH` fallback so the cloud pages populate
- [ ] **No server writes** — the web never calls `SquadStore.save`; the DB/squads are read-only on the
      cloud; the two-edge guardrail holds
- [ ] Tests — `AppTest` (build→download present; upload sets the active squad; Transfer/Analyse run on a
      session squad); the `SQUADS_PATH` fallback (storage)
- [ ] Docs: ADR-054 + index, Architecture, Handbook Ch 12, README (how the cloud squads work),
      PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-168 | **Gate.** Cloud-squad design (**ADR-054**): the session "active squad"; the download format; the demo seed; the available-squads helper; **sidebar upload**; **include a Captain page**; no server writes | Critical | ✅ Done | 0.5 session |
| US-169 | **Session squad + build/download/upload** — a `web_squads` helper (list demo + session, resolve one); a **sidebar** `file_uploader` → `session_state` + active-squad indicator; the **Build** page → engine-based + a **Download** button + "use this squad"; commit `data/seed_squads.json` + the `SQUADS_PATH` fallback. `AppTest` tests | High | ✅ Done | 1 session |
| US-170 | **Wire Transfer + Analyse + Captain + docs** — Transfer + Analyse + a **new Captain page** consume the active/demo squad (running the engine on the dict); docs (Architecture, Handbook Ch 12, README, PROJECT_STATUS). Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-054 recorded + added to the ADR index — _US-168_
- [x] `data/seed_squads.json` committed + `SQUADS_PATH` fallback — _US-169_
- [x] Architecture/Handbook Ch 12/README/PROJECT_STATUS — _US-170_
- [ ] After merge: refresh the seed + redeploy (owner) — _US-170_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — `AppTest`: Build offers a download + sets the active squad; an uploaded
   `squad.json` becomes the active squad; Transfer + Analyse run on a session squad; the `SQUADS_PATH`
   fallback returns the demo squads; the web never calls `SquadStore.save`; existing **442** stay green;
   the two-edge guardrail holds.
2. **Manual smoke test done** — locally + on the cloud after redeploy: build → download a `squad.json`;
   upload it → Transfer shows swaps for it, Analyse shows its health; the demo squad populates on first
   visit; no server writes.
3. **Documentation updated & checked** — ADR-054 + index, Architecture, Handbook Ch 12, README,
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A session **active squad** (build/upload) + Download/Upload persistence | A server-side DB / accounts / per-user isolation (Path 2 — Backlog) |
| A committed **demo** squad (read-only) | Editing a squad player-by-player in the UI (a later nicety) |
| Transfer + Analyse consume the active squad | Writing to `squads.json`/a DB from the web (no server writes) |
| SquadStore-compatible JSON (CLI-interoperable) | A Captain page (optional; can follow) |

**External Dependencies:** None (no DB, no accounts). The **owner** redeploys after merge (auto on push;
refresh the seed if wanted).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| A malformed uploaded `squad.json` | Med | Validate on upload (keys, ids exist in the DB); a clear error, no crash |
| The web accidentally writes server-side | Med | Never call `SquadStore.save` from the web; a test asserts it; the DB/squads read-only |
| Session squad lost on refresh confuses users | Low | Clear UI: Download = your save; Upload = load; a note that it's per-session until downloaded |
| Analyse-by-name doesn't fit an uploaded squad | Med | Run the analyse engine on the squad **dict** directly (not `ask`-by-name) |

---

### 🗝️ Gating decision (US-168 → ADR-054)

Path 1 is chosen; these pin the model. Proposed (confirm/redirect at "start US-168"):

1. **The active squad.** A SquadStore-compatible dict in `st.session_state["squad"]`, set by **building**
   (Build → "use this squad" + Download) or **uploading** a `squad.json`. A unified `web_squads` helper
   lists **demo** squads (committed seed, read-only) + the **session** squad, and resolves the chosen one.
2. **Persistence = the user's file.** `st.download_button` (save) + `st.file_uploader` (load). **No server
   writes** — the DB/`SquadStore` are read-only on the cloud.
3. **Demo seed.** Commit `data/seed_squads.json` (one demo squad) + a `SQUADS_PATH` fallback (like the DB
   `seed.db`), so the cloud pages populate.
4. **Consumers.** **Transfer** (already dict-based) + **Analyse** (run the engine on the dict). *(A Captain
   page is optional — defer unless quick.)*
5. **Upload location.** A **sidebar** `file_uploader` (available on every page) — confirm vs a dedicated
   "My Squad" page.

**Worked example (probed):** the format is `{player_ids, bench_ids, cost}` (CLI-compatible); `select_squad`
yields an Optimal 15 → a downloadable squad; `Transfer` already consumes `squad["player_ids"]`.

---

### 📝 Session Progress Log

- **US-168 (gate) ✅** — Recorded **ADR-054** (Path 1). A session **"active squad"** — a
  SquadStore-compatible dict in `st.session_state["squad"]`, set by **building** (Build → "use this squad")
  or **uploading** a `squad.json`; persistence is the **user's file** (`download_button` / `file_uploader`)
  — **no server writes** (the DB/`SquadStore` stay read-only; the web never calls `SquadStore.save`, a test
  will assert it). A unified **`web_squads`** helper lists demo + session squads and resolves one; a
  committed **`data/seed_squads.json`** demo + a `SQUADS_PATH` fallback populate the cloud pages; the
  format is the CLI `SquadStore` dict (interoperable), validated on upload. Owner's two calls: **sidebar**
  upload controls (every page) and **include a Captain page** — so consumers are **Transfer · Analyse ·
  Captain**, each running the engine on the squad dict. ADR-054 indexed.
- **US-169 ✅** — The mechanism. **config**: `SQUADS_PATH` now falls back to the committed
  `data/seed_squads.json` when the gitignored live `squads.json` is absent (mirrors the `seed.db`
  fallback) — so cloud pages populate. **Seed**: committed `data/seed_squads.json` (a `Demo XI`, an
  Optimal-15 on xP, £100.0), un-ignored via a `!data/seed_squads.json` exception. **Helper**
  `src/web_streamlit/squads.py`: `active_squad`/`set_active_squad` (session), `demo_squads`,
  `available_squads` (demo + session), `parse_uploaded` (JSON → validate shape + 11–15 size + ids exist
  in the current DB → a clear error, no crash), and `render_sidebar` (the every-page **sidebar** uploader
  + active-squad indicator; a re-upload is applied once, keyed by `file_id`, so it won't clobber a built
  squad). **Build page** rewritten **engine-based** (`decision_xp` → `archetype_bands` → `select_squad` →
  `best_legal_xi` → `render_squad`, the same path as the CLI `squad`), with a **Download `squad.json`**
  (the CLI `SquadStore` `{name: squad}` shape — CLI-interoperable) and a **"Use this squad →"** button that
  sets the session active squad; `render_sidebar()` at the top. **No server writes** — a test scans the web
  edges and asserts none call `SquadStore.save`. **Tests** (+11 → **453**): `AppTest` (Build offers a
  download + "Use this squad" sets `session_state["squad"]`); the seed loads + a legal size; the
  `SQUADS_PATH` fallback; `parse_uploaded` accepts a bare squad **and** a named `{name: squad}` file, and
  rejects non-JSON / wrong-shape / bad-size / unknown-ids; the no-server-writes guardrail. Smoke: a built
  squad round-trips download → upload → active. `ruff` clean.
- **US-170 ✅** — The consumers, all running the engine on the squad **dict** (not `ask`-by-name), each with
  the sidebar + a demo/session **`squad_picker`** (defaults to the active squad). **Analyse** (`3_Squads.py`,
  retitled) rewired from `ask "analyse {name}"` to the CLI's `decision_xp` → `best_legal_xi` →
  `analyse_squad` → `render_squad_analysis` path. **Transfer** (`5_Transfer.py`) swapped its
  `SquadStore().names()` selectbox for the picker (its internals were already dict-based). A **new Captain
  page** (`7_Captain.py`) reuses `captain_picks` → `render_captain_picks` (GK-excluded, xMins-weighted). The
  picker guards the empty-store edge (a live `squads.json` that's `{}` → an info + `st.stop()`, no crash).
  **Home** updated (page list + a "your squad" how-to). Docs: **Architecture** changelog (Sprint 057),
  **Handbook Ch 12** (cloud-squads section + the engine-wired pages + ADR-053/054 links), **README** (the
  browser-squad flow), **PROJECT_STATUS** (sprint/story, web pages, cloud-squads, 455 tests / 54 ADRs).
  **Tests** (+2 → **455**): Captain renders for the demo; Analyse/Transfer/Captain all surface a session
  active squad in the picker; the reworked Analyse test asserts the demo populates the picker. Smoke: all
  three pages render headlessly with a squad selector + output. `ruff` clean. **Owner action left:** refresh
  the seed if wanted + redeploy (auto on push).

**Outcome:** ✅ Successful — all three stories done. The deployed app now has **per-user squads** with no
server: build or upload a squad, and Analyse · Transfer · Captain run on it; a committed demo populates the
pages; persistence is the user's own file; the web never writes server-side.

**Delivered**
- **US-168 (gate) ✅** — ADR-054: the session "active squad" model, the SquadStore-compatible download
  format, the demo seed (a `SQUADS_PATH` fallback), the `web_squads` helper, sidebar upload, a Captain page,
  no server writes.
- **US-169 ✅** — the mechanism: `config.SQUADS_PATH` fallback; a committed `data/seed_squads.json` (`Demo
  XI`); `src/web_streamlit/squads.py` (`active_squad`/`set_active_squad`, `demo_squads`, `available_squads`,
  `parse_uploaded` with validation, `render_sidebar`); the Build page rewritten engine-based with a
  **Download `squad.json`** + a **Use this squad** button. A no-server-writes guardrail test.
- **US-170 ✅** — Analyse (rewired from `ask`-by-name to the engine on the dict), Transfer (picker), and a
  new **Captain** page consume the active/demo squad via a shared `squad_picker`; Home + docs (Architecture,
  Handbook Ch 12, README, PROJECT_STATUS).

**Verification** — 455 tests green (+13 over the sprint), `ruff` clean. Smoke: a built squad round-trips
Download → Upload → active; all three consumer pages render headlessly with the picker + output; the demo
seed loads as a legal 15. The two-edge guardrail and the `.save(` scan both hold.

**Carried forward** — the **owner** refreshes the seed (optional) + redeploys (auto on push), then gathers
tester feedback. Next candidates: Data Hardening at GW1 (2026-08-21: per-GW history + form), a
differentials/value `ask` intent.

**What went well** — the format round-tripped exactly as probed at planning (build → download → upload → the
same dict), so no rework; the pages that were already dict-based (Transfer) needed only the picker; "no
server writes" stayed a one-line guardrail test rather than a design headache.

**What to watch** — the session squad is lost on a browser refresh until it's downloaded; the UI says so, but
it's the most likely tester confusion. The demo seed's ids are a snapshot — a stale seed vs a refreshed DB
would drop players (mitigated: `parse_uploaded` validates ids; Analyse/Transfer filter to current players).

**Lessons captured:** `docs/05_Sprints/Sprint57_Lessons_Learnt.md`.
