# Architectural Decision Record: Beta enablement — an opt-in access gate + feedback capture

**Decision ID:** ADR-087
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** new (opt-in) web-edge behaviour. No accounts, no per-user DB, no payments — those
stay deferred (DIRECTION §1). Triggered by the owner's "beta-setup sprint" (wider testing, DIRECTION §3).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner wants to open the app to **~50 external testers** (e.g. via Reddit) with some **access control**,
**low-friction feedback**, and the ability to honour a future *"free for X years"* promise — **without building
accounts/auth** (that's a product pivot, DIRECTION §1). Today the app is public, backend-free, read-only.

**Verified:** `st.secrets.get(...)` **raises** `StreamlitSecretNotFoundError` when there's no `secrets.toml`
(so config must be read through a try/except helper, or local/CI crashes); `st.form`/`st.link_button` exist.
The read-only guardrail (a test asserts the web edges never `.save(` squads) must keep holding.

#### Decision Drivers
- **Control the door** — a shared code, not accounts (a beta, not a product).
- **Off by default** — the public app + the test suite must be **unchanged** until the owner opts in.
- **Low-friction feedback** — an in-app form, not "go make a GitHub account".
- **Honour comps later** — capture **emails** now, even without accounts.
- **Keep the architecture** — no per-user persistence on our infra; the read-only guardrail holds.

---

### ✅ Decision

**1. An opt-in access-code gate (US-263).** A shared `web_streamlit/access.py::require_access()` called at the
top of **every** page: if `FPL_ACCESS_CODE` is configured, show a password prompt and `st.stop()` until it
matches, remembering success in `st.session_state`; if **unset**, return immediately (the app stays open — its
current behaviour). A `_secret(key, default=None)` helper reads `st.secrets` inside a try/except and falls back
to `os.environ`, so a missing secrets file never crashes. A **shared code** (not accounts) — enough to gate a
beta; the owner rotates it by changing the secret.

**2. In-app feedback + a beta signup link (US-264).** A **Feedback** page: a form (message · optional email ·
auto-captured app version/page) that on submit **POSTs to `FPL_FEEDBACK_WEBHOOK`** (the owner's Google Apps
Script / form-service sink) best-effort, degrading to a *"open a GitHub issue"* link when the webhook is unset
or the POST fails. A **"Join the beta"** `link_button` to `FPL_SIGNUP_URL` (the owner's external email-capture
form). The **only** outbound write is this feedback POST to the owner's *own* sink — it does **not** persist
user data (squads/settings) on our infra, so the read-only guardrail is intact.

**3. All opt-in via secrets/env, off by default.** `FPL_ACCESS_CODE` · `FPL_FEEDBACK_WEBHOOK` ·
`FPL_SIGNUP_URL`. Unset → the gate is open, feedback points to GitHub, the signup link is hidden. So the public
deploy + CI are unaffected until the owner sets them; a `docs/BETA.md` runbook covers the setup + recruiting.

---

### 🔀 Alternatives Considered

- **Real accounts/auth** (Supabase/Clerk) + a per-user DB. Rejected for the beta — a product pivot (DIRECTION
  §1); a shared code + an email list is enough to validate demand and honour comps.
- **Community Cloud's viewer allowlist** (by Google email). Rejected — awkward for strangers (needs their
  Google accounts) and it's an all-or-nothing app setting, not a rotatable code.
- **Feedback only via GitHub issues.** Kept as the **fallback**, but too much friction for non-devs as the
  primary — hence the in-app form when a webhook is set.
- **A feedback POST to our own storage.** Rejected — that would break the read-only, no-server-state design;
  the POST goes to the owner's *external* sink instead.

---

### 🧭 Consequences

**Positive**
- The owner can open a controlled beta with one secret, collect feedback in-app, and build a founding-tester
  email list — with **no code change** to flip on, and **zero** change to the public app until they do.
- The architecture is preserved: no accounts, no per-user DB, the read-only guardrail holds.

**Negative / risks (mitigations)**
- **A shared code is weak security** → fine for a beta (it gates casual access, not a threat model); rotate via
  the secret. Not for anything sensitive (there's nothing sensitive — it's read-only public FPL data).
- **`st.secrets` crashes without a file** → the `_secret` try/except is the mitigation (and a test pins it).
- **The feedback POST is an outbound side-effect** → best-effort (try/except, short timeout), to the owner's
  own sink, never persisting user data; degrades to a link.
- **Test/CI safety** → no secrets configured → gate open + feedback degraded → no network, no behaviour change;
  the gate's blocking path is tested with a monkeypatched code.

---

### 📊 Validation

Verified: `st.secrets.get` raises without a file (hence `_secret`); the widgets exist. Acceptance: `_secret`
returns None (no crash) unconfigured; `require_access` is a no-op when `FPL_ACCESS_CODE` is unset and blocks
(then unlocks on the session flag) when set; the Feedback page renders its form + the GitHub fallback with no
webhook (no network in tests); the "Join the beta" link shows only when `FPL_SIGNUP_URL` is set; the read-only
guardrail (`no .save(`) still passes; existing **680** tests stay green; ruff clean.
