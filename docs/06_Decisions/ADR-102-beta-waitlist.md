# Architectural Decision Record: A beta waitlist — capturing failed-registration emails

**Decision ID:** ADR-102
**Date:** 2026-08-10
**Status:** Accepted
**Superseded By / Replaces:** **extends** the capped email-registration gate (ADR-098) — when a registration
*fails* (the cap is full **or** the invite code is wrong), capture the email into a waitlist so the owner can invite
later. Adds the **4th** opt-in, secret-gated server write (after the squad save ADR-094, the registration insert
ADR-098, and the analytics events ADR-100). No change to the analytics/decision core.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The registration gate (ADR-098) admits testers up to a variable `FPL_USER_CAP`. Two registration *failures* today
just turn people away and **lose their interest**:
- **At the cap** — a "beta full — join the waitlist" note links `FPL_SIGNUP_URL`, but the email they typed is
  discarded.
- **A wrong invite code** — an error, and the email is discarded.

The owner wants to **capture these emails** so they can be invited when spots open — *"inc #6 and use only waitlist
#5"*: **one** waitlist recording **both** the cap-full and the wrong-code cases (not two mechanisms).

**Verified at planning:**
- **A sibling of the registration capture.** `access._registration_gate` already has the two branches (`"full"`;
  a wrong code). A `beta_waitlist(email, reason, created_at)` table in the **existing Supabase** — endpoint derived
  from `FPL_STORE_URL`'s base, reusing `FPL_STORE_KEY` (**no new secret**, exactly like `beta_users`) — with a
  best-effort `waitlist.add(email, reason)` slots straight in.
- **A new privacy surface.** Unlike `beta_users` (people who *got in*), the waitlist holds emails of the
  **non-admitted** — including **wrong-code** attempts, which may be **typos or randoms**. The owner accepts this
  (they asked for it); the decision + posture are recorded honestly here.
- **Must never block the gate.** Like the analytics write (ADR-100), it's best-effort and wrapped — a store hiccup
  can't stop a legitimate registration or crash the page.

#### Decision Drivers
- **Don't lose interested testers** — capture the email at the moment of a failed attempt, for a later invite.
- **One mechanism** — a single waitlist for both failure reasons (owner's steer), reusing the store.
- **Opt-in / off by default** — only in registration mode with the store configured; the public deploy writes nothing.
- **Never degrade the gate** — best-effort + fail-silent; a store problem is invisible to the user.
- **Honest privacy** — record that it holds non-admitted emails (incl. wrong-code), minimal, owner-only, deletable.

---

### ✅ Decision

**Add a `beta_waitlist` table that records a would-be tester's email on any *failed* registration — the cap being
full (`reason="full"`) or a wrong invite code (`reason="bad_code"`) — best-effort, opt-in, and off by default.**

**1. One waitlist, two reasons.** `web_streamlit/waitlist.py` (mirrors `user_store`): a `beta_waitlist(email
primary key, reason text, created_at timestamptz)` table in the **same Supabase project** (endpoint derived from
`FPL_STORE_URL`, reusing `FPL_STORE_KEY` — **no new secret**). `add(email, reason)` upserts (idempotent on `email`),
normalising the email (`clean_email`); `reason ∈ {"full", "bad_code"}`.

**2. Wired into the two failure branches.** In `access._registration_gate`: on **`status == "full"`** →
`waitlist.add(email, "full")` (alongside the existing waitlist note + `FPL_SIGNUP_URL`); on a **wrong invite code
with an email provided** → `waitlist.add(email, "bad_code")` (alongside the "code isn't right" error). No change to
who is *admitted* — this only records the miss.

**3. Best-effort, never blocks.** Every `add` is wrapped so a store failure is swallowed (like the analytics
write) — a legitimate registration and the page render are never affected. Idempotent, so a retry doesn't duplicate
a row.

**4. Off by default, secret-gated.** It writes only in **registration mode** (`FPL_USER_CAP` set + the store
configured) — the same condition as the registration insert. Unset the store / the cap → no waitlist write; the
public deploy and CI are unchanged. This is the **4th** deliberate server write; the read-only invariant now names
**four** exceptions (squad save, registration, analytics, waitlist), each opt-in + secret-gated.

**5. Privacy posture — recorded honestly.** The waitlist holds emails of the **non-admitted**, including
**wrong-code** attempts that may be typos or strangers. Minimal PII (`email`, `reason`, `created_at`), owner-only
(the app never reads it back; the owner sees it in Supabase to invite), and **"remove me" = delete the row**. The
wrong-code capture is the sharper point — the owner opted in knowingly; it's documented, not implied. No
verification, no other data.

**6. What this is *not*.** Not accounts/auth. Not automated invites (the owner invites manually from the table).
Native `st.login()` (verified identity) remains the deferred hard-auth path (ADR-098).

---

### 🔀 Alternatives Considered

- **Status quo — a signup link only.** Rejected — it discards the email the person just typed, losing an interested
  tester at the cap and every mistyped-code attempt.
- **Capture only the cap-full case (#5), not wrong-code (#6).** Considered (it avoids holding mistyped-code emails)
  and was the safer-privacy default — but the owner explicitly asked to include both; recorded here with the
  privacy caveat rather than silently narrowing it.
- **Two separate mechanisms/tables** (a waitlist + a separate "denied" log). Rejected — the owner wanted **one**
  waitlist; a single table with a `reason` column is simpler and one runbook.
- **A separate `FPL_WAITLIST_*` secret / project.** Rejected — derive the endpoint from `FPL_STORE_URL` (same
  project, same key), like `beta_users` — no new secret.
- **Email verification / double opt-in.** Rejected for a hobby beta (no free SMTP; ADR-087) — the waitlist is a
  self-declared capture the owner acts on manually.

---

### 🧭 Consequences

**Positive**
- The owner **keeps interested testers** — every failed attempt's email is captured for a later invite, in one
  place, with **no new infra** (reuses Supabase, no new secret).
- **Off by default + best-effort** — the public deploy writes nothing; a store problem never blocks a registration
  or crashes the page; a guardrail test pins the secret-gating.
- **Honest + minimal** — the privacy posture (holds non-admitted emails, incl. wrong-code) is documented, not
  glossed; "remove me = delete the row".

**Negative / risks (mitigations)**
- **Holds emails of the non-admitted, incl. wrong-code** (possible typos/randoms) — a real privacy surface.
  *Mitigation:* minimal PII, owner-only, deletable; the owner opted in knowingly; documented. Prune the table.
- **A 4th server write** — more surface. *Mitigation:* opt-in + secret-gated + best-effort + a guardrail test;
  idempotent (email PK); reuses the store client.
- **A wrong-code capture on every mistyped submit** — could accumulate retries. *Mitigation:* upsert on `email`
  (idempotent), so retries don't duplicate; only when an email was actually entered.

---

### 🧾 Status & follow-ups

- **Accepted.** Built this sprint: US-347 (`waitlist.py` + wiring into `_registration_gate`); docs updated (BETA.md
  §4 — the `beta_waitlist` table SQL + how to see/invite waitlisters, PROJECT_STATUS, Architecture).
- **Owner actions:** create the `beta_waitlist` table (+ anon RLS / disable RLS) in the same Supabase project (the
  runbook lands in BETA.md); it's automatic once the table exists + `FPL_USER_CAP` is set. Invite from the table;
  delete a row when done.
- **Deferred:** unique per-user invite codes; email verification; an in-app waitlist/roster admin view; automated
  invites.
