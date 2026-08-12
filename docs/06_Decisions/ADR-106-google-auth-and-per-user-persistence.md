# Architectural Decision Record: Google auth (st.login) + per-user squad persistence

**Decision ID:** ADR-106
**Date:** 2026-08-12
**Status:** Accepted
**Superseded By / Replaces:** the **hard-identity upgrade** deferred by ADR-087/098/099 — Google **`st.login()`**
(OIDC) becomes the primary gate **and** the anchor for **auto cross-device squad persistence**. Extends the cloud
squad store (ADR-094) — now keyed by the authenticated user; reuses **`beta_users`** (ADR-098) as the allow-list and
the **waitlist** (ADR-102) for non-admitted logins; the auth cookie subsumes the remember-me cookie (ADR-099) in
auth mode. **Off by default** — with no `[auth]` config, the existing shared-code/registration/open gate + manual
handle save/load are **byte-identical** (local, CI, and the open deploy unchanged).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester feedback (2026-08-12, the *Save/load/persistence* cluster): (**C2**) on iPhone, backgrounding Safari and
returning **reruns Streamlit and wipes the loaded team** (session_state is per-connection); (**C3**) no automatic
cross-device persistence; (**C4**) the shared **access code is clunky on mobile** — *"Google auth would be more
robust and ultimately user friendly."* Owner's steer: the UX must be **reliable, simple, and familiar** → go
**straight to Google auth**, with an **allow-list using `beta_users`**.

