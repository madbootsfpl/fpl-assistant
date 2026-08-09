# Lessons Learned

**Sprint:** Sprint 132 — "Remember me": persist a passed gate across a browser refresh

**Dates:** 2026-08-09

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Remove the friction where **every browser refresh re-prompts** for the access code + email (`st.session_state` is
wiped on a full refresh). A first-party **"remember me" cookie** remembers a *passed* gate on a device (~30 days;
~7 on iOS), **off by default**, **re-validated** on load, and **byte-identical** when cookies are unavailable —
**not** the `st.login()` hard-auth pivot.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reach for the platform's native capability before a component** — `st.context.cookies` (native read) did the
  hard-to-flash half for free.
- **Remember a *pass*, re-validate the *access*** — persistence and authorisation are separate concerns.

### New Skills Acquired

- **Streamlit reads cookies natively but can't write them.** `st.context.cookies` exposes the request's cookies
  immediately on the first run (no component, no "loading" rerun) — so the **read** path never flashes the gate.
  Only the **write** needs a component, because there's no native set and a DIY `document.cookie` runs in a
  sandboxed iframe (wrong origin). Splitting the seam this way shrank the dependency's job to one direction.
- **A `st.rerun()` right after a component `set` discards the set.** `st.rerun()` throws away the current run's
  output (including the just-rendered set component) before it reaches the browser — so the cookie silently
  wouldn't persist. Fix: **defer the write** to the *next* clean run (stash the value in session, flush it when
  the gate is already passed). Caught in design, not in a failed smoke.
- **A remembered token must be re-validated, or it becomes a bypass.** Storing "I passed" isn't enough — on load,
  re-check it against the live source (`user_store.is_registered(email)` / `== current FPL_ACCESS_CODE`). That way
  a **pruned tester** or a **rotated code** invalidates the cookie for free; the cookie grants nothing new.
- **Quarantine a new dependency behind a no-op seam.** Lazy import + `try/except` in one module (`remember.py`)
  means a missing/blocked cookie degrades to today's gate — import, CI, AppTest and private-mode all stay safe,
  and the off-by-default invariance (839 byte-identical) is a monkeypatch away in tests.

---

# What Went Well ✅

- **Native read was the unlock** — `st.context.cookies` removed the loading-run flash entirely and reduced the
  component to writes; the design got *simpler* at build, not more complex.
- **Re-validated, not just trusted** — `is_registered` / `== current code` on every load keeps the gate honest.
- **Dependency quarantined + off by default** — one guarded seam; no cookie → today's gate, 839 byte-identical.
- **Deferred the write** — avoided a silent "cookie didn't persist" bug by writing on a clean run.
- 839 → 852 tests (+13); ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A refresh re-prompts | `st.session_state` is session-scoped, wiped on refresh | A first-party cookie remembers the pass |
| Streamlit can't set cookies | no native API; a DIY `document.cookie` is iframe-sandboxed | A small cookie component for the **write** only |
| The loading-run flash | reading *through* a component delivers the value a run late | Read **natively** (`st.context.cookies`) — value on run 1 |
| The write wouldn't persist | `st.rerun()` after a component `set` discards it | **Defer** the write to the clean post-login run |
| A cookie could be a bypass | it remembers "passed" | **Re-validate** on load (`is_registered` / `== code`) |
| Component won't run in AppTest | no browser | Seam read/write; monkeypatch in tests; write roundtrip = manual smoke |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Native vs component | `st.context.cookies` reads (instant, first run); only writing needs a component |
| Rerun vs component set | `st.rerun()` discards a same-run `set` — write on a later clean run |
| Persistence vs authz | Remember a *pass*; re-validate the *access* against the live source on load |
| Dependency hygiene | Lazily import + `try/except` behind one seam; degrade to today's behaviour |
| Off-by-default gates | Empty cookies in CI/AppTest → the gate is byte-identical; an invariance test pins it |

---

# Development Lessons 💻

- Check what the platform gives you natively before adding a component — half this feature needed no dependency.
- When a `set`-style side effect must reach the browser, don't `st.rerun()` in the same run — defer it.
- A "remember me" is a convenience layer; keep the authorisation check on every load so it can't drift into a bypass.

---

# AI Collaboration Lessons 🤖

- The cookie stays **outside** the grounded/read-only analytics core: it's a client-side convenience over the
  access gate (ADR-087/098), re-validated each load, that grants no new access and adds no server state (the email
  already lives in `beta_users`). The read-only invariant's two server-write exceptions (squad save, registration)
  are unchanged.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-099** — a persistent "remember me" cookie for the beta gate. Read natively (`st.context.cookies`), write via
a small quarantined component (`streamlit-cookies-controller`); store *what proves the pass* (email / code) and
**re-validate on load**; TTL ~30d (iOS ITP ~7d); graceful degradation (unavailable → today's per-session gate,
byte-identical); a convenience over ADR-087/098, **not** a new access path and **not** `st.login()` (still
deferred). Built: US-325 (`remember.py` seam + dep), US-326 (wire `require_access`, deferred write). Docs: BETA.md,
PROJECT_STATUS, Architecture, README._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (to enable):** nothing to configure — "remember me" ships in `requirements.txt` and layers on whatever
  gate you run. **Smoke it in a browser:** pass the gate → refresh → you stay in; private tab / clear cookies →
  re-prompts; iOS re-registers ~weekly.
- **Deferred:** a **"not you? / log out"** link (`remember.clear()` plumbing exists); a **signed token** instead of
  the raw value; native **`st.login()`** (hard, verified identity — the product path).
- **GW1 (2026-08-21):** the big body — calibrate the set-piece / DefCon / form weights + backtest; momentum;
  live manager import.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep checking for a native platform capability before adding a dependency; keep client-side conveniences
  re-validated and off-by-default so they can't erode the gate.

---

# Key Commands Learned

```text
python -m pytest tests/test_remember.py tests/test_access.py -q   # the seam + the gate wiring
# no secret to set — the dependency ships in requirements.txt; smoke in a browser (refresh keeps you in)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Remember me | A first-party cookie that persists a *passed* gate across a browser refresh |
| Native cookie read | `st.context.cookies` — the request's cookies, available on the first run (no component) |
| Deferred write | Writing the cookie on the clean post-login run, not before a `st.rerun()` that would drop it |
| Re-validate on load | Re-checking a remembered token against the live source (`is_registered` / `== code`) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/remember.py` | The guarded cookie seam (native read / component write) |
| `src/web_streamlit/access.py` (`require_access`) | Restore-on-load (re-validated) + deferred write |
| `docs/06_Decisions/ADR-099-…` | The decision + the native-read / deferred-write reasoning |
| `docs/BETA.md` | The "remember me" note + the per-device / iOS caveats |

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

- ADR-099 A persistent "remember me" cookie for the beta gate
- US-325 The cookie seam — `remember.py` (native read / component write, guarded)
- US-326 Wire the gate — restore-on-load (re-validated) + deferred write in `require_access`

**Stories Carried Forward:**

- None. (A "log out" link, a signed token, and `st.login()` are deferred follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
