# Sprint 102: Beta enablement — an access gate, in-app feedback, and a runbook

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (an opt-in access gate + an in-app feedback form + a beta runbook)
**Carried Over:** none

> **Direction (owner):** *"beta-setup sprint next."* From [DIRECTION.md](../00_Project/DIRECTION.md) §3: set up
> a **wider beta (~50 testers, e.g. via Reddit)** with **access control**, **low-friction feedback**, and the
> means to honour a future *"free for X years"* promise — **without building accounts/auth**.

---

### 🔎 Verified at planning

- **Config must be opt-in + safe.** `st.secrets.get(...)` **raises** `StreamlitSecretNotFoundError` when there's
  no `secrets.toml` (verified) — so a naive read crashes local/CI. A `_secret(key)` helper that try/excepts and
  falls back to `os.environ` is required; **unset → the feature is off** (the gate is open, feedback degrades).
  This is what keeps the current public deploy + the test suite working unchanged.
- **The widgets exist** (Streamlit 1.61.1): `st.form`, `st.text_area`, `st.link_button`.
- **No accounts needed** (DIRECTION §3): a **shared access code** (a Streamlit secret) gates entry; **emails**
  for the founding-tester list are captured by an **external signup form** (the owner's Google/Tally form — the
  app just links to it); feedback is an **in-app form** that POSTs to the owner's webhook (a Google Apps Script
  / form service), degrading to a link when unset. None of this persists user data on our infra — the
  read-only guardrail (`no .save(` in the web edges) still holds.
- **GW1 is 14 days out (2026-08-21)** — a good window to recruit + shake out feedback before the season.

---

### 🎯 Sprint Goal

**Objective:** make the deployed app **beta-ready** — an **opt-in access-code gate** (so the owner can control
who's in), an **in-app feedback form** (low-friction, → the owner's sink), and a **"Join the beta" link** to
the founding-tester signup — plus a **runbook** so the owner can flip it all on and recruit. All opt-in via
secrets; **off by default** (the public app + tests are unchanged until configured).

#### Success Criteria
- [ ] **US-263 (access-code gate, ADR-087)** — a shared `require_access()` called at the top of every page:
      when `FPL_ACCESS_CODE` is configured (secret/env), show a password prompt and `st.stop()` until it
      matches, remembering success in `st.session_state`; when **unset**, the app is **open** (today's
      behaviour). A safe `_secret()` getter (no crash without a secrets file). Test-safe: no code → open, every
      page test unchanged.
- [ ] **US-264 (in-app feedback + signup + runbook)** — a **Feedback** page: a form (message · optional email ·
      auto-captured context like the app version) that, on submit, **POSTs to `FPL_FEEDBACK_WEBHOOK`**
      (best-effort, short timeout, degrades to a "use GitHub issues" link when unset or on failure); a
      **"✋ Join the beta"** `link_button` to `FPL_SIGNUP_URL` (on Home + Feedback). A **`docs/BETA.md`**
      runbook: create the signup form + the feedback webhook (Google Form/Apps Script), set the access code,
      recruit on Reddit, and honour *"free for X years"* via the captured email list.
- [ ] **No drift** — off by default; the read-only guardrail holds (no squad writes); existing **680** stay
      green (no secret in CI → gate open, feedback degrades); ruff clean.
- [ ] Docs: ADR-087 + index, PROJECT_STATUS, DIRECTION (mark the beta step done), README, Help.

---

### 🧭 Design sketch

**US-263 (ADR-087).** `web_streamlit/access.py`: `_secret(key, default=None)` (try `st.secrets`, except → 
`os.environ`); `require_access()` — if no `FPL_ACCESS_CODE` → return (open); if `st.session_state["_beta_ok"]`
→ return; else render a compact code prompt (`st.text_input(type="password")` + a note) and `st.stop()`; on a
correct code set the session flag and `st.rerun()`. Called right after `st.set_page_config(...)` on **every**
page (Home + `pages/*`). One line per page.

