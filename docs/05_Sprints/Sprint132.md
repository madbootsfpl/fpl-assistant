# Sprint 132: "Remember me" — persist the passed gate across a browser refresh

**Dates:** 2026-08-09
**Status:** 🚧 In progress (ADR-099 accepted · 2 stories to build)
**Capacity:** ~½ session (one small dependency + a guarded cookie seam + wiring the gate)
**Carried Over:** none

> **Direction (owner):** *"every time you refresh your page in browser you have to type the access code and your
> email in again. I really wanted a way to do this once to register and then you're done."* Chosen shape:
> **Option 1 — a browser "remember me" cookie** (confirmed works on phones/tablets, per-device). Register once
> per device; a refresh (or a browser restart) keeps you in.

---

### 🔎 Verified at planning (on real data + the code)

- **Root cause confirmed.** `access.require_access` remembers a pass only in `st.session_state[_beta_ok]`.
  `st.session_state` survives reruns and page navigation **within a session**, but is **wiped on a full browser
  refresh (F5) / new tab** — so the gate re-prompts. Nothing about the *store* is at fault; the pass just isn't
  persisted client-side. A cookie is the missing piece.
- **Streamlit can *read* cookies natively but not *write* them.** `st.context.cookies` exists on the pinned
  **1.61.1** (read-only, request cookies). **Setting** a cookie has no native API — and a DIY `document.cookie`
  from `st.components.v1.html` runs in a **sandboxed iframe**, so it sets the *iframe's* cookie, not the app's
  first-party one. Reliable set/read needs a small **cookie component** that bridges the iframe↔parent. → one
  dependency; that trade is the ADR.
