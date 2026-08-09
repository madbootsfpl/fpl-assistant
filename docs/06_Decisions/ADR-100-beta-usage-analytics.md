# Architectural Decision Record: Beta usage & experience analytics (an opt-in, anonymous, fail-silent write path)

**Decision ID:** ADR-100
**Date:** 2026-08-09
**Status:** Accepted
**Superseded By / Replaces:** adds the **third** deliberate server-side write from the web edge, after the squad
save (ADR-094) and the registration insert (ADR-098) — the read-only invariant (ADR-053/054) now names **three**
opt-in, secret-gated exceptions, each pinned by a guardrail test. Does **not** touch the analytics *engine* or the
grounded-answer posture (ADR-037/041): this observes *the app's usage*, never the FPL decisions.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner is running a private beta and wants to know: **what testers find useful, whether they return, and whether
the app feels fast and reliable** — *"without creating an analytics project of its own."* Today there's no
visibility: no usage counts, no returning-user signal, no performance measurement, no failure rate. The ask is
**lightweight, anonymous, privacy-conscious** analytics — usage (what's used, who returns) + experience (perf,
failures) — with one non-negotiable: **analytics must never affect normal app operation.**

**Verified at planning:**
- **The write reuses proven infra.** `cloud_store`/`user_store` already derive a table endpoint from
  `FPL_STORE_URL`'s base and reuse `FPL_STORE_KEY` (`_headers`, `with_retry`, best-effort). An `events` table is a
  drop-in sibling — **no new store secret**.
- **"Never degrade" collides with Streamlit's rerun model.** The app reruns on every interaction; a **synchronous**
  POST per event would add latency to the user's experience. Emits must be **fire-and-forget** (a daemon thread +
  a tight timeout) and **wrapped so no exception can reach the app**.
- **"Returning users" needs a persistent, anonymous id — and the infra exists.** A per-session UUID counts
  *sessions*; counting *returning* usage needs an id that survives a new session. The **verified `remember.py`
  cookie component** (Sprint 134) can hold a first-party **anonymous** UUID cookie (`fpl_anon`) — no PII.
- **No app-version constant exists** (the app is `0.0.1`); add `config.APP_VERSION` for the event `version`.

#### Decision Drivers
- **Answer the owner's three questions** — usefulness, retention, performance/reliability — with minimal data.
- **Never affect the app** — fail-silent, non-blocking, and a hard no-op when off. This dominates every other call.
- **Anonymous + minimal** — no names/emails/IPs, no click/mouse/screen tracking, no third-party service, no full
  squad data; a random session id + a random returning-id only.
- **Reuse, don't re-architect** — the existing Supabase project + the `cloud_store` client patterns; no new secret.
- **Opt-in / reversible** — off by default behind a deliberate flag; the public deploy and CI write nothing.
- **Observe the app, not the model** — record *that* things happened, never *what the FPL engine decided*.

---

### ✅ Decision

**Add an opt-in, anonymous, fail-silent analytics client that fire-and-forgets small usage & performance events to
a Supabase `events` table — off by default, reusing the existing store, and provably unable to affect the app.**

**1. An observation layer, fail-silent by construction.** A `web_streamlit/analytics.py` client exposes
`track(event, *, page=None, duration_ms=None, ok=True, **meta)` and a `timed(op)` context manager. Every `track`:
**returns immediately if disabled** (no thread, no write); otherwise builds a small anonymised payload and posts it
on a **daemon thread with a tight timeout**, with the whole post **inside a blanket try/except that swallows
everything**. Analytics can therefore **never block, slow, or crash a rerun** — the worst case is a lost event.

**2. Off by default — a dedicated opt-in.** Analytics writes only when **`FPL_ANALYTICS` is truthy AND the store is
configured** (`cloud_store.is_configured()`). A *separate* flag from squads/registration makes it a **deliberate**
choice the owner turns on, and lets it be toggled without touching other features. Unset → a hard no-op; the public
deploy and the test suite are **byte-identical** (a guardrail test pins "no secrets → zero writes, zero threads").

