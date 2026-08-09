# Architectural Decision Record: A capped email-registration gate (soft control, not accounts)

**Decision ID:** ADR-098
**Date:** 2026-09-01
**Status:** Accepted
**Superseded By / Replaces:** **extends** the beta access gate (ADR-087) with a third access *mode* and
**softens** its "no accounts" stance (DIRECTION §1) — a **soft** self-registration cap, **not** hard per-user
auth/paid (native `st.login()` stays the deferred product path). Adds a **second** opt-in server-side write on
top of the cross-device squad store (ADR-094), reusing the same Supabase project.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner is about to recruit testers and wants to **control the numbers** before the ramp — the free
Streamlit-Cloud tier (~1 GB RAM) can struggle with many concurrent users. Today the only gate is a **single
shared code** (`FPL_ACCESS_CODE`, ADR-087): anyone who knows it is in — **no count, no "who", no cap**. The owner
wants: **self-registration**, a **variable cap** ("allow 10, then 20…"), and to **know who** (email) — but
explicitly **not** the "multi-user / registration / paid" pivot we deferred (DIRECTION §1).

**Verified at planning:**
- **This is soft control, a moderate step.** The need is *counting + knowing*, not securing — the app serves
  **public FPL analytics**, so an unverified, self-declared email is enough. Hard auth (passwords / OAuth /
  sessions) is the product pivot and more than the goal requires.
- **Email can't be verified for free** (Proton has no free SMTP; ADR-087/Sprint 123) — so registration is
  **self-declared** by design, not email-confirmed.
- **Supabase is already wired** (cross-device squads, ADR-094 — live). A second small table in the *same* project
  reuses the anon key + the best-effort client + `store_error`; no new store secret (its endpoint derives from
  `FPL_STORE_URL`).
- **The cap limits *registered* users** — a **proxy** for load, not a hard concurrency limit. The real ceiling is
  the free tier; a paid host is the escalation (ADR-095). A variable cap is the gradual lever the owner asked for.

#### Decision Drivers
- **Control the numbers** — a variable cap to protect the free tier while scaling testers gradually.
- **Know who** — capture a tester email at the door (honour a future "free for X" too, per ADR-087).
- **Soft, not hard** — no passwords/OAuth/paid; the smallest step that delivers the control.
- **Reuse, don't re-architect** — the existing Supabase + `cloud_store` patterns.
- **Opt-in / reversible** — unset the cap → today's behaviour exactly; the public deploy is unchanged by default.
- **Honest posture** — record the soft (unverified) nature, the privacy of holding emails, and the cap≠concurrency
  caveat.

---

### ✅ Decision

**Add a capped email-registration *access mode* to `require_access`: a shared invite code + a self-declared
email, admitted up to a variable `FPL_USER_CAP`, backed by a `beta_users` table in the existing Supabase.
Soft control, off by default.**

