# Lessons Learned

**Sprint:** Sprint 102 — Beta enablement (access gate + in-app feedback + a runbook)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the deployed app **beta-ready** — an **opt-in access-code gate**, an **in-app feedback form**, and a
**"Join the beta" link** to the founding-tester signup — plus a runbook, all **off by default** (the public app
+ tests unchanged until the owner opts in). No accounts/auth.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Opt-in, off-by-default features** — gate everything behind a secret so the default behaviour (and the
  tests) don't move.
- **Degrade-safe design** — the gate opens, feedback points to GitHub, the signup hides, all when unconfigured.

### New Skills Acquired

- `st.secrets.get(...)` **raises** `StreamlitSecretNotFoundError` when there's no `secrets.toml` — config must
  be read through a try/except helper (or local/CI crashes).
- A **shared access code** in `st.session_state` + `st.stop()` gates a Streamlit multipage app without
  accounts — call `require_access()` after `set_page_config` on every page.
- The founding-tester **"free for X years" promise only needs an email list now** — captured by an external
  form the app links to; comps can be honoured later if accounts/payments arrive.
- Feedback can stay **read-only to our infra**: POST to the owner's *own* sink (a Google Apps Script webhook),
  never our storage — the `no .save(` guardrail still holds.

---

# What Went Well ✅

- **Zero blast radius** — no secret → nothing changes; the 680 existing tests were untouched, the new paths
  proven by monkeypatching secrets.
- **Caught the crash trap** — the `secret()` try/except (pinned by a test) stops the missing-secrets-file crash.
- **No pivot** — a controllable beta with no auth/DB, exactly the DIRECTION §3 plan.
- **A runbook** — `docs/BETA.md` lets the owner flip it on + recruit solo.
- 680 → 686 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `st.secrets` crashes with no file | it raises rather than returning None | A `secret()` try/except helper (+ a test) |
| A gate must not break the suite | tests render every page | Off-by-default (no code → open); the block path monkeypatches the code |
| `AppTest.from_file` path error | relative paths resolve against the *test* file | Use an absolute path from the repo root |
| Adding a page broke fixed lists | page-count + tab-emoji tests hard-code the pages | Update both for the 8th tab (📣) |
| A duplicate tab emoji | 💬 was taken by Ask | Give Feedback its own 📣 |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| `st.secrets` | Raises without a file — wrap it; fall back to env |
| Multipage gate | `require_access()` after `set_page_config`, `st.stop()`, a session flag |
| Off-by-default | Opt-in via secrets keeps the default + tests stable |
| Read-only feedback | POST to the owner's external sink, not our storage |

---

# Development Lessons 💻

- Gate new deploy behaviour behind a secret so "off" is the default and the public app/tests don't move.
- Read external config through a helper that can't crash (missing file / missing key).
- When a feature adds a page, hunt down the tests that enumerate pages and update them.

---

# AI Collaboration Lessons 🤖

- "Set up a beta" decomposed to: a shared-code gate + an in-app form + an external email form + a runbook —
  the least infrastructure that still validates demand, keeping the no-backend design intact.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-087 | **Beta enablement — an opt-in access gate + feedback capture.** A shared `FPL_ACCESS_CODE` gates entry (no accounts); an in-app feedback form POSTs to the owner's `FPL_FEEDBACK_WEBHOOK` (degrades to GitHub); a "Join the beta" link to `FPL_SIGNUP_URL` captures founding-tester emails. All opt-in via secrets, off by default; a safe `secret()` getter; the read-only guardrail holds (no user data on our infra). Accounts/DB/payments deferred (DIRECTION §1) | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Flip the beta on** when ready: set the three secrets (see `docs/BETA.md`) + recruit on Reddit.
- **A sturdier host** if Community Cloud strains under testers (first nudge to DIRECTION §1).
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the Price Change Predictor.
- Backlog: a hosted LLM for the deploy (free-form chat); persisted chat context; grow the rules KB.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep new deploy behaviour opt-in so the public app never regresses mid-build.

---

# Key Commands Learned

```text
# In Streamlit Community Cloud → Manage app → Settings → Secrets (all optional; unset = off):
#   FPL_ACCESS_CODE / FPL_FEEDBACK_WEBHOOK / FPL_SIGNUP_URL
# See docs/BETA.md for the full runbook.
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Access gate | A shared-code prompt (`require_access`) that stops each page until entered |
| Off-by-default | A feature that's inert until its secret is set |
| Founding testers | Early beta users whose emails you capture to honour future comps |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-087 | The beta-enablement decision (gate + feedback, opt-in, no accounts) |
| `src/web_streamlit/access.py` | The `secret()` helper + `require_access()` gate |
| `docs/BETA.md` | The owner runbook (secrets · feedback sink · signup · recruiting) |

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

- US-263 Opt-in access-code gate — `require_access()` on every page, gated by `FPL_ACCESS_CODE` (ADR-087)
- US-264 In-app feedback + beta signup + `docs/BETA.md` runbook — off by default, degrades to GitHub

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
