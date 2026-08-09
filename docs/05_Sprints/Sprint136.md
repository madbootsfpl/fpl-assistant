# Sprint 136: Beta usage & experience analytics (foundation)

**Dates:** 2026-08-09
**Status:** 🚧 In progress (ADR-100 accepted · 3 foundation stories to build; Sprint 137 = coverage + admin)
**Capacity:** foundation ≈ 1 session; full instrumentation + admin ≈ a second
**Carried Over:** none

> **Direction (owner):** *"Can we see what beta users find useful, whether they return, and whether the app feels
> fast and reliable — without creating an analytics project of its own?"* Lightweight, anonymous, privacy-conscious
> analytics: **usage** (what's used, who returns) + **experience** (perf, failures). Reuse Supabase; no Google
> Analytics; **analytics must never affect normal app operation**.

---

### 🔎 Verified at planning (on real data + the code)

- **The write path reuses what's already proven.** `cloud_store`/`user_store` show the exact pattern: an endpoint
  **derived from `FPL_STORE_URL`'s base** (`.../rest/v1/squads` → `.../rest/v1/events`), reusing `FPL_STORE_KEY` —
  **no new store secret** — with `_headers`, a tight timeout + `with_retry`, best-effort. A new `events` table is a
  drop-in sibling of `beta_users`.
- **This is the *third* deliberate server write.** The read-only invariant (ADR-053/054) already names two
  exceptions — squad-save (ADR-094) + registration (ADR-098). Analytics is a **third, opt-in, secret-gated**
  write; the guardrail test (`tests/test_web_squads.py`) that pins "off by default, no secrets → no POST" gets a
  sibling for analytics. **This is the architectural decision → ADR-100.**
- **"Never degrade" is the hard constraint, and Streamlit reruns a lot.** A synchronous POST on every event would
  add latency to the user's reruns — unacceptable. So `track()` must be **fire-and-forget** (a daemon thread with a
  tight timeout), and **wrapped so no exception can ever reach the app**. Disabled → an immediate no-op (no thread).
- **No app-version constant exists** (the app is `0.0.1` in PROJECT_STATUS). Add `config.APP_VERSION = "0.0.1"` for
  the event `version` field (generally useful too).
