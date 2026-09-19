-- ═══ Stage A + Stage B — the production hardening, in one block ═══
-- Both halves were rehearsed on staging on 2026-09-19. See docs/SUPABASE_PRODUCTION_CUTOVER.md.
--
-- ⚠️ PREREQUISITES, both already true in production as of 2026-09-19:
--   1. sql/stage_b_functions_only.sql has been applied (the four functions exist), AND
--   2. FPL_ADMIN_STORE_KEY is set in Streamlit secrets, or the Admin roster goes blank.
--
-- ⭐ This file only REMOVES access. The functions the app depends on are created by stage_b.sql /
--    stage_b_functions_only.sql — never by this one, so running it out of order cannot 404 the gate.

-- ── A1. beta_waitlist: emails go in, nothing comes out ───────────────────────────────────────────────────
-- ⚠️ Requires the plain-INSERT change in waitlist.py (already deployed). An upsert needs a permissive SELECT
-- policy — ON CONFLICT must read the conflicting row — so an upsert and a locked read are mutually exclusive.
revoke all on public.beta_waitlist from anon, authenticated;
grant insert on public.beta_waitlist to anon;

alter table public.beta_waitlist enable row level security;

drop policy if exists "waitlist insert"        on public.beta_waitlist;
drop policy if exists "waitlist upsert-update" on public.beta_waitlist;

create policy "waitlist insert" on public.beta_waitlist
  for insert to anon with check (true);

-- ── A2. maddie_videos: public read is correct; writable is not ───────────────────────────────────────────
revoke all on public.maddie_videos from anon, authenticated;
grant select on public.maddie_videos to anon;

alter table public.maddie_videos enable row level security;
drop policy if exists "maddie_videos public read" on public.maddie_videos;
create policy "maddie_videos public read" on public.maddie_videos
  for select to anon using (true);

-- ── B. beta_users: the app asks the functions, never the table ───────────────────────────────────────────
-- ⚠️ After this, anything still reading beta_users with the anon key breaks. That is the Admin roster, which
-- is why FPL_ADMIN_STORE_KEY has to be set FIRST.
revoke all on public.beta_users from anon, authenticated;