**3. Anonymous identity — a session id + a returning id, nothing more.** Two random ids, **no PII**:
- **`session_id`** — a `uuid4` in `st.session_state`, distinguishing sessions.
- **`anon_id`** — a `uuid4` persisted in a first-party **anonymous** cookie **`fpl_anon`** (via the verified
  `remember.py` component), distinguishing *returning* usage across sessions on a device. Minted once, best-effort;
  if the cookie is unavailable, events still carry `session_id` (sessions counted, returning degrades gracefully).

  These are **deliberately not** the squad handle and **not** the `fpl_beta` gate cookie/registration email —
  analytics identity is a separate, meaningless-by-design random id.

**4. Minimal, structured events.** Each event: `ts, session_id, anon_id, version, event, page, duration_ms, ok,
meta`. `meta` is **small structured context** (e.g. `{"view": "Health", "n": 15}`) — **never** names, emails, IPs,
or a full/duplicated squad. The event vocabulary: `session_started`, `page_viewed`, `squad_created`,
`analysis_run`, `player_viewed`, `squad_saved`, `squad_loaded`, `feedback_opened`, `feedback_submitted`, `error`,
and `perf` (a timed op with duration + ok). Where practical, operations distinguish **started / completed / failed**
via `ok` and paired events.

**5. Performance for user-visible operations only.** `timed(op)` measures wall-clock for app/page startup, FPL data
loading, analysis/calculation, and squad save/load, emitting a `perf` event with **duration + success/failure**.
The app stores raw durations; **median / P95 are computed by the owner** (SQL / the admin view), not in the app —
this sprint *measures* performance, it does not optimise it.

**6. The store — a sibling `events` table, no new secret.** A Supabase `events(id, ts, session_id, anon_id,
version, event, page, duration_ms, ok, meta)` table in the **same project**; the endpoint is derived from
`FPL_STORE_URL`'s base (reusing `FPL_STORE_KEY`). **Anon INSERT only** (RLS like `squads`); the app never reads
events except the (later, gated) admin view. Insert-only keeps the surface tiny and the data owner-controlled.

**7. Privacy posture, recorded honestly.** Anonymous and minimal: **no** personal data, **no** IP/email/name, **no**
click/mouse/screen/keystroke tracking, **no** third-party analytics service (no Google Analytics), **no** duplicated
squad data. The two ids are random and meaningless outside "distinguish sessions/returns". Documented in
`docs/ANALYTICS.md` + DIRECTION.

**8. Admin visibility — SQL first.** `docs/ANALYTICS.md` ships the `events` DDL/RLS + a set of inspection queries
(unique `anon_id`, sessions, top pages/features, success rates, median/P95 via `percentile_cont`). A **minimal
gated admin view** (behind an `FPL_ADMIN_KEY`) is the fast-follow (Sprint 137); a full BI dashboard is out of scope
until there's meaningful beta data.

**9. Scope — a 2-sprint split.** **Sprint 136 (foundation):** this ADR + the client + the anon id + the guardrail +
core events (`session_started`/`page_viewed`/`error`) + the table/docs — a *provable, safe* write path.
**Sprint 137 (fast-follow):** full event coverage + perf timers on the key ops + the minimal admin view.

---

### 🔀 Alternatives Considered

- **Google Analytics / an external analytics platform.** Rejected — a third-party service, more data exposure, and
  explicitly out of scope. Supabase (already ours) keeps the data first-party and minimal.
- **Synchronous emit** (POST inline in the rerun). Rejected — adds latency to every tracked interaction, directly
  violating "never degrade". Fire-and-forget on a daemon thread is the non-blocking form.
- **Session-only tracking** (a `session_state` UUID, no cookie). Insufficient — can't tell a returning user from a
  new one (a refresh = a new session). The anonymous `fpl_anon` cookie adds *returning* cheaply, reusing verified
  infra; it degrades to session-only if cookies are unavailable.
- **Reuse the squad handle or the `fpl_beta`/registration email as the analytics id.** Rejected — that couples
  analytics to identity/PII. Analytics must use a *separate, random, meaningless* id.
- **A separate analytics database/project.** Rejected — reuse the existing Supabase project (endpoint derived, no
  new secret); "without creating an analytics project of its own" is the owner's framing.
