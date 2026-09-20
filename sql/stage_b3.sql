-- Stage B3 — squads, preferences and watchlists stop being enumerable.
-- See docs/SUPABASE_RLS.md. Applied AFTER sql/stage_b.sql, and after the matching code is deployed.
--
-- ⚠️⚠️ **What this does and does not achieve.** It stops *enumeration*: no caller can list every handle and
-- walk the results. It does **not** stop someone who already knows a handle from reading that row — the
-- functions take the key as an argument and return that one row, by design.
--
-- ⭐ For a `sha256(email)` handle that is effectively protection: the key is not guessable. For the
-- **user-chosen** handles from the no-login path (`ts`, `robots`, `tesheridan` are all live today) it is
-- not — those are guessable, and were always readable to anyone who tried. **Only Stage C fixes that**, by
-- replacing "knowing the key" with "being the user".
--
-- ⚠️ `set search_path = ''` on every definer function: without it a caller-controlled search_path can
-- resolve these tables to ones of their own choosing.

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

-- ── Close the tables ──────────────────────────────────────────────────────────────────────────────────────
-- ⚠️ Only once every caller is on the functions above. The Admin page's `updated_at_by_handle` reads the
-- whole squads table and needs FPL_ADMIN_STORE_KEY, exactly like the roster.
revoke all on public.squads           from anon, authenticated;
revoke all on public.user_prefs       from anon, authenticated;
revoke all on public.player_watchlist from anon, authenticated;
