-- ═══ MadBoots — Supabase setup, in its HARDENED form ═══
--
-- ⭐ **One file, pointed at by every runbook.** `BETA.md`, `CLOUD_SQUADS.md` and `ANALYTICS.md` each used to
-- carry their own copy of this SQL, and all three went stale the day the hardening landed — a reader
-- following them would have rebuilt the `using (true)` policies that Stages A/B/B3 removed. Two copies of a
-- rule is how the last one drifted (ADR-123/127); four copies is how three of them end up wrong.
--
-- **Safe to re-run.** Every statement is `if not exists` or drop-then-create.
--
-- ⚠️ **What this does NOT do:** it does not protect a row from someone who knows its key. The functions take
-- a handle or a user_key and return that one row — enumeration stops, guessing does not. Only real identity
-- (Supabase Auth + owner-scoped policies) closes that; see docs/SUPABASE_RLS.md, Stage C.

-- ── Tables ────────────────────────────────────────────────────────────────────────────────────────────────
create table if not exists public.squads (
  handle      text primary key,           -- a chosen handle, or a sha256(email) for a signed-in user
  data        jsonb not null,
  updated_at  timestamptz not null default now()
);

create table if not exists public.beta_users (
  email       text primary key,
  created_at  timestamptz not null default now(),
  last_seen   timestamptz                 -- stamped at admit (ADR-142)
);

create table if not exists public.beta_waitlist (
  email       text primary key,
  reason      text,                       -- 'not_listed' | 'full' | 'bad_code'
  created_at  timestamptz not null default now()
);

create table if not exists public.user_prefs (
  user_key    text primary key,           -- sha256(email), never the address
  manager_id  text,
  league_id   bigint,
  updated_at  timestamptz default now()
);

create table if not exists public.player_watchlist (
  user_key    text primary key,
  player_ids  jsonb not null default '[]'::jsonb,
  updated_at  timestamptz not null default now()
);

create table if not exists public.maddie_videos (
  id          bigint generated always as identity primary key,
  topic       text not null,
  blurb       text,
  youtube_url text,
  sort_order  int not null default 0,
  published   boolean not null default false,
  created_at  timestamptz not null default now()
);

create table if not exists public.events (
  id          bigint generated always as identity primary key,
  ts          timestamptz not null default now(),
  session_id  text,                       -- random per session; anonymous (ADR-100)
  anon_id     text,                       -- random per returning device; anonymous
  version     text,
  event       text,
  page        text,
  duration_ms int,
  ok          boolean,
  meta        jsonb
);

-- ── First: new tables must arrive CLOSED ──────────────────────────────────────────────────────────────────
-- ⭐⭐ **The door every later table walks through.** A stock Supabase project sets
-- `alter default privileges in schema public grant all on tables to anon, …`, so anything created afterwards
-- — by a migration, by the data pipeline, by someone in the dashboard — comes out with DELETE, INSERT,
-- TRUNCATE and UPDATE granted to the publishable key. Hardening the tables that exist does nothing about the
-- ones that do not exist yet, which is how this file's own tables would have been re-opened one at a time.
--
-- ⚠️ Failing closed is the right direction: a new table the app cannot read is a visible bug on the first
-- page load, where a new table the world can delete is an invisible one until someone deletes it.
alter default privileges in schema public revoke all on tables from anon, authenticated;

-- ── Access: what `anon` may do directly ───────────────────────────────────────────────────────────────────
-- ⭐ The principle: **the app asks questions, it does not read tables.** Everything below either grants a
-- single verb or nothing at all; the reads happen through the functions further down.

-- beta_waitlist — emails go IN and nothing comes out. ⚠️ Insert only: an upsert would need a permissive
-- SELECT policy (ON CONFLICT must read the conflicting row), which is the exposure itself. The app therefore
-- sends a plain INSERT and tolerates the 409 on a repeat.
revoke all on public.beta_waitlist from anon, authenticated;
grant insert on public.beta_waitlist to anon;
alter table public.beta_waitlist enable row level security;
drop policy if exists "waitlist insert" on public.beta_waitlist;
create policy "waitlist insert" on public.beta_waitlist for insert to anon with check (true);

-- events — anonymous analytics: insert only. The owner reads them with the service-role key.
revoke all on public.events from anon, authenticated;
grant insert on public.events to anon;
alter table public.events enable row level security;
drop policy if exists "anon events insert" on public.events;
create policy "anon events insert" on public.events for insert to anon with check (true);

