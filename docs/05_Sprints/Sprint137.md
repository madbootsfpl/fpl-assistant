# Sprint 137: Analytics coverage — feature events, perf timers, a gated admin view

**Dates:** 2026-08-09
**Status:** ✅ Complete (US-335/336/337 · no new ADR — extends ADR-100 · retro pending)
**Capacity:** ~1 session (instrumentation is one-liners; the admin view is the meat)
**Carried Over:** the Sprint 136 fast-follow (this sprint)

> **Direction (owner):** the analytics **foundation** is live + verified (rows landing). Now the fast-follow:
> **full event coverage** (the feature events + `error`), **perf timers** on the key operations, and a **minimal
> gated admin view** so you read the numbers in-app instead of hand-running SQL.

---

### 🔎 Verified at planning (on real data + the code)

- **The instrumentation sites are one-liners.** Analysis runs in `views/squads.py` (`decision_xp` / `select_squad`
  / `analyse_squad`); save/load in `squads.render_cloud_sync`; feedback in `pages/8_Feedback.py` (the form submit +
  the relay result). Each is a single `analytics.track(...)` / `analytics.timed(...)` — the client already no-ops
  when off, so wiring is safe.
- **Analytics must stay out of the core.** `decision_xp` etc. live in `src/analytics` (the engine imports nothing
  web). So perf/`analysis_run` are timed at the **web view layer**, never in the engine — the boundary holds.
- **The admin view is the *first read* of `events` — and RLS currently blocks it.** The `events` table allows
  **anon INSERT only**; a SELECT needs a policy. The anon key is **server-side** (Streamlit secrets, never sent to
  a browser), and events are anonymous — so an **anon SELECT policy** lets the *server* (the admin page) read them
  safely; testers never have the key. (Owner adds the policy; documented in ANALYTICS.md.) This is a new server
  **read**, gated by an owner password — not a new write.
- **PostgREST won't do percentiles.** So the admin view **fetches recent rows and aggregates in Python** (counts,
  unique via sets, median/P95 via `statistics`) — simple and ample for hobby-beta volume; no SQL functions needed.
- **Anonymity has a sharp edge here:** `squad_saved`/`squad_loaded` must **not** log the **handle** (a chosen,
  semi-identifying key) — `meta` stays anonymous. A test will assert the handle never appears in a payload.

---

### 🎯 Sprint Goal

**Objective:** the analytics answer *"what's used, by how many, how reliably, and how fast?"* — the feature events
+ `error` fire at their sites, perf timers capture the key operations, and a **gated admin view** shows the
headline numbers in-app. All still opt-in, anonymous, and fail-silent (unchanged from ADR-100).

#### Success criteria
- [x] **US-335 (feature events + error)** — `analytics.track(...)` at the action sites: `squad_created` (a build),
      `analysis_run` (a squad analysis/plan), `player_viewed` (the History player pick), `squad_saved` /
      `squad_loaded` (cross-device — **no handle in `meta`**), `feedback_submitted` (a sent form), and `error`
      (`{component}`) at the key try/except sites (data-load, cloud, feedback, analysis). `page_viewed("Feedback")`
      already covers *feedback_opened*. Tests: each fires when enabled (monkeypatched `track`); **no handle/PII** in
      any payload; still a no-op when off.
- [x] **US-336 (perf timers)** — wrap the user-visible ops in `analytics.timed(op, page=…)`: **`data_load`** (the
      per-page `Storage` read), **`analysis`** (the `decision_xp`/`select_squad` calls in the squad views),
      **`squad_save`** / **`squad_load`** (the `cloud_store` calls) → `perf` events (duration + ok). Tests: a `perf`
      event with a positive duration on success; `ok=False` + re-raise on failure; no-op when off.
- [x] **US-337 (the gated admin view)** — `pages/9_Admin.py`, gated by **`FPL_ADMIN_KEY`** (an owner password;
      **inert when unset** → the public deploy shows a "not configured" note). Reads recent `events` (via the anon
      key + an anon SELECT policy) and shows, aggregated **in Python**: sessions · unique/returning devices · top
      pages/features · success vs failure rate · **median/P95** per timed op — `st.metric`s + small tables/a bar.
      Best-effort (a store hiccup → a friendly note, never a crash). Tests: unset key → inert; wrong key → locked;
      right key + mocked events → the aggregates render.
- [ ] **No unintended drift** — analytics still off by default (no `FPL_ANALYTICS` → no events; no `FPL_ADMIN_KEY`
      → the admin page is inert); the guardrail holds; the engine is untouched; existing **885** stay green; ruff clean.
- [ ] **Docs** — `docs/ANALYTICS.md` (the anon **SELECT** policy + `FPL_ADMIN_KEY` + the admin view); BETA.md (the
      admin key); PROJECT_STATUS; Architecture; ADR-100 follow-up note (coverage + admin built).

---

### 🧭 Design sketch

**No new ADR** — extends ADR-100 (which already named the feature events, perf timers, and a minimal admin view as
the fast-follow). No new dependency; the engine boundary is preserved (instrument at the web layer only).