- **"Returning users" needs a persistent, anonymous id — and we just built the infra.** A per-session UUID
  (`st.session_state`) counts *sessions*; counting *returning* usage needs an id that survives a new session — a
  first-party **anonymous** cookie `fpl_anon` (a random UUID, **no PII, not the squad handle**), read/written via
  the **verified `remember.py` component** (Sprint 134). Reuses the lesson: read+write through the *same*
  component; the one-run "loading" delay is handled **without blocking** (mint a new id only once the cookie has
  settled, so we don't double-count) — analytics never `st.stop()`s the page.
- **Instrumentation points already have natural homes.** `require_access()` + `render_data_status()` run on every
  page (a hook for `session_started`/`page_viewed`); the action sites (`cloud_store.save/load`, the Build/Health/
  AI-Tips/Analyse renders, the Feedback form) are one-line `track(...)` calls.

---

### 🎯 Sprint Goal

**Objective:** an **opt-in, anonymous, fail-silent** analytics path that records **usage** (sessions, returning
users, feature/page use) and **experience** (perf duration + success/failure) to a Supabase `events` table —
**off by default**, reusing the existing store, and **provably unable to affect the app**. Owner inspects via
documented SQL (a minimal admin view is a fast-follow).

#### Success criteria (foundation)
- [x] **ADR-100 (the gate)** — record the analytics write path: the **third opt-in, secret-gated** server write
      (extends ADR-094/098's revision of ADR-053/054); **fire-and-forget** (daemon thread + tight timeout) that
      **fails silently**; **off by default** behind a dedicated **`FPL_ANALYTICS`** enable flag *and* the store
      being configured; the **anonymous** identity model (a session UUID + a persistent `fpl_anon` UUID cookie —
      **no PII, no email/IP, not the handle, no full squad data**); the `events` schema; the privacy guardrails
      (no click/mouse/screen tracking, no third-party service); admin via SQL/a minimal gated view; that it
      **softens nothing** in the analytics-decide-not-track posture — it observes *the app's* usage, never the FPL
      decisions.
- [x] **US-332 (the analytics client)** — `src/web_streamlit/analytics.py`: `is_enabled()` (store configured **and**
      `FPL_ANALYTICS` truthy), `session_id()` (per-session UUID), `track(event, *, page=None, duration_ms=None,
      ok=True, **meta)` (fire-and-forget to `events`, derived endpoint, best-effort, **swallows everything**),
      `timed(op, page=None)` (a context manager → a `perf` event with duration + ok). `config.APP_VERSION`. **No
      thread, no write when disabled.** Fully unit-tested (monkeypatched requests/thread): enabled → the right
      anonymised payload; disabled → no-op; a raising store → swallowed; **no PII / no squad data** in the payload.
- [x] **US-333 (the returning-user anon id)** — a `fpl_anon` UUID cookie via `remember.py` (read/write through the
      component), attached to events as `anon_id`; minted once (settled, no double-count), best-effort. If the
      cookie is unavailable, events still carry `session_id` (sessions counted; returning degrades gracefully).
- [ ] **US-334 (core wiring + the guardrail)** — `session_started` (once/session) + `page_viewed` (per page) via a
      shared boot hook; `error` on the key try/except sites; **the guardrail**: a test that a raising/389-ing store
      **never** breaks a page, and that **unset `FPL_ANALYTICS` / no store → zero writes, zero threads, the suite
      byte-identical**. (The remaining events + perf timers + admin view = Sprint 137, below.)
- [ ] **Docs** — ADR-100 + index; a new **`docs/ANALYTICS.md`** (owner runbook: the `events` table SQL + RLS, the
      `FPL_ANALYTICS` flag, the inspection SQL queries); DIRECTION (records the analytics decision); BETA.md link;
      PROJECT_STATUS; Architecture.

---

### 🧭 Design sketch

**ADR-100.** Analytics is an **observation layer over the app**, not the analytics engine — it records *that* a
page was viewed / an analysis ran / a save succeeded, never *what the FPL model decided*. The write is the third
deliberate, opt-in, secret-gated server write; everything about it is subordinate to **"can never affect the app"**.

**US-332 — the client (`analytics.py`).**
```
def is_enabled() -> bool:        # cloud_store.is_configured() AND secret("FPL_ANALYTICS") truthy — else all no-ops
def session_id() -> str:         # a per-session uuid4 in st.session_state
def track(event, *, page=None, duration_ms=None, ok=True, **meta) -> None:
    if not is_enabled(): return                      # immediate no-op, no thread
    payload = {ts, session_id, anon_id, version, event, page, duration_ms, ok, meta}   # anonymised, small
    threading.Thread(target=_post, args=(payload,), daemon=True).start()               # fire-and-forget
    # _post: requests.post(events_url, json=payload, timeout=…) inside try/except → swallow everything

class timed:                     # `with analytics.timed("data_load", page="Squads"): …` → a perf event
    __enter__ = start clock;  __exit__ = track("perf", meta={op}, duration_ms=…, ok=(exc is None))
```
Endpoint: `FPL_STORE_URL.rsplit("/",1)[0] + "/events"`, `_headers(key)` reused. `meta` is **small structured
context** (e.g. `{"view": "Health", "n": 15}`) — **never** names/emails/IPs or a full squad.

**US-333 — anon id.** `analytics.anon_id()`: read `fpl_anon` via `remember` (component); present → returning;
absent + settled → mint `uuid4`, write it (best-effort). Attached to every event. No PII; independent of the squad
handle and the `fpl_beta` gate cookie.

**US-334 — wiring + guardrail.** A shared `analytics.boot(page)` (called where `render_data_status()` already is):
`session_started` once (a session flag) + `page_viewed`. `track("error", meta={component})` at the key failure
sites. The guardrail test makes `requests.post` raise and asserts pages still render; and asserts **no POST when
`FPL_ANALYTICS` is unset** (like the ADR-094 guardrail).

**The `events` table (Supabase).**
```
create table if not exists events (
  id bigint generated always as identity primary key,
  ts timestamptz not null default now(),
  session_id text, anon_id text, version text, event text, page text,
  duration_ms int, ok boolean, meta jsonb
);
-- anon INSERT only (like squads); reads are the owner's (service role / SQL / the admin view).
```

**Sprint 137 (fast-follow) — full coverage + admin:** the remaining events (`squad_created`, `analysis_run`,
`player_viewed`, `squad_saved`, `squad_loaded`, `feedback_opened`, `feedback_submitted`) + perf timers on the key
ops (startup, FPL data load, analysis, save, load) + a **minimal gated admin view** (`FPL_ADMIN_KEY`) reading
aggregates (unique anon, sessions, top pages/features, success rates, median/P95 via `percentile_cont`). Dashboard
polish deferred until there's real beta data.

---

### 📋 Sprint Backlog (foundation)

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-100 | **The analytics write path** — opt-in, secret-gated, fire-and-forget, anonymous, fail-silent. | High | ✅ Done | gate |
| US-332 | **The analytics client** — `analytics.py`: `is_enabled`/`session_id`/`track`/`timed` + `APP_VERSION`. | High | ✅ Done | ~⅓ session |
| US-333 | **Returning-user anon id** — a `fpl_anon` UUID cookie via `remember.py`, attached to events. | Med | ✅ Done | ~¼ session |
| US-334 | **Core wiring + the guardrail** — `session_started`/`page_viewed`/`error` + fail-silent/off-by-default tests. | High | ⬜ To do | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you — when enabling, ~5 min)

1. **Create the `events` table** (+ anon-insert RLS) in the same Supabase project (SQL in `docs/ANALYTICS.md`).
2. **Turn it on:** set `FPL_ANALYTICS = "1"` in Streamlit secrets (the store secrets are already set for squads).
   Unset it → analytics is fully off. Inspect via the SQL queries in `ANALYTICS.md` (the admin view lands next).

---

### ✅ Definition of Done (foundation)

1. **Tests** — `track` posts the right **anonymised** payload when enabled (monkeypatched requests/thread), is a
   **no-op with no thread when disabled**, and **swallows a raising store**; the payload carries **no PII/no squad
   data**; `timed` emits a `perf` event with duration + ok; the anon id persists across sessions (mocked cookie);
   the **guardrail** (raising store → pages render; no secrets → zero writes → suite byte-identical). Existing
   **867** stay green; ruff clean.
2. **Manual smoke** — with the store + `FPL_ANALYTICS=1`: use the app → rows land in Supabase `events`; unset the
   flag → none; kill the network → the app is unaffected.
3. **Docs** — ADR-100 + index; `docs/ANALYTICS.md`; DIRECTION; BETA.md; PROJECT_STATUS; Architecture.

---

### 📝 Session Progress Log

- **ADR-100 (the gate)** — wrote `docs/06_Decisions/ADR-100-beta-usage-analytics.md` (Accepted). Records the
  **opt-in, anonymous, fail-silent** analytics write path: a `web_streamlit/analytics.py` client `track()`s small
  usage + `perf` events to a Supabase **`events`** table (endpoint derived from `FPL_STORE_URL`, no new secret);
  the **#1 rule** — never affect the app — via **fire-and-forget** (daemon thread + tight timeout) + a blanket
  swallow, and a hard **no-op when disabled**; **off by default** behind a dedicated **`FPL_ANALYTICS`** flag *and*
  the store configured (the **3rd** opt-in, secret-gated server write; guardrail-pinned, byte-identical without
  it); **anonymous + minimal** identity (a per-session `uuid4` + a persistent `fpl_anon` UUID cookie for returning
  users, via the ADR-099 component — **no PII/email/IP, not the handle, no full squad, no click/mouse/screen
  tracking, no 3rd-party service**); insert-only, owner-controlled; admin = SQL now / a minimal gated view next; a
  2-sprint split (136 foundation · 137 coverage+admin). Alternatives recorded (GA ✗, sync emit ✗, session-only ✗,
  handle-as-id ✗, separate DB ✗, batching deferred). Added to the ADR index. **100 ADRs.** (US-332 builds the
  client next.)
- **US-332 (the analytics client)** — added `src/web_streamlit/analytics.py` + `config.APP_VERSION = "0.0.1"`.
  `is_enabled()` = `FPL_ANALYTICS` truthy **and** `cloud_store.is_configured()` (else every call is a hard no-op);
  `_events_endpoint()` derives `.../rest/v1/events` from `FPL_STORE_URL`'s base (no new secret); `session_id()` (a
  per-session `uuid4` in session state); `anon_id()` (session-state slot, populated by US-333); `track(event, *,
  page, duration_ms, ok, **meta)` — **builds the anonymised payload on the main thread** (session state is safe
  there) then POSTs it **fire-and-forget on a daemon thread**, the whole thing wrapped so **nothing can ever raise
  into the app**; disabled → **no thread, no write**; `timed(op, page)` context manager → a `perf` event (duration
  + ok, re-raises on failure). Headers reuse the anon key + `Prefer: return=minimal`. **+10 tests**
  (`tests/test_analytics.py`): flag+store gating · endpoint derivation · **off → no thread/no POST** · an
  **anonymised** payload (exact key set) · **no-PII** scan (no email/@/handle/player_ids/ip) · a **raising store
  swallowed** · **build failure swallowed** (no thread) · `timed` perf + failure-reraise · session-id stability.
  ruff clean. **867 → 877.** (US-333 wires the `fpl_anon` returning-user id; US-334 the core wiring + guardrail.)
