# Sprint 133: A "log out" link — reset a device / switch tester

**Dates:** 2026-08-09
**Status:** 📝 Planned (2 stories · no new ADR — extends ADR-099)
**Capacity:** ~⅓ session (a sidebar control + a session/cookie clear, mirroring the Sprint 132 deferred-write pattern)
**Carried Over:** none

> **Direction (owner):** the deferred follow-up from Sprint 132 — the `remember.clear()` plumbing exists; add a
> small **"log out"** control so a tester can **reset a shared device** (or switch accounts) and re-show the gate.
> Backlog: *"low effort; UI-placement is the only open question."*

---

### 🔎 Verified at planning (on real data + the code)

- **`require_access()` runs on all 9 surfaces** (Home + the 8 pages), right after `st.set_page_config`. So a
  logout control rendered *inside* `require_access` appears on **every page with zero page edits**, and stays
  **off by default** (it only renders when a gate mode is active *and* the session has passed).
- **`with st.sidebar:` is the house pattern** — `status.py::render_data_status` already renders the freshness
  caption + the local refresh button in the sidebar on every page. The logout control sits naturally at the foot
  of the sidebar the same way.
- **Clearing the cookie hits the *same* rerun trap as writing it.** `remember.clear()` renders a component
  (`_controller().remove(...)`), and a `st.rerun()` immediately after would **discard it** before it reached the
  browser — so the cookie wouldn't actually clear and a refresh would silently log the user back in. The fix is
  the **mirror of Sprint 132's deferred write**: render the clear on a *clean* run (before the gate's `st.stop()`,
  which — unlike `st.rerun()` — keeps the run's output).
- **A stale cookie could re-admit within the same logout run.** `remember.read()` is native (`st.context.cookies`)
  and still returns the **old** cookie until the *next* HTTP request — so logging out must **suppress the
  cookie-restore for the rest of this session** (a `_beta_forgotten` flag), else the gate would re-admit from the
  cookie we're mid-way through clearing. The clear persists to the browser for the *next* load; the flag covers
  *this* session.
- **Session flags are known:** `_beta_ok` (passed), `_beta_email` (registered email), `_beta_remember` (the
  pending write). Logout clears all three, sets `_beta_forgotten`, and queues the cookie clear.

---

### 🎯 Sprint Goal

**Objective:** a passed tester sees a small **"Signed in … · Log out"** control in the sidebar; clicking it
**clears the remember-me cookie + the session** and re-shows the gate — reliably (the clear actually persists), on
every page, and **only** when a gate is active (open mode is untouched, byte-identical).

#### Success Criteria
- [x] **US-327 (the logout mechanism)** — in `access.py`: `gate_active()` (True iff registration *or* shared-code
      mode is configured), `logout()` (set `_beta_forgotten`, clear `_beta_ok`/`_beta_email`/`_beta_remember`,
      queue the cookie clear, rerun), and `_flush_clear()` (render `remember.clear()` once on a clean run — the
      mirror of `_flush_remember`). The cookie-restore helpers **short-circuit when `_beta_forgotten`** so a
      just-logged-out session can't be re-admitted from the stale cookie. Unit/AppTest-covered.
- [x] **US-328 (the sidebar control)** — `_render_account()`: when `gate_active()` and the session has passed,
      render at the foot of the sidebar a caption (**"Signed in as {email}"** in registration mode, else **"Signed
      in to the beta"**) + a **"Log out"** button → `logout()`. Wired into `require_access` (render on the passed
      branch; `_flush_clear()` at the top). **Open mode → nothing renders.** AppTest-covered.
- [ ] **No unintended drift** — open mode (no `FPL_ACCESS_CODE`, no `FPL_USER_CAP`) renders **no** sidebar control
      and the gate is **byte-identical**; the existing **852** stay green (an invariance test pins the open path);
      ruff clean.
- [ ] **Docs** — Sprint doc + Lessons; a note appended to **ADR-099** follow-ups (logout built); BETA.md (a line:
      testers can "Log out" to reset a shared device); PROJECT_STATUS; Architecture; Roadmap/Backlog (mark done).

---

### 🧭 Design sketch

**No new ADR — this extends ADR-099.** It adds no dependency, no new architecture, and no modelling; it reuses the
existing `remember.clear()` + the deferred-side-effect pattern the ADR already established. The design is recorded
here and appended to ADR-099's follow-ups. *(If you'd prefer a formal ADR-100 for the logout/session-suppression
decision, say so and I'll gate it first.)*

