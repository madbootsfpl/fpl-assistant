# Architectural Decision Record: Cross-device squad persistence — a handle-keyed cloud store

**Decision ID:** ADR-094
**Date:** 2026-08-23
**Status:** Accepted — **design gate only; the build is Sprint 123.**
**Superseded By / Replaces:** **extends** ADR-054 (session active squad + downloadable files) and **revises its
read-only invariant** (ADR-053/054): the web edge gains **one** scoped, opt-in server write — a squad save/load
keyed by a user-chosen handle. It does **not** introduce accounts/auth (that stays deferred — ADR-087 §alt,
DIRECTION §1); native `st.login()` is recorded as the future "product" upgrade path.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner doesn't always have the desktop to hand and wants to **jump between devices** — build/edit a squad on
one, pick it up on another. **Today (ADR-054)** persistence is the user's **own downloaded `squad.json`** +
`st.session_state`; the web **never writes** server-side (a guardrail test asserts no `.save(` in `src/web*`).
So cross-device today = *download on the desktop, upload on the phone* — the friction the owner is flagging.

Real cross-device sync needs **identity** (whose squad) + **storage** (where it lives). The constraint: this is
a **hobby beta** — the owner is happy to stay hobby and explicitly does **not** want to build accounts/auth yet,
but does want the sync. Cost must stay ~£0.

**Verified at planning:**
- Squads are a small `SquadStore`-format dict (`{player_ids, player_names, bench_ids, cost, name}`) — a few KB
  of JSON; trivially storable as one text/JSON column.
- The read-only guardrail (`tests/test_web_squads.py::test_web_edges_never_call_squadstore_save`) scans for the
  literal `.save(` — it encodes "no server-side squad writes." Any new write path must be a **deliberate,
  tested** revision of that invariant, not an accidental bypass.
- Streamlit Community Cloud disk is **ephemeral + shared** (ADR-054), so persistence *must* be an external store,
  not a server file. No auth/DB deps exist today (`requirements.txt` clean).

