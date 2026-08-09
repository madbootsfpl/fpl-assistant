# Architectural Decision Record: A persistent "remember me" cookie for the beta gate

**Decision ID:** ADR-099
**Date:** 2026-08-09
**Status:** Accepted
**Superseded By / Replaces:** **layers a client-side convenience on** the beta access gate (ADR-087) and its
capped-registration mode (ADR-098). It does **not** change the access modes or add a way in — it *remembers a pass
already made*. Native `st.login()` (hard, verified identity with built-in cookie persistence) stays the deferred
product path (ADR-098); this is the cheap step that removes the refresh annoyance without it.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Testers reported a real friction: **every full browser refresh re-prompts for the access code + email.** The gate
(`access.require_access`) remembers a pass only in `st.session_state[_beta_ok]` — which survives reruns and page
navigation **within a session** but is **wiped on a full refresh (F5) / a new tab / a browser restart**. So a
registered tester re-types their credentials constantly. The owner's ask: *"a way to do this once to register and
then you're done."* Chosen shape (from three options): **Option 1 — a browser "remember me" cookie**, confirmed to
work on phones/tablets (per-device).

**Verified at planning (code + the platform):**
- **The pass simply isn't persisted client-side.** Nothing about the *store* is at fault — `session_state` is
  session-scoped and a refresh starts a new session. A cookie is the missing durable marker.
