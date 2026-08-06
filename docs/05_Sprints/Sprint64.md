# Sprint 064: Phase 6 Tier 2 (start) — an FPL news lens + import your team by manager-ID

**Dates:** 2026-08-06
**Status:** 📝 Planned
**Capacity:** ~2–3 working sessions (a gate + a news lens + a manager-ID import + docs)
**Carried Over:** None (Sprint 063 shipped the pitch-photo polish)

> **Direction (owner):** open Phase 6 **Tier 2** — *social media news, feeds & trends, manager input*.
> Owner's calls: **start with FPL official news** (free, no keys) and **"manager input" = import my FPL
> team by manager-ID**. Keyed social (Reddit/X) + pundit NLP stay **deferred** (cost/keys/robustness). Still
> a **lens / import, not xP**; external sources **degrade gracefully** (the ClubElo pattern, ADR-010/021).

---

### 🔎 Verified at planning (feasibility + a season gate)

- **FPL official news is already free** — right now **58 players carry `news`** (e.g. *J.Timber — "Groin
  injury, expected back 21 Aug"*), which we **already ingest** as `player.news`, plus `scout_news_link`
  URLs. So the news lens needs **zero new dependencies** and works **now**.
- **The manager-team import is GW1-gated.** `/entry/{id}/` (name, overall rank, `started_event`) works
  preseason, **but `/entry/{id}/event/{gw}/picks/` → HTTP 404** until the **GW1 deadline (2026-08-21)** — a
  manager's squad isn't public until then. So: **build the import now** (fetch + validate + map the known
  picks shape, tested against a mocked payload), **degrade gracefully preseason** (validate the ID, show
  "your team is available after the GW1 deadline"), and it **activates at GW1**.
- **The import is public + no-auth.** `/entry/{id}/…/picks/` is public post-deadline (not the auth-only
  `/my-team/`), so no secrets. It just becomes **another way to set the session active squad** (like
  build/upload, ADR-054) → no server writes.
- **No new external services / secrets this sprint** — both pieces are FPL-API/free; keyed social deferred.

---

### 🧭 What's new — news + your real team

A **News** view surfaces the official FPL news we already hold (injuries / doubts / return dates + a scout
link), degrading to "no current news" when clear. And **Import team**: type your **FPL manager-ID** and pull
your real squad (once GW1 locks it in) straight into the app as your **active squad** — so Analyse /
Transfer / Captain / My Squad all run on *your* team.

---

### 🎯 Sprint Goal

**Objective:** open Phase 6 Tier 2 with two **free, no-key** pieces — an **FPL official-news lens** (works
now) and an **import-team-by-manager-ID** (built now, live at GW1) — both degrade-gracefully, both a
lens/import over the settled edge (xP untouched). A gate settles the Tier-2 model.

#### Success Criteria
- [ ] Approach agreed (**ADR-058**) — Tier 2 opener: an FPL-news lens + a manager-ID import; both free/no
      secrets; **degrade gracefully**; keyed social (Reddit/X) + pundit NLP **deferred**; import = another
      way to set the session squad (no server writes); import picks are **GW1-gated**
- [ ] **FPL news lens** — a **News** page/panel listing currently-flagged players (name · team · status ·
      the `news` text · a scout link), degrading to "no current news"; reuse the ingested `player.news`
- [ ] **Import team by manager-ID** — a manager-ID input → fetch `/entry/{id}/` (validate + show the
      manager name) + `/entry/{id}/event/{gw}/picks/` → map to a squad dict (player_ids · bench_ids ·
      captain_id) → **set as the active squad**; **preseason**: validate the ID + a clear "available after
      the GW1 deadline" message
- [ ] **Degrade gracefully** — a bad ID / API down / 404 picks → a clear message, no crash (ClubElo pattern)
- [ ] **No xP change / no server writes** — the import sets `session_state` only; `decision_xp` untouched
- [ ] Tests — the news lens renders the flagged players (+ the empty case); the picks→squad **mapping**
      (unit-tested against a **mocked** picks payload); ID validation + the preseason/404 message; existing
      **504** stay green
- [ ] Docs: ADR-058 + index, Architecture, Handbook/README note, PROJECT_STATUS, Roadmap (Tier-2 started)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-189 | **Gate.** Tier-2 opener (**ADR-058**): an FPL-news lens + a manager-ID import; free/no-keys; degrade-gracefully; import = another way to set the session squad (no server writes); keyed social + pundit NLP deferred; import picks GW1-gated | Critical | ✅ Done | 0.5 session |
| US-190 | **FPL official-news lens** — a **News** page listing flagged players (name · team · status · `news` · scout link) from the ingested `player.news`; degrades to "no current news". Tests + smoke | High | ✅ Done | 0.5–1 session |
| US-191 | **Import team by manager-ID** — a new FPL-API fetch (`/entry/{id}/` + `…/event/{gw}/picks/`) in the api/ingest layer (retry/degrade, ADR-021); map picks → a squad dict → set the active squad; a manager-ID input (sidebar or a page); **preseason-graceful** ("available after the GW1 deadline"). Unit-test the mapping against a mocked payload. Tests + smoke | High | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-058 recorded + indexed — _US-189_
- [x] `scout_news_link` ingested (model + storage `_migrate` + reseed) + a News page (`pages/9_News.py`) over `player.news` — _US-190_
- [ ] Config endpoints + an api fetch for `/entry/{id}/` + picks (retry/degrade) — _US-191_
- [ ] A pure `picks → squad dict` mapper (unit-tested via a mock) + wire an "Import team" control — _US-191_
- [ ] ADR index, Architecture, Handbook/README, Roadmap (Tier-2 started), PROJECT_STATUS — _US-191_
- [ ] (Post-GW1) confirm the import pulls a real squad once picks unlock — _carry_

---

### ✅ Definition of Done (this sprint)

1. **Automated tests pass** — the News lens renders flagged players + the empty case; the picks→squad mapper
   is unit-tested (mocked payload) incl. captain/bench; ID validation + the preseason/404 message; a test
   asserts `decision_xp` is unchanged; the no-server-writes guardrail holds; existing **504** stay green.
2. **Manual smoke test done** — News shows the 58 flagged players (or "no current news"); Import validates a
   real manager-ID and shows the "available after GW1" note preseason (and, post-GW1, pulls the squad).
3. **Documentation updated & checked** — ADR-058 + index, Architecture, Handbook/README, Roadmap,
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| An FPL official-**news** lens (free, existing data) | **Reddit / X** social feeds (keyed/paid — deferred) |
| **Import team by manager-ID** (public FPL API) | Pundit / **YouTube NLP** (heavy — deferred) |
| Degrade-gracefully external fetch (ClubElo pattern) | The **auth-only** `/my-team/` (pre-deadline private team) |
| Import → set the session squad (no server writes) | Blending any signal **into xP** / any engine change |

**External Dependencies:** FPL API only (no secrets). **Timing:** the news lens works **now**; the import's
**picks are GW1-gated** (built now, live 2026-08-21).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Import can't be fully demoed preseason (picks 404) | Med | Build + unit-test the mapping against a **mocked** payload; validate the ID + a clear "after GW1" message; verify live at GW1 |
| A flaky/absent FPL entry response | Med | Retry/degrade (ADR-021); a bad ID / down API → a clear error, no crash |
| Scope creep into keyed social | Low | ADR-058 explicitly defers Reddit/X/pundit to a later, gated sprint |
| Sentiment/news creeping into xP | Low | Display/import only; a test asserts `decision_xp` unchanged; no server writes |

---

### 🗝️ Gating decision (US-189 → ADR-058)

Proposed (confirm/redirect at "start US-189"):
1. **Tier 2 opens with free, no-key pieces** — an FPL official-**news lens** (surface `player.news` +
   scout links) and a **manager-ID team import** (public `/entry/…/picks/`). Keyed social (Reddit/X) +
   pundit NLP **deferred** (a later, gated sprint if proven worth the infra/secrets).
2. **Degrade gracefully** — the ClubElo pattern (ADR-021): a failed/absent fetch → a clear message, never a
   crash; FPL stays the source of truth.
3. **Import = another way to set the session squad** — maps public picks → a `SquadStore`-shaped dict →
   `session_state` (no server writes; like build/upload, ADR-054). Analyse/Transfer/Captain/My Squad then
   run on *your* team.
4. **GW1-gated import** — picks are 404 until the GW1 deadline; build now, degrade preseason, live at GW1.
5. **Not xP** — news + import are display/state, never inputs to `decision_xp`.

**Worked example (probed):** `/entry/1/` returns `{name, summary_overall_rank, started_event}` now;
`/entry/1/event/1/picks/` is 404 preseason (→ live at GW1); 58 players carry `news` today.

---

### 📝 Session Progress Log

- **US-189 (gate) ✅** — Recorded **ADR-058** (Phase 6 Tier 2 opener). Tier 2 starts with two **free,
  no-key** pieces: an FPL official-**news lens** (surface the ingested `player.news` + `scout_news_link`)
  and **import-team-by-manager-ID** (the **public** FPL entry API — not the auth-only `/my-team/`). Both
  **degrade gracefully** (ClubElo pattern, ADR-021); the import maps public picks → a `SquadStore`-shaped
  dict → `session_state` (a third way to set the active squad alongside build/upload, ADR-054 — **no server
  writes**); neither feeds `decision_xp` (a test guards it). **Keyed social (Reddit/X) + pundit NLP
  deferred**. Verified: `/entry/1/` works now; `/entry/1/event/1/picks/` is **404 until the GW1 deadline**
  → the import is **built now, degrades preseason, live at GW1**. ADR-058 indexed.
- **US-190 ✅** — **FPL official-news lens.** Ingested `scout_news_link` (the news source link) into the
  `Player` model + storage (`_migrate` + `CREATE`/`UPSERT`/`save`), normalising `""`→None; **reseeded
  `seed.db`** (58 players with news, 27 with a link; opening it stays a no-op). New **`pages/9_News.py`** —
  a read-only table of currently-flagged players (photo · badge · **Status** · **Chance** · **News** · a
  **Source** `LinkColumn` "read more"), **most-serious first** (Out → Injured → Suspended → Doubtful),
  degrading to "No current news — everyone's available 🎉". No external calls, no xP (display only). Home +
  the freshness caption included. Tests (+3 → **507**): `from_api` parses/normalises the link; a
  save/get round-trip; the migration adds the column; the News page lists flagged players (News + Source
  cols) or the all-clear. Smoke: 58 flagged rows render; `ruff` clean. Works **now**.

---

### 🏁 Sprint Review & Retrospective

_(to be completed at sprint close)_
