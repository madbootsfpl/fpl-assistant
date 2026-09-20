-- ═══ Stage C spike — owner-scoped RLS, the target state ═══
--
-- The question this answers: **can the database decide who you are, instead of being told?**
--
-- Today every request uses one publishable key and the app passes a `user_key` as a *parameter*. The key is
-- `sha256(email)`, unsalted — so it is not a secret, it is a restatement of the email. That is survivable
-- only while the publishable key stays on a server. A Flutter binary ships it, so it stops being survivable.
--
-- Target: Supabase Auth issues a JWT per person; policies compare `auth.uid()` to a row's `user_id`.

-- ── The Supabase shim ─────────────────────────────────────────────────────────────────────────────────────
-- ⭐ This is what Supabase provides in a real project, reproduced EXACTLY so the spike tests the real rule
-- and not a convenient approximation. `auth.uid()` reads the verified JWT the API gateway put on the
-- connection; nothing the client sends as data can influence it.
create schema if not exists auth;

create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select nullif(current_setting('request.jwt.claims', true)::json->>'sub', '')::uuid;
$$;

do $$ begin
  create role anon nologin;
exception when duplicate_object then null; end $$;
do $$ begin
  create role authenticated nologin;
exception when duplicate_object then null; end $$;
grant usage on schema public, auth to anon, authenticated;
grant execute on function auth.uid() to anon, authenticated;

-- ── The user tables, owner-scoped ─────────────────────────────────────────────────────────────────────────
-- ⚠️ `user_id` is NOT NULL and defaults to `auth.uid()`. The default is the load-bearing part: it makes an
-- INSERT that forgets to set an owner fail rather than create an orphan row nobody can read or delete.
create table if not exists public.squads (
  user_id     uuid not null default auth.uid(),
  handle      text primary key,
  data        jsonb not null,
  updated_at  timestamptz not null default now()
);

create table if not exists public.user_prefs (
  user_id     uuid primary key default auth.uid(),
  manager_id  text,
  league_id   bigint,
  updated_at  timestamptz not null default now()
);

create table if not exists public.player_watchlist (
  user_id     uuid primary key default auth.uid(),
  player_ids  jsonb not null default '[]'::jsonb,
  updated_at  timestamptz not null default now()
);

-- ── The policies ──────────────────────────────────────────────────────────────────────────────────────────
-- ⭐ One rule, four verbs, three tables: **you may touch a row if you own it.** Note what is NOT here —
-- no `using (true)`, no function taking a key as a parameter, no trust in anything the client says.
do $$
declare t text;
begin
  foreach t in array array['squads', 'user_prefs', 'player_watchlist'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from anon, authenticated', t);
    -- `authenticated` only: a signed-out caller has no uid, so it could never match anyway — but saying so
    -- explicitly means an anon request is refused at the GRANT, before any policy is consulted.
    execute format('grant select, insert, update, delete on public.%I to authenticated', t);

    execute format('drop policy if exists "own rows select" on public.%I', t);
    execute format('drop policy if exists "own rows insert" on public.%I', t);
    execute format('drop policy if exists "own rows update" on public.%I', t);
    execute format('drop policy if exists "own rows delete" on public.%I', t);

    execute format('create policy "own rows select" on public.%I for select to authenticated
                      using (user_id = auth.uid())', t);
    -- ⚠️ `with check` on INSERT, not `using` — `using` filters rows that already exist and is silently
    -- ignored on an insert, so a policy written that way would accept a row claiming any owner.
    execute format('create policy "own rows insert" on public.%I for insert to authenticated
                      with check (user_id = auth.uid())', t);
    -- ⚠️ BOTH clauses on UPDATE: `using` decides which rows you may edit, `with check` decides what they may
    -- become. Omitting the second lets someone edit their own row and reassign it to another owner.
    execute format('create policy "own rows update" on public.%I for update to authenticated
                      using (user_id = auth.uid()) with check (user_id = auth.uid())', t);
    execute format('create policy "own rows delete" on public.%I for delete to authenticated
                      using (user_id = auth.uid())', t);
  end loop;
end $$;