**US-327 — the mechanism (`access.py`).**
```
def gate_active() -> bool:          # registration (cap + store) OR shared-code configured; else open
def logout() -> None:               # _beta_forgotten=True; pop _ok/_email/_remember; _beta_clear=True; st.rerun()
def _flush_clear() -> None:         # pop _beta_clear -> remember.clear()  (render on a clean run, like _flush_remember)
```
`_remembered_code` / `_remembered_registration` gain a guard: **if `_beta_forgotten` → return False** (ignore the
cookie this session). `require_access` calls `_flush_clear()` at the very top (before the passed-check and the
gate), so on the post-logout run the remove component renders and survives the gate's `st.stop()`.

**US-328 — the control (`access.py`, sidebar).**
```
def _render_account() -> None:
    if not gate_active(): return                    # off by default — open mode shows nothing
    with st.sidebar:
        email = st.session_state.get(_EMAIL)
        st.caption(f"Signed in as {email}" if email else "Signed in to the beta")
        if st.button("Log out", key="_beta_logout", use_container_width=True):
            logout()
```
Wired into `require_access`: on the **passed** branch (`if _ok: _flush_remember(); _render_account(); return`).
One click resets the device — no confirm dialog (that *is* the intent); a shared handle isn't security.

**Why it's reliable (the two traps, handled):**
| Trap | Handling |
|------|----------|
| `st.rerun()` after `remember.clear()` discards the remove | **Defer** the clear to a clean run (`_flush_clear`, before `st.stop()`) — mirrors the Sprint 132 write |
| Native read still returns the old cookie this run | **`_beta_forgotten`** suppresses cookie-restore for the rest of the session; the clear persists for the next load |

**Deferred (unchanged):** a **signed token** instead of the raw value; native **`st.login()`** (hard identity —
the product path). A "log out everywhere / all devices" is inherently per-device here (no server session) — out of
scope; `st.login()` is the answer if that's ever needed.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-327 | **The logout mechanism** — `gate_active`/`logout`/`_flush_clear` + `_beta_forgotten` suppressor. | High | ✅ Done | ~¼ session |
| US-328 | **The sidebar control** — `_render_account()` ("Signed in as X · Log out") wired into `require_access`. | High | ✅ Done | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you)

1. **Nothing to configure** — the "Log out" link appears automatically for testers whenever a gate is active
   (registration or shared-code). It's hidden on the open/public deploy.
2. **Smoke it (browser):** pass the gate → a **"Signed in … · Log out"** appears in the sidebar → click it → the
   gate returns; **refresh** → still gated (the cookie was actually cleared). *(This rides on the Sprint 132 write
   smoke — if "remember me" persists correctly, so does the clear.)*

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `logout()` clears the session flags, sets `_beta_forgotten`, and queues the clear;
   `_flush_clear()` calls `remember.clear()` once; a forgotten session is **not** re-admitted from a still-present
   cookie (monkeypatched `remember.read`); the sidebar control renders when gated+passed and **not** in open mode;
   open mode stays **byte-identical** (invariance). Existing **852** green; ruff clean.
2. **Manual smoke** — the browser flow above: log out → gate returns → refresh stays gated; in registration mode
   the caption names the email.
3. **Docs updated** — Sprint doc + Lessons; ADR-099 follow-up note; BETA.md; PROJECT_STATUS; Architecture; Roadmap/Backlog.

---

### 📝 Session Progress Log