-- maddie_videos — public marketing content: readable, never writable.
revoke all on public.maddie_videos from anon, authenticated;
grant select on public.maddie_videos to anon;
alter table public.maddie_videos enable row level security;
drop policy if exists "maddie_videos public read" on public.maddie_videos;
create policy "maddie_videos public read" on public.maddie_videos for select to anon using (true);

-- The rest are reached only through functions.
revoke all on public.beta_users       from anon, authenticated;
revoke all on public.squads           from anon, authenticated;
revoke all on public.user_prefs       from anon, authenticated;
revoke all on public.player_watchlist from anon, authenticated;

-- ── Functions: the only way in ───────────────────────────────────────────────────────────────────────────
-- ⭐ Every one is `security definer` with `set search_path = ''`: it runs as the owner, so no policy can
-- narrow it, and it cannot be hijacked by a schema planted on the caller's path. Each answers ONE question.

-- ── Squads ────────────────────────────────────────────────────────────────────────────────────────────────
create or replace function public.get_squad(p_handle text)
returns jsonb
language sql
security definer
set search_path = ''
stable
as $$
  select data from public.squads where handle = p_handle;
$$;

create or replace function public.save_squad(p_handle text, p_data jsonb)
returns void
language sql
security definer
set search_path = ''
as $$
  insert into public.squads (handle, data, updated_at)
  values (p_handle, p_data, now())
  on conflict (handle) do update set data = excluded.data, updated_at = now();
$$;

-- Returns a boolean, never the handle — the UI only asks "new or overwrite?" (US-321).
create or replace function public.squad_exists(p_handle text)
returns boolean
language sql
security definer
set search_path = ''
stable
as $$
  select exists (select 1 from public.squads where handle = p_handle);
$$;

