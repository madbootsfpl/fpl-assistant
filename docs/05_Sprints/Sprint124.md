# Sprint 124: Cross-device squads — build the handle-keyed cloud store (ADR-094)

**Dates:** 2026-08-25 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~¾–1 session (the **first server-side write** + the read-only guardrail revision — the careful one)
**Carried Over:** the ADR-094 design gate (now being built)

> **Direction (owner):** build the deferred **cross-device squads** (ADR-094) — save a squad on one device, load
> it on another. Solves the owner's own Sprint-122 pain (*"I don't always have my desktop"*).

---

### 🔎 Verified at planning (on real data)

- **ADR-094 is the agreed design:** a **handle-keyed Supabase store** (no login — the user-chosen handle is the
  key), a thin swappable `cloud_store` adapter, secret-gated (`FPL_STORE_URL`/`FPL_STORE_KEY`), ~£0. This sprint
  **builds** it.
- **The squad is a small JSON dict** — `{player_ids, player_names, bench_ids, cost, name, saved_at}` (verified on a
  demo squad) — a few KB; store the whole dict in one `jsonb` column keyed by `handle`.
- **A best-effort HTTP pattern exists to mirror** — `api/retry.with_retry(fetch, retries=, backoff=, sleep=)` +
  `is_transient` (tight timeout, retry-once, raise → the caller degrades). The `cloud_store` reuses it.
- **The read-only guardrail** (`tests/test_web_squads.py::test_web_edges_never_call_squadstore_save`) scans web
  files for `.save(` — i.e. no local `SquadStore.save`. The cloud write (`cloud_store.save_squad`) is a
  **different, deliberate** path; per ADR-094 the invariant evolves to *"no local writes; the one server write is
  this opt-in, secret-gated squad save"* — captured by keeping the `.save(` scan **and** adding a secret-gated
  test.
- **The UI anchor** is `views/squads.py::render_my_squad` (line 263), which already has Rename/Swap/Set-bench
  expanders + `active_squad()`/`set_active_squad()` — the "☁ Save/Load across devices" expander slots in beside
  them.
- **Config reads via `access.secret(key, default)`** (`st.secrets` → env), so tests set env vars + monkeypatch
  `requests`; **no live network in tests**, and **unset secrets → the feature is invisible + inert**.

---

### 🎯 Sprint Goal

**Objective:** a tester can **Save** their squad under a handle and **Load** it on any device — a real
cross-device sync at ~£0, no login. Off by default (unset secrets → invisible, the app stays read-only); the one
new server write is scoped, secret-gated, and tested.

#### Success Criteria
- [ ] **US-309 (the `cloud_store` adapter + the guardrail revision)** — `web_streamlit/cloud_store.py`:
      `is_configured()`, `save_squad(handle, squad)` (Supabase upsert), `load_squad(handle) -> dict | None`,
      `delete_squad(handle)`, `_clean_handle` (sanitised: lower-case, `[a-z0-9_-]`, bounded). Secret-gated
      (`FPL_STORE_URL`/`FPL_STORE_KEY`), best-effort (`with_retry` + timeout, raise → degrade). Unit-tested with a
      monkeypatched `requests`; the **read-only invariant evolves** — keep the `.save(` scan **and** add a
      secret-gated test (unset secrets → `is_configured()` False → no write, feature hidden).
- [ ] **US-310 (the My-Squad "☁ Save/Load across devices" UI + a privacy note)** — in `render_my_squad`, when
      `cloud_store.is_configured()`: an expander with a **handle** input + **Save** / **Load** / **Clear**
      buttons; Save→`save_squad`, Load→`set_active_squad`+`st.rerun`, Clear→`delete_squad`; a **privacy caption**
      (what's stored · no login · a handle isn't security · Clear removes it); degrade with a friendly note on
      failure. **Hidden entirely when unconfigured.** Plus a `docs/CLOUD_SQUADS.md` owner-setup runbook.
- [ ] **No unintended drift** — the *only* new server write is `cloud_store.save_squad`/`delete_squad`, secret-
      gated + off by default; the download/upload path (ADR-054) still works; existing **781** stay green (+
      adapter/UI/guardrail tests); ruff clean; CI (no secrets) sees the feature off.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log, Backlog, DEPLOY.md/BETA.md, CLOUD_SQUADS.md
      (implements **ADR-094**; the ADR moves from "design gate" to "built").

---

### 🧭 Design sketch