- **US-327 (the logout mechanism)** — added to `access.py`: **`gate_active()`** (True iff registration or
  shared-code is configured — the account UI stays off on the open deploy), **`logout()`** (set `_beta_forgotten`,
  drop `_beta_ok`/`_beta_email`/`_beta_remember`, queue `_beta_clear`, `st.rerun()`), and **`_flush_clear()`**
  (pops `_beta_clear` → `remember.clear()`, rendered on a clean run — `require_access` calls it at the very top,
  before any `st.stop()`, which keeps the run's output unlike `st.rerun()`; the mirror of `_flush_remember`). The
  cookie-restore helpers (`_remembered_code`/`_remembered_registration`) gained a **`_beta_forgotten` guard** →
  a just-logged-out session ignores the (not-yet-cleared) native-read cookie, so it can't re-admit before the clear
  reaches the browser on the next request. **+4 tests** — `gate_active` (open→False · code→True · registration→
  True) + a **logout roundtrip** (an `AppTest.from_string` harness: a valid cookie admits → click Log out → the
  cookie clear is rendered, the session is dropped, `_beta_forgotten` is set, and the gate re-shows *despite* the
  stale cookie still reading valid). ruff clean. **856** total. (US-328 adds the sidebar "Log out" control that
  calls `logout()`.)
- **US-328 (the sidebar control)** — added `_render_account()`: when `gate_active()` and the session has passed,
  it renders at the foot of the sidebar a caption (**"🔓 Signed in as {email}"** in registration mode, else **"🔓
  Signed in to the beta"**) + a full-width **"Log out"** button → `logout()`. Wired into `require_access` on the
  passed branch. **A gap found + fixed:** the control must also render on the **cookie-admit** run (where `_OK` is
  set inside `_remembered_*` and `require_access` returns *before* the top branch) — otherwise after a refresh the
  "Log out" wouldn't appear until the next interaction; added `_render_account()` to both admit paths. **Off by
  default** — open mode (`gate_active()` False) renders nothing (an explicit test). **+4 AppTests** — no control
  in open mode · control + "Signed in" caption when passed · the caption **names the email** in registration mode
  · clicking the **real sidebar button** re-gates end-to-end on Home. ruff clean. **860** total.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ a tester can **reset a shared device / switch accounts** — a sidebar **"Log out"** clears the
"remember me" cookie + the session and re-shows the gate, reliably (the clear actually persists), on every page,
and **only** when a gate is active (the open deploy is untouched). The `remember.clear()` plumbing from Sprint 132
is now wired to a control.

**Delivered**
- **US-327** — the mechanism in `access.py`: `gate_active()` · `logout()` (drop the session flags, queue a
  deferred cookie clear, rerun) · `_flush_clear()` (render `remember.clear()` on a clean run — the mirror of
  `_flush_remember`) · a `_beta_forgotten` guard so a just-logged-out session can't be re-admitted from the
  still-present native-read cookie. +4 tests.
- **US-328** — `_render_account()`: a sidebar caption ("Signed in as {email}" / "Signed in to the beta") + a
  "Log out" button → `logout()`, wired into `require_access` (incl. the cookie-admit run). +4 AppTests.

**Verified** — open mode → no control, the gate byte-identical (the existing 4 access tests + a new explicit
"no control in open mode"); a valid cookie admits + shows the control; logout clears the session, renders the
cookie clear, sets `_beta_forgotten`, and re-gates **despite** the stale cookie still reading valid; the real
sidebar button re-gates end-to-end on Home. *(The real browser cookie-clear roundtrip = the manual smoke, riding
on the Sprint 132 write smoke.)*

**Metrics** — 860 tests (852 → +8: US-327 +4, US-328 +4) · ruff + CI-parity green · **99 ADRs** (no new ADR — a
recorded extension of ADR-099) · 2 stories, ~⅓ session.

**What went well**
- **Reused the deferred-cookie pattern** — the logout clear is the exact mirror of the Sprint 132 write (defer to
  a clean run so `st.rerun()` can't discard it); no new machinery, just the symmetric case.
- **Named the second trap up front** — a native-read cookie still reads valid the moment you log out, so a
  `_beta_forgotten` session flag suppresses re-admit until the clear lands on the next request. Designed in, tested.
- **Off by default preserved** — the account UI is gated on `gate_active()`, so the public deploy renders nothing
  and the invariance holds (byte-identical, pinned by a test).
- **Caught the admit-run gap** — the control has to render on the cookie-admit run, not just the next rerun, or
  "Log out" would be missing right after a refresh. Fixed before it could ship.

**Even better if**
- **The clear roundtrip is the one untested edge** — like the write, it needs a browser; the manual smoke covers
  it, and it shares fate with the Sprint 132 write smoke (if that persists, so does the clear).
- **No confirm on Log out** — a single click resets the device (that *is* the intent for a shared device); if a
  mis-click becomes a complaint, a lightweight confirm is a small follow-up.
- **"Log out everywhere" isn't possible** here (no server session) — per-device by design; `st.login()` is the
  answer if verified cross-device identity is ever needed.

**Deferred / backlog** — a **confirm** on Log out (only if wanted); a **signed token** instead of the raw cookie
value; native **`st.login()`** (hard identity — the product path); and the big body: **GW1 (2026-08-21)
calibration** (set-piece/DefCon/form) + momentum + live manager import.

---

### 📌 For Tony

- **Wording:** "Log out" · "Not you? Log out" · "Forget me on this device" — which reads best?
- **Placement confirmed** (sidebar foot, every page)?
- **ADR:** happy to extend ADR-099 (no new ADR), or want a formal ADR-100 gate first?
