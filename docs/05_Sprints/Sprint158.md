# Sprint 158: One account-backed team — unified "Your Team" persistence (US-384 / US-385)

**Dates:** 2026-08-16
**Status:** ✅ Complete — US-384 + US-385 (ADR-113). 992 → 994 tests.
**Capacity:** ~1 session
**Carried Over:** none

> **Trigger (tester, 2026-08-16):** loading a team via **☁ Save/Load across devices** then refreshing **reverts**
> it (an uploaded json persists); and Upload · Save · Manager-ID · Save/Load feel like **4 separate tools**.
> **Root cause:** two cloud stores — the **account** (`user_key`, ADR-106, restored on every load) and the manual
> **handle** (ADR-094) — fight over one session squad; ☁ Load writes to the *handle*, but refresh restores the
> *account*, so it reverts. **Fix = one store (the account); retire the handle UI in signed-in mode; one screen.**

---

### 🎯 Scope

**US-384 — correctness (kill the revert bug).**
- In **signed-in mode** (auth configured), **hide `render_cloud_sync`** (the handle ☁ Save/Load expander) — it's
  the divergent write. Show it **only** when auth is *not* configured (the no-login fallback).
- Guarantee every load path persists to the **account**: Upload, Manager-ID import, Build hand-off, and edits all
  route through `set_active_squad → _autosync` with `_CLOUD_LINKED = user_key` (already true on an admitted load) —
  so a **loaded team survives a refresh** on every device.
- No new store, no engine change.

**US-385 — the unified "Your Team" panel.**
- One **inline** panel on My Squad (owner-agreed: inline, not a dialog), three zones:
  **Sync status** ("Signed in as … — syncs automatically across your devices") · **Get your team** (Import by
  Manager-ID · Upload a backup · Build in Squad Lab →) · **Backup** (Download `squad.json`).
- Slim the **sidebar** to the active-team status + an affordance to open the panel; fold in the scattered
  uploader + Manager-ID controls.
- Update **Help** (§ Save/Import) + **BETA.md** copy: "your team now syncs automatically; Download is your backup."

---

### ✅ Definition of Done (3-part)

1. **Tests** (AppTest + fakes, no live network):
   - **Signed-in load → refresh persists** — a squad saved under `user_key` is restored on a fresh run (the
     revert bug is gone); the previous behaviour would have shown the stale account squad.
   - **Handle tool hidden when auth configured** — `render_cloud_sync` renders nothing in signed-in mode; still
     renders in the **no-login fallback** (guardrail: unconfigured = today's behaviour, byte-identical).
   - **Upload / Manager-ID persist to the account** (write through to `user_key`).
   - The **"Your Team" panel renders** — status + the three zones; the sidebar shows the active-team status.
2. **Manual smoke** (owner, post-deploy): sign in → Import by Manager-ID → **refresh** → team stays; edit captain
   → refresh → stays; open on a second device → same team; Download → Upload restores.
3. **Docs:** this plan + retro; ADR-113; PROJECT_STATUS · Roadmap · Backlog · Help · BETA.md · Feedback_Log · memory.

---

### 📋 Sprint Review

**Delivered — one account-backed team; the refresh-revert bug is gone and the four tools are one panel.**

- **US-384 — correctness (the bug).** Root cause: two cloud stores fought over one squad — the **account**
  (`user_key`, restored on every load) vs the manual **handle** (ADR-094). ☁ Load wrote the *handle* while a
  refresh restored the *account* → the team reverted. Fix: `render_cloud_sync` returns early when
  `auth.is_configured()` — in signed-in mode the **account is the store**; the handle tool stays only as the
  no-login fallback. Every other load path (upload/import/edit) already persists to the account, so a **loaded
  team now survives a refresh**. +2 tests (signed-in load→refresh persists; handle tool hidden when signed in).
- **US-385 — the unified panel.** A new `render_your_team(squad)` inline expander on My Squad with three zones —
  **sync status** (account-synced when signed in) · **get your team** (Manager-ID import · Upload backup · Squad
  Lab pointer) · **backup** (Download). The sidebar slims to the active-team status + a pointer; the duplicate
  bottom-of-page Download is removed; **Help §7** rewritten to the one-place model. Owner-approved via an Artifact
  mock. The old sidebar-import test became a panel-consolidation test; the Help test updated.
- **Maps to the tester's three asks:** Upload/Download backup ✓ · see/manage on other devices with the same login,
  save config or local ✓ (account sync + Download) · Manager-ID import that persists across devices / saves local ✓.

**Owner smoke (post-deploy):** sign in → Import by Manager-ID → **refresh** → team stays; edit captain → refresh →
stays; open on a second device → same team; Download → Upload restores. The ☁ handle expander is gone when
signed in — intended.

### 🧠 Lessons

- **A UX-consistency complaint can be a bug in disguise.** "The four tools feel separate" and "it reverts on
  refresh" were the *same* root cause — two persistence systems layered over time (ADR-094 pre-login, ADR-106
  post-login). Reading the whole flow before touching code found the real fault instead of patching a symptom.
- **Retire the old layer when the new one subsumes it.** With login live, the handle store wasn't just redundant —
  it was *actively harmful* (the divergent write). Removing it (in signed-in mode) fixed the bug *and* the
  confusion; a patch that kept both would have done neither.
- **Fix-first sequencing pays off.** Shipping US-384 as its own small, safe change ends the frustrating data loss
  immediately; the larger consolidation (US-385) then rides on a correct base.
- **`st.page_link` raises in AppTest bare mode** (`KeyError: 'url_pathname'`) when a page runs standalone — works
  at runtime, breaks the harness. Use a text caption for in-view page pointers (re-confirming the Sprint-146
  lesson); `page_link` is fine at the top of the *main* script (Home).
- **Match the store's RLS posture to who writes** (carried from ADR-113 design): the account model is read-on-load
  + write-through-edit under one key, which is exactly what makes "survives refresh" hold.