- **Batching/buffering events** (flush on session end). Deferred — Streamlit has no clean session-end hook, and
  per-event fire-and-forget is simpler and sufficient for hobby-beta volume (semantic events, not per-rerun). Revisit
  only if volume grows.
- **Client-side JS analytics** (a component). Rejected — more moving parts in the browser; server-side best-effort
  is simpler, keeps tracking off the client, and reuses the store client we already have.
- **Auto-on whenever the store is configured** (no separate flag). Rejected — analytics should be a *deliberate*
  opt-in, decoupled from enabling squads; a dedicated `FPL_ANALYTICS` flag makes intent explicit and reversible.

---

### 🧭 Consequences

**Positive**
- The owner gets **usage + retention + performance/reliability** signals with **no new infra** (reuses Supabase, no
  new secret) and **no third-party service**.
- **Cannot affect the app** — non-blocking (daemon thread), fail-silent (blanket swallow), and a hard no-op when
  off; a guardrail test pins it, and the suite stays byte-identical without the flag.
- **Anonymous + minimal** — two random ids, small structured events, no PII / no tracking / no squad duplication;
  the privacy posture is documented, not implied.
- **Reversible + contained** — one flag turns it fully off; insert-only, owner-controlled data; the analytics/model
  posture is untouched (it observes the app, not the decisions).

**Negative / risks (mitigations)**
- **A third server write** — more surface. *Mitigation:* opt-in + secret-gated + fail-silent + a guardrail test;
  insert-only; endpoint derived (no new secret).
- **Fire-and-forget can drop events** (process exit, timeout, thread cap under load). *Mitigation:* accepted —
  analytics is best-effort by design; correctness of the *app* always wins over completeness of the *events*.
- **A returning-id cookie is still a cookie** (blocked/cleared → returning under-counts; anonymised). *Mitigation:*
  it's a random, anonymous id (no PII); degrades to session-only; documented.
- **Thread-per-event** at higher volume. *Mitigation:* fine for a hobby beta (semantic events); batching is a
  documented future step if volume grows.
- **Instrumentation touches many call sites.** *Mitigation:* one-line best-effort `track(...)` calls; a shared boot
  hook for session/page; coverage grows in Sprint 137, not all at once.

---

### 🧾 Status & follow-ups

- **Accepted.** Built Sprint 136 (foundation): US-332 (the `analytics.py` client + `config.APP_VERSION`), US-333
  (the `fpl_anon` returning-user id), US-334 (core wiring `session_started`/`page_viewed`/`error` + the guardrail);
  docs: `docs/ANALYTICS.md`, DIRECTION, BETA.md, PROJECT_STATUS, Architecture.
- **Owner actions:** create the `events` table (+ anon-insert RLS, `ANALYTICS.md`); set `FPL_ANALYTICS = "1"` to
  turn it on (store secrets already set); inspect via the `ANALYTICS.md` SQL. Unset the flag → fully off.
- **Built Sprint 137 (coverage):** US-335 (feature events `analysis_run`/`squad_created`/`squad_saved`/
  `squad_loaded`/`feedback_submitted` + `error`, anonymity-tested — `player_viewed` skipped as low-value),
  US-336 (perf timers `data_load`/`analysis`/`squad_save`/`squad_load`, timing the compute/IO not renders),
  US-337 (the **first analytics read** — a best-effort `recent_events` + a pure `summarise`, behind a gated
  `pages/9_Admin.py`/`FPL_ADMIN_KEY`, needing an **anon SELECT policy** on `events`). **Foundation write
  owner-verified** (rows landing, 2026-08-09); **admin read = owner smoke pending** (add the SELECT policy + the key).
- **Owner actions:** create the `events` table (+ anon-insert RLS, `ANALYTICS.md`); set `FPL_ANALYTICS = "1"`;
  for the Admin tab, add the **anon SELECT policy** + set **`FPL_ADMIN_KEY`**. Unset the flags → off / inert.
- **Deferred:** event **batching** (if volume grows); a full **BI dashboard**; **cohort/funnel** analysis.