create or replace function public.delete_squad(p_handle text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare n int;
begin
  delete from public.squads where handle = p_handle;
  get diagnostics n = row_count;
  return n > 0;          -- ⭐ report it: a delete that matched nothing must not read as success (ADR-148)
end;
$$;

-- ── Cross-device preferences (ADR-147) ────────────────────────────────────────────────────────────────────
create or replace function public.get_prefs(p_user_key text)
returns jsonb
language sql
security definer
set search_path = ''
stable
as $$
  select to_jsonb(p) - 'user_key'            -- never echo the key back; the caller already has it
    from public.user_prefs p where p.user_key = p_user_key;
$$;

create or replace function public.save_prefs(p_user_key text, p_manager_id text, p_league_id bigint)
returns void
language sql
security definer
set search_path = ''
as $$
  insert into public.user_prefs (user_key, manager_id, league_id, updated_at)
  values (p_user_key, p_manager_id, p_league_id, now())
  on conflict (user_key) do update set
    -- ⚠️ COALESCE, because `remember(**values)` sets ONE preference at a time: a null must mean "leave it",
    -- not "clear it". Overwriting with null here would make saving a manager id forget the league.
    manager_id = coalesce(excluded.manager_id, public.user_prefs.manager_id),
    league_id  = coalesce(excluded.league_id,  public.user_prefs.league_id),
    updated_at = now();
$$;

-- ── Watchlist ─────────────────────────────────────────────────────────────────────────────────────────────
create or replace function public.get_watchlist(p_user_key text)
returns jsonb
language sql
security definer
set search_path = ''
stable
as $$
  select player_ids from public.player_watchlist where user_key = p_user_key;
$$;

create or replace function public.save_watchlist(p_user_key text, p_player_ids jsonb)
returns void
language sql
security definer
set search_path = ''
as $$
  insert into public.player_watchlist (user_key, player_ids, updated_at)
  values (p_user_key, p_player_ids, now())
  on conflict (user_key) do update set player_ids = excluded.player_ids, updated_at = now();
$$;

-- ── Grants ────────────────────────────────────────────────────────────────────────────────────────────────
revoke execute on function public.get_squad(text)                        from public;
revoke execute on function public.save_squad(text, jsonb)                from public;
revoke execute on function public.squad_exists(text)                     from public;
revoke execute on function public.delete_squad(text)                     from public;
revoke execute on function public.get_prefs(text)                        from public;
revoke execute on function public.save_prefs(text, text, bigint)         from public;
revoke execute on function public.get_watchlist(text)                    from public;
revoke execute on function public.save_watchlist(text, jsonb)            from public;

grant execute on function public.get_squad(text)                         to anon;
grant execute on function public.save_squad(text, jsonb)                 to anon;
grant execute on function public.squad_exists(text)                      to anon;
grant execute on function public.delete_squad(text)                      to anon;
grant execute on function public.get_prefs(text)                         to anon;
grant execute on function public.save_prefs(text, text, bigint)          to anon;
grant execute on function public.get_watchlist(text)                     to anon;
grant execute on function public.save_watchlist(text, jsonb)             to anon;


-- ── B1. The allow-list gate ───────────────────────────────────────────────────────────────────────────────
-- Returns a BOOLEAN, never the list. Even a correct guess learns only whether that one address is listed.
-- The lower(trim(...)) is what the app used to do in Python, having fetched every address to do it — a
-- PostgREST `eq.` filter is case-sensitive, and a hand-typed row like `Colin@x.ie` must admit `colin@x.ie`.
create or replace function public.is_allow_listed(p_email text)
returns boolean
language sql
security definer
set search_path = ''
stable
as $$
  select exists (
    select 1 from public.beta_users
    where lower(trim(email)) = lower(trim(p_email))
  );
$$;

revoke execute on function public.is_allow_listed(text) from public;
grant  execute on function public.is_allow_listed(text) to anon;


-- ── B2. Registration, with the cap actually enforced ──────────────────────────────────────────────────────
-- Returns 'in' | 'full' | 'invalid'.
create or replace function public.register_beta_user(p_email text, p_cap int)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare n int; e text;
begin
  e := lower(trim(p_email));
  if e is null or e = '' or position('@' in e) = 0 then
    return 'invalid';
  end if;

  -- ⚠️ **Without this lock the cap is advisory, and that was measured rather than assumed.** Moving the
  -- check-count-insert sequence into a single function is NOT enough: `select count(*)` takes no lock, so
  -- four concurrent calls against a cap of 5 admitted **6**. With the lock the same test admits exactly 5.
  -- ⭐ *"It is one function" is not the same as "it is atomic".*
  lock table public.beta_users in share row exclusive mode;

  if exists (select 1 from public.beta_users where lower(trim(email)) = e) then
    return 'in';                                    -- already listed: admitted, no new row
  end if;
  select count(*) into n from public.beta_users;
  if p_cap is not null and n >= p_cap then
    return 'full';
  end if;
  insert into public.beta_users (email) values (e);
  return 'in';
end;
$$;

revoke execute on function public.register_beta_user(text, int) from public;
grant  execute on function public.register_beta_user(text, int) to anon;


-- ── B3. "Remove me", which Stage A broke ──────────────────────────────────────────────────────────────────
-- ⚠️ **Stage A revoked DELETE on beta_waitlist, and that silently broke ADR-122's promise** that a tester can
-- remove their own rows — `remove_me` came back `refused (HTTP 401)` and nothing surfaced, because the UI
-- ignores the result by design. Found by testing `remove_me` on staging *after* Stage A was applied; the
-- original rehearsal only checked that the waitlist WRITE still worked.
-- ⭐ *A permission you remove is a promise you may have removed with it.*
--
-- The fix is not to hand DELETE back — it is to expose the one deletion a person is entitled to.
create or replace function public.forget_me(p_email text, p_user_key text default null)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare e text; out jsonb := '{}'::jsonb; n int;
begin
  e := lower(trim(coalesce(p_email, '')));
  if e <> '' and position('@' in e) > 0 then
    delete from public.beta_waitlist where lower(trim(email)) = e;
    get diagnostics n = row_count;  out := out || jsonb_build_object('beta_waitlist', n);
    delete from public.beta_users   where lower(trim(email)) = e;
    get diagnostics n = row_count;  out := out || jsonb_build_object('beta_users', n);
  end if;
  if p_user_key is not null and p_user_key <> '' then
    delete from public.squads            where handle   = p_user_key;
    get diagnostics n = row_count;  out := out || jsonb_build_object('squads', n);
    delete from public.player_watchlist  where user_key = p_user_key;
    get diagnostics n = row_count;  out := out || jsonb_build_object('player_watchlist', n);
    delete from public.user_prefs        where user_key = p_user_key;
    get diagnostics n = row_count;  out := out || jsonb_build_object('user_prefs', n);
  end if;
  return out;
end;
$$;

revoke execute on function public.forget_me(text, text) from public;
grant  execute on function public.forget_me(text, text) to anon;


-- ── B4. Keeping the allow-list's last_seen stamp working ──────────────────────────────────────────────────
-- Called on every admit (auth.py), not by an admin — so it needs to survive the revoke below.
create or replace function public.touch_last_seen(p_email text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare n int;
begin
  update public.beta_users set last_seen = now()
   where lower(trim(email)) = lower(trim(coalesce(p_email, '')));
  get diagnostics n = row_count;
  return n > 0;
end;
$$;

revoke execute on function public.touch_last_seen(text) from public;
grant  execute on function public.touch_last_seen(text) to anon;
