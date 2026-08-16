# Architectural Decision Record: One account-backed team — unified "Your Team" persistence

**Decision ID:** ADR-113
**Date:** 2026-08-16
**Status:** Accepted — design gate. Build = Sprint 158 (fix-first, then the unified panel).
**Superseded By / Replaces:** **Supersedes the *user-facing* role of ADR-094** (the handle-keyed ☁ Save/Load) —
now that Google auth is live (ADR-106), the account *is* the storage, so the manual handle is retired in
signed-in mode (kept only as the no-login fallback). **Extends** ADR-106 (per-user persistence) and consolidates
ADR-054 (session squad + upload/download) and ADR-058 (Manager-ID import) into one surface.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

**Tester report (2026-08-16):** *"Load your team via **☁ Save/Load across devices**, then refresh the page — the
team reverts to what was there before. If you **upload a json** it persists after refresh."* And a broader ask:
*"the **Upload**, **Save team**, **FPL Manager-ID** and **Save/Load across devices** feel like **4 separate
tools** — can we make this one tool/screen?"*

**Root cause (found in the code).** Two cloud stores compete over one session squad:

- **The account store** — keyed by `auth.user_key` (a sha256 of the email, ADR-106). The auth gate calls
  `squads.link_and_restore(user_key)` on **every page load**; a browser refresh wipes `st.session_state`, so it
  **re-loads whatever squad is saved under the account**.
- **The manual handle store** — keyed by a user-typed **handle** (`render_cloud_sync`, ADR-094, built *before*
  login existed).

Both drive the same `_CLOUD_LINKED` pointer that `_autosync` writes through. So:

| Action | Writes to | Survives refresh? |
|---|---|---|
| Upload `squad.json` · Import Manager-ID · edit | the **account** (`user_key` — the pointer set on load) | ✅ |
| **☁ Load (by handle)** | re-points to the **handle**, saves *there* — not the account | ❌ reverts |

On refresh the gate restores the **account** squad, but ☁ Load wrote the team under a *handle*, so the account
still holds the old team → it reverts. **The lone divergent path — the manual handle — is the bug**, and the
overlap of ADR-094 (pre-login) with ADR-106 (post-login) is why the four tools feel incoherent.

#### Decision Drivers
- **Consistency / no data loss** — one persistence path; a loaded team must survive a refresh, everywhere.
- **One mental model** — *"your team lives in your account; import it once, edit anywhere, download a backup."*
- **Everyone logs in now** — so the account is the natural, sufficient store; a hand-typed handle is redundant.
- **Keep the escape hatches** — Download/Upload for **local backup**; Manager-ID to **populate**; nothing lost.
- **Small, safe first step** — relieve the frustrating bug before the larger UX consolidation.
- **Don't break no-auth mode** — local/dev (no `[auth]`) must still have a cross-device option.

---

### ✅ Decision

**1. The account is the store (signed-in mode).** When Google auth is live, a user's team **auto-persists to
their account** (`user_key`) and syncs across devices — no handle, no manual "Save". Every way of *getting* a team
writes through to the account: **Upload**, **Manager-ID import**, **Build in Squad Lab**, and every **edit**
(captain/transfer/bench) — they already route through `set_active_squad → _autosync`, which targets `user_key`.

**2. Retire the manual handle ☁ Save/Load in signed-in mode.** `render_cloud_sync` (the handle expander) is the
divergent write and is now redundant — **hide it whenever auth is configured**. Keep the `cloud_store` module and
show the handle tool **only as the no-login fallback** (no `[auth]` → local/dev), where it remains the sole
cross-device option. This removes the bug at its source with no loss to signed-in testers (account sync already
does cross-device).

**3. One "Your Team" surface (inline).** Replace the four scattered controls with a **single inline panel** on My
Squad (owner-agreed: inline over a pop-up — mirrors the ADR-108 player-actions decision; better on mobile),
reachable from the sidebar (which slims to the active-team status + an "open" affordance). The panel has three
clear zones:
   - **Sync status** — *"Signed in as … — your team syncs automatically across your devices."*
   - **Get your team** — **Import by Manager-ID** · **Upload a backup** · **Build in Squad Lab →**.
   - **Backup** — **Download `squad.json`** (and Upload to restore).

**4. Maps to the tester's three requirements:**
   - *Upload/Download for device backup* → **Download** = backup, **Upload** = restore (always available).
   - *See/manage on other devices, same login; save config or local* → auto-sync to the **account** + **Download**.
   - *Load by Manager-ID and persist across devices / save local* → import **becomes your team** → account +
     **Download**.

**5. What this is *not*.** Not new auth (reuses ADR-106). Not an analytics/engine/`decision_xp` change (session +
store only). Not a removal of `cloud_store` (kept; only its *signed-in* handle UI is retired). Not a change to the
demo squad or the CLI `SquadStore` file format (the download stays interoperable).

---

### 🔀 Alternatives Considered

- **Just patch ☁ Load to also write the account.** Rejected — it keeps two stores and the "4 tools" confusion;
  fixes the symptom, not the incoherence the tester flagged.
- **Keep the handle tool visible alongside the account.** Rejected — the redundancy is the root of both the bug
  and the confusion; with login live it earns its removal.
- **A pop-up dialog for "Your Team".** Considered; owner chose **inline** (mobile-friendly, consistent with
  ADR-108). `st.dialog` stays a future option if the panel grows.
- **Drop `cloud_store` entirely.** Rejected — it's still the no-login fallback and the storage layer under
  per-user sync; only its handle *UI* is retired in auth mode.

---

### 🧭 Consequences

**Positive**
- **The bug dies** — one write path (the account); a loaded team survives refresh on every device.
- **One coherent tool** — import · backup · sync in a single place with a single mental model.
- **Less surface** — the sidebar declutters; no handle to remember or leak.

**Negative / risks (mitigations)**
- **Behaviour change for anyone using handles today.** *Mitigation:* signed-in testers already have account sync;
  the handle tool stays in no-login mode. Note it in Help/BETA; a one-line "your team now syncs automatically".
- **Persistence depends on the account store being reachable.** *Mitigation:* unchanged from today — best-effort
  + the **Download** backup is the offline escape hatch; a store hiccup never blocks an edit.
- **Guardrail:** the "off by default / byte-identical when unconfigured" invariant must hold — **no `[auth]` and
  no store → today's upload/download-only behaviour, unchanged**. Pin it with a test.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (**Sprint 158**, fix-first):
  - **US-384 — correctness:** in signed-in mode, retire `render_cloud_sync` (the handle divergence); guarantee
    Upload/Import/Build/edit persist to the account and a **loaded team survives refresh**. Tests: signed-in
    load→refresh persists; handle tool hidden when auth configured; upload/import persist; no-auth fallback
    unchanged.
  - **US-385 — the unified "Your Team" panel:** the inline three-zone panel + the slimmed sidebar; fold in
    Upload · Manager-ID · Download; update Help/BETA copy.
- **Not this ADR / follow-ups:** an explicit "teams" list (multiple saved squads per account); an in-app Admin
  view of stored squads. Both out of scope.
