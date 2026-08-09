# Sprint 130: Beta-readiness tidy — FormSubmit docs + a "handle taken?" hint

**Dates:** 2026-08-31 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (a docs story + a small persistence UX polish — low risk)
**Carried Over:** none

> **Direction:** with the beta going live, tidy two loose ends — **document the FormSubmit setup** (the
> Origin/activation gotchas just fixed in code) and add a **"handle taken?" hint** on the ☁ cross-device Save.

---

### 🔎 Verified at planning (on real data + the code)

- **The FormSubmit fix has doc debt.** Two blockers were fixed in code — the relay must use `/ajax/<addr>`, the
  app now sends an **`Origin`/`Referer`** header (FormSubmit rejects server-side POSTs without one — the "web
  server" error), and the form needs a **one-time "Activate Form"** click — but `docs/BETA.md` §1B still just says
  "click the confirmation email." A tester/owner following it would hit the same wall. New secret
  `FPL_FEEDBACK_ORIGIN` (default the app URL) is undocumented.
- **The ☁ Save is silent about collisions.** `cloud_store` has `save_squad`/`load_squad`/`delete_squad` (Save is
  an **upsert** — it overwrites). The Save handler just says "Saved as X" whether or not that handle already had a
  squad — so a tester could unknowingly overwrite someone else's (a handle isn't private, ADR-094). A cheap
  existence check (on the Save *click*, not per rerun) can say **new vs overwrite**.
- **No analytics, no drift** — US-320 is docs; US-321 is a display/UX touch on the (dormant, secret-gated) ☁
  expander; the read-only guardrail + `cloud_store` write path are unchanged.

---

### 🎯 Sprint Goal

**Objective:** the beta is easier to stand up (a correct, complete FormSubmit runbook) and the cross-device Save
is clearer (it tells you when a handle already exists). Small, low-risk; no analytics change.

#### Success Criteria
- [ ] **US-320 (document the FormSubmit setup)** — rewrite `docs/BETA.md` §1B + the secrets list: the
      **`/ajax/<addr>`** endpoint, the **`Origin`/`Referer`** requirement for a server-side POST +
      **`FPL_FEEDBACK_ORIGIN`** (set to your app URL if it isn't the default), the **"Activate Form"** one-time
      click (and the tell-tale "web server" / "needs Activation" messages), and that the form now shows the
      **real** relay result. Note FormSubmit needs **no key** (that's Web3Forms).
- [ ] **US-321 (a "handle taken?" hint on ☁ Save)** — a lightweight `cloud_store.exists(handle)` (a minimal
      Supabase select); on **Save**, report **new vs overwrite** ("Saved as **tony17**" vs "Updated **tony17** —
      overwrote the squad already saved under that handle"). Only on the click (no per-rerun network calls); the
      ☁ expander stays secret-gated. A unit test for `exists` + a UI test.
- [ ] **No drift** — docs + a display/UX touch only; `cloud_store` write path, the read-only guardrail, and the
      analytics are unchanged; existing **824** stay green (+ the `exists`/UI tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture (brief), BETA.md, CLOUD_SQUADS.md (the handle hint), Backlog (the
      FormSubmit + handle items). No new ADR.

---

### 🧭 Design sketch

**US-320.** `docs/BETA.md`: add `FPL_FEEDBACK_ORIGIN` to the switches TOML; rewrite §1B FormSubmit with the
`/ajax/` endpoint, the Origin/Referer note (why server-side needs it), the Activate-Form step (+ the two
diagnostic messages), and a one-line "the form shows the real result now" pointer. A short **Troubleshooting**
note: *"feedback says sent but nothing arrives" → confirm the Activate-Form email + that `FPL_FEEDBACK_ORIGIN`
matches your app.* Doc-only.

**US-321.** `cloud_store.exists(handle) -> bool` — `GET ?handle=eq.<h>&select=handle` → `bool(rows)`; unconfigured
/ bad handle → `False`. In `render_my_squad`'s ☁ Save handler: `existed = cloud_store.exists(clean)` (before the
upsert), then `save_squad`, then a message that reflects `existed`. Reuses the best-effort client; only runs on
the Save click.

**Deferred:** a random-suffix *suggestion* (a further collision nicety); a CLI price column; the GW1 calibration
work (set-piece/DefCon/form weights) — the big body of work, waiting on real data.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-320 | **Document the FormSubmit setup** — BETA.md §1B (Origin, activation, `FPL_FEEDBACK_ORIGIN`). | High | ✅ Done | ~¼ session |
| US-321 | **A "handle taken?" hint on ☁ Save** — `cloud_store.exists` + a new-vs-overwrite message. | High | ⬜ To do | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `cloud_store.exists` returns True when a row exists / False when empty or unconfigured
   (monkeypatched `requests`); the ☁ Save shows the overwrite message when the handle already exists (an
   AppTest with a fake store). Existing **824** stay green; ruff clean. No `.save(`; no analytics change.
2. **Manual smoke** — BETA.md §1B reads correctly end-to-end (a fresh owner could set it up); with test store
   secrets, Save a handle twice → the second says "overwrote".
3. **Docs updated** — PROJECT_STATUS, Architecture, BETA.md, CLOUD_SQUADS.md, Backlog.

---

### 📝 Session Progress Log

- **US-320 (document the FormSubmit setup)** — rewrote `docs/BETA.md`: added **`FPL_FEEDBACK_ORIGIN`** to the
  switches TOML + list (the anti-abuse Origin/Referer note — why a server-side POST needs one); rewrote **§1B
  (FormSubmit)** with the two gotchas — the **`/ajax/`** endpoint (JSON) + the one-time **"Activate Form"** click
  — plus that the app sends the Origin for you, no key needed, and the form now shows the **real** result (no more
  false "sent"); added a **Troubleshooting** note with a direct `curl` test that decodes FormSubmit's messages
  ("needs Activation" → click the email; the "web server" message → the Origin header; an address error → fix the
  webhook). Updated the **go-live checklist** feedback line to cover the relay + activation. Doc-only — suite
  unchanged at **824**.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
