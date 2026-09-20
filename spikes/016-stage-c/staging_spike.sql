-- ═══ Spike 016 — Stage C on STAGING. Safe to run, safe to re-run, easy to undo. ═══
--
-- ⚠️ **Touches nothing that exists.** Every table here is prefixed `c_`, so staging's real `squads`,
-- `user_prefs` and `player_watchlist` are untouched and the staging app keeps working exactly as it does now.
-- To undo the whole thing: the DROP block at the bottom of this file.
--
-- What it proves: that a **real Supabase JWT** — not a simulated one — makes owner-scoped RLS work, so one
-- signed-in person cannot read, overwrite or delete another's squad even knowing its exact key.

create table if not exists public.c_squads (
  user_id     uuid default auth.uid(),
  handle      text primary key,
  data        jsonb not null,
  updated_at  timestamptz not null default now()
);

create table if not exists public.c_user_prefs (
  user_id     uuid,
  legacy_key  text,
  manager_id  text,
  id          bigint generated always as identity primary key
);

-- ── The policies: one rule, four verbs — you may touch a row if you own it ────────────────────────────────
do $$
declare t text;
begin
  foreach t in array array['c_squads', 'c_user_prefs'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from anon, authenticated', t);
    execute format('grant select, insert, update, delete on public.%I to authenticated', t);

    execute format('drop policy if exists "own select" on public.%I', t);
    execute format('drop policy if exists "own insert" on public.%I', t);
    execute format('drop policy if exists "own update" on public.%I', t);
    execute format('drop policy if exists "own delete" on public.%I', t);

    execute format('create policy "own select" on public.%I for select to authenticated
                      using (user_id = auth.uid())', t);
    -- ⚠️ INSERT needs `with check`; `using` is ignored on an insert and would accept any claimed owner.
    execute format('create policy "own insert" on public.%I for insert to authenticated
                      with check (user_id = auth.uid())', t);
    -- ⚠️ UPDATE needs BOTH: `using` picks the rows you may edit, `with check` what they may become.
    -- Without the second you can edit your own row and hand it to someone else.
    execute format('create policy "own update" on public.%I for update to authenticated
                      using (user_id = auth.uid()) with check (user_id = auth.uid())', t);
    execute format('create policy "own delete" on public.%I for delete to authenticated
                      using (user_id = auth.uid())', t);
  end loop;
end $$;

-- ── The migration: claiming rows that already exist ───────────────────────────────────────────────────────
-- ⭐ Takes NO arguments. It derives the old key from the email inside the **verified** token, so an impostor
-- who knows the address cannot claim anything. Accepting it as a parameter would rebuild the hole.
create or replace function public.c_claim_my_legacy_rows()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  me uuid := auth.uid();
  email text := nullif(current_setting('request.jwt.claims', true)::json->>'email', '');
  old_key text; out jsonb := '{}'::jsonb; n int;
begin
  if me is null or email is null then return jsonb_build_object('error','not signed in'); end if;
  old_key := substr(encode(extensions.digest(lower(btrim(email)), 'sha256'), 'hex'), 1, 32);
  update public.c_squads set user_id = me where handle = old_key and user_id is null;
  get diagnostics n = row_count;  out := out || jsonb_build_object('squads', n);
  update public.c_user_prefs set user_id = me where legacy_key = old_key and user_id is null;
  get diagnostics n = row_count;  out := out || jsonb_build_object('user_prefs', n);
  return out;
end;
$$;
revoke execute on function public.c_claim_my_legacy_rows() from public;
grant  execute on function public.c_claim_my_legacy_rows() to authenticated;

-- ── A legacy row, exactly as one exists in production today: keyed by sha256(email), no owner ─────────────
insert into public.c_squads (user_id, handle, data)
values (null, 'd76280d790f8a88a3ee1537ff806ce90', '{"picks":[7,7,7],"note":"alice legacy squad"}')
on conflict (handle) do nothing;

-- ═══ TO UNDO EVERYTHING THIS FILE DID ═══
-- drop function if exists public.c_claim_my_legacy_rows();
-- drop table if exists public.c_squads, public.c_user_prefs;
