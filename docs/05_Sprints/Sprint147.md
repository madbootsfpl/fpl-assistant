# Sprint 147: Google auth + per-user squad persistence (ADR-106)

**Dates:** 2026-08-12
**Status:** ✅ Complete — US-361 + US-362 (ADR-106). 966 → 972 tests
**Capacity:** ~1 session (an auth gate + the per-user persistence, then docs)
**Carried Over:** none

> **Direction (ADR-106):** the tester *save/persist* cluster — **C2** iPhone session-wipe · **C3** cross-device ·
> **C4** clunky code login. Fix all three with Google **`st.login()`** (OIDC) as the gate **when configured**,
> **allow-listed by `beta_users`**, and use the identity to **auto-save/restore** each user's squad. **Off by
> default** — no `[auth]` → today's gate + manual handle save/load, byte-identical.

---

### 🔎 Verified at planning (on the code)

- **`require_access()`** precedence is registration → shared-code → open; the **auth branch slots in as the new top**
  (after the `_OK` early-return, gated on `auth.is_configured()`), so with no `[auth]` it's skipped entirely.
- **The allow-list already exists:** `user_store.is_registered(email)` checks **`beta_users`**; `waitlist.add(email,
  reason)` (ADR-102) takes a free reason → **`"not_listed"`** for a logged-in email that isn't invited.
- **Per-user persistence reuses Sprint 145:** `set_active_squad` already **auto-syncs** when `_CLOUD_LINKED` is set →
  on login, set `_CLOUD_LINKED = <email-hash>` and every edit mirrors to `cloud_store` automatically; add a
  **restore-on-load**. A **sha256-hex** of the email passes `cloud_store.clean_handle` (letters+digits).
- **`st.login` is available** (Streamlit 1.61 ✓). It needs `[auth]` secrets — absent locally/CI, so the branch is
  off there (the byte-identical invariant).

---

### 🎯 Sprint Goal

When `[auth]` is configured: Google sign-in → admit iff the email is in `beta_users` (else waitlist) → the squad
auto-saves per user and auto-restores on load/reconnect (fixing C2/C3/C4). When it isn't: nothing changes.

#### Success criteria
- [ ] **US-361 (the Google auth gate)** — a new **`web_streamlit/auth.py`** (`is_configured()` = `[auth]` in
      `st.secrets`; `current_email()` = `st.user.email` when logged in; `login`/`logout`; the allow-list decision via
      `user_store.is_registered`). Wire a **top branch** into `require_access`: unauthenticated → a **"Sign in with
      Google"** screen (badge + tagline + `st.login`); authenticated **in `beta_users`** → admit (set `_OK`/`_EMAIL`);
      **not** in it → a *"not on the list yet"* screen (`waitlist.add(email, "not_listed")` + `FPL_SIGNUP_URL` + **Log
      out**). A **privacy line** on the gate. **Off by default** — no `[auth]` → `require_access` unchanged (a
      guardrail test); tests with a mocked `st.user`.
- [ ] **US-362 (per-user auto-save/restore)** — on admit, **link** the squad to `user_key = sha256(email)` (so the
      S145 auto-sync mirrors edits) and **auto-restore**: if logged-in **and** no active squad → `cloud_store.
      load_squad(user_key)` → set it active (defeats the mobile wipe). The manual handle path (ADR-094) stays for the
      no-auth deploy. Tests (mocked user + monkeypatched `cloud_store`): a linked edit auto-syncs to the user-key; a
      reconnect with no session squad restores it.
- [ ] **No drift** — the whole feature is **opt-in / off by default**; existing **966** stay green (auth-off); ruff clean.
- [ ] **Docs** — BETA.md (the Google OIDC + `[auth]` runbook + *publish the consent screen*); the privacy line;
      PROJECT_STATUS; Architecture; memory.

---

### 🧭 Design sketch

**`web_streamlit/auth.py`** (pure-ish; Streamlit only for `st.user`/`st.login`):
```
def is_configured() -> bool:        # [auth] present → Google-auth mode is on
def current_email() -> str | None:  # st.user.email if st.user.is_logged_in else None
def user_key(email) -> str:         # sha256(clean_email)[:32] — a stable cloud handle, no raw email in the squads table
def gate() -> None:                 # the login → allow-list → admit/waitlist flow (stops the page unless admitted)
```
**`require_access` (top branch):**
```
if auth.is_configured():
    auth.gate()      # sets _OK/_EMAIL + links the per-user squad on admit; else st.stop() on the login/waitlist screen
    return
# … existing registration / shared-code / open, unchanged …
```
**`auth.gate()`** — not logged in → the badge/tagline + `st.login("google")` + the privacy line, `st.stop()`. Logged
in → `email = current_email()`; if `user_store.is_registered(email)` → `_OK=True`, `_EMAIL=email`, **link + restore**
the per-user squad, return; else → `waitlist.add(email, "not_listed")` + the "not on the list" screen + a **Log out**
button, `st.stop()`.

**Persistence** (`squads.py`, reusing `_CLOUD_LINKED`/`_autosync` from S145): on admit set `_CLOUD_LINKED =
auth.user_key(email)`; if `active_squad() is None`, `set_active_squad(cloud_store.load_squad(user_key))` when present.
Edits then auto-sync under the user-key; a reconnect (auth cookie intact) re-restores.

**Deferred:** a self-serve "request access" that auto-adds to `beta_users`; other IdPs; a paid host for concurrency.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-361 | **The Google auth gate** — `auth.py` + the `require_access` branch + allow-list (`beta_users`) + waitlist. | High | ✅ Done | ~½ session |
| US-362 | **Per-user auto-save/restore** — link by email-hash + restore on load. | High | ✅ Done | ~⅓ session |

