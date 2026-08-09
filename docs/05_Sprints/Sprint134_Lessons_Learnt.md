# Lessons Learned

**Sprint:** Sprint 134 — Fix "remember me" persistence (the cookie didn't survive a refresh)

**Dates:** 2026-08-09

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Tester feedback: the invite-code + cookie **didn't persist across a browser refresh on Safari *or* Chrome**. Find
the cause and fix it (Option 1 — the smallest change that keeps the invite-code model), then the owner re-smokes on
both browsers. The confirm-on-Log-out polish was deferred behind this.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Read the dependency's source to diagnose, not guess** — the fix fell out of one grep of the component build.
- **Undo your own over-engineering when it's the cause** — the "clever" native read was the bug.

### New Skills Acquired

- **`st.context.cookies` and a component cookie live in different jars.** `st.context.cookies` reads the cookies
  the browser sends to the **Streamlit server on the top-level request**; a Streamlit cookie component sets
  `document.cookie` **inside its own iframe**. So a component *write* is not visible to a native *read* — they must
  both go through the **same** component to share a jar. Pairing a component write with a native read (Sprint 132)
  silently never persisted.
- **A symptom on *both* browsers rules out the browser.** "Fails on Safari and Chrome" immediately excludes an
  iOS/ITP-specific cause and points at something structural (here, the jar mismatch) — a useful triage reflex.
- **A component that syncs on a rerun forces a one-run wait — handle it safely.** Reading through the component
  means the value arrives on the *second* run of a session, so a cold load's first read is `None`. The gate waits
  one run behind a placeholder — but the wait must be **one-shot** (so it can't loop) and **gated on the component
  being present** (so a headless run or a cookie-blocked browser never hangs — it just shows the gate).
- **A green AppTest suite is necessary, not sufficient, for a browser feature.** AppTest can't run the component,
  so the decision path can be fully tested while the actual cookie roundtrip is still unproven — the owner's
  browser re-smoke is the real gate. Naming that honestly (code-complete ≠ verified) keeps the status truthful.

---

# What Went Well ✅

- **Root-caused from the source** — grepping the component build (`document.cookie` inside the iframe, only
  `window.parent.postMessage` for the value channel) turned "why won't it persist?" into a one-line answer.
- **Small, reversible fix** — read through the same component; no dependency change, the invite-code model intact.
- **Undid the over-engineering honestly** — reverted native-read; brought back the one-run wait it had avoided.
- **The wait can't hang or break CI** — one-shot + component-gated; 860 → 864, ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Cookie never persisted (both browsers) | component writes in its iframe jar; native read looked at the top-level jar | Read through the **same** component (`_controller().get()`) |
| Component value arrives late | it syncs to Python on a rerun, not run 1 | A one-run placeholder wait (`_maybe_wait_for_cookie`) |
| The wait could hang / break tests | if it waited with no component to respond | One-shot + gated on `remember.available()` (headless → no wait) |
| Two AppTests expected the gate on run 1 | they'd now hit the wait | Set `available()=False` in those (the headless reality) |
| Can't test the real fix | AppTest has no browser | Test the decision path; the cookie roundtrip = owner re-smoke |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Cookie jars | Native `st.context.cookies` ≠ a component's iframe cookie; read+write must share the component |
| Component timing | The value syncs on a rerun → the first read of a session is None → wait one run |
| Safe waiting | One-shot + presence-gated, so it degrades to "show the gate" instead of hanging |
| Test limits | AppTest proves the logic, not the browser cookie — say "code-complete, not verified" |

---

# Development Lessons 💻

- When a browser feature "just doesn't work", read the dependency's built JS before theorising — origins and jars
  are where cookie bugs hide.
- If a past optimisation (native read) is the cause, revert it plainly; don't add more cleverness on top.
- Make an unavoidable wait one-shot and presence-gated so it can never loop or hang a headless run.

---

# AI Collaboration Lessons 🤖

- The whole remember-me/logout family is still a **client-side convenience** over the access gate (ADR-087/098/099)
  — no server state, no new server write, re-validated on load. This sprint only corrected *how the cookie is
  read*; the read-only invariant's two exceptions (squad save, registration) are untouched.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — **ADR-099 corrected**. The Sprint 132 "native read" (`st.context.cookies`) was wrong: it can't see
a cookie the component writes in its iframe (different jars), so nothing persisted. `remember.read()` now reads
through the **same component** as the write; the component's one-run delivery delay is covered by a one-shot,
presence-gated "Checking your device…" wait (`access._maybe_wait_for_cookie`). If the owner re-smoke still fails,
the escalation is native **`st.login()`** (Sprint 134 Option 2), not another cookie iteration. (US-330.)_

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (the real test):** re-smoke on the deployed app in **Safari + Chrome** — pass the gate → refresh → stay
  in (a brief "Checking…" is fine); private tab / clear cookies → re-prompt; Log out → re-gate. Reboot the app if
  the deploy looks half-synced.
- **If it works:** pick up **US-329** (confirm on Log out). **If it still fails:** open the **`st.login()`** pivot
  (Sprint 134 Option 2) — native persistence + verified identity, no iframe cookie.
- **GW1 (2026-08-21):** the big body — calibrate the set-piece / DefCon / form weights + backtest; momentum;
  live manager import.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep separating "code-complete" from "verified" for browser features; the owner smoke is the gate, and the
  escalation (here, `st.login()`) is agreed before the smoke, not after.

---

# Key Commands Learned

```text
python -m pytest tests/test_remember.py tests/test_access.py -q   # the seam + the gate wiring + the loading wait
# inspect a component's built JS to see how it sets cookies (iframe document vs window.parent)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Cookie jar | The (origin-scoped) store a cookie lives in — a component's iframe jar ≠ the app's top-level jar |
| Loading run | The first run of a session, before the cookie component has synced its value to Python |
| Presence-gated wait | Waiting for the cookie only when `available()` — so headless/blocked never hangs |
| Code-complete ≠ verified | Logic tested in AppTest; the real browser cookie roundtrip still needs a manual smoke |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/remember.py` | Read/write/clear + `available()`, all through the one component |
| `src/web_streamlit/access.py` (`_maybe_wait_for_cookie`) | The one-shot, presence-gated loading wait |
| `docs/06_Decisions/ADR-099-…` (correction note) | Why native read failed and component-read is right |
| `docs/05_Sprints/Sprint134.md` | The root cause + the Option 1/2/3 decision (st.login is the fallback) |

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

**Sprint Outcome:** ☐ Successful ☑ Partially Successful (code-complete — awaiting the owner browser re-smoke) ☐ Needs Follow-up

**Stories Completed:**

- US-330 Read the "remember me" cookie through the component (fix the jar mismatch) + a one-run loading wait

**Stories Carried Forward:**

- US-329 Confirm on Log out — deferred until the re-smoke confirms persistence works.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