**US-309 — the adapter.** `cloud_store.py` reads `FPL_STORE_URL` (the Supabase REST table endpoint, e.g.
`https://<proj>.supabase.co/rest/v1/squads`) + `FPL_STORE_KEY` (anon key) via `secret()`. Headers: `apikey` +
`Authorization: Bearer <key>` + JSON. **Save** = `POST` with `Prefer: resolution=merge-duplicates` (upsert) and
body `{handle, data: squad}`. **Load** = `GET ?handle=eq.<handle>&select=data` → `rows[0]["data"]` or `None`.
**Delete** = `DELETE ?handle=eq.<handle>`. All wrapped in `with_retry`, tight timeout, `raise_for_status` →
raise on failure (the caller shows a note). `_clean_handle` guards the `eq.` filter (lower-case, `[a-z0-9_-]`,
2–32 chars). Tests monkeypatch `requests.{post,get,delete}` + set the env vars.

**US-310 — the UI.** In `render_my_squad`:
```
if cloud_store.is_configured():
    with st.expander("☁ Save / Load across devices"):
        handle = st.text_input("Your handle", help="A name only you know — it's the key to your squad.")
        cols = st.columns(3)
        if cols[0].button("Save"):   cloud_store.save_squad(clean, squad) → toast
        if cols[1].button("Load"):   sq = cloud_store.load_squad(clean) → set_active_squad + rerun
        if cols[2].button("Clear"):  cloud_store.delete_squad(clean) → toast
        st.caption("Stored: your handle + squad (public FPL players), no login. Anyone with the handle can "
                   "read/overwrite it — use something only you'd guess. Clear removes it.")
```
Each action try/excepts → a friendly error on network failure. Hidden when unconfigured (secret-gated).

**Owner runbook (`docs/CLOUD_SQUADS.md`, ~10 min, £0):** create a free Supabase project; a `squads(handle text
primary key, data jsonb, updated_at timestamptz default now())` table; an **anon insert/select/update/delete
policy** on it (or disable RLS for the beta); set `FPL_STORE_URL` (the `/rest/v1/squads` endpoint) +
`FPL_STORE_KEY` (the anon key) in Streamlit secrets.

**Deferred:** native `st.login()` per-user identity (the "product" upgrade — the adapter interface already fits);
a handle "already taken?" check (a nicety, not security); encryption / rate-limiting (a hobby beta on public FPL
data); a My-Squad "list my handles" view.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-309 | **The `cloud_store` adapter + guardrail revision** — Supabase save/load/delete, secret-gated. | High | ✅ Done | ~½ session |
| US-310 | **My-Squad "☁ Save/Load across devices" UI** — handle + Save/Load/Clear + a privacy note. | High | ⬜ To do | ~½ session |

---

### 🧑‍💻 Owner runbook actions (you — ~10 min, £0)

_(the sprint delivers the code + the runbook; the store needs your account)_
1. Create a free **Supabase** project + the `squads` table + the anon access policy (`docs/CLOUD_SQUADS.md`).
2. Set `FPL_STORE_URL` + `FPL_STORE_KEY` in Streamlit secrets → the "☁ Save/Load" expander appears; test a
   Save on one device + a Load on another.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `cloud_store` save/load/delete hit the configured URL with auth headers + the right
   body/params (monkeypatched `requests`); `load_squad` returns the row data or `None`; `is_configured()` is
   **False** without secrets; `_clean_handle` sanitises. The My-Squad view shows **no** cloud expander when
   unconfigured, and (configured, monkeypatched) **Save** calls `save_squad` + **Load** sets the active squad.
   Existing **781** stay green. The `.save(` guardrail still holds; the new secret-gated test passes.
2. **Manual smoke** — with test secrets + a fake store, `python -m src.web_streamlit` → My Squad → ☁ expander:
   Save under a handle, Load it back; unconfigured run → the expander is absent.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log, Backlog, DEPLOY/BETA,
   CLOUD_SQUADS.md; ADR-094 marked **built**.

---

### 📝 Session Progress Log

- **US-309 (the `cloud_store` adapter + guardrail revision)** — added `src/web_streamlit/cloud_store.py`:
  `is_configured()` (both `FPL_STORE_URL`/`FPL_STORE_KEY` set), `save_squad` (Supabase upsert — POST +
  `Prefer: resolution=merge-duplicates`, body `{handle, data}`), `load_squad → dict|None` (GET
  `?handle=eq.<h>&select=data`), `delete_squad`, and `clean_handle` (lower-case, `[a-z0-9_-]`, 2–32 chars —
  guards the `eq.` filter). Config via `access.secret` (→ env in tests); best-effort via `api.retry.with_retry`
  (retry-once + timeout, raise → caller degrades). **Read-only invariant revised (ADR-094):** kept the `.save(`
  scan (no local `SquadStore.save`) **and** added `test_cloud_store_squad_write_is_secret_gated` — unset secrets →
  `is_configured()` False, `load_squad` None, and `save_squad` refuses **before any HTTP** (a monkeypatched
  `requests.post` that would raise is never called). +8 tests (`tests/test_cloud_store.py` ×7 + the guardrail);
  no live network (monkeypatched `requests` + env). ruff clean. **789** total. The write path exists but is
  **off** until the owner sets the secrets (Sprint's US-310 wires the UI).

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
