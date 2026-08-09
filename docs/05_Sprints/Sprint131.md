# Sprint 131: A capped email-registration gate (soft control, not accounts)

**Dates:** 2026-09-01 (planned)
**Status:** 📝 Planned (0/2 stories · 1 ADR)
**Capacity:** ~¾ session (a new access mode + a second Supabase store — plus a thorough docs pass)
**Carried Over:** none

> **Direction (owner):** get **ahead of the ramp** — add **self-registration with a variable user cap** so we can
> control tester numbers (avoid free-tier performance issues) and know who they are (email). Chosen shape:
> **shared code + email + cap**. *Soft* control, **not** the accounts/auth/paid pivot. Update **all** relevant docs.

---

### 🔎 Verified at planning (on real data + the code)

- **This is soft control, a moderate step — not hard auth.** The email is **self-declared** (no password, no
  verification — Proton has no free SMTP anyway); the **cap** limits how many register; the **shared code**
  (`FPL_ACCESS_CODE`) gates *who can* register; the emails tell you *who*. It **softens** ADR-087/DIRECTION §1's
  "no accounts", but stays short of real per-user identity (native `st.login()` is the deferred hard-auth path).
- **Reuses the Supabase already set up.** `cloud_store` (squads) is live; a second tiny table
  **`beta_users(email primary key, created_at)`** in the *same* project (endpoint derived from `FPL_STORE_URL`'s
  base, same anon key) needs no new store secret. Best-effort + `store_error` are already there to reuse.
- **The gate extends `access.require_access`** (ADR-087): today it's a shared-code prompt; registration mode adds
  the email + the cap on top. **Off by default** — unset `FPL_USER_CAP` → today's behaviour exactly.
- **The cap limits *registered* users, a proxy for load** — not hard concurrency; the real ceiling is the
  free tier (~1 GB RAM), and a paid host is the escalation (ADR-095). The variable cap is the gradual lever
  ("10, then 20").

---

### 🎯 Sprint Goal

**Objective:** a visitor can **self-register** (invite code + email) up to a **variable cap**; the owner sees who
(a Supabase table) and raises the cap gradually. Off by default; a *soft* gate; all docs updated.

#### Success Criteria
- [ ] **ADR-098 (the gate)** — record the **capped email-registration** access mode: shared code + email + a
      `FPL_USER_CAP`; the **soft** (self-declared, no verification) nature + the **privacy posture** (we hold
      tester emails — minimal PII, consented, a "remove me" = delete the row); reuse of Supabase (a second
      opt-in, secret-gated server write, extending the ADR-094 read-only revision); the cap = registered-not-
      concurrent caveat; **opt-in / off by default**; `st.login()` recorded as the deferred hard-auth upgrade;
      that it **softens** ADR-087/DIRECTION §1 (a moderate, reversible step, not accounts/paid).
- [ ] **US-323 (the `user_store`)** — `web_streamlit/user_store.py`: a `beta_users` table (endpoint derived from
      `FPL_STORE_URL`, reusing `FPL_STORE_KEY`); `is_configured()`, `count()`, `is_registered(email)`, and
      `register(email, cap) -> "in" | "full"` (already-registered → in; `count < cap` → insert → in; else →
      full). Email normalised (lower/strip/`@` check). Best-effort; reuses `cloud_store.store_error`. Unit-tested
      (monkeypatched `requests`); secret-gated.
- [ ] **US-324 (the registration gate)** — extend `access.require_access`: when `FPL_USER_CAP` is set **and** the
      store is configured, show a **code (if `FPL_ACCESS_CODE` set) + email** form; validate the code, then
      `register` → **in** (session-remember the email) or, at the cap, a **"beta full — join the waitlist"** note
      (linking `FPL_SIGNUP_URL`). Unset cap → the existing code-only/open behaviour (byte-identical). Tests
      (AppTest / gate unit) for register-in, welcome-back, at-cap, wrong-code, and off-by-default.