#### Decision Drivers
- **Cross-device sync** — the owner's actual ask: save on one device, load on another.
- **No accounts/auth yet** — stay hobby; a user-chosen **handle**, not a login (the owner's explicit choice).
- **~£0** — a free tier that comfortably covers 20–50 testers.
- **Opt-in + off by default** — unset secret → the feature hides and the app stays exactly read-only (public
  deploy + CI unchanged), mirroring the ADR-087 secrets pattern.
- **Scoped, honest invariant** — evolve the read-only guardrail to "no writes **except** this one named store,"
  with a test — not a silent loophole.
- **A clean upgrade path** — if the app ever goes "product," swap the handle for real per-user identity without
  re-architecting the store.

---

### ✅ Decision

**Adopt a handle-keyed cloud squad store on a free tier (Supabase), no login — the user-chosen handle is the
key. This ADR is the design gate; the Save/Load UI + the adapter are built in Sprint 123.**

**1. The store — a thin, swappable adapter.** A new `cloud_store` module behind a minimal interface:
`save_squad(handle, squad) -> None` and `load_squad(handle) -> dict | None` (plus `exists(handle)`). Backed by a
**Supabase** table `squads(handle text primary key, data jsonb, updated_at timestamptz)` via its **REST**
endpoint + an **anon key** held as a Streamlit secret (`FPL_STORE_URL` / `FPL_STORE_KEY`). Best-effort, like our
other external clients (tight timeout, one retry, raise on failure → the caller shows a friendly note and falls
back to the download/upload path). **No new heavy dependency** — the REST call is plain `requests`.

**2. Identity = a handle, not an account.** The user types a **handle** (e.g. `tony17`) on a "Save/Load on any
device" control; the handle *is* the key. **Trade-off, accepted for a hobby beta:** anyone who knows a handle can
read/overwrite it — acceptable because the payload is *public FPL data* (a squad of public players), there is no
PII beyond an optional handle, and the alternative (accounts) is the product pivot the owner is deferring. A
short random suffix suggestion (`tony17-4f2a`) mitigates accidental collisions; a "handle taken?" check is a
nicety, not security.

**3. The read-only invariant evolves — explicitly and tested.** The guardrail changes from *"the web never
writes"* to **"the web never writes to the local DB/squad files; the sole server-side write is the opt-in
`cloud_store` squad save."** Concretely (Sprint 123): the `.save(` scan **stays** for `SquadStore`/local-file
writes; a **new** test asserts the only outbound write path is `cloud_store.save_squad`, and that it is
**secret-gated** (unset `FPL_STORE_URL` → the Save/Load UI hides and no write can occur). So the public deploy is
read-only **until** the owner opts in, and even then the write is a single, named, tested path.

**4. Off by default, opt-in via secrets.** `FPL_STORE_URL` + `FPL_STORE_KEY` unset → the feature is invisible and
the app behaves exactly as today (ADR-054 download/upload only). Set → a "☁ Save/Load across devices" expander
appears on **My Squad**. Same pattern as ADR-087's beta switches.

**5. Cost = £0.** Supabase free tier (a 500 MB Postgres + REST) stores tens of thousands of few-KB squads —
orders of magnitude past 50 testers. The cost is *complexity + a light privacy posture* (a handle + a squad in a
free DB), not money.

**Deferred to Sprint 123 (the build):** the `cloud_store` adapter + the My-Squad Save/Load UI + the guardrail
test change + a `docs/` note. **This ADR does not ship code** — it is the agreed design the build gates on.

---

### 🔀 Alternatives Considered

- **Native `st.login()` (Google OIDC) + per-user store.** The *clean* answer and now built into Streamlit
  (free). **Deferred, not rejected** — it's the "product" upgrade path: proper per-user identity, but it makes us
  hold user data (a privacy/GDPR-lite posture) and is more setup than a hobby beta needs. The adapter interface
  is chosen so the handle can later become an authenticated user id **without** changing the store.
- **Shareable code / URL (no infra).** Encode the squad in a short code/URL the user pastes between devices.
  £0 and keeps the app fully read-only — but the user manages the code by hand; only a small step up from
  download/upload. Rejected as the primary (kept implicitly — an exported `squad.json` already is a portable
  code), too clunky for the "just pick it up on my phone" goal.
- **Keep ADR-054 download/upload only.** The status quo; rejected — it *is* the friction the owner is asking to
  remove.
- **A GitHub Gist / Google Sheet as the store.** Works and £0, but Gist needs a token with write scope (a
  secret that can touch the repo) and a Sheet/Apps-Script is awkward for read-back; Supabase REST is a cleaner
  key-value fit with a real primary key.
- **Real accounts + a per-user DB now (Supabase Auth / Clerk).** Rejected for the beta — the product pivot
  (DIRECTION §1); a handle + a free store validates the *cross-device* need without it.

---

### 🧭 Consequences

**Positive**
- Genuine **cross-device sync** — save on the desktop, load on the phone with a handle — at **£0**, no accounts.
- **Off by default** — the public deploy + CI stay read-only until the owner sets the secrets (ADR-087 pattern).
- A **thin, swappable adapter** — the handle can become an authenticated user id later (native `st.login()`)
  without re-architecting the store; the store backend (Supabase) can be swapped behind the same interface.
- The read-only invariant becomes **honest and tested** (one named write path), not a blanket claim with a
  future loophole.

**Negative / risks (mitigations)**
- **No security on a handle** — anyone who knows it can overwrite. *Mitigation:* public FPL data only, no PII, a
  random-suffix suggestion; documented as a hobby-beta trade-off. Real per-user protection = the deferred
  `st.login()` path.
- **A new external dependency at runtime** (Supabase). *Mitigation:* best-effort client (timeout + retry +
  degrade to download/upload); secret-gated so it's absent unless opted in; no new heavy library (`requests`).
- **A privacy posture** (we now hold a handle + a squad in a free DB). *Mitigation:* minimal data, a "clear my
  saved squad" affordance in the build, and a short note in `docs/` on what's stored + how to delete it.
- **Free-tier limits / outages.** *Mitigation:* the store is a convenience over the still-present download/upload
  fallback; a Supabase outage degrades, it doesn't break the app.

---

### 🧾 Status & follow-ups

- **This is a design gate (Accepted).** No code ships under ADR-094.
- **Sprint 123 (the build):** `cloud_store` adapter (Supabase REST) · a secret-gated "☁ Save/Load across devices"
  expander on My Squad · the guardrail-test revision (named write path + secret-gated) · a privacy note + a
  "clear my saved squad" control.
- **Owner action (Sprint 123):** create a free Supabase project + the `squads` table; set `FPL_STORE_URL` /
  `FPL_STORE_KEY` in Streamlit secrets.
- **Future (deferred):** native `st.login()` → authenticated per-user identity (the "product" upgrade), reusing
  this adapter interface.