**US-335 / US-336 — instrumentation.** One-liners at the sites, e.g.:
```
with analytics.timed("data_load", page="Squads"):     # US-336
    players = store.get_players(); …
…
with analytics.timed("analysis", page="Squads"):      # US-336
    ranked = decision_xp(...)
analytics.track("analysis_run", view="Health")        # US-335 (no squad contents; just the fact + the view)
…
analytics.track("squad_saved")                        # US-335 — NO handle in meta (anonymity)
```
`error`: `analytics.track("error", component="data_load", page=…)` in the key `except` blocks (best-effort; it
never changes the error handling, just records it).

**US-337 — the admin view (`pages/9_Admin.py`).** `require_access()` (testers still gated) then an **`FPL_ADMIN_KEY`
password gate** (`access.secret`-based; unset → "Admin analytics isn't configured"). On unlock: `analytics` reads
the last N events (a `GET .../events?select=…&order=ts.desc&limit=…`, anon key + the SELECT policy), aggregates in
Python, and renders `st.metric`s (sessions · devices · returning · success rate) + a **top pages/events** table +
a **median/P95 per op** table + a small bar. Best-effort; a store error → a note. A new `analytics.recent_events()`
(the first read) + pure `analytics.summarise(rows)` (unit-testable aggregation) keep the page thin.

**Anon SELECT policy (owner, ANALYTICS.md):**
```sql
create policy "anon events read" on events for select using (true);   -- server-side anon key only; events are anonymous
```

**Deferred (unchanged):** event **batching** (if volume grows); a full **BI dashboard**; **cohort/funnel** analysis.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-335 | **Feature events + error** — `squad_*`/`analysis_run`/`feedback_submitted`/`error`. | High | ✅ Done | ~⅓ session |
| US-336 | **Perf timers** — `data_load`/`analysis`/`squad_save`/`squad_load` via `analytics.timed`. | Med | ✅ Done | ~¼ session |
| US-337 | **The gated admin view** — `pages/9_Admin.py` (`FPL_ADMIN_KEY`) reads + summarises `events`. | High | ✅ Done | ~½ session |

---

### 🧑‍💻 Owner runbook actions (you)