- [ ] **No unintended drift** — the second server write (`register`) is **opt-in + secret-gated** (unset cap /
      store → no write, gate is today's); the read-only guardrail's named exceptions grow to two (squad save +
      registration), pinned by a test; existing **829** stay green; ruff clean.
- [ ] **Docs — thorough** (owner's ask): ADR-098 + the index; **DIRECTION.md §1** (record the decision — soft
      registration cap chosen, hard auth/paid still deferred); **BETA.md** (a "capped registration" section — the
      `beta_users` table SQL, `FPL_USER_CAP`, how to see/raise/remove testers); PROJECT_STATUS; Architecture;
      README; a note in CLOUD_SQUADS.md (same Supabase project).

---

### 🧭 Design sketch

**ADR-098.** Capped email-registration is an **access mode** (ADR-087 family), not a persistence or analytics
change beyond a second small opt-in write. Modes, by precedence: **registration** (`FPL_USER_CAP` set + store
configured) → **shared-code** (`FPL_ACCESS_CODE` set) → **open**. Soft by design; the honest limits (no
verification; cap ≠ concurrency; holds emails) are recorded, as is the reversibility (unset the cap).

**US-323.** `user_store.py` mirrors `cloud_store`: `_base = FPL_STORE_URL.rsplit("/", 1)[0]`, table URL
`f"{_base}/beta_users"`, `_headers` from `FPL_STORE_KEY`. `register(email, cap)`: `is_registered` → `"in"`; else
`count()` → `"in"` (POST insert) if `< cap`, else `"full"`. `count()` = `GET ?select=email` → `len`. Normalise
the email (lower, strip, must contain `@`); an invalid email → not registered. Failures → `store_error` for the
gate to surface.

**US-324.** In `require_access`: if registration mode, render the code (when set) + email inputs; on submit,
check the code, `status = user_store.register(email, cap)`; `"in"` → `session[_OK]=True`, `session[_EMAIL]=email`,
rerun; `"full"` → a full/waitlist message (+ the signup link) + `st.stop()`; a store error → `store_error` shown,
`st.stop()`. Session-remembered like today. The **owner sees registrants** in Supabase → **Table editor →
beta_users** (raise the cap in secrets; delete a row to free a seat) — documented, no in-app admin for the MVP.

**Deferred:** an in-app admin/roster view; unique per-user invite codes (a redemption system); email verification;
native `st.login()` (hard per-user identity — the product path); a true concurrency limit (a paid-host concern).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-098 | **Capped email-registration gate** — the soft-control access mode (the gate). | High | ✅ Done | gate |
| US-323 | **The `user_store`** — `beta_users` register/count/is_registered on Supabase. | High | ✅ Done | ~⅓ session |
| US-324 | **The registration gate** — code + email + cap in `require_access`. | High | ⬜ To do | ~½ session |

---

### 🧑‍💻 Owner runbook actions (you — ~10 min, £0)

1. **The users table:** in Supabase SQL Editor, `create table beta_users(email text primary key, created_at
   timestamptz default now())` + the anon RLS policies (or disable RLS) — the runbook lands in BETA.md.
2. **Turn it on:** set `FPL_USER_CAP = 10` (and keep `FPL_ACCESS_CODE`) in Streamlit secrets → the gate switches
   to registration. Raise the cap (20, 50…) as performance holds; view/remove testers in the Supabase table.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `user_store.register` returns "in" for a new email under the cap (inserts) / "in" for an
   already-registered one (no insert) / "full" at the cap; `count`/`is_registered` hit the right endpoint
   (monkeypatched `requests`); `is_configured` False without the store. The gate: registration mode shows the
   email field + admits under the cap, welcomes back a known email, blocks a wrong code, shows the full/waitlist
   note at the cap, and is **byte-identical when `FPL_USER_CAP` is unset**; the registration write is secret-gated
   (a guardrail test). Existing **829** stay green; ruff clean. No `.save(`.
2. **Manual smoke** — with test store secrets + `FPL_USER_CAP=1`: register email A → in; email B → "full/waitlist";
   A again → welcomes back; unset the cap → the plain code prompt.
3. **Docs updated** — ADR-098 + index; DIRECTION.md, BETA.md, CLOUD_SQUADS.md, PROJECT_STATUS, Architecture, README.

---

### 📝 Session Progress Log

- **ADR-098 (the gate)** — wrote `docs/06_Decisions/ADR-098-capped-email-registration-gate.md` (Accepted). Records
  the **capped email-registration** access mode: **shared code + email + `FPL_USER_CAP`**, admitted up to the cap
  (else a waitlist note); a second `beta_users` table in the **existing Supabase** (endpoint derived from
  `FPL_STORE_URL`, reusing the key — no new secret) via a `user_store`; three access modes by precedence
  (registration → shared-code → open, **byte-identical when the cap is unset**); the **soft** (self-declared, no
  verification) nature + the **anti-abuse** reality (the code gates who-can-register); the **privacy** posture
  (holds emails — minimal PII, consented, "remove me = delete the row"); the **second opt-in, secret-gated** server
  write (the read-only invariant now names two exceptions); cap = registered-not-concurrent; that it **softens**
  ADR-087/DIRECTION §1 without the accounts/paid pivot; `st.login()` = the deferred hard-auth upgrade. Added to the
  ADR index. No code (gate) — suite unchanged at **829**.
- **US-323 (the `user_store`)** — added `web_streamlit/user_store.py`: `_endpoint()` derives the `beta_users`
  REST endpoint from `FPL_STORE_URL`'s base (same Supabase project, reusing `FPL_STORE_KEY` — no new secret) +
  `is_configured()` · `count()` · `is_registered(email)` · `register(email, cap) → "in" | "full"` (already
  registered → in, no write; `count < cap` → insert → in; else full) · `clean_email` (lower/strip/`@`-shape check).
  Best-effort (`with_retry`); a bad email → `ValueError`, unconfigured → `RuntimeError`, store failure propagates
  (the gate surfaces it via `cloud_store.store_error`). A documented count-then-insert race (±1 at the cap —
  accepted). Probe: register A@b.com/c@d.com at cap 2 → in/in; a repeat → in (no dup); a 3rd → full. +7 tests
  (endpoint derivation · not-configured · email hygiene · the cap logic · idempotent · bad-email · is_registered).
  ruff clean. **836** total. (US-324 wires it into the access gate.)

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