---

### ✅ Definition of Done

1. **Tests** — auth-off: `require_access` is byte-identical (a guardrail; the 966 stay green). Auth-on (mocked
   `st.user` + `[auth]`): a listed email is admitted; a non-listed one is waitlisted (`"not_listed"`) + not admitted;
   the per-user squad auto-syncs by the email-hash; a no-session reconnect restores it. ruff clean.
2. **Manual smoke** (owner, after setting the secrets) — sign in with Google; a listed email gets in + the squad
   follows across devices/a reload; a non-listed email is waitlisted; Log out works.
3. **Docs** — BETA.md (Google OIDC client + redirect URI + publish the consent screen + `[auth]` secrets); the
   privacy line; PROJECT_STATUS; Architecture; memory.

---

### 📝 Session Progress Log

- **US-361 (the Google auth gate)** — new **`web_streamlit/auth.py`**: `is_configured()` (`[auth]` in `st.secrets`,
  read defensively), `current_email()` (`st.user.email` when logged in, guarded), `user_key()` (a truncated
  **sha256** of the cleaned email — a valid `clean_handle`, no raw email in the squads table), `render_account()`
  (sidebar "Signed in · Log out (Google)"), and **`gate()`** — not signed in → the badge + tagline + `st.login
  ("google")` + the **privacy line**; signed in **& in `beta_users`** → set `_OK`/`_EMAIL`, return; signed in but
  **not invited** → `waitlist.add(email, "not_listed")` + a "not on the list yet" screen + **Log out**. Wired into
  **`require_access` as the top branch, gated on `auth.is_configured()`** — so with no `[auth]` it's skipped and the
  existing cookie path runs **byte-identical**. **+5 tests** (`test_auth.py`: off-by-default · the email-hash key
  hides the email + is a valid handle · admits an allow-listed email · waitlists a non-listed one (`"not_listed"`) ·
  shows the Sign-in screen) — the OAuth redirect itself is owner-smoke-verified (can't be AppTested; `st.login`/
  `current_email` mocked). ruff clean. **966 → 971.** (US-362 next: link + restore the per-user squad on admit.)
- **US-362 (per-user auto-save/restore)** — a `squads.link_and_restore(handle)` (reuses the S145 `_CLOUD_LINKED` /
  `_autosync`): sets the link so every edit **auto-syncs** to the cloud under the handle, and — when the session has
  **no** active squad (a mobile reconnect wiped it) — **re-fetches** the user's squad so it **follows them across
  devices/reconnects**; best-effort, and it never clobbers a squad already active this session (a fresh build stays).
  `auth.gate()` calls it on admit with `user_key(email)` (the sha256 key). This is the **C2 mobile-wipe fix** (the
  auth cookie keeps the user signed in → the squad restores) + **C3 cross-device**. **+1 test** (on admit: the squad
  is restored from the cloud by the email-hash key + linked for auto-sync). ruff clean. **971 → 972.** Sprint 147
  build complete — the BETA.md `[auth]` runbook lands at retro.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Complete — the tester *save/persist* cluster (C2 mobile session-wipe · C3 cross-device · C4 clunky
code login) is fixed with **Google `st.login`** as the gate *when `[auth]` is configured*, allow-listed by
`beta_users`, plus per-user auto-save/restore of the squad. **Off by default** — no `[auth]` → the existing gate,
byte-identical (the 966 stayed green throughout).

**Shipped**
- **US-361** — `auth.py` (`is_configured`/`current_email`/`user_key`/`render_account`/`gate`) + a `require_access`
  top branch: Sign in with Google → admit iff the email is in `beta_users`, else the waitlist (`"not_listed"`) +
  Log out; a privacy line on the gate. +5 tests (decision logic mocked; the OAuth redirect is owner-smoke-verified).
- **US-362** — `squads.link_and_restore` (reuses the S145 auto-sync): on admit, link the squad to `sha256(email)`
  (edits auto-sync) + restore it from the cloud when the session has none — so it follows the user across devices /
  a mobile reconnect. +1 test.

**Tests:** 966 → **972** (+6). ruff clean; CI-parity green.

**What went well:** off-by-default held perfectly (zero risk to the live app); almost all reuse (allow-list,
waitlist, auto-sync); the mobile-wipe fix falls out of the auth cookie + restore-on-load.

**Owner to switch it on (BETA.md §5):** create the Google OAuth client (redirect URI + basic scopes + publish the
consent screen) + the `[auth]` secrets; invite testers by adding emails to `beta_users`. Then smoke: sign in →
squad survives a mobile refresh + follows across devices; a non-invited email → the waitlist.

**Lessons:** `docs/05_Sprints/Sprint147_Lessons_Learnt.md`.

---

### 📌 For Tony — confirm before I start US-361

1. **Auth mode assumes the store is configured** (`beta_users` + the squads table live in your Supabase) — it's the
   allow-list + the persistence backend. If `[auth]` is set but the store isn't, I'll treat it as a config error
   (can't verify the allow-list). OK? *(My rec: yes — the store is a prerequisite for auth mode.)*
2. **The per-user key is a `sha256` hash of the email** (so the squads table isn't a second copy of raw emails;
   `beta_users` already holds the email for the allow-list). OK? *(My rec: yes.)*
3. **The OAuth login flow can't be AppTested** (it's a real Google redirect) — I test the **decision logic** (mocked
   `st.user`) + the **byte-identical-when-off** guardrail; the live sign-in is **owner-smoke-verified** on the deploy
   after you set the secrets (like the cookie/analytics writes). OK?
4. **A new waitlist reason `"not_listed"`** for a logged-in-but-not-invited email (alongside `full`/`bad_code`). OK?
