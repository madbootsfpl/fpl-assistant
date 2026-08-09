# Sprint 135: Confirm on Log out + surface ☁ Save/Load in the Squads sidebar

**Dates:** 2026-08-09
**Status:** 📝 Planned (2 stories · no new ADR — extends ADR-099 / ADR-094)
**Capacity:** ~½ session (two small UI changes)
**Carried Over:** US-329 (confirm on Log out — deferred from Sprint 134, now that remember-me is verified)

> **Direction (owner):** (1) build the **confirm on "Log out"** (Sprint 134 US-329, Option A — an `st.dialog`
> modal) now that remember-me is verified working; (2) tester ask — the **☁ Save / Load across devices** should be
> visible from the **Squads tab / sidebar**, not buried under the **My Squad** sub-view.

---

### 🔎 Verified at planning (on real data + the code)

- **US-329 — `st.dialog` is available (1.61.1) and AppTest-drivable.** Verified: after clicking a button that opens
  an `@st.dialog`, the modal's buttons appear in `at.button` and can be `.click().run()`. The `logout()` mechanism
  (US-327) is untouched — we only gate the *call* behind a confirm, so its guarantees hold.
- **US-331 — the ☁ block is a self-contained, moveable widget.** In `views/squads.py` (lines ~393–433) the
  "☁ Save / Load across devices" expander needs only the **active squad** (from session, via `active_squad()`) +
  `cloud_store` — no players/photos. So it can move to **`squads.render_sidebar()`** (the "Your squad" sidebar —
  active-name + upload + manager-ID import), which renders on the **Squads tab regardless of sub-view**. That's the
  owner's "side tab". It stays **secret-gated** (`cloud_store.is_configured()`) — off on the read-only deploy.
- **It must *move*, not duplicate.** The widgets use fixed keys (`cloud_handle`/`cloud_save`/…); rendering in both
  the sidebar and My Squad would be a duplicate-key error. So it moves to the sidebar and leaves the My Squad body
  (a one-line pointer caption there is optional). The existing My-Squad cloud tests get re-pointed to the sidebar.
- **Save needs a squad; Load doesn't.** In the sidebar it may render with **no active squad** (e.g. on Build before
  building) — **Save** is disabled with a hint, **Load** always works (it brings a squad in and sets it active).

---

### 🎯 Sprint Goal

**Objective:** (1) clicking **"Log out"** asks to confirm (Option A modal) — Cancel keeps you in; (2) **☁ Save /
Load across devices** is visible in the **Squads sidebar** on any sub-view, moved out of the My Squad body. Both
off by default (gate-active / store-configured); the analytics + `cloud_store`/`logout` mechanisms unchanged.

#### Success Criteria
- [x] **US-329 (confirm on Log out)** — `access._render_account()`: clicking "Log out" opens an `@st.dialog`
      confirm ("Log out of the beta on this device? You'll re-enter to get back in.") with a **primary "Log out"**
      → `logout()` and **"Cancel"** → dismiss (session unchanged). Confirm/Cancel keyed so tests target them. The
      US-328 immediate-re-gate test is updated to confirm-through; a new test asserts "asks first / Cancel keeps in".