**1. The chosen shape — shared code + email + cap.** In registration mode a visitor enters the **shared invite
code** (`FPL_ACCESS_CODE` — gates *who can* register) **and their email** (identity). They're admitted when the
code matches **and** (they're already registered **or** the registered count is below `FPL_USER_CAP`). At the
cap → a **"beta full — join the waitlist"** message (linking `FPL_SIGNUP_URL`). The email is remembered in the
session like the code is today.

**2. A second small store — `beta_users`.** `web_streamlit/user_store.py` (mirrors `cloud_store`): a
`beta_users(email primary key, created_at)` table in the **same Supabase project** — the REST endpoint is derived
from `FPL_STORE_URL`'s base, reusing `FPL_STORE_KEY` (**no new store secret**). Primitives: `is_configured`,
`count`, `is_registered`, and `register(email, cap) → "in" | "full"`. Best-effort (timeout + retry); failures
surface via the shared `cloud_store.store_error`, so the gate shows the real cause (e.g. an RLS policy).

**3. Three access modes, by precedence.** **registration** (`FPL_USER_CAP` set **and** the store configured) →
**shared-code** (`FPL_ACCESS_CODE` set, no cap) → **open** (nothing set). So the app is **byte-identical to today
until the owner sets the cap** — an invariance test pins it.

**4. Soft by design — recorded honestly.** The email is **self-declared** (no verification, no password): a
determined person could type a fake or a stranger's address, or register several. Acceptable for a hobby beta
gating public data — the goal is a *headcount + a who*, not security. The **shared code** limits *who can*
register (only people the owner gave it to), which is the real anti-abuse lever; the cap bounds the total.

**5. Privacy posture.** We now hold **tester emails** (minimal PII, given with consent at the door). Documented:
what's stored (`email`, `created_at`), that the owner sees the roster in Supabase, and that **"remove me" = delete
the row** (which also frees a seat). No other personal data.

**6. Opt-in, reversible, secret-gated.** `FPL_USER_CAP` unset → registration mode is off (the code-only/open gate
of ADR-087). The registration **write** is the **second** deliberate server-side write from the web edge (after
the squad save, ADR-094) — both opt-in + secret-gated; the read-only invariant now names **two** exceptions, each
pinned by a test.

**7. What this is *not*.** Not accounts/auth/paid. Native **`st.login()`** (Google OIDC — real, verified per-user
identity) remains the **deferred** hard-auth upgrade if the beta becomes a product; this soft cap buys the
control now without that step.

---

### 🔀 Alternatives Considered

- **Keep the shared code only (status quo).** Rejected — gives no count, no "who", no cap: the exact gap.
- **Unique per-user invite codes** (a redemption system: generate N one-time codes, one per person). More
  control ("a code = a seat, un-shareable") but more machinery (generate + distribute + track). Deferred — the
  owner chose shared-code + email + cap as the lighter path; unique codes can layer on later if sharing bites.
- **Native `st.login()` / Supabase Auth (hard accounts).** The "real" version, now smaller than before — but
  it's the product pivot (OAuth setup, verified identity, holding auth'd users) and more than *counting +
  knowing* needs. Deferred as the upgrade path.
- **Email verification** (confirm the address). Rejected for now — needs sending mail, and Proton has no free
  SMTP; the soft self-declared email suffices for a hobby beta.
- **A separate `FPL_USER_STORE_URL` secret.** Rejected — deriving the `beta_users` endpoint from the existing
  `FPL_STORE_URL` avoids a second store secret (same project, same key).
- **Enforce concurrency, not registrations.** Rejected — a real concurrency limit is a host concern; the
  registered-user cap is a simple, sufficient proxy, and the escalation (a paid tier) is ADR-095.

---

### 🧭 Consequences

**Positive**
- The owner gets **exactly** the asked-for control — self-registration, a **variable** cap, and a who (emails) —
  with **no new infra** (reuses Supabase) and **no hard auth**.
- **Off by default + reversible** — the public deploy and CI are unchanged until `FPL_USER_CAP` is set; unset →
  back to today; an invariance test pins it.
- **Honest + auditable** — failures show the real store error; the soft/privacy/cap caveats are documented, not
  glossed.
- A clean **upgrade path** — `st.login()` slots in later for hard identity without re-architecting the gate.

**Negative / risks (mitigations)**
- **Soft (unverified) email** — a fake/stranger/multi-register is possible. *Mitigation:* the shared code gates
  who can register; the cap bounds the total; the owner can prune the Supabase table. Hard identity = the
  deferred `st.login()`.
- **Holding emails** (privacy). *Mitigation:* minimal PII, consented, a documented "remove me = delete the row".
- **Cap ≠ concurrency** — many registered users could still coincide. *Mitigation:* raise the cap gradually as
  perf holds; a paid host is the escalation (ADR-095).
- **A second server write** — more surface. *Mitigation:* opt-in + secret-gated + a guardrail test; best-effort +
  degrade (a store failure shows a clear message, doesn't corrupt the gate).

---

### 🧾 Status & follow-ups

- **Accepted.** Built this sprint: US-323 (`user_store`) + US-324 (the registration gate); docs updated
  (DIRECTION §1, BETA.md, PROJECT_STATUS, Architecture, README).
- **Owner actions:** create the `beta_users` table (+ anon RLS / disable RLS) in the same Supabase project; set
  `FPL_USER_CAP` (keep `FPL_ACCESS_CODE`) to switch the gate on; raise the cap + prune the table as needed.
- **Deferred:** an in-app roster/admin view; **unique per-user invite codes**; **email verification**; native
  **`st.login()`** (hard per-user identity — the product path); a true **concurrency** limit (paid host).
