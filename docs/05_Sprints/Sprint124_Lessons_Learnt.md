# Lessons Learned

**Sprint:** Sprint 124 — Cross-device squads (build the handle-keyed cloud store)

**Dates:** 2026-08-25

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Build the deferred cross-device squads (ADR-094): save a squad under a handle on one device, load it on another,
via a free Supabase store — no login, ~£0. The app's **first server-side write**, so evolve the read-only
guardrail deliberately and keep the feature off by default.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Evolve an invariant with a test, not by luck** — pin the real "off by default" property, don't rely on a name.
- **Thin swappable adapter** — a small interface that a future auth model can slot into unchanged.

### New Skills Acquired

- **A guardrail should test the property, not the spelling.** `save_squad` happens to dodge the old `.save(`
  scan (`.save_squad(` ≠ `.save(`) — so the scan "passed" for the wrong reason. The honest fix was a *new* test
  that pins what actually matters: without the secrets, `is_configured()` is False, reads return None, and
  `save_squad` refuses **before any HTTP** (a `requests.post` rigged to raise is never reached).
- **Secret-gating makes a big change ship safely.** The whole first-server-write feature is invisible + inert
  without `FPL_STORE_URL`/`FPL_STORE_KEY`, so CI, forks and the live public deploy are unaffected — the risky
  architectural change lands with zero blast radius until the owner opts in.
- **Test a network adapter by monkeypatching `requests`.** Env vars configure it (via `secret()`'s env
  fallback), a fake `requests.{post,get,delete}` captures the call — the whole save/load/delete contract is
  covered with no live network.
- **Sanitise anything that reaches a query filter.** `clean_handle` (lower-case, `[a-z0-9_-]`, bounded) guards
  the Supabase `handle=eq.<…>` filter and keeps keys predictable across devices.

---

# What Went Well ✅

- **The guardrail evolved honestly** — a dedicated secret-gated test, not an accidental pass.
- **Off by default = safe by default** — zero risk to current users; the feature is hidden until secrets are set.
- **Additive, with a fallback** — the ADR-054 download/upload path still works; the cloud store is convenience.
- **A swappable adapter** — fits a future `st.login()` id without a rewrite.
- 781 → 791 tests; ruff + CI-parity green; no live network in tests.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The `.save(` scan passed for the wrong reason | `save_squad` ≠ `.save(` literal | Add a test that pins the *property*: secret-gated, no HTTP without secrets |
| First server write breaks "read-only" | a real architecture change | Revise the invariant (ADR-094): one opt-in, tested, secret-gated write |
| A handle in a query filter | injection / odd keys | `clean_handle` sanitises + bounds it |
| Test without a real Supabase | network in tests is banned | Env-config + monkeypatched `requests` |
| Ship a big change safely | live testers on the deploy | Secret-gate it → invisible + inert until opted in |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Property-based guardrail | Test what must be true, not a string's presence |
| Secret-gated features | Off-by-default lets a risky change ship with no blast radius |
| Network adapter tests | Env config + monkeypatched `requests` = full contract, no network |
| Input hygiene | Sanitise anything reaching a query filter |
| Swappable interface | A handle now, an authed id later — same adapter |

---

# Development Lessons 💻

- When a new feature relaxes an invariant, add a test for the *new* invariant; don't lean on an old test passing.
- Gate anything that touches the network / writes behind a secret so it's inert by default.
- Keep the old path working — make the new capability additive with a graceful fallback.

---

# AI Collaboration Lessons 🤖

- The read-only/grounded posture is a *decision*: relaxing it for persistence is an ADR + a revised, tested
  guardrail — one named, opt-in write path — not an incidental code change. The rest of the app stays read-only.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — this **implements ADR-094**. `web_streamlit/cloud_store.py` (Supabase REST, handle-keyed,
secret-gated by `FPL_STORE_URL`/`FPL_STORE_KEY`); the read-only invariant revised (the `.save(` scan kept + a
new secret-gated test); a My-Squad "☁ Save/Load across devices" UI; `docs/CLOUD_SQUADS.md` owner setup. Native
`st.login()` stays the deferred product-identity upgrade._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (to go live):** create the Supabase project + `squads` table + anon policy + the two secrets
  (`docs/CLOUD_SQUADS.md`), then Save on one device / Load on another — ideally before recruiting testers.
- **Deferred levers:** native `st.login()` (per-user identity); a "handle taken?" check; encryption /
  rate-limiting; a "list my saved handles" view.
- Post-**GW1 (2026-08-21)**: the Data Hardening flip (per-GW history + form) is still the big data milestone.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep gating risky/architectural changes behind a secret so they ship inert; test the invariant, not the spelling.

---

# Key Commands Learned

```text
# docs/CLOUD_SQUADS.md — Supabase table + anon RLS, then set FPL_STORE_URL / FPL_STORE_KEY
python -m src.web_streamlit   # My Squad → ☁ Save / Load across devices (once the secrets are set)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Handle-keyed store | Cross-device persistence keyed by a user-chosen handle, not a login |
| Secret-gated feature | Off (hidden + inert) until its secrets are set |
| Property-based guardrail | A test that pins what must be true, not a substring's absence |
| Upsert | Insert-or-update on the primary key (Supabase `Prefer: resolution=merge-duplicates`) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/cloud_store.py` | The handle-keyed Supabase adapter |
| `tests/test_cloud_store.py` | The adapter contract (monkeypatched `requests`) |
| `tests/test_web_squads.py` (secret-gated) | The revised read-only guardrail |
| `docs/CLOUD_SQUADS.md` | The owner Supabase setup + privacy note |

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

- US-309 The `cloud_store` adapter (Supabase, handle-keyed, secret-gated) + the read-only guardrail revision
- US-310 The My-Squad "☁ Save/Load across devices" UI + a privacy note + `docs/CLOUD_SQUADS.md`

**Stories Carried Forward:**

- None. (Native `st.login()` + a handle-availability check are deferred follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