- [ ] **US-331 (☁ Save/Load in the sidebar)** — extract the cloud block into `squads.render_cloud_sync()` and call
      it in `render_sidebar()` (under "Your squad"), reading the active squad from session; **Save** disabled with
      a hint when no squad is active, **Load**/**Clear** as today. Removed from the My Squad body (optional pointer
      caption). Secret-gated (hidden unless the store is configured). The My-Squad cloud tests move to the sidebar.
- [ ] **No unintended drift** — open/unconfigured deploys render nothing new; the analytics + server-write posture
      (ADR-094: the sole squad-save write stays opt-in, secret-gated) unchanged; the existing **864** stay green
      (net); ruff clean.
- [ ] **Docs** — Sprint doc + Lessons; ADR-099 follow-up note (confirm built); CLOUD_SQUADS.md + Help (the ☁ is in
      the Squads sidebar now); PROJECT_STATUS; Architecture; Roadmap/Backlog.

---

### 🧭 Design sketch

**No new ADR** — US-329 extends ADR-099 (logout family); US-331 extends ADR-094 (a UI relocation of the existing
cross-device save, same secret-gated single write). No dependency, no analytics change.

**US-329 (Option A).**
```
@st.dialog("Log out?")
def _confirm_logout():
    st.write("This signs you out on **this device** — you'll re-enter the beta to get back in.")
    c1, c2 = st.columns(2)
    if c1.button("Log out", type="primary", key="_beta_logout_yes", use_container_width=True): logout()
    if c2.button("Cancel",  key="_beta_logout_no",  use_container_width=True): st.rerun()
# in _render_account: clicking the sidebar "Log out" opens it instead of logging out immediately
if st.button("Log out", key="_beta_logout", use_container_width=True): _confirm_logout()
```

**US-331.** Move `views/squads.py`'s cloud block into `squads.render_cloud_sync()` (beside `render_sidebar`),
`with st.sidebar:` under "Your squad"; `squad = active_squad()`; **Save** `disabled=not (clean and squad)` with a
"build or load a squad first" hint; **Load**/**Clear** unchanged (Load sets the active squad). `render_sidebar()`
calls it (secret-gated). Remove the block from `render_my_squad`; leave a caption pointing to the sidebar.

**Deferred (unchanged):** a **signed token**; native **`st.login()`** (hard identity — the product path).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-329 | **Confirm on Log out** — an `st.dialog` modal in front of `logout()`. | Med | ✅ Done | ~¼ session |
| US-331 | **☁ Save/Load in the Squads sidebar** — move the cross-device block into `render_sidebar()`. | Med | ⬜ To do | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — US-329: clicking "Log out" opens a confirm (session still passed, no `remember.clear()`);
   confirm → `logout()` re-gates + clears; Cancel → dismiss, session intact; open mode renders nothing. US-331:
   the ☁ controls render in the **sidebar** when the store is configured (a test drives Save/Load/Clear there,
   `cloud_store` monkeypatched); Save disabled with no active squad; hidden when unconfigured; not in the My Squad
   body. The **864** stay green (net); ruff clean.
2. **Manual smoke** — Log out → confirm/Cancel behave; on the Squads tab the ☁ Save/Load shows in the sidebar on
   every sub-view; Save a handle → Load on another device (as before).
3. **Docs updated** — Sprint doc + Lessons; ADR-099 note; CLOUD_SQUADS.md + Help; PROJECT_STATUS; Architecture.

---

### 📝 Session Progress Log

- **US-329 (confirm on Log out)** — added `access._confirm_logout()` (`@st.dialog("Log out?")`): a modal with a
  primary **"Log out"** → `logout()` and **"Cancel"** → dismiss; the sidebar "Log out" now **opens** it instead of
  logging out on the click. **AppTest wrinkle found + fixed:** a dialog only stays interactive while its body is
  re-called each run, and AppTest doesn't auto-persist an open dialog — so clicking the modal's "Log out" on the
  next run did nothing (the opener wasn't re-clicked). Fixed with a `_beta_confirming` session flag: the opener
  sets it, `_render_account` re-calls the dialog while it's set, and each choice pops it (also more robust in the
  real browser). +3 AppTests (asks-to-confirm-not-logout · confirm → re-gates + clears · Cancel → stays signed in,
  no clear); the old immediate-re-gate test became the "asks to confirm" one. ruff clean. **864 → 866.**
  (US-331 next: move the ☁ Save/Load block into the Squads sidebar.)

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony

- **US-331 placement** — the **Squads sidebar** (under "Your squad") is my read of "side tab"; confirm, or would
  you rather it sit at the **top of the Squads tab** (above the sub-view control)?
- **Keep a pointer** in My Squad ("☁ Save/Load is in the sidebar"), or remove it cleanly?
