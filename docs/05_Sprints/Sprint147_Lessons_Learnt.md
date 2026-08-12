# Lessons Learned

**Sprint:** Sprint 147 — Google auth + per-user squad persistence

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Fix the tester *save/persist* cluster — **C2** iPhone session-wipe · **C3** cross-device · **C4** clunky code login —
with Google **`st.login()`** as the gate *when configured*, allow-listed by `beta_users`, and the identity used to
**auto-save/restore** each user's squad. **Off by default** (ADR-106).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Add a risky/architectural feature gated + off by default.** The whole auth branch is behind
  `auth.is_configured()` (`[auth]` in secrets) — so local, CI, and the open deploy are byte-identical, and the 966
  existing tests stayed green throughout. The proven pattern for anything that touches identity/writes.
- **Reuse the machinery.** The allow-list is `user_store.is_registered` (beta_users); the waitlist is ADR-102; the
  auto-save is the Sprint-145 `_CLOUD_LINKED`/`_autosync`. The new code is just the auth wiring + a restore hook.

### New Skills Acquired

- **`st.user` is the source of truth; the session flag is a cache.** The auth *cookie* keeps `st.user` logged in
  across a mobile reconnect even when `session_state` is wiped — so re-checking `st.user` each run (and caching the
  admit in `_OK`) is what makes the mobile-wipe fix work: reconnect → still signed in → the squad restores.
- **Test the decision, not the redirect.** The Google OAuth flow can't be AppTested (a real redirect). Extracting
  `current_email()` and mocking it (plus `st.login`) let the *admit / waitlist / sign-in* logic be tested
  deterministically; the live sign-in is owner-smoke-verified — the same "can't AppTest the write" split as the
  cookie/analytics work.
- **Hash the identity for the storage key.** Keying the squad by `sha256(email)` (a valid `clean_handle`) gives a
  stable per-user handle without duplicating raw emails into the squads table — a small, honest privacy win.
- **Own the whole gate in one branch.** Auth mode handles login *and* the admitted account/logout UI (`st.logout`),
  so it doesn't fall through to the cookie gate's logout — cleaner than sprinkling `if auth` checks around.

---

# What Went Well ✅

- **Off-by-default held perfectly** — the 966 stayed green (auth inactive in the test env); the feature only lights
  up with the `[auth]` secrets.
- **Almost all reuse** — allow-list (beta_users), waitlist (ADR-102), auto-sync (S145); the net new is `auth.py` + a
  restore hook + a `require_access` branch.
- **The mobile-wipe fix is a natural consequence** — the auth cookie + restore-on-load means the squad just comes
  back on reconnect (C2), and follows the user across devices (C3), with a familiar login (C4).
- 966 → 972 tests (+6); ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Can't AppTest the OAuth redirect | `st.login` is a real Google redirect | Test `current_email`/decision mocked; owner-smoke the live sign-in |
| The account/logout UI differs in auth mode | auth uses `st.logout`, not the cookie clear | Auth mode owns its own `render_account` (top branch in `require_access`) |
| Don't leak the mobile-wipe fix into every page | restore must run on admit, once | Do the link + restore in `auth.gate()` on admit (session-cached `_OK`) |
| PII step-up (emails ↔ squads) | Google gives the email | Email-only + basic scopes; squad keyed by a hash; a privacy line on the gate |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Gated features | Behind `is_configured()` (a secrets check) → byte-identical when off; the suite is the guardrail |
| Auth identity | The auth cookie (`st.user`) survives a reconnect — that's the mobile-wipe fix, with restore-on-load |
| Testing auth | Mock the identity + `st.login`; test the decision; owner-smoke the redirect |
| Privacy | Hash the email for the storage key; hold email-only + basic scopes |

---

# Development Lessons 💻

- Put anything touching identity/writes behind a config check, off by default, and pin "off = unchanged" with a test.
- When you can't test the external hop (OAuth, a POST), test the *decision* around it and smoke the hop.
- Reuse the persistence primitives you already built (link/auto-sync) — the new work is the trigger, not the plumbing.

---

# AI Collaboration Lessons 🤖

- The read-only invariant's sanctioned server writes are unchanged in *kind* (squad-save · registration · analytics ·
  waitlist) — the squad-save is now *auto-keyed by identity*, not a manual handle. No engine/xP change. The feature
  is opt-in + off by default, honest about the PII it holds (email-only, hashed key, remove-me = delete).

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-106 — Google auth + per-user persistence.** `st.login` (OIDC) as the primary gate *when `[auth]` is set*,
allow-listed by `beta_users` (else the waitlist, `reason="not_listed"`); the squad auto-saves/restores per user keyed
by `sha256(email)`. Off by default. `auth.py` + a `require_access` top branch + `squads.link_and_restore`.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (to switch it on):** follow **BETA.md §5** — create the Google OAuth client (redirect URI + basic scopes +
  **publish the consent screen**) + the `[auth]` secrets; invite testers by adding emails to `beta_users`.
- **Owner (smoke, once live):** sign in on the phone → build/load a squad → background Safari + return → the squad's
  still there; open on another device (same Google account) → the same squad; a non-invited email → the waitlist.
- **Still on the 2026-08-12 intake (`docs/Backlog.md`):** MADBOOTS vocabulary in the cards (branding-E); per-GW xP
  display (A5); the player-actions consolidation (A6).
- **GW1 (2026-08-21, ~9 days):** the dormant-weight calibration remains the data-gated thread (ADR-101).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "gated + off by default + a guardrail test" discipline for every identity/write feature — it kept a big
  change zero-risk to the existing app.

---

# Key Commands Learned

```text
python -m pytest tests/test_auth.py -q     # the auth gate: off-by-default, admit, waitlist, sign-in, restore
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Auth mode | `[auth]` configured → Google sign-in gate + per-user persistence (else off) |
| `user_key` | `sha256(email)` — the per-user cloud handle (hides the raw email) |
| Restore-on-load | Re-fetch the user's squad when the session has none (the mobile-wipe fix) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-106-…` · `docs/BETA.md` §5 | The decision + the owner runbook (Google OIDC + `[auth]`) |
| `src/web_streamlit/auth.py` | The gate + the allow-list + the email-hash key |
| `src/web_streamlit/squads.py` (`link_and_restore`) | The per-user auto-save/restore |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-361 The Google auth gate (`auth.py` + the `require_access` branch + allow-list via `beta_users` + waitlist)
- US-362 Per-user auto-save/restore (link by the email-hash + restore on load — the mobile-wipe + cross-device fix)

**Stories Carried Forward:**

- None. (The rest of the 2026-08-12 intake — branding-E vocabulary, per-GW display, player-actions — remain.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
