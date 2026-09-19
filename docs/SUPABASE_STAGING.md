# Supabase staging — setup and connection runbook

**Purpose:** rehearse the access hardening in [`SUPABASE_RLS.md`](SUPABASE_RLS.md) against a throwaway
project before anything touches production. **Nothing in this file changes production.**

> ⚠️ **The repo is public** (Streamlit Community Cloud requires it — see `.gitignore`). Never paste a key
> into a file that is not ignored. `.env`, `.env.*`, and `**/secrets.toml` are ignored; that is the whole
> safe list.

**Naming.** This runbook has **Steps 1–6** (do them in order). The hardening they rehearse is **Phase 1.5**,
whose parts are **Stage A / B / C** in [`SUPABASE_RLS.md`](SUPABASE_RLS.md) — letters, never numbers, and
unrelated to ADR-211's **Stage 2a–2f**, which is the data pipeline.

**Where this stops.** Steps 1–5 leave you with a staging project that is a faithful copy of production's
*current, insecure* state, the exposure reproduced and measured, and your local app pointed at it. The
hardening itself is Step 6 onwards and is deliberately not in this file yet — ⭐ *you cannot tell whether a
fix worked without a before.*

---

## Step 1 — Collect the staging credentials

**Where to click**

1. Open the **staging** project at [supabase.com/dashboard](https://supabase.com/dashboard). ⚠️ Check the
   project name in the top-left switcher before every step in this runbook.
2. **Project Settings** (the gear, bottom of the left sidebar) → **API**.
   *Newer projects show this as **API Keys** with a separate **Legacy API keys** tab.*

**What to copy**

| you need | where it is | looks like |
|---|---|---|
| **Project URL** | "Project URL" | `https://abcdefghijkl.supabase.co` |
| **Anon / publishable key** | "Project API keys → `anon` `public`", or the newer "Publishable key" | a long `eyJhbGciOi…` JWT, or `sb_publishable_…` |

⚠️ **Do not copy the `service_role` / secret key.** Nothing in this runbook uses it, and it bypasses RLS
entirely — which would make every verification below pass for the wrong reason.

**What you should see:** a URL ending `.supabase.co` and a key of 100+ characters.

**Verify:** the project reference in the URL matches the staging project you just created, not production.

---

## Step 2 — Recreate production's *current* schema

⭐ **Staging must start insecure.** This is production's setup SQL, exactly as `CLOUD_SQUADS.md`, `BETA.md`
and ADR-147 document it — permissive policies and all. Copying the *fixed* version here would mean testing
the fix against a problem you had already removed.

**Where to click:** left sidebar → **SQL Editor** → **New query** → paste the block below → **Run**
(or ⌘/Ctrl + Enter).

```sql
-- MadBoots staging: production's user-data schema AS IT IS TODAY (deliberately permissive).
-- Safe to re-run.

create table if not exists squads (
  handle      text primary key,
  data        jsonb not null,
  updated_at  timestamptz not null default now()
);
alter table squads enable row level security;
drop policy if exists "anon squads read"   on squads;
drop policy if exists "anon squads write"  on squads;
drop policy if exists "anon squads update" on squads;
drop policy if exists "anon squads delete" on squads;
create policy "anon squads read"   on squads for select using (true);
create policy "anon squads write"  on squads for insert with check (true);
create policy "anon squads update" on squads for update using (true) with check (true);
create policy "anon squads delete" on squads for delete using (true);

create table if not exists beta_users (
  email       text primary key,
  created_at  timestamptz not null default now(),
  last_seen   timestamptz
);
alter table beta_users enable row level security;
drop policy if exists "anon users read"   on beta_users;
drop policy if exists "anon users write"  on beta_users;
drop policy if exists "anon users delete" on beta_users;
create policy "anon users read"   on beta_users for select using (true);
create policy "anon users write"  on beta_users for insert with check (true);
create policy "anon users delete" on beta_users for delete using (true);

create table if not exists beta_waitlist (
  email       text primary key,
  reason      text,
  created_at  timestamptz not null default now()
);
alter table beta_waitlist disable row level security;

create table if not exists public.user_prefs (
  user_key   text primary key,
  manager_id text,
  league_id  bigint,
  updated_at timestamptz default now()
);
alter table public.user_prefs enable row level security;
drop policy if exists "prefs read"   on public.user_prefs;
drop policy if exists "prefs insert" on public.user_prefs;
drop policy if exists "prefs update" on public.user_prefs;
drop policy if exists "prefs delete" on public.user_prefs;
create policy "prefs read"   on public.user_prefs for select to anon using (true);
create policy "prefs insert" on public.user_prefs for insert to anon with check (true);
create policy "prefs update" on public.user_prefs for update to anon using (true) with check (true);
create policy "prefs delete" on public.user_prefs for delete to anon using (true);

create table if not exists public.player_watchlist (
  user_key    text primary key,
  player_ids  jsonb not null default '[]'::jsonb,
  updated_at  timestamptz not null default now()
);
alter table public.player_watchlist disable row level security;

create table if not exists public.maddie_videos (
  id          bigint generated always as identity primary key,
  topic       text    not null,
  blurb       text,
  youtube_url text,
  sort_order  int     not null default 0,
  published   boolean not null default false,
  created_at  timestamptz not null default now()
);
alter table public.maddie_videos enable row level security;
drop policy if exists "maddie_videos public read" on public.maddie_videos;
create policy "maddie_videos public read" on public.maddie_videos for select using (true);

create table if not exists events (
  id          bigint generated always as identity primary key,
  ts          timestamptz not null default now(),
  session_id  text,
  anon_id     text,
  version     text,
  event       text,
  page        text,
  duration_ms int,
  ok          boolean,
  meta        jsonb
);
alter table events enable row level security;
drop policy if exists "anon events insert" on events;
create policy "anon events insert" on events for insert with check (true);
```

**What you should see:** *"Success. No rows returned."*

**Verify** — run this and expect **7 rows**:

```sql
select table_name,
       (select count(*) from pg_policies p where p.tablename = t.table_name) as policies,
       (select relrowsecurity from pg_class c where c.relname = t.table_name) as rls_on
from information_schema.tables t
where table_schema = 'public'
  and table_name in ('squads','beta_users','beta_waitlist','user_prefs',
                     'player_watchlist','maddie_videos','events')
order by table_name;
```

Expect `beta_waitlist` and `player_watchlist` to show **`rls_on = false`** — that is production's state, and
two of the things Step 6 will change.

---

## Step 3 — Seed obviously-fake data

⚠️ **Never copy real tester rows into staging.** Real emails in a throwaway project is the problem you are
trying to fix, reproduced somewhere with less care taken over it.

```sql
insert into beta_users (email) values
  ('alice@example.invalid'), ('bob@example.invalid'), ('carol@example.invalid')
on conflict (email) do nothing;

insert into beta_waitlist (email, reason) values
  ('dave@example.invalid', 'not_listed'), ('erin@example.invalid', 'full')
on conflict (email) do nothing;

insert into squads (handle, data) values
  ('TESTONE', '{"player_ids":[1,2,3],"bench_ids":[3]}'::jsonb),
  ('TESTTWO', '{"player_ids":[4,5,6],"bench_ids":[6]}'::jsonb)
on conflict (handle) do update set data = excluded.data;

insert into public.user_prefs (user_key, manager_id) values
  ('hash-of-alice', '2885974')
on conflict (user_key) do nothing;
```

**Verify:** `select count(*) from beta_users;` → **3**. `.invalid` is a reserved TLD that can never resolve,
so these addresses cannot reach a real person even by accident.

---

## Step 4 — Reproduce the exposure, and write the number down

⭐ **This is the step that makes Step 6 provable.** Right now the anon key can read every row of tables
holding email addresses. Measure it before fixing it.

Put the credentials in a shell:

```bash
export SUPA_URL="https://<your-staging-ref>.supabase.co"
export SUPA_KEY="<the anon / publishable key>"
```

Then:

```bash
# 1. Dump the entire allow-list — the emails of every tester.
curl -s "$SUPA_URL/rest/v1/beta_users?select=email" \
     -H "apikey: $SUPA_KEY" -H "Authorization: Bearer $SUPA_KEY"

# 2. Dump the waitlist — people who were REFUSED, which is arguably worse.
curl -s "$SUPA_URL/rest/v1/beta_waitlist?select=email,reason" \
     -H "apikey: $SUPA_KEY" -H "Authorization: Bearer $SUPA_KEY"

# 3. Enumerate every saved squad without knowing a single handle.
curl -s "$SUPA_URL/rest/v1/squads?select=handle" \
     -H "apikey: $SUPA_KEY" -H "Authorization: Bearer $SUPA_KEY"
```

**What you should see — and it is meant to be uncomfortable:**

```json
[{"email":"alice@example.invalid"},{"email":"bob@example.invalid"},{"email":"carol@example.invalid"}]
[{"email":"dave@example.invalid","reason":"not_listed"}, …]
[{"handle":"TESTONE"},{"handle":"TESTTWO"}]
```

**Write these three results down.** After Step 6, commands 2 and 3 must change and command 1 must keep
working *for the app* while ceasing to work as a bulk dump — and you will only be able to tell because you
have the before.

⚠️ **Note what this proves about production**: the same three commands, with production's URL and key, would
return **real tester emails today**. Do not run them there to find out; the staging copy is the evidence.

---

### 📌 The recorded baseline — staging, 2026-09-19, before any hardening

Run with `scripts/supabase_probe.sh` against the staging project, using the **anon** key:

| probe | result | HTTP |
|---|---|---|
| `beta_users` — the allow-list | **all 3 addresses returned** | 200 |
| `beta_waitlist` — people **refused** | **all 2 addresses + reasons returned** | 200 |
| `squads` — every saved squad | **both handles enumerated**, no handle needed | 200 |
| `maddie_videos` — marketing copy | `[]` (nothing seeded) | 200 |

⚠️ **This is with the key that ships inside every browser that loads the app.** Not a stolen credential — the
one the page is built to hand out. In production those first two lists are real tester addresses, and the
third is every squad anyone has saved.

⭐ `maddie_videos` returning `[]` is correct and not a failure: nothing was seeded into it, and its public
read is the one permission in the set that *should* stay open.

**After Stage A, row 2 must change and rows 1, 3 and 4 must not.** That asymmetry is the test — a change
everywhere would mean the app had broken, and a change nowhere would mean the fix had not landed.

---

## Step 5 — Point local MadBoots at staging

Every one of the seven tables derives its endpoint from **`FPL_STORE_URL`'s base** plus **`FPL_STORE_KEY`**,
so two variables move the whole user-data layer. ⭐ Nothing in the code changes, and unsetting them puts you
straight back.

⚠️ **First check nothing overrides them.** `secret()` reads `st.secrets` *before* the environment, so a
stale `.streamlit/secrets.toml` would silently keep you on production while you believed you were on
staging. There is no such file in this checkout today — confirm it is still true:

```bash
ls .streamlit/secrets.toml 2>/dev/null && echo "⚠️ this file WINS over the env vars — check what is in it"
```

Then run the app against staging — the script reads `.env.staging`, so there is nothing to retype:

```bash
./scripts/run_app_staging.sh
```

It does three things before launching: **refuses outright** if `.streamlit/secrets.toml` sets
`FPL_STORE_URL` (see the warning above — that file beats the environment, so the run would silently hit
production while every screen said it was fine), prints the target host, and **positively identifies
staging** by checking the `.invalid` seed rows from Step 3 are present.

*(The long form, if you prefer it explicit: `FPL_STORE_URL="$SUPA_URL/rest/v1/squads"
FPL_STORE_KEY="$SUPA_KEY" FPL_LOCAL=1 python -m src.web_streamlit`.)*

**Verify, in the browser:**

1. **My Squad** → the sidebar shows **☁ Save / Load across devices**.
2. Save a squad under a new handle, e.g. `STAGINGCHECK`.
3. Back in Supabase → **Table Editor** → **squads** → the row is there.
4. Reload the app and load it back.

⭐ **The check that matters is #3**: it proves the write reached *staging*. If the row appears in production
instead, stop — something is overriding your environment.

**To go back to normal:** close the app and drop the variables. They were never written to a file.

---

## What is deliberately not here yet

**Step 6 — apply Stage A** (`SUPABASE_RLS.md` → *Stage A*: `beta_waitlist` and `maddie_videos`), then
re-running Step 4 to show commands 2 and 3 now refuse, then confirming the app still saves, loads, and still
puts a refused sign-in on the waitlist.

⚠️ That last one is the one to test **by hand**: the waitlist write is **fail-silent**, so if the policy is
wrong it will not tell you — it will simply stop recording people. ⭐ *The one path that cannot report its
own failure is the one you have to watch.*
