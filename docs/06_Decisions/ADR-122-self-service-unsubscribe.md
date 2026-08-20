# Architectural Decision Record: Self-service "Remove me" / unsubscribe

**Decision ID:** ADR-122
**Date:** 2026-08-20
**Status:** Accepted — owner-approved (in-app, full remove-me), **build now**.
**Superseded By / Replaces:** Makes **self-service** the *"remove me = we delete your rows"* promise already shown on
the auth login screen (ADR-106) and in the waitlist/privacy notes (ADR-102/098). Mirrors the waitlist store shape
(ADR-102) — a small best-effort, secret-gated store module.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The app **promises** an unsubscribe — the Google sign-in screen says *"Remove me = we delete your rows,"* and
BETA.md's privacy notes say the same — but today that is a **manual owner action** (delete a row in the Supabase
table editor). With more testers arriving at GW1 there needs to be a **self-service** way for someone to take
themselves out: remove their email from the beta and delete the data we hold for them.

The owner steer (2026-08-20): **do it like the waitlist process** — a small best-effort store module — and
**in-app only**. Confirmed there is **no email to the waitlist after sign-up**, so a tokenised email-unsubscribe
**link is not needed** (deferred until/unless bulk email is ever sent).

#### Decision Drivers
- **Deliver a promise already made** — "remove me = we delete your rows" should be one click, not a manual chore.
- **Mirror the waitlist** — a tiny `requests`-only module: best-effort, fail-silent, secret-gated, no new secret.
- **In-app is enough** — the people who need it are *in* the app (testers); the waitlist isn't emailed.
- **Honest + safe** — irreversible, so it's confirmed; it must never crash the app.

---

### ✅ Decision *(owner-approved, build now)*

A **self-service "Remove me"** that deletes a person's rows across the shared Supabase store and signs them out.

**Engine — `web_streamlit/unsubscribe.py`** (Streamlit-free, like `waitlist.py`): `remove_me(email, user_key=None)`
issues **best-effort `DELETE`s** and **never raises**:
- **`beta_waitlist`** + **`beta_users`** by `email=eq.<clean_email>` (their waitlist entry + their allow-list seat);
- **`squads`** by `handle=eq.<user_key>` + **`player_watchlist`** by `user_key=eq.<user_key>` — only when a
  `user_key` is given (a signed-in tester; the hashed key, ADR-106). Endpoints derive from `FPL_STORE_URL`'s base
  (no new secret); off until the store is configured.

**UI (in-app only):**
- A **"Leave the beta → Remove me"** control under the sidebar account line, in **both** gate modes
  (`auth.render_account` — Google; `access._render_account` — cookie), behind a **confirm dialog** (the proven
  `_CONFIRMING`/`@st.dialog` logout pattern) → `remove_me` → sign out (`st.logout()` in auth mode, the cookie
  `logout()` otherwise).
- A **"Remove me from the waitlist"** button on the auth **not-invited** screen (where the promise is shown) →
  `remove_me(email)` (no `user_key` — they have no saved data) → log out.

**Owner setup (BETA.md):** `beta_users` currently has **only** `select`+`insert` policies, so a client-key
`DELETE` is **blocked** — the owner adds a one-line **delete policy** (or disables RLS, consistent with the store).
`beta_waitlist` / `squads` / `player_watchlist` are already RLS-off, so those deletes work today.

**What this is *not*.** Not an email unsubscribe **link** (no bulk email → deferred; a tokenised `?unsubscribe=` page
is the future shape). Not an "email suppression, keep testing" flag — unsubscribe here means **leave + delete**.
Not a server-side identity check — soft control, consistent with ADR-094/098 (the harm of a mis-submitted email is
low: someone removes an address they typed).

---

### 🔀 Alternatives Considered

- **Waitlist-only unsubscribe.** Rejected — it wouldn't serve active testers (the in-app population) or fulfil the
  "delete your rows" promise; full remove-me is barely more code.
- **Tokenised email-unsubscribe link.** Deferred — needs a public URL + an HMAC token; only worth it once bulk
  invite/announcement email is actually sent (owner confirmed it isn't).
- **A `beta_unsubscribes` suppression list** (add-a-row, like the waitlist). Rejected for the primary case — the
  honest answer is to *delete* the data, not keep it plus a flag; a suppression list only matters for email sending.
- **Leave it manual (Supabase table editor).** Rejected — the app already promises self-service; it doesn't scale.

---

### 🧭 Consequences

**Positive** — delivers the promised one-click remove-me; frees a `beta_users` seat automatically; mirrors the
waitlist (small, best-effort, fail-silent, no new secret); confirmed + honest; in-app only keeps the build tight.
**Negative / risks (mitigations)** — the `beta_users` delete needs an **owner policy** or it silently no-ops
(*mitigation:* documented in BETA.md as required setup; the other three tables work today; the tester is still
signed out either way, and the owner can delete the seat by hand); a delete is **irreversible** (*mitigation:* a
confirm dialog; copy says so); no token means someone could remove an email they don't own (*mitigation:* low harm
for a hobby beta — they'd just re-join; a token is the deferred email-link's job, ADR-094/098 soft-control posture).

---

### 🧾 Status & follow-ups

- **Accepted — build now (US-428):** `unsubscribe.py` + the two in-app entry points + a confirm; BETA.md gets the
  `beta_users` delete-policy SQL + a "Remove me / unsubscribe" note; 3-part DoD (pytest for best-effort/fail-silent
  + the unconfigured no-op + the per-table targets · a manual smoke · docs).
- **Not this ADR / follow-ups:** a tokenised **email-unsubscribe page** if bulk email is ever sent; an owner Admin
  view of removals; `Prefer: return=representation` to confirm+report exactly which rows were deleted.