**Grounding (what we already have):** `session_state["squad"]` (lost on reset — the C2 cause); `cloud_store`
(handle-keyed Supabase save/load, ADR-094; Sprint 145 auto-syncs a *linked* squad's edits to the cloud);
`remember.py` (a generic first-party cookie); **`st.login` is available** (Streamlit 1.61 ✓ — the "deferred product
path" ADR-098/099 named). **Cost: none** — `st.login`, Google OAuth sign-in, and the Supabase free tier are all free.

**Why Google auth fixes the cluster:** a verified per-user identity + its **login cookie survive a reconnect** (the
identity half of C2), and it **auto-keys the store across devices** (C3) with a **familiar** sign-in (C4).

#### Decision Drivers
- **Reliable, simple, familiar UX** — a squad that just *follows you* across devices and reconnects (owner's priority).
- **Fix the worst symptom** — the mobile session-wipe that testers hit most.
- **Reuse, don't rebuild** — the allow-list is the existing `beta_users`; non-admitted → the existing waitlist.
- **Opt-in / off by default** — like every server-touching feature (ADR-053/054): no `[auth]` → today's behaviour.
- **Honest privacy** — hold the **email only**, key the squad by a hash of it; remove-me = delete the row.

---

### ✅ Decision

**Adopt Google `st.login()` (OIDC) as the primary gate when configured, allow-listed by `beta_users`, and use the
authenticated identity to auto-save/restore each user's squad in the cloud — fixing C2/C3/C4. Everything degrades to
today's behaviour when `[auth]` is unset.**

**1. Google auth as the gate (when configured).** With Streamlit `[auth]` secrets set (a Google OIDC client),
`access.require_access` gains a top branch: unauthenticated → a **"Sign in with Google"** screen (`st.login`);
authenticated → `st.user.email`. `st.logout()` signs out. The auth **cookie** persists the session across reruns and
reconnects (so a mobile return keeps the user logged in).

**2. Allow-list via `beta_users` (ADR-098).** A logged-in email **in `beta_users`** → admitted. **Not** in it → a
*"you're not on the list yet"* screen that adds them to the **waitlist** (ADR-102, `reason="not_listed"`) + the
`FPL_SIGNUP_URL`, and offers **Log out**. The owner curates `beta_users` (invite = add the row). The **shared code +
cap** (ADR-087/098) become the *no-auth fallback*.

**3. Per-user auto-persistence (C2/C3).** When logged in, the squad is **linked to a stable per-user key** — a
**hash of the email** (so the squads table doesn't duplicate raw emails) — and:
- **Auto-save:** every edit mirrors to `cloud_store` under that key (extends the Sprint-145 auto-sync — automatic, no
  manual handle).
- **Auto-restore:** on load, if logged in **and** there's no active squad in the session, fetch the user's squad from
  `cloud_store` → set it active. This is what defeats the **mobile wipe**: on reconnect the auth cookie is intact →
  the squad is re-fetched. Same login on another device → the same squad (**cross-device**).
- The manual **handle** save/load (ADR-094) stays for the no-login/open path.

**4. Off by default — degrade gracefully.** No `[auth]` configured → **no** Google branch; the app uses the existing
**shared-code / registration / open** gate + manual handle save/load, **byte-identical**. Local dev, CI, and the open
deploy are unchanged (the Google branch is skipped when `st.secrets` has no `[auth]`). The opt-in, off-by-default
invariant holds — a guardrail test pins it.

**5. Privacy posture (recorded honestly).** Google auth means holding **emails ↔ squads** (PII) — a step up from the
self-chosen handle. Minimal + honest: request **basic scopes only** (openid · email · profile name); store the
**email** (already collected via `beta_users`, ADR-098) + the squad **keyed by a hash of the email**; **no** other
profile data; a short **privacy line** ("we store your Google email to admit you + sync your squad; *remove-me* =
delete your rows"); **remove-me = delete** the `beta_users` + squad rows. Extends ADR-094/054.

**6. Relationship to the existing gates.** In auth mode the **auth cookie replaces the remember-me cookie** (ADR-099
is the no-auth fallback). The **waitlist** (ADR-102) catches non-allow-listed logins. The read-only invariant's
sanctioned server writes are unchanged in *kind* (squad-save · registration · analytics · waitlist) — the squad-save
is now *auto-keyed by identity* rather than a manual handle.

**7. What this is *not*.** Not **sensitive/restricted** OAuth scopes (so no paid Google security review — the consent
screen is published with basic scopes, free). Not required on the **open deploy** (opt-in). Not a paid service. Not
abandoning the **handle** model (it's the no-login fallback). Not storing the Google profile beyond email + name.

---

### 🔀 Alternatives Considered

- **Cookie-only auto-restore (no login).** Remember the handle in a cookie → auto-restore on reconnect. Fixes C2
  same-device cheaply, but leaves C3 as "type the handle once per device" and C4 (clunky code login) unaddressed.
  Considered as an interim Phase 1 — the owner chose to go straight to the target (Google auth) for a reliable,
  familiar UX. (The cookie approach remains a fallback if the OAuth setup ever isn't wanted.)
- **Open Google access (no allow-list).** Rejected — the owner wants a controlled beta; reusing `beta_users` as the
  allow-list is low-effort and keeps the invite/waitlist model.
- **Auth0 / Supabase Auth instead of direct Google OIDC.** Rejected for now — Google direct OIDC via `st.login` is
  the simplest "Sign in with Google", free, and needs no extra service. (`st.login` is provider-generic, so swapping
  later is cheap.)
- **Keep handle-only (status quo).** Rejected — it's exactly the mobile-wipe + clunky-login pain the tester flagged.

---

### 🧭 Consequences

**Positive**
- **The squad just follows you** — across devices and reconnects; the mobile-wipe (C2) is fixed, cross-device (C3) is
  automatic, and login is **familiar** (C4). The owner's UX priority, delivered.
- **Reuses the beta infra** — the allow-list is `beta_users`; non-admitted → the waitlist; no new tables.
- **Off by default** — local/CI/open deploy byte-identical; a guardrail test pins "no `[auth]` → today's behaviour".

**Negative / risks (mitigations)**
- **OAuth setup + the "unverified app" warning.** *Mitigation:* a one-time owner runbook — create the Google OIDC
  client, set the redirect URI (`https://madboots.streamlit.app/oauth2callback`), and **publish the consent screen**
  (basic scopes → no cap, no paid review, minimal warning).
- **PII commitment (emails ↔ squads).** *Mitigation:* email-only, squad keyed by a hash, a privacy line, remove-me =
  delete. Documented posture; no over-collection.
- **Recruitment friction** — a Google login wall loses some casual "just clicked the link" tries. *Mitigation:*
  accepted trade for reliability + a real founding-tester list; the open/shared-code path stays available if wanted.
- **Auth-off must never break** the app (local/CI/open). *Mitigation:* the Google branch is strictly gated on
  `[auth]` being configured; tests run auth-off; a guardrail pins byte-identical behaviour when unset.
- **Redirect-URI fragility** — a future subdomain change breaks the OAuth callback. *Mitigation:* the domain is now
  settled (`madboots.streamlit.app`); the runbook notes the coupling.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (a gated sprint): an **`auth.py`** helper (`is_auth_configured()`, `current_user()`,
  login/logout, the allow-list check vs `beta_users`, non-admitted → waitlist); wire it into `require_access` as the
  top branch (auth-configured only); **per-user auto-save/restore** in `squads.py` (link by the email-hash on login;
  restore on load when logged-in + no active squad; extend the Sprint-145 auto-sync); a **guardrail test** (no
  `[auth]` → byte-identical, no login) + tests with a mocked `st.user`; the **privacy line** on the gate. Docs:
  BETA.md (the Google OIDC + `[auth]` runbook + publish-the-consent-screen), PROJECT_STATUS, Architecture, memory.
- **Owner actions:** create the Google OAuth client (redirect URI + basic scopes, publish the consent screen), set
  the `[auth]` Streamlit secrets, and invite testers by adding their emails to `beta_users`.
- **Not this ADR / deferred:** a self-serve "request access" that auto-adds to `beta_users`; other IdPs; a paid host
  for true concurrency; the MADBOOTS vocabulary (branding-E) and the other 2026-08-12 P1/P2 items.
