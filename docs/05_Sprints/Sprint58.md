# Sprint 058: Your squad, editable in the browser (name · transfers · captain · manual edit)

**Dates:** 2026-08-05
**Status:** ✅ Complete (5/5 stories; retro done)
**Capacity:** ~3–4 working sessions (a gate + a fix + a validator + guided & manual editing + captain + docs)
**Carried Over:** None (Sprint 057 shipped cloud squads; the app is live)

> **Direction (owner):** the Sprint-057 session squad is **read-only** once set. Tony's testing notes ask to
> make it **yours and changeable**: fix the Build page (xP/xMins render as 0), **name** a squad, **apply
> transfers**, **set a captain that sticks**, and **hand-edit** the 15. Chosen scope: **guided edits + a
> manual picker**, and the captain is **set & persisted** on the squad. Still no server writes — the
> download is the save.

---

### 🔎 Verified at planning (real data — the bug is real; the pieces exist)

- **The Build xP/xMins bug is confirmed.** The Build page renders **xMins 0 / xP 0.0** for every player: it
  never attaches `xp`/`minutes_weight` onto `result["selected"]`. The CLI does exactly this before
  rendering (`cli.py:320–323`); the fix is to mirror it. `render_squad(objective="xp")` already prints the
  columns — it just reads empty fields.
- **Squad legality has a model but no 15-man validator.** `legal_xi_issues(starters)` validates an XI
  against `XI_FLEX`; `SQUAD_15 = {GK2,DEF5,MID5,FWD3}` and `MAX_PER_CLUB = 3` are constants; `best_legal_xi`
  derives an XI. There is **no** "is this 15 legal?" check — the manual editor needs a new pure
  **`squad_15_issues(players)`** (position counts + ≤3/club; budget stays a soft edge-side warning),
  modelled on `legal_xi_issues`. Generic core; the web edge just calls it.
