# Lessons Learned

**Sprint:** Sprint 131 — A capped email-registration gate (soft control, not accounts)

**Dates:** 2026-09-01

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let the owner **control tester numbers** before recruiting (protect the free tier) and **know who they are** —
via a **capped email-registration gate** (shared code + email + a variable cap), backed by the existing Supabase.
Soft control, off by default, **not** the accounts/auth/paid pivot. Update all relevant docs.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Right-size the answer to the actual need** — *counting + knowing* wants a soft cap, not hard OAuth.
- **Reuse infra over re-architecting** — a second small table in the store we already had.

### New Skills Acquired

- **Soft control is a real, cheaper category between "shared code" and "accounts".** The need was a headcount + a
  who, not security. Naming it *soft* (self-declared email, no verification; the code is the anti-abuse lever)
  gave the smallest honest step — and kept `st.login()` as the deferred hard-auth upgrade rather than the answer.
- **A new server table can ride the existing config.** Deriving the `beta_users` endpoint from `FPL_STORE_URL`'s
  base (same project, same key) meant **no new secret** and one runbook — reuse beats another knob.
- **Guard a lazy import to break a cycle.** `user_store` imports `secret` from `access`; the gate imports
  `user_store` — importing at call time (inside the function) sidesteps the circular import cleanly.
- **A gate change is high-blast-radius — pin it off-by-default.** `require_access` runs on every page; shipping it
  a **no-op unless `FPL_USER_CAP` is set** (with the 839 byte-identical) put all the risk behind one secret.

---

# What Went Well ✅

- **Right-sized** — a soft email cap, not hard auth; the ADR says so and keeps the upgrade path open.
- **Reused Supabase** — a second table, no new secret, `store_error` reused.
- **Off by default + invariance-pinned** — a change to every page's gate, 839 byte-identical without the cap.
- **Docs matched the code** — DIRECTION §1 records the decision; BETA.md §4 is a full runbook.
- 829 → 839 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A second store table | needs an endpoint + key | Derive from `FPL_STORE_URL`'s base, reuse the key — no new secret |
| access ↔ user_store cycle | user_store imports `secret` from access | Lazy-import `user_store` inside the gate |
| Gate touches every page | high blast radius | Off by default (no cap → no-op), invariance-pinned |
| Cap vs concurrency | a cap limits registrations, not load | Documented as a proxy; a paid host = the escalation |
| A count-then-insert race | non-transactional upsert | Documented ±1 at the cap — accepted for a hobby beta |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Soft vs hard control | Counting + knowing ≠ securing; a soft cap is the cheaper category |
| Config reuse | Derive a second endpoint from an existing URL — no new secret |
| Lazy import | Import at call time to break a module cycle |
| Off-by-default gates | Ship a page-wide gate change as a no-op behind a secret; pin with invariance |

---

# Development Lessons 💻

- Match the mechanism to the goal — don't reach for OAuth when a soft, counted email gate is the ask.
- Reuse an existing store's config for a sibling table; one runbook, no extra knob.
- When a new module and an old one import each other, lazy-import inside the function that needs it.

---

# AI Collaboration Lessons 🤖

- The gate stays outside the grounded/read-only *analytics* core: it's an access-mode + a second opt-in,
  secret-gated write (registration). The read-only invariant now names two exceptions (squad save + registration),
  each pinned by a test — the posture is a decision, tracked, not eroded.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-098** — a capped email-registration gate (soft control, not accounts). `web_streamlit/user_store.py`
(a `beta_users` table in the existing Supabase, endpoint derived from `FPL_STORE_URL`, no new secret):
`register(email, cap) → in/full`. `access.require_access` gains a third mode (registration → shared-code →
open), gated by `FPL_USER_CAP`, off by default. Softens DIRECTION §1; native `st.login()` deferred. Docs:
DIRECTION §1, BETA.md §4, CLOUD_SQUADS, PROJECT_STATUS, Architecture, README._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (to enable):** create the `beta_users` table (+ RLS, BETA.md §4) and set `FPL_USER_CAP` (e.g. 10) —
  then testers register with the code + email, capped; raise it as perf holds; prune the table to free seats.
- **Deferred:** an in-app roster view; **unique per-user invite codes**; **email verification**; native
  **`st.login()`** (hard identity — the product path); a real concurrency limit (a paid-host concern).
- **GW1 (2026-08-21):** the big body — calibrate the set-piece / DefCon / form weights + backtest; momentum;
  live manager import.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep matching the mechanism to the real need; keep page-wide gate changes off-by-default + invariance-pinned.

---

# Key Commands Learned

```text
# enable the cap (Streamlit secrets): FPL_USER_CAP = "10"  (+ the beta_users table, BETA.md §4)
python -m pytest tests/test_user_store.py -q     # the register/count/cap logic
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Soft control | A headcount + a who (self-declared email + a cap), not hard auth/security |
| Registration mode | The gate variant (code + email + cap) when `FPL_USER_CAP` is set |
| Derived endpoint | A sibling table's REST URL computed from the existing store URL's base |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/user_store.py` | The capped beta-user register (reuses the squads store config) |
| `src/web_streamlit/access.py` (`require_access`) | The three-mode gate |
| `docs/06_Decisions/ADR-098-…` | The soft-control decision + the traps |
| `docs/BETA.md` §4 | The owner runbook (table SQL, cap, see/raise/remove testers) |

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

- ADR-098 A capped email-registration gate (soft control, not accounts)
- US-323 The `user_store` — a `beta_users` register/count/cap in the existing Supabase
- US-324 The registration gate — code + email + cap in `require_access` (off by default)

**Stories Carried Forward:**

- None. (Unique invite codes, email verification, `st.login()`, a roster view = deferred follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
