-- ═══ Claiming the rows that already exist ═══
--
-- 29 testers have squads/prefs/watchlists keyed by `sha256(clean_email(email))[:32]`. After Stage C the key
-- is `auth.uid()`. Somebody has to connect the two, once, per person.
--
-- ⭐⭐ **The function derives the old key from the JWT's verified email, NEVER from an argument.** Taking the
-- old key as a parameter would reproduce the exact hole Stage C exists to close — anyone could claim
-- anyone's rows by computing a hash. The whole security of this rests on the email coming from the token
-- Supabase verified, not from the caller.
--
-- ⭐ And it only works at all *because* the old key is an unsalted function of the email — the same property
-- that makes the current scheme unsafe is what makes the migration computable. A salted key would have
-- needed a mapping table built while the old system was still running.

-- ⚠️ Supabase installs pgcrypto into the `extensions` schema, a bare Postgres into `public`. With
-- `set search_path = ''` the call must be schema-qualified, so the two are NOT interchangeable — a
-- function that works locally would fail on Supabase and vice versa. The spike mirrors Supabase.
create schema if not exists extensions;
create extension if not exists pgcrypto schema extensions;

create or replace function public.claim_my_legacy_rows()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  me       uuid := auth.uid();
  email    text := nullif(current_setting('request.jwt.claims', true)::json->>'email', '');
  old_key  text;
  out      jsonb := '{}'::jsonb;
  n        int;
begin
  if me is null or email is null then
    return jsonb_build_object('error', 'not signed in');
  end if;

  -- Mirrors src/web_streamlit/auth.py: sha256 of the lower-cased, trimmed address, first 32 hex chars.
  old_key := substr(encode(extensions.digest(lower(btrim(email)), 'sha256'), 'hex'), 1, 32);

  -- ⚠️ `user_id is null` is what makes this safe to run twice: a row already claimed is not re-claimed, and
  -- a row claimed by somebody else is untouched. Re-running is a no-op, which matters because the app will
  -- call it on every sign-in until it stops finding anything.
  update public.squads set user_id = me where handle = old_key and user_id is null;
  get diagnostics n = row_count;  out := out || jsonb_build_object('squads', n);

  update public.user_prefs set user_id = me where legacy_key = old_key and user_id is null;
  get diagnostics n = row_count;  out := out || jsonb_build_object('user_prefs', n);

  update public.player_watchlist set user_id = me where legacy_key = old_key and user_id is null;
  get diagnostics n = row_count;  out := out || jsonb_build_object('player_watchlist', n);

  return out;
end;
$$;

revoke execute on function public.claim_my_legacy_rows() from public;
grant  execute on function public.claim_my_legacy_rows() to authenticated;