- **US-333 (the returning-user anon id)** — generalised `remember.py` to **named cookies** (`read_cookie(name)` /
  `write_cookie(name, value, days)`; the gate's `read`/`write` now delegate — non-breaking, same jar), so the
  analytics `fpl_anon` cookie rides the **verified** component alongside `fpl_beta`. `analytics.anon_id()` resolves
  best-effort (never raises): session cache → the existing `fpl_anon` cookie (a **returning** device) → **mint a
  `uuid4` + write it**, but **only once the component has settled** (`_cookie_settled`, a one-shot mirroring the
  gate's wait) so a still-loading first run **can't overwrite a returning id / inflate unique-users**; no component
  → mint session-only. Anonymous, long-lived (365d), independent of the handle + the gate cookie. Attached to every
  event as `anon_id` (US-332 already reads it); unresolved → events still carry `session_id`. **+4 tests** (named
  cookie roundtrip + gate delegation; returning cookie → no mint; **defer-then-mint** across the loading run;
  mint-without-a-component). ruff clean. **877 → 881.** (US-334 wires session/page/error + the guardrail.)

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony — decisions before I gate ADR-100

1. **Split into two sprints?** I recommend **yes**: Sprint 136 = the foundation (client + anon id + guardrail +
   core events + the table/docs — a *provable, safe* write path), then Sprint 137 = full event coverage + perf
   timers + the admin view. Cleaner gate, smaller modules. Or do it all as one bigger sprint?
2. **Enable flag** — a dedicated **`FPL_ANALYTICS=1`** opt-in (my recommendation — analytics is deliberate + can be
   toggled without touching squads), or just auto-on whenever the store is configured?
3. **Returning users** — include the anonymous `fpl_anon` cookie now (reuses the verified infra) so "returning" is
   measurable, or ship session-only first and add persistence later?
4. **Admin** — SQL queries in `ANALYTICS.md` now + a minimal gated view next sprint (my rec), or a view this sprint?
