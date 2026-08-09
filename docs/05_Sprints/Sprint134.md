# Sprint 134: Fix "remember me" persistence (the cookie doesn't survive a refresh)

**Dates:** 2026-08-09
**Status:** 📝 Planned — **repurposed by tester feedback** (the confirm-dialog is deferred; see below)
**Capacity:** ~⅓–½ session (a read-path fix + re-smoke), or a larger pivot (`st.login()`)
**Carried Over:** the confirm-on-Log-out step (deferred until persistence works)

> **Direction (owner):** the confirm-dialog was planned, but **tester feedback (2026-08-09)** is that the invite
> code + cookie **doesn't persist across a refresh on Safari *or* Chrome**. Fixing persistence comes first — a
> confirm on a logout that doesn't stick is pointless.

---

### ⚠️ Tester feedback → root cause (2026-08-09)

**Symptom:** pass the gate → refresh → **re-prompted** (both Safari and Chrome). "Remember me" (Sprint 132) isn't
working.

**Diagnosed from the component source:** `streamlit-cookies-controller` sets the cookie with `document.cookie`
**inside its own component iframe** (its only `window.parent` use is Streamlit's message channel, not the cookie).
But `remember.read()` reads via **`st.context.cookies`** — the cookies sent to the **Streamlit server on the
top-level page request**. Those are **different cookie jars**: the write lands in the iframe's jar, the native read
looks at the app's top-level jar, so `read()` never sees the write. That it fails on **both** browsers (not just
Safari/ITP) confirms it's **structural**, not a browser quirk. The Sprint 132 "native read" paired a *component*
write with a *native* read — the mismatch is the bug.

### 🔀 Reframed options (pick the direction before building)

- **Option 1 — Read through the *same* component that writes (recommended; smallest fix).** Make `remember.read()`
  use the controller's `.get()` (same iframe jar as `.set()`), instead of `st.context.cookies`. Jar-consistent by
  construction, regardless of the iframe-origin nuance. Keeps the exact **invite code + email + cookie** model.
  **Cost:** re-introduces the "loading run" (the component delivers the value on a rerun, not run 1), so a brief
  "checking…" placeholder is needed to avoid a gate flash — the very thing native-read avoided, now unavoidable.
  **Risk:** component cookies *can* still be flaky in some embeds; **you re-smoke it** — if it still fails, escalate
  to Option 2.
- **Option 2 — Pivot persistence to native `st.login()` (robust; bigger step).** Drop the cookie component;
  Streamlit's native OIDC persists a **first-party secure cookie automatically** (no iframe), so it survives a
  refresh reliably on all browsers — and gives **verified** identity (real emails, not self-declared). **Cost:**
  set up a Google (or other) OIDC client + `[auth]` secrets; the model shifts from "invite code" to "sign in with
  Google" (keep control via an email allowlist / count logins for the cap). This is the deferred hard-auth pivot —
  now *justified* because the cookie path failed. Bigger than a hobby-beta tweak, but it's the real fix.
