# Cross-device squads — owner setup (~10 min, £0)

Let testers **save a squad on one device and load it on another** via a free **Supabase** store, keyed by a
user-chosen **handle** (no login). Background: [ADR-094](06_Decisions/ADR-094-cross-device-squad-persistence.md).

> **Same Supabase project also powers the capped registration gate** (ADR-098) — a second `beta_users` table
> reusing these same `FPL_STORE_URL`/`FPL_STORE_KEY` secrets. See [BETA.md §4](BETA.md) to cap tester numbers.

**Off by default:** until you set the two secrets below, the "☁ Save / Load across devices" expander is hidden
and the app stays read-only (download/upload only, ADR-054). Setting them is the *only* thing that turns on the
one server-side write the app makes.

---

## 1. Create the store (Supabase)

1. Sign up at [supabase.com](https://supabase.com) (free tier) → **New project**. Note the project's **API URL**
   and **anon public** key (Project **Settings → API**).
2. Open the **SQL Editor** and run [`sql/setup.sql`](../sql/setup.sql). It creates all seven tables and the
   twelve functions in their **hardened** form, and is safe to re-run.

   🔴 **This page used to print permissive policies here** — `create policy ... using (true)` on `squads`, or
   the one-line `disable row level security`. Both make every saved squad readable by anyone holding the
   publishable key. Stage B3 closed that ([`SUPABASE_RLS.md`](SUPABASE_RLS.md)), and pasting the old SQL back
   would undo it.

   ⭐ **What replaced them:** four functions — `get_squad`, `save_squad`, `squad_exists`, `delete_squad`. Each
   takes a handle and answers about *that one squad*. The table itself is unreadable, so the list of handles
   cannot be pulled.

   ⚠️ **A handle is still not security, and the functions do not make it one.** Anyone who knows or guesses a
   handle can read or overwrite it, exactly as ADR-094 intended for a hobby beta. What changed is that they
   can no longer **enumerate** — guessing one handle is now the only way in, rather than downloading all of
   them. Real per-user ownership needs Supabase Auth (Stage C, Phase 3).

## 2. Wire the secrets (Streamlit)

In **Streamlit Community Cloud → Manage app → Settings → Secrets** (TOML) — or local env vars:

```toml
FPL_STORE_URL = "https://<project-ref>.supabase.co/rest/v1/squads"   # the project API URL + /rest/v1/squads
FPL_STORE_KEY = "<your-anon-public-key>"
```

## 3. Test it

1. Reload the app → open the **Squads** tab → **☁ Save / Load across devices** now appears in the **sidebar**
   (under *Your squad*), on any sub-view (Sprint 135, US-331).
2. Build or upload a squad (so it's your **active** squad — Save is disabled until then), type a **handle** (e.g.
   `tony17`) → **Save**. In Supabase → **Table editor → squads**, a row appears.
3. On another device (or a fresh browser), open the app → **Squads** → enter the same handle in the sidebar →
   **Load** → your squad appears. **Clear** removes it.

---

## What's stored / privacy

- One row per handle: `{handle, data, updated_at}`, where `data` is the squad dict (public FPL player ids +
  names, bench, cost, name). **No login, no email, no personal data** beyond the handle the tester chooses.
- The in-app caption tells testers plainly: *"no login; anyone who knows the handle can read or overwrite it; use
  one only you'd guess; Clear removes it."* **Save** also warns when a handle is **already taken** ("overwrote the
  squad already saved under that handle", US-321), so a shared handle isn't clobbered silently.
- **Turn it off:** delete the two secrets → the expander disappears and the app is read-only again. (Existing
  rows stay in Supabase until you delete the table/project.)

## How it fails safe

The store is **best-effort**: a tight timeout + one retry, then it degrades — a friendly "try again" note, and
the **download/upload** path (ADR-054) always still works. A Supabase outage never breaks the app.

## Later (deferred)

Native `st.login()` (Google) → real per-user identity instead of a shared handle — the adapter interface already
fits it (ADR-094), so it's a swap, not a rewrite. Add only if the app goes "product".
