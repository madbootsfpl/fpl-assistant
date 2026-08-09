# Lessons Learned

**Sprint:** Sprint 130 — Beta-readiness tidy (FormSubmit docs + a "handle taken?" hint)

**Dates:** 2026-08-31

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Tidy two loose ends before the beta goes wide: **document the FormSubmit setup** (the Origin/activation gotchas
fixed in code) and add a **"handle taken?" hint** on the ☁ cross-device Save. Docs + a small UX polish; no
analytics change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Turn a debugging session into durable docs** — write down the exact wall you hit, with a self-diagnosing test.
- **Fix silent-success at the root** — a form that always says "sent" is worse than one that surfaces the error.

### New Skills Acquired

- **A server-side POST isn't a browser fetch.** FormSubmit's anti-abuse rejects requests with no `Origin`/
  `Referer` — fine for browser AJAX, but our form POSTs from Streamlit's *backend*, so it must send one. The
  generic "…open this page through a web server…" error was the tell; adding an Origin header fixed it. Know where
  your HTTP actually originates.
- **Report the real result, not a hopeful one.** The form showed "sent 🎉" on any response, hiding a stalled
  relay. Reading `{success, message}` and surfacing it (`relay_result`) is the honest behaviour — and it *is* the
  diagnosis the user needs.
- **Place a check where it's cheap.** The "handle taken?" existence check runs only on the Save **click**, not on
  every rerun of the text input — one request, not a network call per keystroke.
- **Docs are part of the fix.** The code fix isn't done until the runbook reflects it, or the next person repeats
  the debugging round.

---

# What Went Well ✅

- **The live fix became a runbook** — Origin + activation + a self-diagnosing `curl` are now in BETA.md.
- **Silent-success fixed at the root** — the form tells the truth now.
- **A cheap, well-placed existence check** — one request on Save, not per keystroke.
- 822 → 827 tests (across the fix + this sprint); ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Relay rejected the POST | server-side request, no Origin/Referer | Send an Origin header (`FPL_FEEDBACK_ORIGIN`) |
| Form said "sent" but nothing arrived | it ignored the relay's reply | `relay_result` reads `{success, message}` |
| Runbook didn't match reality | the fix wasn't documented | Rewrote BETA.md §1B + a Troubleshooting curl |
| A shared handle could be clobbered | Save is a silent upsert | `exists()` → warn new vs overwrite on Save |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Server-side vs browser POST | A backend request has no browser Origin — send one if the relay needs it |
| Honest results | Read the relay's response; don't assume 2xx = delivered |
| Cheap checks | Put an existence check on the click, not on every rerun |
| Docs close the loop | A fix isn't finished until the runbook reflects it |

---

# Development Lessons 💻

- When integrating a third-party relay, test whether it needs browser headers your server-side call won't send.
- Surface a service's real response to the user; a blind success message hides the actual failure.
- After a live fix, update the runbook in the same breath — that's where the debugging value is banked.

---

# AI Collaboration Lessons 🤖

- Feedback capture stays outside the grounded/read-only core: the POST goes to the owner's own relay; the fix was
  about *honesty of the result*, not adding any user-data persistence — the read-only guardrail is untouched.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR. The feedback fix: `web_streamlit/feedback.relay_result` (read the relay's real reply) + an
`Origin`/`Referer` header (`FPL_FEEDBACK_ORIGIN`). US-320: BETA.md documents the FormSubmit setup end-to-end.
US-321: `cloud_store.exists(handle)` + a new-vs-overwrite Save message (ADR-094)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner:** reboot the Streamlit app to pick up the feedback fix; then a real in-app submit lands in the inbox.
- **GW1 (2026-08-21+):** the big body of work — calibrate the set-piece / DefCon / form weights + backtest;
  momentum boards; live manager import — all waiting on real in-season data.
- **Deferred:** a random-suffix suggestion on ☁ Save; a CLI price column.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Bank a live fix into the runbook immediately; put cheap checks on the action, not the render.

---

# Key Commands Learned

```text
# self-diagnose a FormSubmit relay (BETA.md Troubleshooting):
curl -s -X POST https://formsubmit.co/ajax/<addr> -H "Content-Type: application/json" \
  -H "Origin: https://<app>.streamlit.app" -d '{"message":"test","_subject":"FPL test"}'
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Origin/Referer gate | A relay's anti-abuse check that a POST came from a real web page |
| Silent success | A UI that reports success without reading the service's real reply |
| Handle-taken hint | A Save that warns it's overwriting an existing cloud squad |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/BETA.md` §1B + Troubleshooting | The full FormSubmit setup + a self-diagnosing curl |
| `src/web_streamlit/feedback.py` (`relay_result`) | Read the relay's real result |
| `src/web_streamlit/cloud_store.py` (`exists`) | The light existence check behind the Save hint |

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

- US-320 Document the FormSubmit setup in BETA.md (Origin, activation, `FPL_FEEDBACK_ORIGIN`, the real-result form)
- US-321 A "handle taken?" hint on ☁ Save (`cloud_store.exists` → new vs overwrite)
- _(interstitial) Feedback fix — `relay_result` + an Origin header so the relay works server-side_

**Stories Carried Forward:**

- None. (A suffix suggestion + a CLI price column are follow-ups; the GW1 calibration is the big deferred body.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