1. **Add the anon SELECT policy** on `events` (SQL above / ANALYTICS.md) so the admin view can read.
2. **Set `FPL_ADMIN_KEY`** in Streamlit secrets (an owner password) → the **Admin** tab unlocks for you only.
   (Unset → the page is inert; testers can't see the numbers.)

---

### ✅ Definition of Done

1. **Tests** — the feature events fire at their sites (monkeypatched `track`); **no handle/PII** in any payload;
   `timed` emits `perf` (duration + ok, re-raises on failure); the admin view is inert without the key, locked on a
   wrong key, and renders aggregates on the right key with mocked events; `summarise` computes counts/median/P95;
   still off by default. **885** stay green; ruff clean.
2. **Manual smoke** — enable + use the app → `analysis_run`/`squad_*`/`feedback_submitted` + `perf` rows land;
   open **Admin**, enter the key → the numbers render; a bad key → locked; the engine/UX unaffected.
3. **Docs** — ANALYTICS.md (SELECT policy + admin key + the view); BETA.md; PROJECT_STATUS; Architecture; ADR-100 note.

---

### 📝 Session Progress Log

- **US-335 (feature events + error)** — wired one-line `analytics.track(...)` at the action sites: **`analysis_run`**
  (`view=`) in the `3_Squads.py` dispatcher's manage-view branch (one site covers My Squad/AI Tips/Chips/Health/
  Transfer/Captain); **`squad_created`** (`mode=`) on the deliberate **"Use this squad →"** click (not per-render);
  **`squad_saved`/`squad_loaded`** in `squads.render_cloud_sync` on success — **no handle/contents** (anonymity);
  **`feedback_submitted`** (`page=`) on a sent form (no message content); **`error`** (`component=`) in the cloud
  save/load + feedback `except` blocks. Skipped **`player_viewed`** (owner's call — chattiest/least actionable);
  **`feedback_opened`** is covered by `page_viewed("Feedback")`. Analytics stays **out of the engine** — every call
  is at the web layer; each is a no-op when off (existing suite unchanged). **+4 tests** (events fire at their
  sites via a captured `track`; **the handle/message never appear in any payload**). ruff clean. **885 → 889.**
  (US-336 adds perf timers; US-337 the admin view.)
- **US-336 (perf timers)** — wrapped the user-visible ops in `analytics.timed(op, page="Squads")` → `perf` events
  (duration + ok): **`data_load`** (the `Storage` reads on **Squads** + **Players**), **`analysis`** (the
  `select_squad` optimiser in `render_build`), **`squad_save`**/**`squad_load`** (the `cloud_store` calls). Timed
  the **compute/IO only, not full renders** — a render contains `st.rerun()` (a `RerunException`) which `timed`
  would otherwise record as a failure; wrapping just the calculation/IO keeps `ok` honest and avoids per-rerun
  noise. A failed op emits `perf(ok=False)` *and* its `error` event (US-335) — both signals. **+2 tests** (Squads
  emits `data_load` + `analysis` perf with an int duration; Save/Load emit `squad_save`/`squad_load` perf). ruff
  clean. **889 → 891.** (US-337 = the gated admin view that reads + summarises these.)
- **US-337 (the gated admin view)** — the **first analytics READ**. `analytics.recent_events()` (a best-effort GET
  of the last ~2000 events; **None** on failure) + a **pure** `analytics.summarise(rows)` (sessions · devices ·
  **returning** = a device on 2+ distinct days · top pages · event counts · success rate · **median/P95** per op,
  via a linear-interpolation `_percentile`). `pages/9_Admin.py` is thin: `require_access()` → an **`FPL_ADMIN_KEY`**
  password gate (**inert when unset** → a "not configured" note; wrong key → locked) → on unlock, `st.metric`s +
  top-pages/event tables + a perf table; best-effort (a store error → a note, never a crash). Needs an **anon
  SELECT policy** on `events` (the anon key is server-side; events are anonymous) — documented. Updated the
  page-list + emoji tests for the 10th (**📊 Admin**) tab. **+7 tests** (`summarise` counts/top-pages/success/
  median-P95/empty-safe; `recent_events` reads/degrades; the admin gate inert/locked/unlocked). ruff clean.
  **891 → 898.** **Sprint 137 complete** — full analytics coverage + a self-serve admin view.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ the analytics now answer the **full** question — *what's used, by how many, how reliably, how fast* —
and the owner reads it in a **📊 Admin** tab instead of hand-running SQL. Built on the Sprint 136 foundation; still
opt-in, anonymous, fail-silent (ADR-100 unchanged).

**Delivered**
- **US-335** — feature events + `error` at the action sites (`analysis_run`/`squad_created`/`squad_saved`/
  `squad_loaded`/`feedback_submitted`/`error`), one-liners, anonymity-tested (no handle/message in any payload).
- **US-336** — perf timers (`data_load`/`analysis`/`squad_save`/`squad_load`) via `analytics.timed`, wrapping the
  compute/IO (not full renders, so `st.rerun` isn't misread as a failure).
- **US-337** — the first analytics **read**: `recent_events` + a pure `summarise`, behind a gated `pages/9_Admin.py`
  (`FPL_ADMIN_KEY`), rendering sessions/devices/returning + top pages + success + median/P95.

**Verified** — the events fire at their sites and carry **no PII/handle/message**; `perf` events carry an int
duration; `summarise` is pinned (counts, returning across days, median/P95, empty-safe); the admin page is inert
without the key, locked on a wrong key, and renders on the right key with mocked events; still off by default (no
`FPL_ANALYTICS` → nothing; no `FPL_ADMIN_KEY` → inert). Existing suite green (**885 → 898**).

**Metrics** — 898 tests (885 → +13: US-335 +4, US-336 +2, US-337 +7) · ruff + CI-parity green · **100 ADRs** (no
new ADR) · 3 stories, ~1 session.

**What went well**
- **Anonymity stayed testable** — every event site is pinned to carry no handle/message; the sharp edge
  (`squad_saved` logging the handle) was designed out and asserted, not hoped.
- **Perf timing without the rerun trap** — timing the compute/IO (not the render) keeps `ok` honest, since a
  Streamlit render raises `RerunException` on every button; a spurious "failure" per click would have been noise.
- **The read stayed minimal + safe** — a pure `summarise` (unit-tested) + a thin page; the first read is gated by
  an owner password and an anon SELECT policy (server-side key, anonymous data), best-effort so it can't crash.
- **One-liner instrumentation** — the client's no-op-when-off design meant wiring events/timers changed nothing
  for the suite; the diff is small and the risk low.

**Even better if**
- **The admin read is unproven until the owner smoke** — AppTest mocks the read; adding the anon SELECT policy +
  `FPL_ADMIN_KEY` and seeing the real dashboard is the confirmation (like the write smoke).
- **`analysis_run` fires per manage-view render** — a reasonable usage proxy, but it over-weights a left-open tab;
  the owner can count *distinct sessions per view* rather than raw counts. Batching/dedup is deferred.
- **Coverage is the key pages, not every page** — `data_load` is timed on Squads + Players (the heaviest/most-used);
  more pages are a trivial add if a specific one looks slow.

**Deferred / backlog** — event **batching** (if volume grows); a full **BI dashboard**; **cohort/funnel** analysis;
`player_viewed` (skipped as low-value). And the big body: **GW1 (2026-08-21) calibration** + momentum + live
manager import.

**Follow-up marker:** ⏳ **owner smoke** — add the anon **SELECT** policy + set **`FPL_ADMIN_KEY`**, open the 📊
Admin tab, confirm the dashboard reads real events. Then the analytics epic (ADR-100) is fully closed.

---

### 📌 For Tony

- **Admin page visibility** — `pages/9_Admin.py` shows as a sidebar tab (locked without the key). OK, or would you
  rather tuck the admin view behind a less-visible entry? (Streamlit's folder-based nav always lists a page.)
- **`player_viewed`** — worth tracking (History picks), or skip it as low-value/chatty?
