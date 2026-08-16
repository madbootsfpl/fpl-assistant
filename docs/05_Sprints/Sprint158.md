# Sprint 158: One account-backed team — unified "Your Team" persistence (US-384 / US-385)

**Dates:** 2026-08-16 →
**Status:** 🚧 Planned — gated by **ADR-113**. Fix-first (US-384), then the unified panel (US-385).
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

*(filled at retro)*

### 🧠 Lessons

*(filled at retro)*