- **Option 3 — Drop persistence for now; keep the gate session-only.** Revert the remember-me/cookie complexity;
  testers re-enter the code each session (today's behaviour, minus the cookie). Honest fallback — the friction
  returns, but the app is simple and correct — while you decide whether Option 2 is worth it.

**Recommendation:** **Option 1 first** (smallest change, keeps your model, diagnosis-targeted) → **you re-smoke on
Safari + Chrome**. If it still won't persist, **Option 2** is the robust answer. Option 3 is the clean retreat if
neither is worth it right now. **The confirm-dialog (old A/B) is deferred** until persistence actually works.

---

### 🎯 Sprint Goal (Option 1 — chosen)

**Objective:** "remember me" **survives a browser refresh** because read and write now share the **same cookie jar**
(both via the component); the one-run delivery delay is covered by a neutral placeholder, not a gate flash. Off by
default / fail safe unchanged. **Owner re-smokes on Safari + Chrome** to confirm the real roundtrip.

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-330 | **Read through the component** — `remember.read()` via `_controller().get()` + a one-run "loading" wait. | High | ✅ Done | ~⅓ session |
| US-329 | **Confirm on Log out** — deferred until the re-smoke confirms persistence works (see below). | Med | ⏸ Deferred | ~¼ session |

### ✅ Definition of Done

1. **Tests pass** — read/write/clear roundtrip through the *same* component (one jar); `available()` True/False;
   the gate waits **one run** (a "Checking your device…" placeholder, not the gate) when a component is present and
   the cookie hasn't arrived, then shows the gate (no infinite wait); **no component → no wait** (headless/blocked).
   Existing gate/logout tests still green (two updated to `available()=False` for the headless path). **864** total;
   ruff clean.
2. **Manual smoke (owner) — the real test** — ✅ **passed (2026-08-09, Safari + Chrome):** pass the gate → refresh →
   **stay in**. (Private tab / clear cookies → re-prompt; Log out → re-gate.)
3. **Docs** — this Sprint doc + Lessons; ADR-099 updated (read-path correction); PROJECT_STATUS; Architecture.

### 📝 Session Progress Log

- **US-330 (read through the component)** — **root-caused** the "doesn't persist on Safari or Chrome" report: the
  component writes `document.cookie` **inside its iframe**, but `remember.read()` read via **`st.context.cookies`**
  (the app's top-level request jar) — different jars, so the read never saw the write. **Fix:** `remember.read()`
  now uses `_controller().get()` (same jar as `write`), and a new `remember.available()` tells the gate whether a
  `None` read might be "still loading". Because the component delivers its value on a **rerun** (not run 1), added
  `access._maybe_wait_for_cookie()` — a **one-shot**, component-gated wait that shows a "🔑 Checking your device…"
  placeholder for one run instead of flashing the gate, then falls through (never hangs: no component → no wait).
  Wired into both restore helpers after a `None` read. Reverted the native-read path (removed `_request_cookies`).
  **+4 tests net** — read/write roundtrip through one jar · `available()` T/F · the loading placeholder · the gate
  after the wait · no-wait-without-a-component; two existing tests set `available()=False` for the headless path.
  ruff clean. **860 → 864.** *(No dependency/token change — a source change; Community Cloud redeploys on push.)*
  **Now: owner re-smokes on Safari + Chrome — this is the real proof (AppTest has no browser).**

---

<details><summary>Original plan (confirm-dialog — deferred)</summary>

> **Direction (owner):** the deferred Sprint 133 follow-up — a **confirmation** before "Log out" so a **mis-click**
> doesn't reset a device (clear the cookie + session). The `logout()` mechanism is done; this only adds a
> "are you sure?" in front of it.

---

### 🔎 Verified at planning (on real data + the code)

- **The mechanism is untouched.** `access.logout()` (deferred cookie clear + `_beta_forgotten` guard) already
  works and is tested. This sprint only gates the **call** to it behind a confirm — so US-327's guarantees hold;
  the risk is confined to `_render_account()`.
- **`st.dialog` is available on the pinned 1.61.1 and is AppTest-testable.** Verified: after clicking a button that
  opens an `@st.dialog`, the modal's buttons (e.g. "Log out"/"Cancel") appear in `at.button` and can be
  `.click().run()` — so a native confirm modal keeps the logout flow fully covered (no browser needed for the
  decision path; only the real cookie clear is a manual smoke, as today).
- **One existing test changes by design.** `test_clicking_the_sidebar_logout_re_gates` (US-328) currently expects
  the sidebar "Log out" to re-gate **immediately**; with a confirm step it must now **confirm** first
  (click "Log out" → the confirm's "Log out"). That's a one-line test update, not a regression — a separate test
  will assert the new "asks first / cancel keeps you in" behaviour.
- **Off by default is preserved.** The confirm lives inside `_render_account()`, which only renders when
  `gate_active()` and the session has passed — the open/public deploy is unchanged (byte-identical).

---

### 🎯 Sprint Goal

**Objective:** clicking the sidebar **"Log out"** now **asks to confirm**; only on confirm does it clear the
device (call `logout()`); **Cancel** keeps the tester signed in. Off by default; the logout mechanism unchanged.

#### Success Criteria
- [ ] **US-329 (the confirm step)** — `_render_account()`: clicking "Log out" opens a **confirm** ("Log out of the
      beta on this device? You'll need to re-enter to get back in.") with a **primary "Log out"** → `logout()` and
      a **"Cancel"** → dismiss (session unchanged). The existing `logout()` is called **only** on confirm.
- [ ] **No unintended drift** — open mode renders nothing; a passed session shows the same "Signed in … · Log out"
      until clicked; **Cancel** leaves `_beta_ok` set and calls **no** `remember.clear()`. The one US-328 test is
      updated to confirm-through; the rest of the **860** stay green; ruff clean.
- [ ] **Docs** — Sprint doc + Lessons; a note on ADR-099's follow-ups (confirm built); BETA.md (a word that
      Log out asks first); PROJECT_STATUS; Architecture; Roadmap/Backlog (mark the confirm done).

---

### 🧭 Design sketch — pick the mechanism

**No new ADR** — this extends ADR-099 (the logout family), no dependency, no architecture change.

**Option A — a native `st.dialog` modal (recommended).** Literally a "confirm dialog"; the clearest UX; testable.
```
@st.dialog("Log out?")
def _confirm_logout():
    st.write("This signs you out on **this device** — you'll re-enter the beta to get back in.")
    c1, c2 = st.columns(2)
    if c1.button("Log out", type="primary", use_container_width=True):
        logout()                       # deferred clear + rerun (US-327)
    if c2.button("Cancel", use_container_width=True):
        st.rerun()                     # dismiss, session unchanged
# in _render_account (sidebar):
if st.button("Log out", key="_beta_logout", use_container_width=True):
    _confirm_logout()                  # opens the modal
```

**Option B — an inline two-step in the sidebar (simpler, no modal).** Click "Log out" → the sidebar swaps to a
"Log out of the beta?" caption + **"Yes, log out"** / **"Cancel"** (driven by a `_beta_confirm_logout` session
flag). No modal semantics; everything stays in the sidebar.
```
if st.session_state.get(_CONFIRM):
    st.caption("Log out of the beta?")
    if st.button("Yes, log out", type="primary"): logout()
    if st.button("Cancel"): st.session_state.pop(_CONFIRM, None); st.rerun()
elif st.button("Log out", key="_beta_logout"):
    st.session_state[_CONFIRM] = True; st.rerun()
```

**Recommendation: Option A** — it's the "confirm dialog" you asked for, it's the conventional pattern, and I've
verified AppTest can drive the modal's buttons so the flow stays fully tested. Option B is the lighter-touch
fallback if you'd rather avoid a modal (everything inline in the sidebar). Either is one small story.

**Deferred (unchanged):** a **signed token** instead of the raw cookie value; native **`st.login()`** (hard
identity — the product path).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-329 | **The confirm step** — "Log out" asks to confirm; confirm → `logout()`, Cancel → dismiss. | Med | ⬜ To do | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you)

1. **Nothing to configure** — the confirm appears wherever the "Log out" link already does (a gate active).
2. **Smoke it (browser):** pass the gate → click **Log out** → a confirm appears → **Cancel** keeps you in;
   **Log out** signs you out and re-shows the gate (and a refresh stays gated).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — clicking "Log out" **does not** log out yet (session still passed, no `remember.clear()`);
   **confirming** calls `logout()` → re-gates + clears the cookie (spy); **Cancel** dismisses with the session
   intact. Open mode renders nothing (invariance). The US-328 immediate-re-gate test is updated to confirm-through.
   The **860** stay green (net); ruff clean.
2. **Manual smoke** — the browser flow above (Cancel keeps in · Log out re-gates · refresh stays gated).
3. **Docs updated** — Sprint doc + Lessons; ADR-099 follow-up note; BETA.md; PROJECT_STATUS; Architecture; Roadmap/Backlog.

---

### 📝 Session Progress Log

_(filled as the story lands)_

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ **fixed and verified in-browser.** Tester feedback said "remember me" didn't persist on Safari or
Chrome; root-caused it to a **cookie-jar mismatch** (component-iframe write vs native top-level read) and fixed the
**read** to go through the same component. **Owner re-smoke confirmed: works on Safari and Chrome (2026-08-09)** —
a refresh keeps the tester in. The `st.login()` escalation is no longer needed; the deferred confirm-on-Log-out
(US-329) is now unblocked.

**Delivered**
- **US-330** — `remember.read()` reads through `_controller().get()` (same jar as `write`); `remember.available()`
  + `access._maybe_wait_for_cookie()` handle the component's one-run delivery delay with a "Checking your device…"
  placeholder (one-shot, component-gated, never hangs); native-read reverted. +4 tests. ADR-099 corrected.
- **US-329 (confirm on Log out)** — **deferred**: pointless to polish a logout until persistence is confirmed.

**Verified (in tests)** — read/write/clear share one jar; `available()` gates the wait; the placeholder shows
(not the gate) when a component is present + the cookie hasn't arrived, and the gate shows after one run (no
infinite wait); no component → no wait. Existing gate/logout tests green (two set `available()=False` for the
headless path). **Not yet verified (needs a browser):** the actual cookie surviving a refresh — the owner re-smoke.

**Metrics** — 864 tests (860 → +4) · ruff + CI-parity green · **99 ADRs** (ADR-099 corrected, no new ADR) · 1
story built + 1 deferred, ~⅓ session.

**What went well**
- **Read the source, found the real cause** — the component writes `document.cookie` in its iframe; the native
  read looked at the app's top-level jar. Grepping the component build turned a mystery into a one-line diagnosis.
- **Targeted, reversible fix** — read through the same component (one jar); no dependency change, model unchanged.
- **The over-engineering was named and undone** — Sprint 132's "native read to avoid a flash" was the very thing
  that broke persistence; this reverts to component-read + the one-run wait it had tried to avoid, honestly.
- **The wait is safe** — one-shot + component-gated, so headless/blocked never hangs and the 864 stay green.

**Even better if**
- **The fix is unproven until the re-smoke** — AppTest can't run the component, so a green suite is necessary, not
  sufficient. If a refresh still re-prompts, the component-cookie path is a dead end in the Cloud iframe sandbox.
- **Escalation is pre-agreed** — if the re-smoke fails, go straight to **`st.login()`** (Option 2), not a third
  cookie iteration.
- **A small first-visit quirk** — a brand-new tester (no cookie) sees "Checking your device…" for one run before
  the gate. Harmless; could be suppressed later if it grates.

**Deferred / backlog** — the **confirm on Log out** (US-329, once persistence holds); **`st.login()`** as the
robust fallback if the re-smoke fails; a **signed token**; and the big body: **GW1 (2026-08-21) calibration** +
momentum + live manager import.

**Follow-up marker:** ✅ **owner re-smoke passed on Safari + Chrome (2026-08-09)** — remember-me is working end-to-
end. Next: the deferred **US-329 confirm-on-Log-out** is unblocked; `st.login()` stays a future *option*, not a
needed escalation.

---

### 📌 For Tony

- **Mechanism:** a native **modal** (Option A, recommended) or an **inline** sidebar two-step (Option B)?
- **Wording** of the confirm — "Log out of the beta on this device?" OK, or shorter?

</details>
