# Sprint 123: Feedback to your inbox — a mailto route + an email relay

**Dates:** 2026-08-24 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (a small, high-value enablement — a mailto route + relay compatibility + docs)
**Carried Over:** the **ADR-094 persistence build** — *re-deferred to a later sprint* at the owner's request
(this sprint prioritises getting feedback flowing to the new inbox); still gated + ready.

> **Direction (owner):** *"Look at the Feedback form — I've set up an email to capture feedback:
> **fpl.assistant@proton.me**."* Wire the in-app feedback so it reaches that inbox.

---

### 🔎 Verified at planning (on real data)

- **The form already POSTs** `{message, email, source, page, version, ts}` to `FPL_FEEDBACK_WEBHOOK`
  (ADR-087; enriched in Sprint 122); its **fallback today is a dev-only GitHub-issue link** (`8_Feedback.py`
  lines 55/71/73) — too much friction for non-dev testers, and it doesn't use the new email.
- **⚠️ Proton has no free SMTP.** Direct sending from the app would need Proton **Bridge** (paid, desktop-only) or
  a paid plan — so "the app emails you" via SMTP is **out** (cost + creds in the app). The two free routes to the
  inbox are: **(a) a `mailto:` link** (opens the tester's own mail client, pre-filled) and **(b) a form-to-email
  relay** (FormSubmit / Web3Forms → forwards a POST to your address).
- **A mailto builds cleanly + renders.** `mailto:fpl.assistant@proton.me?subject=…&body=…` (URL-encoded via
  `urllib.parse.quote`) is a valid href; `st.link_button` / `st.markdown` render it clickably (verified).
- **The address is config-able.** `access.secret(key, default)` supports a default → `secret("FPL_FEEDBACK_EMAIL",
  "fpl.assistant@proton.me")` works out of the box and stays overridable.
- **No new server write.** The POST path already exists (ADR-087); a mailto is just a link. The read-only
  guardrail is untouched.

---

### 🎯 Sprint Goal

**Objective:** feedback reaches **fpl.assistant@proton.me** with as little friction as possible — a **one-click
pre-filled email** that works with zero setup, plus the option to wire the in-app form to a free **email relay**
for structured capture. Replace the dev-only GitHub fallback as the primary path for non-dev testers.

#### Success Criteria
- [ ] **US-307 (a `mailto:` email route)** — a config'd `FPL_FEEDBACK_EMAIL` (default **fpl.assistant@proton.me**)
      and a **pre-filled email route**: an always-available **"✉ Email your feedback"** link, *and* — when no
      webhook is set — a submit builds a **pre-filled mailto** (subject + the typed message + page + version) so
      one click opens the tester's mail client ready to send. The GitHub link demotes to a secondary "prefer
      GitHub?" line. A pure, unit-tested `feedback_mailto(...)` helper.
- [ ] **US-308 (email-relay compatibility + docs)** — make the JSON POST work with a **free form-to-email relay**:
      add a `_subject` (FormSubmit honours it) and, when `FPL_FEEDBACK_KEY` is set, an `access_key` (Web3Forms) to
      the payload; `email` stays the reply-to. Document in `docs/BETA.md` how to point `FPL_FEEDBACK_WEBHOOK` at a
      relay → **fpl.assistant@proton.me** (FormSubmit zero-signup, or Web3Forms with a key), incl. the why-not-SMTP
      note + FormSubmit's one-time confirmation click.
- [ ] **No drift** — display/link + payload-field only; no new server-write path (the POST already existed); the
      read-only guardrail holds; existing **776** stay green (+ mailto/relay tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README (n/a), Help (n/a), Feedback_Log, BETA.md (extends **ADR-087**;
      no new ADR — a route/config change).

---

### 🧭 Design sketch

**US-307 — the mailto route.** A pure helper (in `8_Feedback.py` or a tiny module):
`feedback_mailto(email, message, page, version) -> str` builds
`mailto:{email}?subject={quote(subject)}&body={quote(body)}` where the body carries the message + a
`page: … | version: …` footer. In the page: a header **"✉ Email your feedback"** `st.link_button` (template
body — always available); and in the **no-webhook** branch, replace the GitHub `st.info` with a **pre-filled**
mailto link built from the *typed* message (known post-submit) → "✉ Click to email this to us". `FPL_FEEDBACK_EMAIL
= secret("FPL_FEEDBACK_EMAIL", "fpl.assistant@proton.me")`. The GitHub link stays only as a small secondary
option.

**US-308 — relay compatibility.** Extend the POST payload with `"_subject": "FPL Assistant beta feedback"` and,
when `secret("FPL_FEEDBACK_KEY")` is set, `"access_key": <key>` — so the *same* `requests.post(webhook, json=…)`
works with **FormSubmit** (`https://formsubmit.co/ajax/<addr-or-token>`, no key) or **Web3Forms**
(`https://api.web3forms.com/submit`, needs the key). BETA.md §1 gains an **"Option B — email relay"** beside the
existing Sheet, targeting fpl.assistant@proton.me, with the SMTP caveat + FormSubmit's confirmation step.

**Deferred:** direct **SMTP** send (Proton has no free SMTP — a paid Bridge/plan; revisit only if a relay proves
insufficient); a captcha/anti-spam on the relay (FormSubmit has basic spam filtering; revisit if abused); the
**ADR-094 persistence build** (re-deferred — still gated + ready for a later sprint).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-307 | **A `mailto:` email route** — a pre-filled "✉ Email your feedback" to fpl.assistant@proton.me. | High | ✅ Done | ~¼ session |
| US-308 | **Email-relay compatibility + docs** — POST works with FormSubmit/Web3Forms → the inbox. | High | ⬜ To do | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you — ~5 min, £0)

_(the sprint delivers the code + docs; you pick a route)_
1. **Zero-setup:** nothing — the **mailto** route works the moment this ships (testers' mail client → your inbox).
2. **Structured capture (optional):** set `FPL_FEEDBACK_WEBHOOK` to a **FormSubmit** endpoint for
   fpl.assistant@proton.me (click the one-time confirmation email), *or* a **Web3Forms** endpoint + set
   `FPL_FEEDBACK_KEY`. Then in-app submits email you structured feedback (no Sheet needed).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `feedback_mailto` builds a correct, URL-encoded `mailto:` (address + subject + message + page
   + version) — a unit test; the Feedback page shows an "✉ Email…" route and, with no webhook, a submit yields a
   **mailto** link (not only GitHub) — an AppTest; the POST payload carries `_subject` (+ `access_key` when the
   key is set) — extend the Sprint-122 payload test. Existing **776** stay green. No new `.save(`.
2. **Manual smoke** — `python -m src.web_streamlit` → Feedback: the "✉ Email your feedback" opens a pre-filled
   mail draft to fpl.assistant@proton.me; with no webhook, submitting offers the pre-filled email link.
3. **Docs updated** — PROJECT_STATUS, Architecture, Feedback_Log, BETA.md (the relay option + the SMTP note).

---

### 📝 Session Progress Log

- **US-307 (a `mailto:` email route)** — added a pure `web_streamlit/feedback.py::feedback_mailto(email, message,
  page, version)` (URL-encoded subject/body; `(not sure)` page ignored; empty message → a template body) — split
  into its own importable module because the page (`pages/8_Feedback.py`, numeric prefix) can't be imported for a
  unit test. Wired into the Feedback page: `FPL_FEEDBACK_EMAIL = secret("FPL_FEEDBACK_EMAIL",
  "fpl.assistant@proton.me")`; an always-available **"✉ Email your feedback"** `st.link_button` (template body);
  and — when **no webhook** (or a POST fails) — a **pre-filled** "✉ Email this feedback" built from the typed
  message + page + version (replacing the dev-only GitHub `st.info`; GitHub demoted to the secondary caption).
  Display/link only — no new server write; the read-only guardrail holds. Smoke: header link →
  `mailto:fpl.assistant@proton.me`; submit w/o webhook → a second mailto carrying the message + page. +5 tests
  (4 unit in `tests/test_feedback.py` + the renamed page AppTest now asserting the pre-filled email). ruff clean.
  **780** total.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