- **The cookie only ever *remembers a pass the user already made*** — it is **not a new way in**. On load we
  **re-validate**: registration mode → `user_store.is_registered(email)` (a removed tester's stale cookie fails);
  shared-code mode → the cookie value must equal the *current* `FPL_ACCESS_CODE` (rotating the code invalidates
  every remember cookie). So the gate's security posture is unchanged — the cookie is a convenience, re-checked.
- **Off by default holds.** No component installed, cookies blocked (private mode, iOS ITP expiry), or the read
  failing → the seam returns `None` and the gate is **exactly today's** (re-prompt). The 839 stay byte-identical;
  worst case is the current annoyance, never a broken app.
- **The known component wrinkle** (verified against how these components work): the value arrives on a **rerun**,
  not the first script run — so a cold refresh runs once with `None` before the cookie is delivered. We render the
  reader **early** and treat "still loading" as *don't show the gate yet* to avoid a flash of the code prompt.
- **Mobile reality (told to the owner, recorded here):** **per-device** (register once per phone/tablet/laptop);
  **private/incognito won't persist**; **iOS Safari's ITP** caps client-JS cookies at **~7 days** (so iPhone/iPad
  users re-register weekly — Android/desktop get the full ~30). These are documented, not bugs.

---

### 🎯 Sprint Goal

**Objective:** a tester who has passed the gate on a device is **remembered across a browser refresh and restart**
(≈30 days, ~7 on iOS) — no re-typing the code/email — while the gate stays **off by default**, **re-validated**,
and **byte-identical** when cookies are unavailable.

#### Success Criteria
- [x] **ADR-099 (the gate)** — record the **persistent "remember me" cookie**: the dependency choice (a Streamlit
      cookie component — native read / no native write, iframe isolation → why a component); **what's stored**
      (registration → the tester's own email; shared-code → the code) and **why re-validated on load** (removed
      tester / rotated code → the cookie fails); **TTL ~30 days** + the **iOS ITP ~7-day** cap; **privacy** (a
      first-party cookie on the user's own device, their own email — minimal, consented); **graceful degradation**
      (unavailable → today's per-session gate, 839 byte-identical); that it is a **convenience over** ADR-087/098,
      **not** a new access path and **not** the `st.login()` hard-auth pivot (still deferred).
- [x] **US-325 (the cookie seam)** — `web_streamlit/remember.py`: a thin, **guarded** wrapper over the cookie
      component exposing `read() -> str | None`, `write(value, days=30)`, `clear()`. Every call is `try/except`
      and **no-ops / returns `None` if the component is missing or errors** (so import + all non-browser paths are
      safe). Adds the one dependency to `requirements.txt` (+ the rebuild-token bump so Community Cloud reinstalls).
      Unit-tested with a **fake controller** (roundtrip) and with the component **absent** (no-op / `None`).
- [ ] **US-326 (wire the gate)** — in `access.require_access`: **on load**, before prompting, `remember.read()` →
      validate per mode (`is_registered` / `== code`) → on success set `session[_beta_ok]` (+ `_beta_email`) and
      skip the gate; **on a successful gate pass**, `remember.write(<email|code>)`; handle the **first-load
      loading run** (don't flash the gate). **Off by default / unavailable → the existing gate, unchanged.** Tests
      (monkeypatched `read`/`write`): restore-admits in both modes, a **stale/invalid** cookie → the gate still
      shows, `write` is called on a fresh pass, and the **839 stay byte-identical** when `read()` returns `None`.
- [ ] **No unintended drift** — the cookie is **opt-in by availability** and **re-validated**; existing **839**
      green (a no-op without a readable cookie — an invariance test pins it); ruff clean.
- [ ] **Docs** — ADR-099 + the index; **BETA.md** (a short "remember me" note — the dependency, the ~30-day /
      iOS-7-day + per-device caveats, how to *not-remember*: private mode / clear cookies); **CLOUD_SQUADS.md**
      (unaffected, but note the new dep if relevant); PROJECT_STATUS; Architecture; README (the dependency line).

---

### 🧭 Design sketch

**ADR-099.** A **client-side convenience** layered on the ADR-087/098 gate, not a new mode. Native `st.context.
cookies` reads but can't write, and an iframe DIY write is isolated — so a small cookie component is the honest
cost. The cookie **stores what proves the pass** and the load path **re-validates** it, so it grants nothing the
live gate wouldn't: a pruned tester or a rotated code invalidates the cookie. **Graceful degradation** is the
spine — any failure falls back to today's session gate (839 byte-identical). `st.login()` (native persistence +
verified identity) stays the deferred hard-auth upgrade; this is the cheap step that removes the refresh
annoyance without it.

**US-325 — `remember.py` (the seam).** Isolates the dependency so `access.py` stays clean and the failure mode is
one place:
```
COOKIE = "fpl_beta"          # first-party; value = the registered email (reg mode) or the code (shared-code mode)
def read() -> str | None:    # returns the cookie value, or None if unavailable / still loading / error
def write(value, days=30):   # best-effort set with a ~30-day expiry; no-op if unavailable
def clear():                 # best-effort delete (for a future "not you? / log out")
```
The component (candidate: **`streamlit-cookies-controller`** — small, focused, maintained; exact pick + 1.61.1
compatibility **verified at build**) is imported **lazily inside** these functions, wrapped in `try/except` →
missing/erroring ⇒ `read()` is `None`, `write`/`clear` no-op. This is what makes every non-browser path (CI,
AppTest, private mode) safe and keeps the gate a no-op without a cookie.

**US-326 — wire `require_access`.** New shape at the top of the function:
```
if session[_beta_ok]: return
val = remember.read()
if val is _still_loading: <render the reader, don't show the gate this run>   # avoid the first-load flash
if val and _valid_for_mode(val):        # reg: user_store.is_registered(val); code: val == FPL_ACCESS_CODE
    session[_beta_ok] = True; (session[_beta_email] = val in reg mode); return
... existing gate ...                    # on success, additionally: remember.write(<email|code>); rerun
```
`_valid_for_mode(val)` is a **pure** helper (mode + value + code/cap in, bool out) — the unit-testable core;
`remember.read/write` are the monkeypatched seam. The cookie roundtrip in a real iframe = **manual smoke** (AppTest
has no browser).

**Deferred:** a "not you? / log out" link (uses `remember.clear()` — the plumbing lands this sprint, the UI later);
a signed/opaque token instead of the raw value (needs server-side mapping — over-engineering for a hobby beta);
native `st.login()` (the hard-auth path).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-099 | **Persistent "remember me" cookie** — the dependency + TTL + re-validation + degradation (the gate). | High | ✅ Done | gate |
| US-325 | **The cookie seam** — `remember.py`: guarded `read`/`write`/`clear` over a cookie component (+ the dep). | High | ✅ Done | ~¼ session |
| US-326 | **Wire the gate** — restore-on-load (re-validated) + set-on-pass in `require_access`; degrade gracefully. | High | ⬜ To do | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you — after the deploy)

1. **Nothing to configure** — "remember me" turns on automatically once deployed (the dependency ships in
   `requirements.txt`). It layers on whatever gate you already run (registration or shared-code).
2. **Smoke it:** pass the gate on your phone → **refresh** → you stay in (no re-typing). To *not* be remembered,
   use a private/incognito tab or clear the site's cookies. On iPhone/iPad expect to re-register ~weekly (Safari
   ITP); Android/desktop keep it ~30 days.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `remember.read()` returns a set value via a fake controller and **`None` when the component is
   absent** (monkeypatched import); `write`/`clear` no-op safely. The gate: a valid cookie **admits without the
   prompt** in both modes (monkeypatched `read`), a **stale/wrong** cookie (`is_registered` False / `!= code`)
   **still shows the gate**, a fresh pass **calls `remember.write`**, and with `read()` → `None` the gate is
   **byte-identical to today** (an invariance test). Existing **839** stay green; ruff clean.
2. **Manual smoke** — deployed: pass the gate → **F5 / reopen the tab** → still in (both a phone and desktop);
   private tab → re-prompts; clear cookies → re-prompts. Confirm no flash of the code prompt on a cold refresh.
3. **Docs updated** — ADR-099 + index; BETA.md ("remember me" + caveats); PROJECT_STATUS; Architecture; README
   (the dependency); CLOUD_SQUADS note if relevant.

---

### 📝 Session Progress Log

- **ADR-099 (the gate)** — wrote `docs/06_Decisions/ADR-099-remember-me-cookie.md` (Accepted). Records the
  **persistent "remember me" cookie** layered on ADR-087/098: **what's stored** (registration → the tester's own
  email; shared-code → the code) and **why re-validated on load** (`is_registered` / `== FPL_ACCESS_CODE` → a
  pruned tester / rotated code invalidates it) — so it **grants no new access**; the **dependency rationale**
  (1.61.1 reads cookies via `st.context.cookies` but can't write; a DIY `document.cookie` is iframe-sandboxed →
  one small cookie component, quarantined behind a guarded `remember.py` seam that no-ops when absent); **TTL ~30d
  + iOS ITP ~7d** + per-device / private-mode caveats; **privacy** (first-party, the user's own data); **off by
  default / fail safe** (unavailable → today's gate, 839 byte-identical, invariance-pinned); alternatives
  (URL token = URL-as-credential ✗, DIY iframe cookie ✗, `st.context.cookies` alone can't write, `st.login()` =
  the deferred hard-auth path, a signed token = over-engineering). Added to the ADR index. No code — suite
  unchanged at **839**. (US-325 builds the seam; US-326 wires the gate.)
- **US-325 (the cookie seam)** — added `src/web_streamlit/remember.py`: a **guarded** wrapper over the cookie
  component exposing `read() → str | None` · `write(value, days=30)` · `clear()` (cookie `fpl_beta`, `TTL_DAYS=30`).
  The dependency (`streamlit-cookies-controller==0.0.4`) is **lazily imported inside `_controller()`** and every
  public call is `try/except` → a missing/erroring component ⇒ `read()` is `None` and `write`/`clear` **no-op**
  (import/CI/AppTest/private-mode all safe; the gate falls back to today's per-session behaviour). Verified the
  component at build: it imports without a `ScriptRunContext` (a warning, not a crash), and its `__init__` renders
  the read component **once per session** (caches into `st.session_state['cookies']`) — so constructing a fresh
  controller per read/write is collision-free, and a cold run returns the `{}` default (the value lands on the
  follow-up rerun — the "loading run" US-326 handles). Added the pinned dep to `requirements.txt` + bumped the
  rebuild-token (`2026-08-09-01`) so Community Cloud reinstalls. **+8 tests** (`tests/test_remember.py`, via a
  fake controller + a broken-controller seam): write→read roundtrip, clear forgets, none-when-unset, empty-value
  no-op, a multi-day `max_age`, and graceful degradation (unavailable → `None`/no-op; a runtime error swallowed).
  ruff clean. **847** total. (US-326 wires it into `require_access`.)

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony

- **Biggest learning this sprint:**
- **Happy with ~30-day / iOS-7-day per-device remembering (vs the deferred `st.login()`)?:**
- **Want the "not you? / log out" link built next, now the `clear()` plumbing exists?:**