- **The squad dict tolerates a superset.** `SquadStore` stores `{player_ids, player_names, bench_ids, cost,
  saved_at}`; adding **`captain_id`** (and the existing `name`) is ignored by the CLI and passes
  `parse_uploaded` (which checks `player_ids` + size + ids-exist). We'll also validate `captain_id ∈
  player_ids` on upload.
- **Mutation is a session edit, not a write.** Applying a transfer / a manual swap / a captain edits
  `st.session_state["squad"]` in place (ids, bench, cost, captain) and re-derives — **no `SquadStore.save`,
  no DB write** (the Sprint-057 guardrail test still holds). Re-**Download** captures the edits.
- Preseason (GW1 2026-08-21).

---

### 🧭 What's new — your squad, and you can change it

The session **active squad** becomes **editable**: **name** it; **apply** a suggested transfer (out→in);
**hand-swap** any player for any other (legality-checked); **set a captain** that sticks; adjust the
**bench**. Every edit updates the session squad and the **Download** reflects it. A new **My Squad** page is
the hub (shows the 15 with **(C)**, cost, and a legality line); Transfer/Captain keep inline
**Apply**/**Set** buttons that mutate the same squad. Still per-user, no accounts, no server writes.

---

### 🎯 Sprint Goal

**Objective:** turn the read-only session squad into an **editable** one — **name · apply-transfer ·
manual-swap · set-captain · bench** — all mutating `st.session_state` (download = save; no server writes),
backed by a new generic **`squad_15_issues`** legality validator; and **fix** the Build xP/xMins rendering.
A gate settles the model.

#### Success Criteria
- [ ] Approach agreed (**ADR-055**) — the editable-session-squad model (mutate in session_state, no server
      writes); the `captain_id`/`name` schema superset; the new **`squad_15_issues`** validator; where
      editing lives (a **My Squad** hub + inline Apply/Set); how upload validates `captain_id`
- [ ] **Bug fix** — Build attaches `xp` + `minutes_weight`, so xMins/xP (and the projected-xP total) render
- [ ] **Name a squad** — a text input on Build (and rename on My Squad); the download + active squad use it
- [x] **`squad_15_issues`** — a pure validator (position counts vs `SQUAD_15`, ≤3/club; structural-only,
      budget warned at the edge), with tests; reused by apply-transfer + the manual editor
- [ ] **Apply a transfer** — Transfer gets an **Apply** that mutates the session squad (swap out→in,
      recompute cost + bench), guarded by the validator; the download reflects it
- [ ] **Manual editor** — a **My Squad** page: swap **any** player for any other (searchable), legality
      validated (clear issues, no illegal save); adjust the bench
- [ ] **Set & persist a captain** — Captain page **Set as captain** → `squad["captain_id"]`; **(C)** shown
      in Analyse and in the downloaded `squad.json`; upload validates it
- [ ] **No server writes** — still no `SquadStore.save` in the web edges (the guardrail test holds)
- [ ] Tests — `squad_15_issues` (unit); `AppTest` (Build renders xP; name persists; Apply mutates;
      manual swap validates; captain persists); the no-server-writes guardrail
- [ ] Docs: ADR-055 + index, Architecture, Handbook Ch 12, README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-171 | **Gate.** Editable-squad design (**ADR-055**): mutate `session_state` (no server writes); the `captain_id`/`name` schema; the `squad_15_issues` validator; the **My Squad** hub + inline Apply/Set; upload validates `captain_id` | Critical | ✅ Done | 0.5 session |
| US-172 | **Fix Build xP/xMins + name a squad** — attach `xp`/`minutes_weight` so the table + total render; a squad-name text input used by Download + the active squad | High | ✅ Done | 0.5 session |
| US-173 | **Validator + apply a transfer** — a pure `squad_15_issues` (tests); Transfer gets **Apply** → mutate the session squad (out→in, recompute cost/bench, validate); download reflects it | High | ✅ Done | 1 session |
| US-174 | **Manual editor (My Squad page)** — swap **any** player for any other (searchable), legality-validated; adjust the bench; shows the 15 with **(C)** + cost + a legality line. *(Heaviest; may carry to 059.)* | High | ✅ Done | 1–1.5 sessions |
| US-175 | **Set & persist a captain** — Captain **Set as captain** → `squad["captain_id"]`; **(C)** in Analyse + the download; `parse_uploaded` validates `captain_id ∈ player_ids`. Docs | Medium | ✅ Done | 0.5 session |

#### Technical Tasks & Maintenance
- [x] ADR-055 recorded + added to the ADR index — _US-171_
- [x] `squad_15_issues` in `src/analytics/optimizer.py` (+ exported) — _US-173_
- [x] Web mutation helpers in `src/web_streamlit/squads.py` (rename ✅ / apply_transfer ✅ / set_bench ✅ / set_captain ✅) — _US-173/174/175_
- [x] Architecture/Handbook Ch 12/README/PROJECT_STATUS — _US-175_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — `squad_15_issues` unit tests (legal / wrong-counts / >3-club / over-budget);
   `AppTest`: Build renders non-zero xP; a named squad round-trips; Apply changes the session squad; a
   manual swap validates (legal applies, illegal is refused with a reason); a set captain persists +
   appears in the download; the web never calls `SquadStore.save`; existing **455** stay green.
2. **Manual smoke test done** — locally + on the cloud after redeploy: build → name → download; apply a
   transfer → the squad + download change; hand-swap a player (and see an illegal one refused); set a
   captain → **(C)** shows in Analyse + the download.
3. **Documentation updated & checked** — ADR-055 + index, Architecture, Handbook Ch 12, README,
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Editing the **session** squad (name/transfer/manual/captain/bench) | Server-side persistence / accounts (Path 2 — Backlog) |
| A pure **`squad_15_issues`** legality validator | Multi-week transfer *planning* changes (the engine is unchanged) |
| A **My Squad** hub page + inline Apply/Set | A vice-captain / chip modelling (later) |
| `captain_id` persisted on the dict + in the download | Writing squads.json / a DB from the web (no server writes) |

**External Dependencies:** None. The **owner** redeploys after merge (auto on push).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| A manual edit yields an illegal 15 | Med | `squad_15_issues` gates every edit; illegal → a clear reason, no apply |
| Mutation scattered across pages drifts | Med | One set of mutation helpers in `web_squads`; pages call them, never edit the dict inline |
| A stale `captain_id` (after a swap-out) | Low | Clear the captain if its id leaves the squad; validate on upload |
| The web accidentally writes server-side | Med | Still no `SquadStore.save`; the guardrail test holds; mutation is session-only |
| Scope is large (5 stories) | Med | Ship the fix + name first (US-172); US-174 (manual) is the heaviest and may carry to 059 |

---

### 🗝️ Gating decision (US-171 → ADR-055)

Proposed (confirm/redirect at "start US-171"):

1. **Editable session squad.** `st.session_state["squad"]` is mutated in place (name, player_ids,
   bench_ids, **captain_id**, cost). **No server writes** — the DB/`SquadStore` stay read-only; the
   download is the save. All edits go through **mutation helpers** in `src/web_streamlit/squads.py`
   (`rename`, `apply_transfer`, `replace_player`, `set_captain`, `set_bench`) — pages never edit the dict
   inline.
2. **Schema superset.** Add `captain_id` (+ keep `name`) — ignored by the CLI, tolerated by
   `parse_uploaded` (which will also validate `captain_id ∈ player_ids`).
3. **A generic validator.** New pure **`squad_15_issues(players, max_per_club=3)`** in the optimizer
   (modelled on `legal_xi_issues`): position counts vs `SQUAD_15` + ≤3/club → a list of issues (empty =
   legal). **Structural only** — budget is a soft, edge-side warning (never in the legality list, so it
   can't block). Unit-tested; reused by apply-transfer + the manual editor.
4. **Where editing lives.** A new **My Squad** hub page (the 15 with **(C)**, cost, a legality line; rename;
   the manual swap + bench controls) **plus** inline **Apply** (Transfer) and **Set as captain** (Captain)
   that mutate the same session squad. *(Confirm vs folding it all onto Build.)*
5. **Captain display.** `render_squad_analysis` (and the Build/My-Squad table) marks the `captain_id` with
   **(C)**; the download includes it.

**Worked example (probed):** the Build bug is `p.get("xp",0)`→0 because ids aren't attached (fix mirrors
`cli.py:320–323`); a legal-15 check has no home yet (add `squad_15_issues`); `captain_id` is a harmless
superset key on the dict.

---

### 📝 Session Progress Log

- **US-171 (gate) ✅** — Recorded **ADR-055** (the editable session squad). The active squad becomes
  **mutable in `st.session_state`** (name · `player_ids` · `bench_ids` · **`captain_id`** · cost) — **no
  server writes** (mutation is session-only; download = save; the ADR-054 guardrail holds). All edits go
  through **mutation helpers** in `web_squads` (`rename`/`apply_transfer`/`replace_player`/`set_captain`/
  `set_bench`; each recomputes cost, re-derives bench, clears a departed captain, re-validates) — pages
  never edit the dict inline. A new generic **`squad_15_issues(players, budget=None)`** validator (core,
  modelled on `legal_xi_issues`): position split vs `SQUAD_15` + ≤3/club are **hard**, **budget is a soft
  warning** (owner's call — prices drift, so over-budget warns but still applies). `captain_id` is a
  schema **superset** (CLI ignores; validated on upload; shown as **(C)**). Editing lives **wherever the
  opportunity appears** (owner) — inline **Apply** (Transfer) + **Set as captain** (Captain) — **plus** a
  **My Squad** hub (the 15 with (C)/cost/legality, rename, manual swap, bench). ADR-055 indexed.
- **US-172 ✅** — **Bug fixed:** the Build page now attaches `xp` + `minutes_weight` onto `result["selected"]`
  before rendering (mirroring `cli.py` cmd_squad), so the **xMins/xP** columns and the projected-xP total +
  XI/bench breakout render real numbers (was 0 / 0.0). **Name a squad:** a `text_input` ("Squad name",
  default "My squad") flows into the **Download** file key and the **active squad**'s name. Tests (+2 →
  **457**): a regression asserting a non-zero projected total; the name flowing into `session_state`. Smoke:
  Build now shows e.g. `Total: £100.0m · projected 305.8 xP` with per-player xMins/xP; `ruff` clean.
- **US-173 ✅** — **Validator:** a pure **`squad_15_issues(players, max_per_club=3)`** in the optimizer
  (exported), modelled on `legal_xi_issues` — 15-in-`SQUAD_15`-split + ≤3/club are the hard checks; **budget
  is structural-only-excluded** and warned at the edge (so it can't block; prices drift). **Apply a
  transfer:** a `web_squads.apply_transfer(squad, out, in, players)` helper edits a **copy** of the squad
  (swap out→in, recompute cost, carry bench, **clear a transferred-out captain**), returns
  `(ok, issues, warning, new_squad)` — illegal → refused with reasons, over-budget → a soft warning but
  still applies. The **Transfer** page gains a swap selector + **Apply** button (single-swap view) that sets
  the mutated squad as the session active squad and reruns. **Latent bug found & fixed:** demo squads (from
  `SquadStore`) had no `name`, so adopting one via Apply crashed `render_sidebar` — now `demo_squads()`
  injects a `name` and the sidebar reads defensively. Tests (+11 → **468**): 5 `squad_15_issues`
  (legal/split/count/club/budget-ignored) + 5 `apply_transfer` (legal/illegal/captain-clear/captain-keep/
  budget-warn) + a Transfer `AppTest` (bank→swaps→Apply mutates the session squad, named + re-costed). Smoke
  on the live DB: an over-bank swap applies (£109.0m, warned); an illegal MID→GK is refused; `ruff` clean.
- **US-174 ✅** — The **manual editor**: a new **`pages/8_My_Squad.py`** hub. Shows your 15 (sorted
  XI-then-bench) with **(C)**, per-player xP, a **cost + legality banner** (`squad_15_issues` + the soft
  over-budget note). Edit sections: **Rename** (→ `rename`); **Swap a player** — pick any owned player, pick
  any **same-position** available replacement (searchable, xP-ranked; any→any within position keeps it
  legal, illegal picks refused by the validator anyway) → reuses `apply_transfer`; **Set the bench** (a
  4-max multiselect → `set_bench`, warns if the XI isn't legal). A **Download** reflecting all edits.
  Editing a demo **adopts a copy** as your active squad. Two new pure helpers `rename`/`set_bench` in
  `web_squads`. Tests (+7 → **475**): 3 unit (`rename` sets/keeps-name; `set_bench` orders by `player_ids`)
  + 4 `AppTest` (renders with a legality banner + download; swap adopts+mutates; rename; set-bench-of-4).
  Home updated (the page list + the edit how-to). Smoke: swap/rename/bench/download all work headlessly;
  dropped a `use_container_width` deprecation; `ruff` clean.
- **US-175 ✅** — **Set & persist a captain.** A `web_squads.set_captain(squad, id)` helper (only an owned
  id sticks, else `None`). The **Captain** page gains a **Set as captain** selector (defaults to the current
  captain, else the top recommendation) → sets `squad["captain_id"]` on the adopted session squad. The
  captain shows **(C)** in **Analyse** — `render_squad_analysis`/`_name` gained a width-safe `captain_id`
  marker (the CLI keeps the default `None`, unchanged) — and in **My Squad** + the **download**.
  `parse_uploaded` now validates `captain_id ∈ player_ids`. **Docs (batched for the whole feature):**
  Architecture changelog (Sprint 058), Handbook Ch 12 (the editable-squad section + ADR-055 link), README
  (edit/captain flow), PROJECT_STATUS (editable-squad line, pages, 481 tests / 55 ADRs). Tests (+6 →
  **481**): a renderer `(C)` marker test; 2 `set_captain` (owned/non-owned); 2 `parse_uploaded` (valid /
  captain-not-in-squad); a Captain `AppTest` (Set persists an owned captain). Smoke: set captain → (C) in
  Analyse; CLI analyse renderer unchanged (21 tests green); `ruff` clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — all **5** stories done (the heaviest, US-174, landed without slipping to 059).
The session squad went from **read-only to fully editable** — name · apply-transfer · manual swap · bench ·
captain — all mutating `session_state` (no server writes), backed by one generic legality validator. A
confirmed Build bug was fixed along the way.

**Delivered**
- **US-171 (gate) ✅** — ADR-055: the editable-session-squad model; mutation helpers; the
  `squad_15_issues` validator; `captain_id`/`name` superset; edit inline + a My Squad hub; no server writes.
- **US-172 ✅** — fixed the Build **xP/xMins = 0** bug (attach `xp`/`minutes_weight` like the CLI); **name
  a squad**.
- **US-173 ✅** — the generic **`squad_15_issues`** validator (structural hard, budget a soft edge warning)
  + **apply a transfer** (`apply_transfer` helper; Transfer *Apply*). Fixed a latent nameless-demo crash.
- **US-174 ✅** — the **My Squad** hub: the 15 with (C)/cost/legality; rename; manual same-position swap
  (validated); bench; download.
- **US-175 ✅** — **set & persist a captain** (`set_captain`; Captain *Set as captain*; **(C)** in Analyse +
  the download; upload-validated).

**Verification** — 481 tests green (**+26** over the sprint), `ruff` clean. Live-DB smokes: Build shows real
xP; an over-bank swap applies (£109m, warned) and an illegal MID→GK is refused; My Squad swap/rename/bench/
download work; set-captain → (C) in Analyse. The two-edge guardrail and the `.save(` scan both still hold;
the CLI analyse renderer is unchanged (21 tests green).

**Carried forward** — the **owner** redeploys (auto on push) + gathers tester feedback on editing. Backlog
candidates: Data Hardening at GW1 (2026-08-21: per-GW history + form); a differentials/value `ask` intent;
Path 2 server-side persistence.

**What went well** — the tested `apply_transfer` was reused verbatim for the manual swap (a swap is a swap);
"one generic validator + mutation-helpers-only" kept edit logic from scattering; the ADR's two settled
questions (edit-everywhere; warn-not-block) removed all mid-build guesswork. Building the mutating path also
*surfaced* the latent nameless-demo bug — a real edit path exercises corners a read-only one never did.

**What to watch** — the manual swap is same-position only (keeps a single swap legal); a true positional
reshape would need a multi-swap flow (deferred). Session edits are still lost on a browser refresh until
downloaded — the biggest likely tester confusion; the UI says so.

**Refinement logged honestly** — `squad_15_issues` shipped **structural-only** (budget warned at the edge),
a cleaner realisation of "budget never blocks" than the ADR's first draft; ADR-055 + the plan were updated
to match the code.

**Lessons captured:** `docs/05_Sprints/Sprint58_Lessons_Learnt.md`.
