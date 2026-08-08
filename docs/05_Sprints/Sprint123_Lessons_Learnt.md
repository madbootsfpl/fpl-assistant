# Lessons Learned

**Sprint:** Sprint 123 — Feedback to your inbox (a mailto route + an email relay)

**Dates:** 2026-08-24

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Wire the in-app feedback form to the owner's new inbox (**fpl.assistant@proton.me**) with as little friction as
possible — a zero-setup pre-filled `mailto:` plus the option of a free form-to-email relay for structured
capture. Display/link + payload-field only; no new server write.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Verify the constraint before designing** — "Proton has no free SMTP" reshaped the whole approach up front.
- **One POST, many sinks** — make the existing request work with several services via additive fields.

### New Skills Acquired

- **The blocking fact decides the design.** Proton offering no free SMTP meant "the app emails you" was never on
  the table — so the sprint went straight to the two viable free routes (`mailto:` + a relay) instead of building
  a dead end. Checking that in planning saved the whole sprint from a wrong turn.
- **A zero-setup path beats a better path that needs setup.** The `mailto:` works the instant it deploys (no
  owner action); the structured relay is strictly nicer but needs a webhook + a confirmation click. Shipping the
  zero-setup route as the floor, the relay as the ceiling, means feedback flows *now*.
- **Additive payload fields keep one code path service-agnostic.** `_subject` (FormSubmit) + an optional
  `access_key` (Web3Forms) let the *same* `requests.post` target a Sheet, FormSubmit, or Web3Forms — the owner
  picks by config, no branching.
- **Refactor for the test boundary.** A pure helper in a page module with a numeric prefix (`8_Feedback.py`)
  can't be imported for a unit test — moving `feedback_mailto` into `feedback.py` made it testable and matched
  the codebase's "small importable helpers" pattern.

---

# What Went Well ✅

- **Named the SMTP constraint first** → straight to the right two routes.
- **Zero owner setup for the floor** — the mailto works on deploy; the relay is optional polish.
- **Same POST, many sinks** — Sheet / FormSubmit / Web3Forms, no code change to switch.
- 776 → 781 tests; ruff + CI-parity green; the read-only guardrail untouched.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "Send an email from the app" | Proton has no free SMTP | Use a `mailto:` + a form-to-email relay, not SMTP |
| A pre-filled link can't see typed text at render | link_button is static | Build the pre-filled mailto *post-submit* from the message |
| The pure helper wasn't importable | `8_Feedback.py` has a numeric prefix | Move `feedback_mailto` into `web_streamlit/feedback.py` |
| Relay services want different fields | FormSubmit vs Web3Forms | Add `_subject` always + `access_key` only when the key is set |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Constraint-first design | The blocking fact (no free SMTP) picks the approach |
| Floor vs ceiling | Ship the zero-setup route; add the better one on top |
| Service-agnostic POST | Additive fields target many sinks from one request |
| Importable test boundary | Pure helpers belong in importable modules, not numeric-prefixed pages |
| Post-submit pre-fill | Build a `mailto:` from the submitted value, not at render |

---

# Development Lessons 💻

- Check the hard external constraint in planning; it often eliminates the "obvious" approach.
- Put pure, testable helpers in importable modules; keep pages as thin, un-imported edges.
- Prefer additive config-driven fields over branching when one path must serve several back-ends.

---

# AI Collaboration Lessons 🤖

- Feedback capture stays outside the grounded/read-only core: the POST goes to the owner's *own* sink and the
  mailto to the owner's inbox — no user data persists on our infra, so the read-only guardrail is intact.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-307/308 extend **ADR-087** (beta feedback). New: `web_streamlit/feedback.py::feedback_mailto`;
`FPL_FEEDBACK_EMAIL` (default fpl.assistant@proton.me) drives a pre-filled `mailto:` fallback; the webhook POST
gains `_subject` + an optional `access_key` so it works with a free form-to-email relay (FormSubmit / Web3Forms)
as well as the Sheet sink. Direct SMTP is **rejected** for now (Proton has no free SMTP)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (to go live):** pick a route — the mailto works now; for structured capture, point `FPL_FEEDBACK_WEBHOOK`
  at FormSubmit for fpl.assistant@proton.me (+ the one-time confirmation click), or Web3Forms + `FPL_FEEDBACK_KEY`.
- **ADR-094 persistence build** — still gated + ready whenever you want cross-device squads.
- **Deferred levers:** direct SMTP (only if a relay is insufficient); anti-spam on the relay (only if abused).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep leading with the hard constraint check; keep pure helpers in importable modules.

---

# Key Commands Learned

```text
python -m src.web_streamlit    # Feedback → "✉ Email your feedback" (mailto) / submit → pre-filled email
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Form-to-email relay | A free service (FormSubmit/Web3Forms) that emails a POST to your inbox |
| Pre-filled mailto | A `mailto:` link carrying subject + body so one click drafts the email |
| Floor vs ceiling route | A zero-setup path (mailto) + an optional better one (relay) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/feedback.py` | The pure `feedback_mailto` helper (unit-tested) |
| `src/web_streamlit/pages/8_Feedback.py` | The form: mailto route + relay-ready POST |
| `docs/BETA.md` (§1A/§1B) | Sheet vs email-relay setup + the why-not-SMTP note |

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

- US-307 A pre-filled `mailto:` feedback route to fpl.assistant@proton.me (zero setup)
- US-308 Webhook compatibility with a free form-to-email relay (FormSubmit/Web3Forms) + BETA docs

**Stories Carried Forward:**

- The ADR-094 persistence build (re-deferred; still gated + ready).

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
