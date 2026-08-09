# Cross-device squads — owner setup (~10 min, £0)

Let testers **save a squad on one device and load it on another** via a free **Supabase** store, keyed by a
user-chosen **handle** (no login). Background: [ADR-094](06_Decisions/ADR-094-cross-device-squad-persistence.md).

**Off by default:** until you set the two secrets below, the "☁ Save / Load across devices" expander is hidden
and the app stays read-only (download/upload only, ADR-054). Setting them is the *only* thing that turns on the
one server-side write the app makes.

---

## 1. Create the store (Supabase)

1. Sign up at [supabase.com](https://supabase.com) (free tier) → **New project**. Note the project's **API URL**
   and **anon public** key (Project **Settings → API**).
2. Open **SQL Editor** and run:
   ```sql
   create table if not exists squads (
     handle      text primary key,
     data        jsonb not null,
     updated_at  timestamptz not null default now()
   );

   -- Beta access with NO login: allow the anon key to read/write this one table.
   alter table squads enable row level security;
   create policy "anon squads read"   on squads for select using (true);
   create policy "anon squads write"  on squads for insert with check (true);
   create policy "anon squads update" on squads for update using (true) with check (true);
   create policy "anon squads delete" on squads for delete using (true);
   ```
   *(A handle isn't security — this is a hobby beta on public FPL data. Anyone who knows a handle can read or
   overwrite it, by design, ADR-094.)*

## 2. Wire the secrets (Streamlit)

In **Streamlit Community Cloud → Manage app → Settings → Secrets** (TOML) — or local env vars:

```toml
FPL_STORE_URL = "https://<project-ref>.supabase.co/rest/v1/squads"   # the project API URL + /rest/v1/squads
FPL_STORE_KEY = "<your-anon-public-key>"
```

## 3. Test it

1. Reload the app → **Squads → My Squad → ☁ Save / Load across devices** now appears.
2. Type a **handle** (e.g. `tony17`) → **Save**. In Supabase → **Table editor → squads**, a row appears.
3. On another device (or a fresh browser), open the app → My Squad → enter the same handle → **Load** → your
   squad appears. **Clear** removes it.

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
