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
- **Streamlit 1.61.1 can *read* cookies but not *write* them.** `st.context.cookies` exists (read-only, the
  request's cookies). There is **no native API to set a cookie**, and a DIY `document.cookie` injected via
  `st.components.v1.html` runs in a **sandboxed iframe** — it sets the *iframe's* cookie, not the app's first-party
  one. Reliable set/read therefore needs a small **cookie component** that bridges the iframe↔parent. → one
  dependency; that is the trade this ADR weighs.
- **The value arrives on a rerun, not the first run.** These components deliver the cookie to Python on a
  follow-up script run, so a cold refresh runs once with "nothing yet" before the value lands — we must avoid
  flashing the gate in that window.
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
`write(value, days=30)`, `clear()`. The cookie component is **lazily imported inside** these functions and every
call is wrapped in `try/except`: if the component is **missing or errors**, `read()` returns `None` and
`write`/`clear` **no-op**. This is what makes import, CI, AppTest, and private-mode paths safe, and keeps the gate
a no-op without a readable cookie. The concrete component (candidate **`streamlit-cookies-controller`** — small,
focused, maintained) and its 1.61.1 compatibility are **verified at build**; the seam means swapping it is local.

**3. Wiring the gate.** At the top of `require_access`: if already passed this session → return; else
`remember.read()` → if a value is present **and** `_valid_for_mode(value)` (the pure, unit-tested decision) → set
`session[_beta_ok]` (+ `_beta_email` in registration mode) and **skip the prompt**; otherwise show today's gate
and, **on success, additionally `remember.write(<email|code>)`**. The **first-load loading run** (value not yet
delivered) is treated as *don't show the gate yet* to avoid a flash of the code prompt.

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
- **The first-load rerun could flash the gate.** *Mitigation:* render the reader early and treat "still loading"
  as *don't prompt yet*; covered by the manual smoke (no-flash check).
- **Testability** — the real cookie roundtrip needs a browser (AppTest can't). *Mitigation:* the decision
  (`_valid_for_mode`) is pure + unit-tested and the seam is monkeypatched in tests; the iframe roundtrip is a
  manual smoke.

---

### 🧾 Status & follow-ups

- **Accepted.** Built this sprint: US-325 (`remember.py` — the guarded cookie seam + the dependency) + US-326
  (wire restore-on-load / set-on-pass into `require_access`, degrading gracefully); docs updated (BETA.md,
  PROJECT_STATUS, Architecture, README).
- **Owner actions:** none to configure — "remember me" ships in `requirements.txt` and layers on whatever gate you
  already run. Smoke it: pass the gate → refresh → stay in; private tab / clear cookies → re-prompts; iOS ~weekly.
- **Deferred:** a **"not you? / log out"** link (uses `remember.clear()` — plumbing lands now, UI later); a
  **signed token** instead of the raw value; native **`st.login()`** (hard, verified identity — the product path).