- **Streamlit 1.61.1 can *read* cookies natively but not *write* them.** `st.context.cookies` (read-only, the
  request's cookies) is populated **immediately** on a cold load — so the **read** path needs *no* component and
  has **no "loading" rerun**, which means restoring a remembered session never flashes the gate. **Writing** is
  the hard half: there is **no native API to set a cookie**, and a DIY `document.cookie` injected via
  `st.components.v1.html` runs in a **sandboxed iframe** (wrong origin). So only the **write** needs a small
  **cookie component** — one dependency, and the read side stays native. (This is better than reading *through*
  the component, which would deliver the value only on a follow-up run and risk a gate flash — avoided entirely.)
- **Mobile caveats are real, not bugs.** **Per-device** (each phone/tablet/laptop registers once);
  **private/incognito won't persist**; **iOS Safari's ITP** caps client-JS (`document.cookie`) cookies at **~7
  days**, so iOS users re-register roughly weekly while Android/desktop get the full ~30.

#### Decision Drivers
- **Remove the friction** — pass once per device, then a refresh/restart keeps you in.
- **Grant nothing new** — remember only a pass the live gate *would already give*; re-validate on load.
- **Off by default / fail safe** — any failure degrades to today's per-session gate; never break the app.
- **Small + isolated** — one dependency, quarantined behind a seam so failure lives in one place.
- **Honest posture** — record the TTL, the iOS cap, the per-device reality, and the minimal-PII cookie.

---

### ✅ Decision

**Add a first-party "remember me" cookie that persists a *passed gate* across browser refreshes (~30 days; ~7 on
iOS), stored behind a guarded seam and re-validated on every load. It is a convenience over ADR-087/098, off by
default when unavailable, and grants no new access.**

**1. What's stored, and why it's safe.** On a successful gate pass we set a first-party cookie `fpl_beta` whose
value is **what proves the pass in the active mode**: in **registration** mode the tester's **own email**; in
**shared-code** mode the **code** they entered. On load we **re-validate** before trusting it — registration →
`user_store.is_registered(email)` (a **pruned tester's** stale cookie fails); shared-code → the value must equal
the **current** `FPL_ACCESS_CODE` (**rotating the code** invalidates every remember cookie). So the cookie grants
nothing the live gate wouldn't at that moment — it's a re-checked convenience, not a bypass.

**2. A quarantined seam — `web_streamlit/remember.py`.** A thin wrapper exposing `read() -> str | None`,
`write(value, days=30)`, `clear()`. **Read** is native (`st.context.cookies`, behind a `_request_cookies()` seam
for tests) — instant, no component. **Write/clear** lazily import the cookie component (**`streamlit-cookies-
controller` 0.0.4**, pinned, verified at build) inside `_controller()`. Every call is wrapped in `try/except`: an
unreadable cookie or a missing/erroring component ⇒ `read()` returns `None` and `write`/`clear` **no-op**. This is
what makes import, CI, AppTest, and private-mode paths safe and keeps the gate a no-op without a readable cookie;
the seam means swapping the component is local.

**3. Wiring the gate.** At the top of `require_access`: if already passed this session → `_flush_remember()`
(below) then return; else, for the active mode, `remember.read()` → if a value is present **and** it re-validates
(`user_store.is_registered(email)` / `== FPL_ACCESS_CODE`) → set `session[_beta_ok]` (+ `_beta_email` in
registration mode) and **skip the prompt**; otherwise show today's gate. **On a fresh pass** the value is stashed
in `session[_beta_remember]` and the gate reruns; the *next* (clean) run does `_flush_remember()` →
`remember.write(...)`. The write is **deferred** because a `st.rerun()` immediately after a component `set` would
discard it before it reached the browser — writing on the post-login run avoids that. (Native read means there is
**no loading run to flash** — the value is in the request from the first run.)

**4. TTL + the iOS cap — recorded honestly.** ~**30-day** expiry (a balance: long enough to stop re-typing, short
enough that an abandoned device forgets). **iOS Safari ITP** caps JS-set cookies at **~7 days** regardless — iOS
testers re-register ~weekly, by design of the platform, not a bug. Documented for the owner/testers.

**5. Privacy posture.** The cookie is **first-party, on the user's own device**, holding **their own** email (or
the shared code) — minimal, and it's data they just typed. No third-party/tracking cookie, no new server storage
(the email already lives in `beta_users`, ADR-098). To *not* be remembered: a private/incognito tab, or clear the
site's cookies — documented.

**6. Off by default / fail safe.** No component installed, cookies blocked, ITP-expired, or a read error → the
seam returns `None` and the gate is **exactly today's** (re-prompt). The existing **839** stay byte-identical —
an invariance test pins the no-cookie path. Worst case is the *current* annoyance, never a broken app.

**7. What this is *not*.** Not a new access mode and not identity. It doesn't authenticate — it remembers a pass
the gate already granted. Native **`st.login()`** (Google OIDC — verified identity with automatic secure-cookie
persistence) remains the **deferred** hard-auth upgrade; this buys "register once per device" without it.

---

### 🔀 Alternatives Considered

- **Do nothing (status quo).** Rejected — the re-prompt-on-refresh friction is the exact complaint, and it worsens
  as testers ramp.
- **A URL query-param token** (`?t=…` carries the pass; no dependency). Rejected — a **URL-as-credential** leaks
  via history/sharing/referer and weakens the very gate it rides on; it also litters the address bar.
- **DIY `document.cookie` via `components.html`** (no third-party dep). Rejected — the component **iframe is
  sandboxed**, so the write lands on the iframe's origin, not the app's; unreliable for a first-party cookie. The
  maintained components exist precisely to bridge this.
- **`st.context.cookies` alone** (native, no dep). Insufficient — it **reads** but cannot **write**; setting the
  cookie still needs a component. (We could read via it and write via the component, but one library for both is
  simpler and avoids a version-coupled split.)
- **Native `st.login()` now** (real persistence + verified identity). Deferred — it's the product/hard-auth pivot
  (OIDC setup, holding authenticated users) and more than "remember my pass" needs; kept as the upgrade path.
- **A signed/opaque server token** instead of the raw email/code. Rejected as over-engineering for a hobby beta —
  it needs server-side token↔identity mapping; re-validating the raw value against `beta_users` / the code already
  gives the property that matters (a pruned tester / rotated code is rejected).
- **A longer TTL (e.g. 90 days) or "forever".** Rejected — ~30 days balances convenience against an abandoned
  device staying logged in; iOS caps it at ~7 regardless.

---

### 🧭 Consequences

**Positive**
- **Removes the friction** the owner reported — register once per device, refresh/restart keeps you in.
- **Grants no new access** — re-validated on load; a pruned tester or rotated code invalidates the cookie.
- **Fail safe** — unavailable/blocked/expired → today's gate; the 839 stay byte-identical (an invariance test).
- **Isolated cost** — one dependency behind a guarded seam; failure and the eventual swap live in one file.
- **A clean next step** — `remember.clear()` ships the plumbing for a future "not you? / log out" link.

**Negative / risks (mitigations)**
- **One new dependency** (a cookie component). *Mitigation:* small/focused, quarantined behind `remember.py`,
  lazily imported + `try/except` so a missing/broken component degrades, not breaks; pinned + verified at build.
- **iOS ~7-day cap / per-device / private-mode** re-prompts. *Mitigation:* documented as platform reality; the
  fallback is simply today's behaviour.
- **A cookie value is client-readable** (the email or the shared code). *Mitigation:* first-party, on the user's
  own device, their own data; the code is a hobby-beta shared secret and rotating it invalidates cookies anyway.
  Hard identity = the deferred `st.login()`.
- **No loading-run flash.** *Resolved at build:* reading natively via `st.context.cookies` gives the value on the
  first run, so a remembered session restores with no flash (no reader component to wait on). The manual smoke
  still confirms no flash on a real refresh.
- **Testability** — the real cookie *write* needs a browser (AppTest can't run the component). *Mitigation:* read
  goes through `_request_cookies` (monkeypatched to a dict) and write/clear through `_controller` (a fake); the
  gate's restore/re-validate/deferred-write are AppTest-covered with `remember` monkeypatched; the real iframe
  write is a manual smoke.

---

### 🧾 Status & follow-ups

- **⚠️ Correction (Sprint 134) — the read path was wrong.** The "native read" above (`st.context.cookies`) reads
  the cookies the browser sends to the **Streamlit server on the top-level request**, but the component writes
  `document.cookie` **inside its own iframe** — **different cookie jars**, so the native read never saw the
  component's write and **nothing persisted** (owner verified on Safari *and* Chrome). **Fixed:** `remember.read()`
  now reads through the **same component** (`_controller().get()`, same jar as `write`). The cost is the loading
  delay this ADR originally tried to avoid: the component delivers its value on a **rerun**, so the gate waits one
  run via `access._maybe_wait_for_cookie()` (a "Checking your device…" placeholder, one-shot + component-gated so
  it never hangs). So the earlier "native read → no loading run to flash" claim is **superseded** — component-read
  + a one-run wait is the working design. (US-330.) If the re-smoke still fails, the escalation is native
  **`st.login()`** — Option 2 in `docs/05_Sprints/Sprint134.md`.
- **Accepted.** Built this sprint: US-325 (`remember.py` — the guarded cookie seam + the dependency) + US-326
  (wire restore-on-load / set-on-pass into `require_access`, degrading gracefully); docs updated (BETA.md,
  PROJECT_STATUS, Architecture, README).
- **Owner actions:** none to configure — "remember me" ships in `requirements.txt` and layers on whatever gate you
  already run. Smoke it: pass the gate → refresh → stay in; private tab / clear cookies → re-prompts; iOS ~weekly.
- **Follow-up built — the "Log out" link (Sprint 133, US-327/328).** A sidebar **"Log out"** (gated on
  `gate_active()`, off on the open deploy) that `remember.clear()`s the cookie + drops the session and re-shows the
  gate. Two traps handled the same way the write was: the clear is **deferred** to a clean run (a `st.rerun()`
  after `remember.clear()` would discard the remove component), and a **`_beta_forgotten`** session flag suppresses
  re-admit from the still-present native-read cookie until the clear reaches the browser on the next request. The
  control renders on the passed branch *and* the cookie-admit run. **No new ADR** — recorded here as an extension.
- **Deferred:** a **confirm** on Log out (only if a mis-click becomes an issue); a **signed token** instead of the
  raw value; native **`st.login()`** (hard, verified identity — the product path).
