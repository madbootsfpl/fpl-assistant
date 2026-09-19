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
