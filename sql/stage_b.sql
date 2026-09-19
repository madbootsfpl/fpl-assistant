-- Stage B — narrow functions, so the app asks questions instead of reading tables.
-- Applied to Supabase; see docs/SUPABASE_RLS.md (Stage B) and docs/SUPABASE_PRODUCTION_CUTOVER.md.
--
-- ⭐ **One definition, loaded by both the runbook and the tests.** `tests/test_stage_b_sql.py` runs this file
-- against a real Postgres and asserts the behaviour the Python side can no longer see — because the logic now
-- lives here. Two copies of a rule is how the last one drifted (ADR-123/127).
--
-- ⚠️ `set search_path = ''` is mandatory on every `security definer` function: without it a caller-controlled
-- search_path can resolve `beta_users` to a table of their own choosing.

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


-- ── Close the table ───────────────────────────────────────────────────────────────────────────────────────
-- ⚠️ Only after every caller is on the functions above. `anon` keeps no direct access to beta_users at all.
-- The owner's Admin reads (all_emails, last_seen_by_email) still use the anon key today and will break here —
-- they need a service-role credential, which is tracked separately.
revoke all on public.beta_users from anon, authenticated;


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