**US-264.** `pages/8_Feedback.py` — `st.title("💬 Feedback")`; a `st.form` (a `text_area` "what worked / what
broke / ideas", an optional email, a hidden auto-context: app version + the page). On submit: if a webhook is
configured, `requests.post(webhook, json=payload, timeout=…)` in a try/except → a success/‌failure toast; else
show *"feedback isn't wired to a sink yet — open a GitHub issue"* with the existing link. A **"✋ Join the beta
→"** `link_button(FPL_SIGNUP_URL)` on Feedback + Home (shown only when the URL is set). `docs/BETA.md`: the
step-by-step owner runbook (forms, secrets, recruiting, comps).

**Config keys (all optional, via secrets or env):** `FPL_ACCESS_CODE` (gate) · `FPL_FEEDBACK_WEBHOOK` (in-app
feedback sink) · `FPL_SIGNUP_URL` (founding-tester signup). Unset → the feature is simply off.

**Deferred:** real accounts/auth · a per-user DB · payments · rate-limiting the gate (a shared code is enough
for a beta) — all in DIRECTION §1, revisited only if the beta proves demand.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-263 | **Access-code gate** — opt-in `FPL_ACCESS_CODE`, a shared `require_access()` on every page; open when unset. ADR-087. | High | ⬜ To do | ~½ session |
| US-264 | **In-app feedback + beta signup + runbook** — a Feedback page (webhook POST, degrade to GitHub), a "Join the beta" link, `docs/BETA.md`. | High | ⬜ To do | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `_secret` returns None (no crash) without a secrets file; `require_access` is a **no-op
   when unset** (a page renders) and **blocks when a code is set** (monkeypatched) until the session flag is
   set; the Feedback page renders its form + the GitHub fallback when no webhook (no network in tests); the
   "Join the beta" link shows only when `FPL_SIGNUP_URL` is set. Existing **680** stay green.
2. **Manual smoke** — with `FPL_ACCESS_CODE` set, a page asks for the code and unlocks on the right one; unset,
   the app is open. The Feedback form submits (with a webhook) or points to GitHub (without).
3. **Docs updated** — ADR-087 + index, PROJECT_STATUS, DIRECTION, README, Help, and the new `docs/BETA.md`.

---

### 📝 Session Progress Log

**US-263 — access-code gate (ADR-087).** ✅ Done.
- `web_streamlit/access.py`: a safe `secret(key, default)` (try `st.secrets` → except → `os.environ` → default;
  never raises without a `secrets.toml`) + `require_access()` — a no-op unless `FPL_ACCESS_CODE` is set; else a
  `🔒 private beta` prompt that `st.stop()`s the page until the code matches, remembering success in
  `st.session_state` (then `st.rerun()`). Wrong code → an error.
- Wired `require_access()` right after `st.set_page_config(...)` on **all 8 pages** (Home + Players · Fixtures ·
  Squads · Ask · News · Trending · Help).
- **Tests (+4):** `secret` never raises unconfigured + reads env; the app is **open** with no code; the gate
  **blocks then unlocks** on the right code (wrong → error). Existing **680** stay green (no code in CI → open
  → every page test unchanged). ruff clean.
- **Manual smoke:** unset → open (Home title renders); `FPL_ACCESS_CODE=letmein` → the lock screen, a wrong
  code errors, the right code unlocks to the real app. Off by default; the public deploy is unchanged until the
  owner sets the secret.

**US-264 — in-app feedback + beta signup + runbook (ADR-087).** ✅ Done.
- `pages/8_Feedback.py` — a **📣 Feedback** tab: an `st.form` (message + optional email) that on submit
  **POSTs to `FPL_FEEDBACK_WEBHOOK`** (`{message, email, source}`, best-effort, 6s timeout, try/except),
  **degrading to a GitHub-issue link** when the webhook is unset or the POST fails. A **"✋ Join the beta"**
  `link_button` to `FPL_SIGNUP_URL` (shown only when set) on Feedback + Home. No user data persisted on our
  infra (the POST goes to the owner's own sink) — the read-only guardrail holds.
- `docs/BETA.md` — the owner runbook: the three opt-in secrets (`FPL_ACCESS_CODE` · `FPL_FEEDBACK_WEBHOOK` ·
  `FPL_SIGNUP_URL`), a copy-paste Google Apps Script feedback sink, a signup form, recruiting on Reddit, and
  honouring "free for X years" via the email list.
- **Tests (+2, 2 updated):** the Feedback form renders + **degrades to GitHub without a webhook** (no network
  in tests); the "Join the beta" link appears only when `FPL_SIGNUP_URL` is set; the page-list + tab-emoji
  tests updated for the 8th tab (📣). **686** green, ruff clean.
- **Manual smoke:** the Feedback form submits to GitHub-fallback with no webhook; the beta link appears once
  the signup URL is configured.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
